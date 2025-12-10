from backend.models import PuzzleGrid
from backend.utils import (
    sums_composite,
    get_cells_of,
    get_essential_values_with_counts,
    is_grid_solved,
    has_grid_changed,
)


def solve_by_elimination_and_selection(grid: PuzzleGrid) -> PuzzleGrid:
    """
    Iterate over constraints and select the essential number in the rows and
    columns, as well as deselect numbers that cannot be part of any possible
    combination that sums to the target sum.
    An essential number is a number that, without it, the sum of the constraint
    cannot be reached. If a number is essential, it should appear in all
    possible combinations that sum to the target sum.

    Args:
        grid: The puzzle grid to solve.

    Returns:
        The solved grid.
    """

    # Iterate over constraints
    for constraint in grid.constraints:
        if constraint.is_satisfied is True:
            continue
        # Get cells of the constraint
        cells = get_cells_of(constraint, grid)

        known_sum = 0
        remaining_cells = []
        for cell in cells:
            if cell.isSelected is True:
                known_sum += cell.value
            elif cell.isSelected is None:
                remaining_cells.append(cell)
        remaining_sum = constraint.sum - known_sum

        # If remaining sum is less than or equal to 0, mark constraint as
        # satisfied and deselect remaining cells
        if remaining_sum <= 0:

            constraint.is_satisfied = True

            if remaining_cells:
                for cell in remaining_cells:
                    cell.isSelected = False

            continue

        # get possible combinations that sum to remaining sum
        combos = sums_composite(
            remaining_sum, tuple(cell.value for cell in remaining_cells)
        )

        # Get union of all combos to find which numbers can possibly be used
        all_numbers = set().union(*combos) if combos else set()

        # Get essential values using the utility function
        available_values = [cell.value for cell in remaining_cells]
        essential_values_with_counts = get_essential_values_with_counts(
            combos, available_values
        )

        # Now apply the selection/deselection logic
        for cell in remaining_cells:
            # If this value is essential and we need all instances, select it
            if cell.value in essential_values_with_counts:
                cell.isSelected = True

            # If this value doesn't appear in ANY combo, deselect it
            if cell.value not in all_numbers:
                cell.isSelected = False

        # After processing, check if constraint is now satisfied
        # Recalculate to see if we've selected exactly the right sum
        selected_sum = sum(cell.value for cell in cells if cell.isSelected is True)
        unselected_cells = [cell for cell in cells if cell.isSelected is None]

        # Constraint is satisfied if:
        # 1. We have the exact sum and no undecided cells, OR
        # 2. All cells are decided (True or False)
        if selected_sum == constraint.sum:
            if not unselected_cells:
                # select all unselected cells as False
                for cell in unselected_cells:
                    cell.isSelected = False
            constraint.is_satisfied = True

    return grid


def main_solver(grid: PuzzleGrid, max_iterations: int = 100) -> PuzzleGrid:
    """
    Main solver function that iteratively applies solving strategies until
    the grid is solved or no more progress can be made.

    The solver will:
    1. Apply solve_by_elimination_and_selection repeatedly
    2. Stop when the grid is fully solved (all cells decided)
    3. Stop when no progress is made (solver is stuck)
    4. Stop after max_iterations to prevent infinite loops

    Args:
        grid: The puzzle grid to solve.
        max_iterations: Maximum number of iterations to prevent infinite loops.
        Default is 100, which should be more than enough for most puzzles.

    Returns:
        The solved (or partially solved) grid.
    """

    iteration = 0

    while iteration < max_iterations:
        # Check if grid is already solved
        if is_grid_solved(grid):
            break

        # Apply solving strategy
        grid_before = grid.model_copy(deep=True)
        grid = solve_by_elimination_and_selection(grid)

        # Check if we made any progress
        if not has_grid_changed(grid_before, grid):
            # No progress made, solver is stuck
            break

        iteration += 1

    return grid
