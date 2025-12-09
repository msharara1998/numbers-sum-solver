from __future__ import annotations

from typing import List, Optional, Literal

from pydantic import BaseModel, Field


class GridCell(BaseModel):
    """Represents a single cell in the puzzle grid.

    Attributes:
        value: The numeric value of the cell, or ``None`` if empty.
        isSelected: Selection state: True=selected, False=deselected, None=unchanged.
        row: Zero‑based row index.
        col: Zero‑based column index.
    """

    value: Optional[int] = Field(
        default=None, description="The number in the cell, null if empty"
    )
    isSelected: Optional[bool] = Field(
        default=None,
        description="Selection state: True=selected, False=deselected, None=unchanged",
    )
    row: int = Field(..., description="Row index (0‑based)")
    col: int = Field(..., description="Column index (0‑based)")


class Constraint(BaseModel):
    """Sum constraint for a row or column.

    Attributes:
        type: ``"row"`` or ``"column"`` indicating which dimension the constraint applies to.
        index: Zero‑based index of the row/column.
        sum: Target sum for the specified row/column.
    """

    type: Literal["row", "column"] = Field(..., description="Type of constraint")
    index: int = Field(..., description="Which row/column (0‑based)")
    sum: int = Field(..., description="Target sum for that row/column")
    is_satisfied: Optional[bool] = Field(
        default=False,
        description="Whether the constraint is satisfied (True) or not (False)",
    )


class PuzzleGrid(BaseModel):
    """Full representation of a puzzle grid.

    Attributes:
        cells: 2‑D array of ``GridCell`` objects.
        constraints: List of ``Constraint`` objects.
    """

    cells: List[List[GridCell]] = Field(..., description="2‑D array of cells")
    constraints: List[Constraint] = Field(..., description="Array of sum constraints")


class ProcessImageResponse(BaseModel):
    """Response payload for ``POST /api/process-image``.

    Contains the extracted ``PuzzleGrid``.
    """

    grid: PuzzleGrid


class SolveResponse(BaseModel):
    """Response payload for ``POST /api/solve``.

    Returns a UUID that identifies the solving session.
    """

    solvingId: str = Field(
        ..., description="Unique identifier for the solving session (UUID)"
    )


class ProgressEvent(BaseModel):
    """Structure of events streamed from ``GET /api/solve-stream``.

    ``type`` can be ``"progress"``, ``"complete"`` or ``"error"``.
    ``cells`` holds the current grid state.
    ``message`` is optional and only present for error events.
    """

    type: Literal["progress", "complete", "error"]
    cells: List[List[GridCell]]
    message: Optional[str] = None
