from fastapi import APIRouter, FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from typing import AsyncGenerator, Dict
import uuid
import asyncio
import logging
from asyncio import Lock
from datetime import datetime

from .models import (
    ProcessImageResponse,
    SolveResponse,
    ProgressEvent,
    PuzzleGrid,
    GridCell,
)
from .utils import is_grid_solved
from .ocr import extract_puzzle_from_bytes
from .config import (
    MAX_SOLVER_ITERATIONS,
    SOLVER_ITERATION_DELAY,
    SSE_POLL_INTERVAL,
    SESSION_TIMEOUT,
    SESSION_CLEANUP_INTERVAL,
)

logger = logging.getLogger(__name__)

router = APIRouter()

solving_sessions: Dict[str, Dict] = {}
session_lock = Lock()


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
        logger.info(f"Processing uploaded image: {image.filename}")
        image_bytes = await image.read()

        grid = extract_puzzle_from_bytes(image_bytes)
        logger.info(f"Successfully extracted grid with {len(grid.cells)} rows")

        return ProcessImageResponse(grid=grid)

    except ValueError as e:
        logger.error(f"Failed to extract puzzle from image: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not extract puzzle from image: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error processing image: {e}", exc_info=True)
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
    if not grid.cells or not grid.constraints:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Grid must have cells and constraints",
        )

    if any(len(row) == 0 for row in grid.cells):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Grid must not contain empty rows",
        )

    num_rows = len(grid.cells)
    num_cols = len(grid.cells[0]) if grid.cells else 0

    for constraint in grid.constraints:
        if constraint.type == "row" and constraint.index >= num_rows:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Row constraint index {constraint.index} out of bounds (grid has {num_rows} rows)",
            )
        if constraint.type == "column" and constraint.index >= num_cols:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Column constraint index {constraint.index} out of bounds (grid has {num_cols} columns)",
            )

    logger.info(f"Starting solve for grid with {num_rows}x{num_cols} cells")

    solving_id = str(uuid.uuid4())
    
    async with session_lock:
        solving_sessions[solving_id] = {
            "grid": grid,
            "status": "pending",
            "created_at": datetime.now(),
            "progress": [],
        }

    task = asyncio.create_task(solve_in_background(solving_id, grid))
    task.add_done_callback(lambda t: _handle_task_exception(t, solving_id))
    
    logger.info(f"Created solving session {solving_id}")

    return SolveResponse(solvingId=solving_id)


def _handle_task_exception(task: asyncio.Task, solving_id: str) -> None:
    """Handle exceptions from background solving tasks.

    Args:
        task: The completed asyncio Task.
        solving_id: The solving session ID.
    """
    try:
        task.result()
    except Exception as e:
        logger.error(f"Background task for session {solving_id} failed: {e}", exc_info=True)


async def solve_in_background(solving_id: str, grid: PuzzleGrid) -> None:
    """Solve the puzzle in the background and store progress updates.

    Args:
        solving_id: The solving session ID.
        grid: The puzzle grid to solve.
    """
    try:
        logger.info(f"Starting background solving for session {solving_id}")
        async with session_lock:
            solving_sessions[solving_id]["status"] = "solving"

        iteration = 0

        while iteration < MAX_SOLVER_ITERATIONS:
            if is_grid_solved(grid):
                async with session_lock:
                    solving_sessions[solving_id]["status"] = "complete"
                    solving_sessions[solving_id]["final_grid"] = grid
                logger.info(f"Session {solving_id} completed successfully after {iteration} iterations")
                break

            # Save state before solving
            grid_before = grid.model_copy(deep=True)

            # Apply one iteration of solving
            from .solver import solve_by_elimination_and_selection

            grid = solve_by_elimination_and_selection(grid)

            from .utils import has_grid_changed

            if not has_grid_changed(grid_before, grid):
                async with session_lock:
                    solving_sessions[solving_id]["status"] = "stuck"
                    solving_sessions[solving_id]["final_grid"] = grid
                logger.warning(f"Session {solving_id} stuck after {iteration} iterations")
                break

            async with session_lock:
                solving_sessions[solving_id]["progress"].append(
                    {"iteration": iteration, "grid": grid.model_copy(deep=True)}
                )

            await asyncio.sleep(SOLVER_ITERATION_DELAY)

            iteration += 1

        if iteration >= MAX_SOLVER_ITERATIONS:
            async with session_lock:
                solving_sessions[solving_id]["status"] = "max_iterations"
                solving_sessions[solving_id]["final_grid"] = grid
            logger.warning(f"Session {solving_id} reached max iterations ({MAX_SOLVER_ITERATIONS})")

    except Exception as e:
        logger.error(f"Error in solving session {solving_id}: {e}", exc_info=True)
        async with session_lock:
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
    async with session_lock:
        if solving_id not in solving_sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Solving session {solving_id} not found",
            )
    
    logger.info(f"Starting SSE stream for session {solving_id}")

    async def event_generator() -> AsyncGenerator[bytes, None]:
        """Yield SSE‑formatted events as the solver progresses."""
        last_progress_index = 0

        while True:
            async with session_lock:
                session = solving_sessions.get(solving_id)
                if not session:
                    logger.warning(f"Session {solving_id} disappeared during streaming")
                    break
                
                progress_list = session.get("progress", [])
                status_val = session.get("status")
            while last_progress_index < len(progress_list):
                progress_item = progress_list[last_progress_index]
                event = ProgressEvent(
                    type="progress",
                    cells=progress_item["grid"].cells,
                )
                sse_data = f"data: {event.model_dump_json()}\n\n"
                yield sse_data.encode("utf-8")
                last_progress_index += 1

            if status_val == "complete":
                async with session_lock:
                    final_grid = session.get("final_grid")
                event = ProgressEvent(
                    type="complete",
                    cells=final_grid.cells if final_grid else [],
                )
                sse_data = f"data: {event.model_dump_json()}\n\n"
                yield sse_data.encode("utf-8")
                logger.info(f"Completed SSE stream for session {solving_id}")
                break

            elif status_val in ["stuck", "max_iterations"]:
                async with session_lock:
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
                logger.warning(f"Partial completion for session {solving_id}: {status_val}")
                break

            elif status_val == "error":
                async with session_lock:
                    error_msg = session.get("error", "Unknown error occurred")
                event = ProgressEvent(
                    type="error",
                    cells=[],
                    message=error_msg,
                )
                sse_data = f"data: {event.model_dump_json()}\n\n"
                yield sse_data.encode("utf-8")
                logger.error(f"Error in SSE stream for session {solving_id}: {error_msg}")
                break

            await asyncio.sleep(SSE_POLL_INTERVAL)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


async def cleanup_old_sessions() -> None:
    """Remove sessions older than SESSION_TIMEOUT to prevent memory leaks.
    
    Runs periodically in the background to clean up expired solving sessions.
    """
    while True:
        await asyncio.sleep(SESSION_CLEANUP_INTERVAL)
        current_time = datetime.now()
        
        async with session_lock:
            expired = [
                sid for sid, data in solving_sessions.items()
                if current_time - data["created_at"] > SESSION_TIMEOUT
            ]
            for sid in expired:
                del solving_sessions[sid]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")


app = FastAPI(title="Numbers Sum Solver API", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize background tasks on application startup."""
    asyncio.create_task(cleanup_old_sessions())
    logger.info("Started session cleanup background task")
