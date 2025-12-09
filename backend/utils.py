from functools import lru_cache
from collections import Counter

from .models import GridCell, Constraint, PuzzleGrid


@lru_cache(maxsize=256)
def sums_composite(number: int, candidates: tuple[int, ...]) -> list[list[int]]:
    """
    Find all combinations of numbers from the list that sum to the given number.
    The combinations can be of any length.

    This function handles duplicate values correctly - if candidates contains
    multiple instances of the same value, they are treated as distinct items.

    Args:
        number: The target sum.
        candidates: A tuple of numbers to choose from (tuple is required for
        caching). Can contain duplicates.

    Returns:
        A list of lists of numbers that sum to the given number.
    """
    # Sort candidates but keep duplicates - each position represents a distinct choice
    candidates = sorted(candidates)
    results: list[list[int]] = []

    def backtrack(start: int, current: list[int], current_sum: int) -> None:
        if current_sum == number:
            results.append(current.copy())
            return
        if current_sum > number:
            return

        for i in range(start, len(candidates)):
            cand = candidates[i]

            # Skip duplicates at the same recursion level to avoid duplicate combinations
            # But allow using the same value from different positions
            if i > start and candidates[i] == candidates[i - 1]:
                continue

            # Prune if adding cand exceeds target
            if current_sum + cand > number:
                break

            # Include this candidate and continue from next position
            backtrack(i + 1, current + [cand], current_sum + cand)

    backtrack(0, [], 0)
    return results


def get_cells_of(constraint: Constraint, grid: PuzzleGrid) -> list[GridCell]:
    """
    Get the cells of a constraint.

    Args:
        constraint: The constraint to get the cells of.
        grid: The puzzle grid.

    Returns:
        A list of cells that belong to the constraint.
    """
    return (
        grid.cells[constraint.index]
        if constraint.type == "row"
        else [grid.cells[r][constraint.index] for r in range(len(grid.cells))]
    )


def get_essential_values_with_counts(
    combos: list[list[int]], available_values: list[int]
) -> dict[int, int]:
    """
    Analyze combinations to find essential values that must be selected.

    A value is considered essential if:
    1. It appears with the SAME frequency in ALL combinations, AND
    2. That frequency equals the number of available instances

    This handles the edge case where duplicate values exist (e.g., three 5s)
    but only some are needed (e.g., [5, 5] for sum 10). In such cases, we
    cannot determine which specific instances to select, so the value is
    NOT marked as essential.

    Args:
        combos: List of all possible combinations that satisfy the constraint.
        available_values: List of available values (can contain duplicates).

    Returns:
        Dictionary mapping essential values to their required count.
        Only values that appear in ALL combos with the same count AND
        where that count equals available instances are included.

    Example:
        >>> combos = [[5, 5], [5, 5]]
        >>> available_values = [5, 5]
        >>> get_essential_values_with_counts(combos, available_values)
        {5: 2}  # Both 5s are essential

        >>> combos = [[5, 5]]
        >>> available_values = [5, 5, 5]
        >>> get_essential_values_with_counts(combos, available_values)
        {}  # Not essential - we have 3 but only need 2
    """

    if not combos:
        return {}

    # Get all possible values that appear in any combo
    all_numbers = set().union(*combos)

    # Count how many times each value appears in available_values
    available_counts = Counter(available_values)

    # For each combo, count the frequency of each value
    combo_counters = [Counter(combo) for combo in combos]

    # Find values that appear with the SAME frequency in ALL combos
    # and where that frequency equals the available count
    essential_values_with_counts = {}
    for value in all_numbers:
        # Get the count of this value in each combo
        counts_in_combos = [counter.get(value, 0) for counter in combo_counters]

        # Check if all combos have the same count for this value
        if len(set(counts_in_combos)) == 1:
            # All combos have the same count
            required_count = counts_in_combos[0]

            # Only mark as essential if we need ALL available instances
            if required_count > 0 and required_count == available_counts[value]:
                essential_values_with_counts[value] = required_count

    return essential_values_with_counts


def is_grid_solved(grid: PuzzleGrid) -> bool:
    """
    Check if the puzzle grid is completely solved.

    A grid is considered solved when every constraint is satisfied.

    Args:
        grid: The puzzle grid to check.

    Returns:
        True if all constraints are satisfied, False otherwise.
    """
    for constraint in grid.constraints:
        if not constraint.is_satisfied:
            return False
    return True


def has_grid_changed(grid_before: PuzzleGrid, grid_after: PuzzleGrid) -> bool:
    """
    Check if the grid state changed between two iterations.

    Compares the isSelected state of all cells to detect if any progress was made.
    This is useful for detecting when the solver is stuck and can't make further
    progress with the current strategy.

    Args:
        grid_before: The grid state before an operation.
        grid_after: The grid state after an operation.

    Returns:
        True if any cell's isSelected state changed, False otherwise.
    """
    for i, row in enumerate(grid_before.cells):
        for j, cell_before in enumerate(row):
            cell_after = grid_after.cells[i][j]
            if cell_before.isSelected != cell_after.isSelected:
                return True
    return False


if __name__ == "__main__":
    print(sums_composite(11, (1, 5, 5, 6, 11)))
