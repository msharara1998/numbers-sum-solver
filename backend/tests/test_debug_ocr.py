"""Debug script to understand OCR detection issues."""

import sys
from pathlib import Path

# Add parent directory to path to import from backend
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.ocr import PuzzleOCRExtractor

test_image_path = Path(__file__).parent / "Numbers-Sum.jpg"

if test_image_path.exists():
    extractor = PuzzleOCRExtractor()
    
    # Run OCR
    ocr_result = extractor.engine(str(test_image_path))
    
    if ocr_result and ocr_result.boxes is not None and ocr_result.txts is not None:
        print("All detected numbers with positions:\n")
        for i, (box, text, conf) in enumerate(zip(ocr_result.boxes, ocr_result.txts, ocr_result.scores)):
            if text.strip().isdigit():
                top_left_x = float(box[0][0])
                top_left_y = float(box[0][1])
                bottom_right_x = float(box[2][0])
                bottom_right_y = float(box[2][1])
                width = abs(bottom_right_x - top_left_x)
                height = abs(bottom_right_y - top_left_y)
                area = width * height
                
                print(f"{i:3d}. Value: {text:3s}  X:{top_left_x:7.2f}  Y:{top_left_y:7.2f}  "
                      f"W:{width:6.2f}  H:{height:6.2f}  Area:{area:8.1f}  Conf:{conf:.3f}")
        
        # Try the extraction
        print("\n" + "="*70)
        print("Attempting extraction...")
        grid = extractor.extract_from_image(str(test_image_path))
        
        print(f"\nExtracted grid ({len(grid.cells)}x{len(grid.cells[0]) if grid.cells else 0}):")
        for i, row in enumerate(grid.cells):
            vals = [str(cell.value) if cell.value is not None else "." for cell in row]
            print(f"  Row {i}: {' '.join(vals)}")
        
        print(f"\nConstraints:")
        row_constraints = sorted([c for c in grid.constraints if c.type == "row"], key=lambda x: x.index)
        col_constraints = sorted([c for c in grid.constraints if c.type == "column"], key=lambda x: x.index)
        print(f"  Row constraints: {[c.sum for c in row_constraints]}")
        print(f"  Col constraints: {[c.sum for c in col_constraints]}")
else:
    print(f"Test image not found at: {test_image_path}")
