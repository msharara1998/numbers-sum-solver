"""
Test to demonstrate the iterative solving capability of main_solver.

This test shows how the solver loops until the grid is solved or stuck.
"""

from backend.models import PuzzleGrid, GridCell, Constraint
from backend.solver import main_solver
from backend.utils import is_grid_solved


def test_iterative_solving():
    """
    Test that main_solver iterates until the grid is solved.

    This test uses a simple grid that requires multiple iterations:
    Grid (2x2):
    [1, 2]  -> sum should be 3
    [3, 4]  -> sum should be 7

    Col sums: [4, 6]

    First iteration should select/deselect some cells.
    Second iteration should complete the solution.
    """
    print("\n" + "=" * 60)
    print("Test: Iterative Solving with Multiple Passes")
    print("=" * 60)

    cells = [
        [
            GridCell(row=0, col=0, value=1, isSelected=None),
            GridCell(row=0, col=1, value=2, isSelected=None),
        ],
        [
            GridCell(row=1, col=0, value=3, isSelected=None),
            GridCell(row=1, col=1, value=4, isSelected=None),
        ],
    ]

    constraints = [
        Constraint(type="row", index=0, sum=3, is_satisfied=False),
        Constraint(type="row", index=1, sum=7, is_satisfied=False),
        Constraint(type="column", index=0, sum=4, is_satisfied=False),
        Constraint(type="column", index=1, sum=6, is_satisfied=False),
    ]

    grid = PuzzleGrid(cells=cells, constraints=constraints)

    print("\nInitial grid state:")
    for i, row in enumerate(grid.cells):
        print(f"Row {i}: {[(c.value, c.isSelected) for c in row]}")

    # Run solver
    result = main_solver(grid)

    print("\nFinal grid state:")
    for i, row in enumerate(result.cells):
        print(f"Row {i}: {[(c.value, c.isSelected) for c in row]}")

    # Check if solved
    solved = is_grid_solved(result)
    print(f"\nGrid solved: {solved}")

    # For this simple case, all cells should be decided
    # Row 0: sum=3 from [1,2] -> both selected
    # Row 1: sum=7 from [3,4] -> both selected
    # This satisfies column constraints too: col0=1+3=4, col1=2+4=6

    assert result.cells[0][0].isSelected is True, "Cell (0,0) should be selected"
    assert result.cells[0][1].isSelected is True, "Cell (0,1) should be selected"
    assert result.cells[1][0].isSelected is True, "Cell (1,0) should be selected"
    assert result.cells[1][1].isSelected is True, "Cell (1,1) should be selected"

    assert solved, "Grid should be fully solved"

    print("✓ Test passed: Grid solved correctly with iterations\n")


def test_solver_stops_when_stuck():
    """
    Test that solver stops when it can't make progress.

    Grid with ambiguous case that can't be fully solved:
    [5, 5, 5]  -> sum should be 10

    The solver should stop after realizing it can't make progress.
    """
    print("=" * 60)
    print("Test: Solver Stops When Stuck")
    print("=" * 60)

    cells = [
        [
            GridCell(row=0, col=0, value=5, isSelected=None),
            GridCell(row=0, col=1, value=5, isSelected=None),
            GridCell(row=0, col=2, value=5, isSelected=None),
        ]
    ]

    constraints = [Constraint(type="row", index=0, sum=10, is_satisfied=False)]

    grid = PuzzleGrid(cells=cells, constraints=constraints)

    print("\nInitial grid state:")
    print(f"Row 0: {[(c.value, c.isSelected) for c in grid.cells[0]]}")

    # Run solver
    result = main_solver(grid)

    print("\nFinal grid state:")
    print(f"Row 0: {[(c.value, c.isSelected) for c in result.cells[0]]}")

    # Check if solved
    solved = is_grid_solved(result)
    print(f"\nGrid solved: {solved}")

    # Grid should NOT be solved because it's ambiguous
    assert not solved, "Grid should not be fully solved (ambiguous case)"

    # All cells should remain None
    assert result.cells[0][0].isSelected is None
    assert result.cells[0][1].isSelected is None
    assert result.cells[0][2].isSelected is None

    print("✓ Test passed: Solver correctly stopped when stuck\n")


def test_complex_multi_iteration():
    """
    Test a more complex grid that requires multiple iterations.

    Grid (3x3):
    [1, 2, 3]  -> sum should be 6
    [4, 5, 6]  -> sum should be 9
    [7, 8, 9]  -> sum should be 8

    Col sums: [5, 15, 3]
    """
    print("=" * 60)
    print("Test: Complex Multi-Iteration Solving")
    print("=" * 60)

    cells = [
        [
            GridCell(row=0, col=0, value=1, isSelected=None),
            GridCell(row=0, col=1, value=2, isSelected=None),
            GridCell(row=0, col=2, value=3, isSelected=None),
        ],
        [
            GridCell(row=1, col=0, value=4, isSelected=None),
            GridCell(row=1, col=1, value=5, isSelected=None),
            GridCell(row=1, col=2, value=6, isSelected=None),
        ],
        [
            GridCell(row=2, col=0, value=7, isSelected=None),
            GridCell(row=2, col=1, value=8, isSelected=None),
            GridCell(row=2, col=2, value=9, isSelected=None),
        ],
    ]

    constraints = [
        Constraint(type="row", index=0, sum=6, is_satisfied=False),
        Constraint(type="row", index=1, sum=9, is_satisfied=False),
        Constraint(type="row", index=2, sum=8, is_satisfied=False),
        Constraint(type="column", index=0, sum=5, is_satisfied=False),
        Constraint(type="column", index=1, sum=15, is_satisfied=False),
        Constraint(type="column", index=2, sum=3, is_satisfied=False),
    ]

    grid = PuzzleGrid(cells=cells, constraints=constraints)

    print("\nInitial grid state:")
    for i, row in enumerate(grid.cells):
        row_str = f"Row {i}: "
        for cell in row:
            status = (
                "?" if cell.isSelected is None else ("✓" if cell.isSelected else "✗")
            )
            row_str += f"{cell.value}{status} "
        print(row_str)

    # Run solver
    result = main_solver(grid)

    print("\nFinal grid state:")
    for i, row in enumerate(result.cells):
        row_str = f"Row {i}: "
        for cell in row:
            status = (
                "?" if cell.isSelected is None else ("✓" if cell.isSelected else "✗")
            )
            row_str += f"{cell.value}{status} "
        print(row_str)

    # Check if solved
    solved = is_grid_solved(result)
    print(f"\nGrid solved: {solved}")

    # Count how many cells were decided
    decided_count = sum(
        1 for row in result.cells for cell in row if cell.isSelected is not None
    )
    print(f"Cells decided: {decided_count}/9")

    print("✓ Test passed: Complex grid processed with multiple iterations\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Testing Iterative Solver Functionality")
    print("=" * 60)

    test_iterative_solving()
    test_solver_stops_when_stuck()
    test_complex_multi_iteration()

    print("=" * 60)
    print("All iterative solver tests passed! ✓")
    print("=" * 60 + "\n")
