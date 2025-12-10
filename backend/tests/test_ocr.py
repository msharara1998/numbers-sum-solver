"""
Test suite for OCR extraction functionality.

Tests the OCR module's ability to extract puzzle grids from images.
"""

from pathlib import Path

from backend.ocr import PuzzleOCRExtractor, extract_puzzle_from_image


def test_ocr_extractor_initialization():
    """Test that OCR extractor can be initialized."""
    print("\nTest: OCR extractor initialization")
    
    extractor = PuzzleOCRExtractor()
    assert extractor.engine is not None
    
    print("✓ OCR extractor initialized successfully")


def test_extract_from_test_image():
    """Test extracting puzzle from the Numbers-Sum.jpg test image."""
    print("\nTest: Extract from Numbers-Sum.jpg")
    
    # Path to test image
    test_image_path = Path(__file__).parent / "Numbers-Sum.jpg"
    
    if not test_image_path.exists():
        print(f"⚠ Test image not found at: {test_image_path}")
        print("  Skipping test")
        return
    
    try:
        # Extract grid from image
        grid = extract_puzzle_from_image(str(test_image_path))
        
        # Verify grid structure
        assert grid is not None
        assert grid.cells is not None
        assert len(grid.cells) > 0
        assert grid.constraints is not None
        
        # Print Extracted Grid
        print("  Extracted Puzzle Grid:")
        
        for row in grid.cells:
            row_values = [str(cell.value) if cell.value is not None else "." for cell in row]
            print("   " + " ".join(row_values))
        
        
        # Based on Level 128 image: should be 7x7 grid
        # assert len(grid.cells) == 7, f"Expected 7 rows, got {len(grid.cells)}"
        # assert len(grid.cells[0]) == 7, f"Expected 7 columns, got {len(grid.cells[0])}"
        
        # Print extracted information
        print(f"  Grid size: {len(grid.cells)}x{len(grid.cells[0]) if grid.cells else 0}")
        print(f"  Number of cells: {sum(len(row) for row in grid.cells)}")
        print(f"  Number of constraints: {len(grid.constraints)}")
        print(f" Constraints: {[(c.type, c.index, c.sum) for c in grid.constraints]}")
        # Verify constraints count: 7 rows + 7 columns = 14 total
        row_constraints = [c for c in grid.constraints if c.type == "row"]
        col_constraints = [c for c in grid.constraints if c.type == "column"]
        assert len(row_constraints) == 7, f"Expected 7 row constraints, got {len(row_constraints)}"
        assert len(col_constraints) == 7, f"Expected 7 column constraints, got {len(col_constraints)}"
        
        print(f"  Row constraints: {len(row_constraints)} (sums: {[c.sum for c in row_constraints]})")
        print(f"  Column constraints: {len(col_constraints)} (sums: {[c.sum for c in col_constraints]})")
        
        # Verify expected constraint sums from image
        expected_col_sums = [25, 16, 17, 20, 11, 14, 26]
        expected_row_sums = [11, 20, 28, 14, 16, 25, 15]
        
        actual_col_sums = [c.sum for c in sorted(col_constraints, key=lambda x: x.index)]
        actual_row_sums = [c.sum for c in sorted(row_constraints, key=lambda x: x.index)]
        
        assert actual_col_sums == expected_col_sums, f"Column sums mismatch: expected {expected_col_sums}, got {actual_col_sums}"
        assert actual_row_sums == expected_row_sums, f"Row sums mismatch: expected {expected_row_sums}, got {actual_row_sums}"
        
        # Verify some specific cell values from the image
        # First row: [4, 5, 2, 4, 2, 1, 6]
        assert grid.cells[0][0].value == 4, f"Cell [0,0] should be 4, got {grid.cells[0][0].value}"
        assert grid.cells[0][1].value == 5, f"Cell [0,1] should be 5, got {grid.cells[0][1].value}"
        assert grid.cells[0][2].value == 2, f"Cell [0,2] should be 2, got {grid.cells[0][2].value}"
        assert grid.cells[0][3].value == 4, f"Cell [0,3] should be 4, got {grid.cells[0][3].value}"
        assert grid.cells[0][4].value == 2, f"Cell [0,4] should be 2, got {grid.cells[0][4].value}"
        assert grid.cells[0][5].value == 1, f"Cell [0,5] should be 1, got {grid.cells[0][5].value}"
        assert grid.cells[0][6].value == 6, f"Cell [0,6] should be 6, got {grid.cells[0][6].value}"
        
        # Last row: [4, 4, 6, 1, 7, 9, 8]
        assert grid.cells[6][0].value == 4, f"Cell [6,0] should be 4, got {grid.cells[6][0].value}"
        assert grid.cells[6][1].value == 4, f"Cell [6,1] should be 4, got {grid.cells[6][1].value}"
        assert grid.cells[6][2].value == 6, f"Cell [6,2] should be 6, got {grid.cells[6][2].value}"
        assert grid.cells[6][3].value == 1, f"Cell [6,3] should be 1, got {grid.cells[6][3].value}"
        assert grid.cells[6][4].value == 7, f"Cell [6,4] should be 7, got {grid.cells[6][4].value}"
        assert grid.cells[6][5].value == 9, f"Cell [6,5] should be 9, got {grid.cells[6][5].value}"
        assert grid.cells[6][6].value == 8, f"Cell [6,6] should be 8, got {grid.cells[6][6].value}"
        
        # Print first few cells
        print("\n  First row cells:")
        for cell in grid.cells[0]:
            print(f"    Cell({cell.row},{cell.col}): value={cell.value}")
        
        print("✓ Successfully extracted grid from image with correct values")
        
    except Exception as e:
        print(f"✗ Error extracting from image: {e}")
        raise


def test_extract_numbers_from_image():
    """Test that numbers are detected from the image."""
    print("\nTest: Number detection")
    
    test_image_path = Path(__file__).parent / "Numbers-Sum.jpg"
    
    if not test_image_path.exists():
        print(f"⚠ Test image not found at: {test_image_path}")
        print("  Skipping test")
        return
    
    try:
        from rapidocr.utils.output import RapidOCROutput
        
        extractor = PuzzleOCRExtractor()
        
        # Run OCR - RapidOCR returns RapidOCROutput object
        ocr_result = extractor.engine(str(test_image_path))
        
        assert ocr_result is not None
        
        # Extract numbers from RapidOCROutput
        numbers = []
        if isinstance(ocr_result, RapidOCROutput):
            if ocr_result.txts is not None:
                for text in ocr_result.txts:
                    if text.strip().isdigit():
                        numbers.append(int(text.strip()))
            
            print(f"  Detected {len(ocr_result.txts) if ocr_result.txts else 0} text items")
        else:
            print(f"  Unexpected OCR result type: {type(ocr_result)}")
        
        print(f"  Detected {len(numbers)} numbers")
        if numbers:
            print(f"  Numbers: {numbers[:10]}...")  # First 10 numbers
        
        assert len(numbers) > 0, "No numbers detected in image"
        
        print("✓ Numbers successfully detected")
        
    except Exception as e:
        print(f"✗ Error detecting numbers: {e}")
        raise


def test_grid_structure_validation():
    """Test that extracted grid has valid structure."""
    print("\nTest: Grid structure validation")
    
    test_image_path = Path(__file__).parent / "Numbers-Sum.jpg"
    
    if not test_image_path.exists():
        print(f"⚠ Test image not found at: {test_image_path}")
        print("  Skipping test")
        return
    
    try:
        grid = extract_puzzle_from_image(str(test_image_path))
        
        # Validate grid structure
        assert isinstance(grid.cells, list), "cells should be a list"
        assert all(isinstance(row, list) for row in grid.cells), "Each row should be a list"
        
        # All rows should have same length (rectangular grid)
        row_lengths = [len(row) for row in grid.cells]
        assert all(length == row_lengths[0] for length in row_lengths), f"All rows should have same length, got {row_lengths}"
        
        # Check all cells have required attributes and proper indexing
        for row_idx, row in enumerate(grid.cells):
            for col_idx, cell in enumerate(row):
                assert hasattr(cell, 'value'), "Cell should have value"
                assert hasattr(cell, 'row'), "Cell should have row"
                assert hasattr(cell, 'col'), "Cell should have col"
                assert hasattr(cell, 'isSelected'), "Cell should have isSelected"
                
                # Verify correct row/col indexing
                assert cell.row == row_idx, f"Cell at position [{row_idx}][{col_idx}] has wrong row index: {cell.row}"
                assert cell.col == col_idx, f"Cell at position [{row_idx}][{col_idx}] has wrong col index: {cell.col}"
                
                # All cells should have numeric values (not None for this puzzle)
                assert cell.value is not None, f"Cell [{row_idx}][{col_idx}] should have a value"
                assert isinstance(cell.value, int), f"Cell [{row_idx}][{col_idx}] value should be int"
                assert cell.value >= 1 and cell.value <= 9, f"Cell [{row_idx}][{col_idx}] value should be 1-9, got {cell.value}"
                
                # isSelected should initially be None (not decided yet)
                assert cell.isSelected is None, f"Cell [{row_idx}][{col_idx}] isSelected should be None initially"
        
        # Check constraints
        assert isinstance(grid.constraints, list), "constraints should be a list"
        for constraint in grid.constraints:
            assert hasattr(constraint, 'type'), "Constraint should have type"
            assert hasattr(constraint, 'index'), "Constraint should have index"
            assert hasattr(constraint, 'sum'), "Constraint should have sum"
            assert hasattr(constraint, 'is_satisfied'), "Constraint should have is_satisfied"
            assert constraint.type in ['row', 'column'], "Constraint type should be row or column"
            
            # Constraint sums should be positive
            assert constraint.sum > 0, f"Constraint sum should be positive, got {constraint.sum}"
            
            # Constraint index should be within grid bounds
            if constraint.type == 'row':
                assert 0 <= constraint.index < len(grid.cells), f"Row constraint index out of bounds: {constraint.index}"
            else:
                assert 0 <= constraint.index < len(grid.cells[0]), f"Column constraint index out of bounds: {constraint.index}"
            
            # Initially constraints should not be satisfied
            assert constraint.is_satisfied == False, "Constraints should initially be unsatisfied"
        
        print(f"  ✓ All {len(grid.cells) * len(grid.cells[0])} cells have valid structure")
        print(f"  ✓ All {len(grid.constraints)} constraints have valid structure")
        print("✓ Grid structure is fully valid")
        
    except Exception as e:
        print(f"✗ Error validating grid structure: {e}")
        raise


def test_ocr_with_invalid_image():
    """Test OCR with invalid image data."""
    print("\nTest: Invalid image handling")
    
    try:
        extractor = PuzzleOCRExtractor()
        
        # Try with invalid bytes
        invalid_bytes = b"not an image"
        
        try:
            grid = extractor.extract_from_bytes(invalid_bytes)
            print("✗ Should have raised an error for invalid image")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            print(f"  Correctly raised ValueError: {e}")
            print("✓ Invalid image handling works correctly")
        
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        raise


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Testing OCR Extraction")
    print("=" * 60)
    
    test_ocr_extractor_initialization()
    test_extract_from_test_image()
    test_extract_numbers_from_image()
    test_grid_structure_validation()
    test_ocr_with_invalid_image()
    
    print("\n" + "=" * 60)
    print("All OCR tests completed! ✓")
    print("=" * 60 + "\n")
