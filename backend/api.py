from fastapi import APIRouter, FastAPI, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from typing import AsyncGenerator, Dict
import uuid
import asyncio
from datetime import datetime

# Import Pydantic models
from .models import (
    ProcessImageResponse,
    SolveResponse,
    ProgressEvent,
    PuzzleGrid,
    GridCell,
)

# Import solver functions
from .solver import main_solver
from .utils import is_grid_solved

router = APIRouter()

# In-memory storage for solving sessions
# In production, use Redis or similar
solving_sessions: Dict[str, Dict] = {}


# ---------------------------------------------------------------------------
# Endpoint: POST /api/process-image
# ---------------------------------------------------------------------------
@router.post(
    "/api/process-image",
    response_model=ProcessImageResponse,
    status_code=status.HTTP_200_OK,
    summary="Process uploaded puzzle image and extract grid",
    description=(
        "Accepts an image file containing a Numbers Sum puzzle grid, processes it using OCR/AI to "
        "extract the grid structure, numbers, and constraints. Returns the extracted ``PuzzleGrid``."
    ),
)
async def process_image(image: UploadFile = File(...)) -> ProcessImageResponse:
    """Process an uploaded image and return the extracted puzzle grid.

    Args:
        image: Uploaded image file (JPG, PNG, JPEG).

    Returns:
        ProcessImageResponse: Contains the ``PuzzleGrid`` extracted from the image.

    Raises:
        HTTPException: If the image format is unsupported or processing fails.
    """
    # Validate file type
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image (JPG, PNG, JPEG)",
        )

    try:
        # Read image bytes
        image_bytes = await image.read()

        # Extract grid using OCR
        from .ocr import extract_puzzle_from_bytes

        grid = extract_puzzle_from_bytes(image_bytes)

        return ProcessImageResponse(grid=grid)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not extract puzzle from image: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {str(e)}",
        )



# ---------------------------------------------------------------------------
# Endpoint: POST /api/solve
# ---------------------------------------------------------------------------
@router.post(
    "/api/solve",
    response_model=SolveResponse,
    status_code=status.HTTP_200_OK,
    summary="Initiate solving of a puzzle grid",
    description=(
        "Starts the solving process for a given puzzle grid and returns a unique solving session ID "
        "that can be used to stream progress updates via SSE."
    ),
)
async def solve_puzzle(grid: PuzzleGrid) -> SolveResponse:
    """Start solving the provided puzzle grid.

    Args:
        grid: The ``PuzzleGrid`` representing the puzzle to solve.

    Returns:
        SolveResponse: Contains a UUID ``solvingId`` identifying the solving session.

    Raises:
        HTTPException: If the grid is invalid or has contradictory constraints.
    """
    # Validate grid has cells and constraints
    if not grid.cells or not grid.constraints:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Grid must have cells and constraints",
        )

    # Create solving session
    solving_id = str(uuid.uuid4())
    solving_sessions[solving_id] = {
        "grid": grid,
        "status": "pending",
        "created_at": datetime.now(),
        "progress": [],
    }

    # Start solving in background
    asyncio.create_task(solve_in_background(solving_id, grid))

    return SolveResponse(solvingId=solving_id)


async def solve_in_background(solving_id: str, grid: PuzzleGrid) -> None:
    """Solve the puzzle in the background and store progress updates.

    Args:
        solving_id: The solving session ID.
        grid: The puzzle grid to solve.
    """
    try:
        solving_sessions[solving_id]["status"] = "solving"

        # Solve the puzzle with iteration tracking
        iteration = 0
        max_iterations = 100

        while iteration < max_iterations:
            # Check if already solved
            if is_grid_solved(grid):
                solving_sessions[solving_id]["status"] = "complete"
                solving_sessions[solving_id]["final_grid"] = grid
                break

            # Save state before solving
            grid_before = grid.model_copy(deep=True)

            # Apply one iteration of solving
            from .solver import solve_by_elimination_and_selection

            grid = solve_by_elimination_and_selection(grid)

            # Check if we made progress
            from .utils import has_grid_changed

            if not has_grid_changed(grid_before, grid):
                # Stuck - no more progress
                solving_sessions[solving_id]["status"] = "stuck"
                solving_sessions[solving_id]["final_grid"] = grid
                break

            # Store progress update
            solving_sessions[solving_id]["progress"].append(
                {"iteration": iteration, "grid": grid.model_copy(deep=True)}
            )

            # Small delay to make progress visible
            await asyncio.sleep(0.1)

            iteration += 1

        # If we hit max iterations
        if iteration >= max_iterations:
            solving_sessions[solving_id]["status"] = "max_iterations"
            solving_sessions[solving_id]["final_grid"] = grid

    except Exception as e:
        solving_sessions[solving_id]["status"] = "error"
        solving_sessions[solving_id]["error"] = str(e)


# ---------------------------------------------------------------------------
# Endpoint: GET /api/solve-stream/{solving_id}
# ---------------------------------------------------------------------------
@router.get(
    "/api/solve-stream/{solving_id}",
    response_class=StreamingResponse,
    summary="Stream real‑time solving progress via Server‑Sent Events",
    description=(
        "Provides a Server‑Sent Events (SSE) stream that emits progress updates, completion, "
        "or error events for the solving session identified by ``solving_id``."
    ),
)
async def solve_stream(solving_id: str) -> StreamingResponse:
    """Stream solving progress for a given session ID.

    Args:
        solving_id: UUID returned by the ``/api/solve`` endpoint.

    Returns:
        StreamingResponse: SSE stream of ``ProgressEvent`` objects.

    Raises:
        HTTPException: If the solving session is not found.
    """
    if solving_id not in solving_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Solving session {solving_id} not found",
        )

    async def event_generator() -> AsyncGenerator[bytes, None]:
        """Yield SSE‑formatted events as the solver progresses."""
        session = solving_sessions[solving_id]
        last_progress_index = 0

        while True:
            # Send any new progress updates
            progress_list = session.get("progress", [])
            while last_progress_index < len(progress_list):
                progress_item = progress_list[last_progress_index]
                event = ProgressEvent(
                    type="progress",
                    cells=progress_item["grid"].cells,
                )
                sse_data = f"data: {event.model_dump_json()}\n\n"
                yield sse_data.encode("utf-8")
                last_progress_index += 1

            # Check if solving is complete
            status_val = session.get("status")

            if status_val == "complete":
                final_grid = session.get("final_grid")
                event = ProgressEvent(
                    type="complete",
                    cells=final_grid.cells if final_grid else [],
                )
                sse_data = f"data: {event.model_dump_json()}\n\n"
                yield sse_data.encode("utf-8")
                break

            elif status_val in ["stuck", "max_iterations"]:
                final_grid = session.get("final_grid")
                message = (
                    "Solver got stuck - partial solution returned"
                    if status_val == "stuck"
                    else "Max iterations reached - partial solution returned"
                )
                event = ProgressEvent(
                    type="complete",
                    cells=final_grid.cells if final_grid else [],
                    message=message,
                )
                sse_data = f"data: {event.model_dump_json()}\n\n"
                yield sse_data.encode("utf-8")
                break

            elif status_val == "error":
                error_msg = session.get("error", "Unknown error occurred")
                event = ProgressEvent(
                    type="error",
                    cells=[],
                    message=error_msg,
                )
                sse_data = f"data: {event.model_dump_json()}\n\n"
                yield sse_data.encode("utf-8")
                break

            # Wait a bit before checking again
            await asyncio.sleep(0.05)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Optional Test Endpoints (mock implementations)
# ---------------------------------------------------------------------------
@router.post(
    "/api/test/mock-process",
    response_model=ProcessImageResponse,
    status_code=status.HTTP_200_OK,
    summary="Mock image processing for testing",
)
async def mock_process_image() -> ProcessImageResponse:
    """Return a static ``PuzzleGrid`` without performing any image processing.

    Useful for frontend development and UI testing.

    Returns:
        ProcessImageResponse: Contains a mock puzzle grid.
    """
    from .models import Constraint

    # Create a simple 2x2 test grid
    mock_cells = [
        [
            GridCell(row=0, col=0, value=1, isSelected=None),
            GridCell(row=0, col=1, value=2, isSelected=None),
        ],
        [
            GridCell(row=1, col=0, value=3, isSelected=None),
            GridCell(row=1, col=1, value=4, isSelected=None),
        ],
    ]

    mock_constraints = [
        Constraint(type="row", index=0, sum=3, is_satisfied=False),
        Constraint(type="row", index=1, sum=7, is_satisfied=False),
        Constraint(type="column", index=0, sum=4, is_satisfied=False),
        Constraint(type="column", index=1, sum=6, is_satisfied=False),
    ]

    mock_grid = PuzzleGrid(cells=mock_cells, constraints=mock_constraints)
    return ProcessImageResponse(grid=mock_grid)


@router.post(
    "/api/test/mock-solve",
    response_model=SolveResponse,
    status_code=status.HTTP_200_OK,
    summary="Mock solving with artificial delay for UI testing",
)
async def mock_solve_puzzle(grid: PuzzleGrid) -> SolveResponse:
    """Simulate solving with a delay, returning a fake solving ID.

    The client can then connect to ``/api/solve-stream`` to receive dummy progress events.

    Args:
        grid: The puzzle grid (not actually solved in mock mode).

    Returns:
        SolveResponse: Contains a mock solving ID.
    """
    solving_id = str(uuid.uuid4())
    return SolveResponse(solvingId=solving_id)


# ---------------------------------------------------------------------------
# FastAPI application instance (optional – can be imported elsewhere)
# ---------------------------------------------------------------------------
app = FastAPI(title="Numbers Sum Solver API", version="0.1.0")
app.include_router(router)
