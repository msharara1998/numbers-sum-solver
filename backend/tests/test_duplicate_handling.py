"""
Test to verify that the solver correctly handles duplicate values.

This test specifically checks the edge case where a combination contains
duplicate numbers (like [5, 5] for sum 10), and we have more instances
of that number available than needed.
"""

from backend.models import PuzzleGrid, GridCell, Constraint
from backend.solver import solve_by_elimination_and_selection


def test_duplicate_handling():
    """
    Test case: We have three 5s and need to select two of them to sum to 10.

    Grid (1 row, 3 columns):
    [5, 5, 5]  -> sum should be 10

    Expected behavior:
    - Since we have 3 instances of 5 but only need 2, we CANNOT determine
      which two to select, so all three should remain as isSelected=None
    - If we had exactly 2 instances of 5, both should be selected
    """
    print("\n" + "=" * 60)
    print("Test 1: Three 5s, need sum of 10 (ambiguous case)")
    print("=" * 60)

    # Create grid with three 5s
    cells = [
        [
            GridCell(row=0, col=0, value=5, isSelected=None),
            GridCell(row=0, col=1, value=5, isSelected=None),
            GridCell(row=0, col=2, value=5, isSelected=None),
        ]
    ]

    constraints = [Constraint(type="row", index=0, sum=10, is_satisfied=False)]

    grid = PuzzleGrid(cells=cells, constraints=constraints)

    # Run solver
    result = solve_by_elimination_and_selection(grid)

    # Check results
    print(
        f"Cell 0: value={result.cells[0][0].value}, isSelected={result.cells[0][0].isSelected}"
    )
    print(
        f"Cell 1: value={result.cells[0][1].value}, isSelected={result.cells[0][1].isSelected}"
    )
    print(
        f"Cell 2: value={result.cells[0][2].value}, isSelected={result.cells[0][2].isSelected}"
    )

    # All should remain None because we can't determine which two to select
    assert (
        result.cells[0][0].isSelected is None
    ), "Cell 0 should remain None (ambiguous)"
    assert (
        result.cells[0][1].isSelected is None
    ), "Cell 1 should remain None (ambiguous)"
    assert (
        result.cells[0][2].isSelected is None
    ), "Cell 2 should remain None (ambiguous)"

    print("✓ Test 1 passed: Correctly handled ambiguous duplicate case\n")


def test_exact_duplicate_match():
    """
    Test case: We have exactly two 5s and need both to sum to 10.

    Grid (1 row, 2 columns):
    [5, 5]  -> sum should be 10

    Expected behavior:
    - Both 5s should be selected because we need all available instances
    """
    print("=" * 60)
    print("Test 2: Two 5s, need sum of 10 (exact match)")
    print("=" * 60)

    # Create grid with two 5s
    cells = [
        [
            GridCell(row=0, col=0, value=5, isSelected=None),
            GridCell(row=0, col=1, value=5, isSelected=None),
        ]
    ]

    constraints = [Constraint(type="row", index=0, sum=10, is_satisfied=False)]

    grid = PuzzleGrid(cells=cells, constraints=constraints)

    # Run solver
    result = solve_by_elimination_and_selection(grid)

    # Check results
    print(
        f"Cell 0: value={result.cells[0][0].value}, isSelected={result.cells[0][0].isSelected}"
    )
    print(
        f"Cell 1: value={result.cells[0][1].value}, isSelected={result.cells[0][1].isSelected}"
    )

    # Both should be selected
    assert result.cells[0][0].isSelected is True, "Cell 0 should be selected"
    assert result.cells[0][1].isSelected is True, "Cell 1 should be selected"

    print("✓ Test 2 passed: Correctly selected all instances when count matches\n")


def test_mixed_values_with_duplicates():
    """
    Test case: Mixed values including duplicates.

    Grid (1 row, 5 columns):
    [1, 5, 5, 6, 11]  -> sum should be 11

    Possible combinations: [1, 5, 5], [5, 6], [11]

    Expected behavior:
    - No value should be selected because each appears in different combos
    - No value should be deselected because all appear in at least one combo
    """
    print("=" * 60)
    print("Test 3: Mixed values [1, 5, 5, 6, 11], sum=11")
    print("=" * 60)

    cells = [
        [
            GridCell(row=0, col=0, value=1, isSelected=None),
            GridCell(row=0, col=1, value=5, isSelected=None),
            GridCell(row=0, col=2, value=5, isSelected=None),
            GridCell(row=0, col=3, value=6, isSelected=None),
            GridCell(row=0, col=4, value=11, isSelected=None),
        ]
    ]

    constraints = [Constraint(type="row", index=0, sum=11, is_satisfied=False)]

    grid = PuzzleGrid(cells=cells, constraints=constraints)

    # Run solver
    result = solve_by_elimination_and_selection(grid)

    # Check results
    for i, cell in enumerate(result.cells[0]):
        print(f"Cell {i}: value={cell.value}, isSelected={cell.isSelected}")

    # All should remain None because no value appears in ALL combos with same frequency
    for i, cell in enumerate(result.cells[0]):
        assert cell.isSelected is None, f"Cell {i} should remain None"

    print("✓ Test 3 passed: Correctly handled mixed values with duplicates\n")


def test_deselection_with_duplicates():
    """
    Test case: Some values should be deselected.

    Grid (1 row, 4 columns):
    [1, 2, 5, 5]  -> sum should be 10

    Possible combinations: [5, 5]

    Expected behavior:
    - Both 5s should be selected (we need all instances)
    - 1 and 2 should be deselected (don't appear in any combo)
    """
    print("=" * 60)
    print("Test 4: Values [1, 2, 5, 5], sum=10 (with deselection)")
    print("=" * 60)

    cells = [
        [
            GridCell(row=0, col=0, value=1, isSelected=None),
            GridCell(row=0, col=1, value=2, isSelected=None),
            GridCell(row=0, col=2, value=5, isSelected=None),
            GridCell(row=0, col=3, value=5, isSelected=None),
        ]
    ]

    constraints = [Constraint(type="row", index=0, sum=10, is_satisfied=False)]

    grid = PuzzleGrid(cells=cells, constraints=constraints)

    # Run solver
    result = solve_by_elimination_and_selection(grid)

    # Check results
    for i, cell in enumerate(result.cells[0]):
        print(f"Cell {i}: value={cell.value}, isSelected={cell.isSelected}")

    # 1 and 2 should be deselected
    assert (
        result.cells[0][0].isSelected is False
    ), "Cell 0 (value=1) should be deselected"
    assert (
        result.cells[0][1].isSelected is False
    ), "Cell 1 (value=2) should be deselected"

    # Both 5s should be selected
    assert result.cells[0][2].isSelected is True, "Cell 2 (value=5) should be selected"
    assert result.cells[0][3].isSelected is True, "Cell 3 (value=5) should be selected"

    print("✓ Test 4 passed: Correctly selected duplicates and deselected others\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Testing Duplicate Value Handling in Solver")
    print("=" * 60)

    test_duplicate_handling()
    test_exact_duplicate_match()
    test_mixed_values_with_duplicates()
    test_deselection_with_duplicates()

    print("=" * 60)
    print("All tests passed! ✓")
    print("=" * 60 + "\n")
