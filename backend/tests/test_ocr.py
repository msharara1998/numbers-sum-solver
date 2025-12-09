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
    test_image_path = Path(__file__).parent.parent.parent / "Numbers-Sum.jpg"
    
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
        
        # Print extracted information
        print(f"  Grid size: {len(grid.cells)}x{len(grid.cells[0])}")
        print(f"  Number of cells: {sum(len(row) for row in grid.cells)}")
        print(f"  Number of constraints: {len(grid.constraints)}")
        
        # Print first few cells
        print("\n  First row cells:")
        for cell in grid.cells[0][:5]:  # First 5 cells
            print(f"    Cell({cell.row},{cell.col}): value={cell.value}")
        
        print("✓ Successfully extracted grid from image")
        
    except Exception as e:
        print(f"✗ Error extracting from image: {e}")
        raise


def test_extract_numbers_from_image():
    """Test that numbers are detected from the image."""
    print("\nTest: Number detection")
    
    test_image_path = Path(__file__).parent.parent.parent / "Numbers-Sum.jpg"
    
    if not test_image_path.exists():
        print(f"⚠ Test image not found at: {test_image_path}")
        print("  Skipping test")
        return
    
    try:
        extractor = PuzzleOCRExtractor()
        
        # Run OCR
        result, elapse = extractor.engine(str(test_image_path))
        
        assert result is not None
        assert len(result) > 0
        
        # Extract numbers
        numbers = []
        for item in result:
            box, text, confidence = item
            if text.strip().isdigit():
                numbers.append(int(text.strip()))
        
        print(f"  Detected {len(result)} text items")
        print(f"  Detected {len(numbers)} numbers")
        print(f"  Numbers: {numbers[:10]}...")  # First 10 numbers
        
        assert len(numbers) > 0, "No numbers detected in image"
        
        print("✓ Numbers successfully detected")
        
    except Exception as e:
        print(f"✗ Error detecting numbers: {e}")
        raise


def test_grid_structure_validation():
    """Test that extracted grid has valid structure."""
    print("\nTest: Grid structure validation")
    
    test_image_path = Path(__file__).parent.parent.parent / "Numbers-Sum.jpg"
    
    if not test_image_path.exists():
        print(f"⚠ Test image not found at: {test_image_path}")
        print("  Skipping test")
        return
    
    try:
        grid = extract_puzzle_from_image(str(test_image_path))
        
        # Validate grid structure
        assert isinstance(grid.cells, list), "cells should be a list"
        assert all(isinstance(row, list) for row in grid.cells), "Each row should be a list"
        
        # Check all cells have required attributes
        for row in grid.cells:
            for cell in row:
                assert hasattr(cell, 'value'), "Cell should have value"
                assert hasattr(cell, 'row'), "Cell should have row"
                assert hasattr(cell, 'col'), "Cell should have col"
                assert hasattr(cell, 'isSelected'), "Cell should have isSelected"
        
        # Check constraints
        assert isinstance(grid.constraints, list), "constraints should be a list"
        for constraint in grid.constraints:
            assert hasattr(constraint, 'type'), "Constraint should have type"
            assert hasattr(constraint, 'index'), "Constraint should have index"
            assert hasattr(constraint, 'sum'), "Constraint should have sum"
            assert constraint.type in ['row', 'column'], "Constraint type should be row or column"
        
        print("✓ Grid structure is valid")
        
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
