"""
Unit tests for the get_essential_values_with_counts utility function.
"""

from backend.utils import get_essential_values_with_counts


def test_exact_match():
    """Test when we need all available instances."""
    combos = [[5, 5]]
    available_values = [5, 5]
    result = get_essential_values_with_counts(combos, available_values)

    assert result == {5: 2}, f"Expected {{5: 2}}, got {result}"
    print("✓ Test exact_match passed")


def test_ambiguous_case():
    """Test when we have more instances than needed."""
    combos = [[5, 5]]
    available_values = [5, 5, 5]
    result = get_essential_values_with_counts(combos, available_values)

    assert result == {}, f"Expected empty dict, got {result}"
    print("✓ Test ambiguous_case passed")


def test_multiple_combos_same_frequency():
    """Test when multiple combos use the same frequency."""
    combos = [[1, 2, 3], [2, 3, 1]]  # Same values, different order
    available_values = [1, 2, 3]
    result = get_essential_values_with_counts(combos, available_values)

    # All values appear exactly once in all combos and we have exactly one of each
    assert result == {1: 1, 2: 1, 3: 1}, f"Expected {{1: 1, 2: 1, 3: 1}}, got {result}"
    print("✓ Test multiple_combos_same_frequency passed")


def test_different_frequencies():
    """Test when values appear with different frequencies across combos."""
    combos = [[1, 5, 5], [5, 6], [11]]
    available_values = [1, 5, 5, 6, 11]
    result = get_essential_values_with_counts(combos, available_values)

    # No value appears with the same frequency in all combos
    assert result == {}, f"Expected empty dict, got {result}"
    print("✓ Test different_frequencies passed")


def test_empty_combos():
    """Test with empty combinations list."""
    combos = []
    available_values = [1, 2, 3]
    result = get_essential_values_with_counts(combos, available_values)

    assert result == {}, f"Expected empty dict, got {result}"
    print("✓ Test empty_combos passed")


def test_partial_match():
    """Test when values appear in all combos with same frequency."""
    combos = [[1, 2], [1, 2]]  # Same combination repeated
    available_values = [1, 2]
    result = get_essential_values_with_counts(combos, available_values)

    # Both values appear exactly once in all combos, and we have one of each
    assert result == {1: 1, 2: 1}, f"Expected {{1: 1, 2: 1}}, got {result}"
    print("✓ Test partial_match passed")


def test_duplicates_in_multiple_combos():
    """Test with duplicates appearing in multiple combinations."""
    combos = [[2, 2, 2], [1, 2, 3]]
    available_values = [1, 2, 2, 2, 3]
    result = get_essential_values_with_counts(combos, available_values)

    # Value 2 appears 3 times in first combo but only 1 time in second combo
    # So it's not consistent across all combos
    # Values 1 and 3 appear once in second combo but not in first
    assert result == {}, f"Expected empty dict, got {result}"
    print("✓ Test duplicates_in_multiple_combos passed")


def test_single_value_essential():
    """Test when only one value is essential across all combos."""
    combos = [[3, 7], [3, 4, 3]]  # 3 appears in all, but with different counts
    available_values = [3, 3, 4, 7]
    result = get_essential_values_with_counts(combos, available_values)

    # 3 appears with different frequencies (1 vs 2), so not essential
    # 7 and 4 don't appear in all combos
    assert result == {}, f"Expected empty dict, got {result}"
    print("✓ Test single_value_essential passed")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Testing get_essential_values_with_counts Utility Function")
    print("=" * 60 + "\n")

    test_exact_match()
    test_ambiguous_case()
    test_multiple_combos_same_frequency()
    test_different_frequencies()
    test_empty_combos()
    test_partial_match()
    test_duplicates_in_multiple_combos()
    test_single_value_essential()

    print("\n" + "=" * 60)
    print("All utility function tests passed! ✓")
    print("=" * 60 + "\n")
