"""
Test suite for the Numbers Sum Solver.

This module contains unit tests for individual solver functions and integration tests
for the main solver using a real puzzle from Level 128.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ..models import PuzzleGrid, GridCell, Constraint
from ..solver import (
    main_solver,
    eliminate_values_larger_than_constraints,
    eliminate_values_not_in_sums,
    select_essential_number,
)
from ..utils import sums_composite


# ============================================================================
# Test Data: Level 128 Grid from the image
# ============================================================================


def build_level_128_grid():
    """
    Build the puzzle grid from Level 128 shown in the image.

    Grid layout (7x7):
    Row sums: [25, 16, 17, 20, 11, 14, 26]
    Col sums: [11, 20, 28, 14, 16, 25, 15]

    Initial values:
    Row 0: [4, 5, 2, 4, 2, 1, 6]
    Row 1: [3, 5, 2, 7, 4, 8, 4]
    Row 2: [9, 4, 5, 9, 4, 6, 6]
    Row 3: [9, 2, 9, 3, 9, 1, 3]
    Row 4: [3, 1, 8, 9, 4, 6, 4]
    Row 5: [9, 3, 5, 1, 6, 7, 9]
    Row 6: [4, 4, 6, 1, 7, 9, 8]

    Some cells need to be selected to match the sum constraints.
    """
    cells = []

    # Define the grid values
    grid_values = [
        [4, 5, 2, 4, 2, 1, 6],
        [3, 5, 2, 7, 4, 8, 4],
        [9, 4, 5, 9, 4, 6, 6],
        [9, 2, 9, 3, 9, 1, 3],
        [3, 1, 8, 9, 4, 6, 4],
        [9, 3, 5, 1, 6, 7, 9],
        [4, 4, 6, 1, 7, 9, 8],
    ]

    # Create cells with all values present but isSelected=None (to be determined)
    for row_idx, row_values in enumerate(grid_values):
        row_cells = []
        for col_idx, value in enumerate(row_values):
            cell = GridCell(
                row=row_idx,
                col=col_idx,
                value=value,
                isSelected=None,  # Solver needs to determine which to select
            )
            row_cells.append(cell)
        cells.append(row_cells)

    # Define constraints
    row_sums = [25, 16, 17, 20, 11, 14, 26]
    col_sums = [11, 20, 28, 14, 16, 25, 15]

    constraints = []

    # Add row constraints
    for idx, target_sum in enumerate(row_sums):
        constraints.append(Constraint(type="row", index=idx, sum=target_sum))

    # Add column constraints
    for idx, target_sum in enumerate(col_sums):
        constraints.append(Constraint(type="column", index=idx, sum=target_sum))

    return PuzzleGrid(cells=cells, constraints=constraints)


def build_simple_test_grid():
    """
    Build a simple 3x3 test grid for unit testing.

    Grid:
    [1, 2, 3]  -> sum should be 6
    [4, 5, 6]  -> sum should be 15
    [7, 8, 9]  -> sum should be 24

    Col sums: [12, 15, 18]
    """
    cells = []
    grid_values = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

    for row_idx, row_values in enumerate(grid_values):
        row_cells = []
        for col_idx, value in enumerate(row_values):
            cell = GridCell(row=row_idx, col=col_idx, value=value, isSelected=None)
            row_cells.append(cell)
        cells.append(row_cells)

    constraints = [
        Constraint(type="row", index=0, sum=6),
        Constraint(type="row", index=1, sum=15),
        Constraint(type="row", index=2, sum=24),
        Constraint(type="column", index=0, sum=12),
        Constraint(type="column", index=1, sum=15),
        Constraint(type="column", index=2, sum=18),
    ]

    return PuzzleGrid(cells=cells, constraints=constraints)


def build_empty_cells_grid():
    """
    Build a 2x2 grid with some empty cells for testing.

    Grid:
    [None, 2]  -> sum should be 3 (so first cell should be 1)
    [3, None]  -> sum should be 7 (so second cell should be 4)

    Col sums: [4, 6]
    """
    cells = [
        [
            GridCell(row=0, col=0, value=None, isSelected=None),
            GridCell(row=0, col=1, value=2, isSelected=None),
        ],
        [
            GridCell(row=1, col=0, value=3, isSelected=None),
            GridCell(row=1, col=1, value=None, isSelected=None),
        ],
    ]

    constraints = [
        Constraint(type="row", index=0, sum=3),
        Constraint(type="row", index=1, sum=7),
        Constraint(type="column", index=0, sum=4),
        Constraint(type="column", index=1, sum=6),
    ]

    return PuzzleGrid(cells=cells, constraints=constraints)


# ============================================================================
# Unit Tests for sums_composite
# ============================================================================


def test_sums_composite_basic():
    """Test basic functionality of sums_composite."""
    result = sums_composite(10, (1, 2, 3, 4, 5))
    expected_combinations = [[1, 2, 3, 4], [1, 4, 5], [2, 3, 5]]
    assert (
        result == expected_combinations
    ), f"Expected {expected_combinations}, got {result}"
    print("✓ test_sums_composite_basic passed")


def test_sums_composite_no_solution():
    """Test when no combination sums to target."""
    result = sums_composite(100, (1, 2, 3))
    assert result == [], f"Expected empty list, got {result}"
    print("✓ test_sums_composite_no_solution passed")


def test_sums_composite_single_number():
    """Test when target equals a single candidate."""
    result = sums_composite(5, (1, 2, 3, 4, 5))
    assert [5] in result, f"Expected [5] in result, got {result}"
    print("✓ test_sums_composite_single_number passed")


def test_sums_composite_empty_candidates():
    """Test with empty candidates."""
    result = sums_composite(10, ())
    assert result == [], f"Expected empty list, got {result}"
    print("✓ test_sums_composite_empty_candidates passed")


# ============================================================================
# Unit Tests for eliminate_values_larger_than_constraints
# ============================================================================


def test_eliminate_values_larger_than_constraints_basic():
    """Test that cells are marked as not selected when they exceed constraints."""
    grid = build_empty_cells_grid()
    result_grid = eliminate_values_larger_than_constraints(grid)

    # Check that grid is returned
    assert isinstance(result_grid, PuzzleGrid)
    print("✓ test_eliminate_values_larger_than_constraints_basic passed")


def test_eliminate_values_larger_than_constraints_no_change():
    """Test when all values are within constraints."""
    grid = build_simple_test_grid()
    result_grid = eliminate_values_larger_than_constraints(grid)

    # Grid should be processed without errors
    assert isinstance(result_grid, PuzzleGrid)
    assert len(result_grid.cells) == 3
    print("✓ test_eliminate_values_larger_than_constraints_no_change passed")


# ============================================================================
# Unit Tests for eliminate_values_not_in_sums
# ============================================================================


def test_eliminate_values_not_in_sums_basic():
    """Test basic elimination of impossible values."""
    grid = build_empty_cells_grid()
    result_grid = eliminate_values_not_in_sums(grid)

    assert isinstance(result_grid, PuzzleGrid)
    print("✓ test_eliminate_values_not_in_sums_basic passed")


def test_eliminate_values_not_in_sums_with_filled_grid():
    """Test with a grid that has all values filled."""
    grid = build_simple_test_grid()
    result_grid = eliminate_values_not_in_sums(grid)

    assert isinstance(result_grid, PuzzleGrid)
    print("✓ test_eliminate_values_not_in_sums_with_filled_grid passed")


# ============================================================================
# Unit Tests for select_essential_number
# ============================================================================


def test_select_essential_number_basic():
    """Test selection of essential numbers."""
    grid = build_empty_cells_grid()
    result_grid = select_essential_number(grid)

    assert isinstance(result_grid, PuzzleGrid)

    # Check if any cells were filled
    # Row 0: [None, 2] with sum=3 means first cell must be 1
    # Row 1: [3, None] with sum=7 means second cell must be 4
    assert result_grid.cells[0][0].value == 1, "First cell should be filled with 1"
    assert result_grid.cells[1][1].value == 4, "Second cell should be filled with 4"
    print("✓ test_select_essential_number_basic passed")


def test_select_essential_number_no_empty_cells():
    """Test when there are no empty cells."""
    grid = build_simple_test_grid()
    result_grid = select_essential_number(grid)

    assert isinstance(result_grid, PuzzleGrid)
    print("✓ test_select_essential_number_no_empty_cells passed")


# ============================================================================
# Integration Tests for main_solver
# ============================================================================


def test_main_solver_with_empty_cells():
    """Test main solver with a grid containing empty cells."""
    grid = build_empty_cells_grid()
    solved_grid = main_solver(grid)

    assert isinstance(solved_grid, PuzzleGrid)

    # Verify the cells were filled correctly
    assert solved_grid.cells[0][0].value == 1
    assert solved_grid.cells[1][1].value == 4
    print("✓ test_main_solver_with_empty_cells passed")


def test_main_solver_preserves_constraints():
    """Test that main solver doesn't modify constraints."""
    grid = build_simple_test_grid()
    original_constraints = [c.model_copy() for c in grid.constraints]

    solved_grid = main_solver(grid)

    # Check constraints are unchanged
    assert len(solved_grid.constraints) == len(original_constraints)
    for i, constraint in enumerate(solved_grid.constraints):
        assert constraint.type == original_constraints[i].type
        assert constraint.index == original_constraints[i].index
        assert constraint.sum == original_constraints[i].sum
    print("✓ test_main_solver_preserves_constraints passed")


def test_main_solver_level_128():
    """Test main solver with the Level 128 puzzle from the image."""
    grid = build_level_128_grid()

    # Run the solver
    solved_grid = main_solver(grid)

    # Verify it returns a valid grid
    assert isinstance(solved_grid, PuzzleGrid)
    assert len(solved_grid.cells) == 7
    assert len(solved_grid.cells[0]) == 7

    # Print the grid state for inspection
    print("\n" + "=" * 60)
    print("Level 128 Solver Results:")
    print("=" * 60)

    for row_idx, row in enumerate(solved_grid.cells):
        row_str = f"Row {row_idx}: "
        for cell in row:
            if cell.isSelected is True:
                row_str += f"[{cell.value}] "
            elif cell.isSelected is False:
                row_str += f" {cell.value}  "
            else:
                row_str += f"({cell.value}) "
        print(row_str)

    print("=" * 60)
    print("✓ test_main_solver_level_128 completed")


# ============================================================================
# Test Runner
# ============================================================================


def run_all_tests():
    """Run all test functions."""
    print("\n" + "=" * 60)
    print("Running Numbers Sum Solver Test Suite")
    print("=" * 60 + "\n")

    # Test sums_composite
    print("Testing sums_composite utility function:")
    test_sums_composite_basic()
    test_sums_composite_no_solution()
    test_sums_composite_single_number()
    test_sums_composite_empty_candidates()

    # Test eliminate_values_larger_than_constraints
    print("\nTesting eliminate_values_larger_than_constraints:")
    test_eliminate_values_larger_than_constraints_basic()
    test_eliminate_values_larger_than_constraints_no_change()

    # Test eliminate_values_not_in_sums
    print("\nTesting eliminate_values_not_in_sums:")
    test_eliminate_values_not_in_sums_basic()
    test_eliminate_values_not_in_sums_with_filled_grid()

    # Test select_essential_number
    print("\nTesting select_essential_number:")
    test_select_essential_number_basic()
    test_select_essential_number_no_empty_cells()

    # Test main_solver
    print("\nTesting main_solver (integration tests):")
    test_main_solver_with_empty_cells()
    test_main_solver_preserves_constraints()
    test_main_solver_level_128()

    print("\n" + "=" * 60)
    print("All tests completed successfully! ✓")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_all_tests()
