"""Script to visualize the image preprocessing effects."""

import sys
from pathlib import Path
from PIL import Image
import io

# Add parent directory to path to import backend module
sys.path.insert(0, str(Path(__file__).parent))

from backend.ocr import PuzzleOCRExtractor

test_image_path = Path("backend/tests/Numbers-Sum.jpg")
comparison_path = Path("backend/tests/preprocessing_comparison.png")

if test_image_path.exists():
    print(f"Loading original image from: {test_image_path}")

    # Load original
    img_original = Image.open(test_image_path)

    # Use the preprocessing function from OCR module
    print("Applying preprocessing steps...")
    extractor = PuzzleOCRExtractor(enable_preprocessing=True)
    preprocessed_bytes = extractor._preprocess_image(str(test_image_path))

    # Convert bytes to image for saving
    img = Image.open(io.BytesIO(preprocessed_bytes))

    # Create a side-by-side comparison
    # Resize if needed to fit side by side
    width, height = img_original.size

    # Create new image for side-by-side comparison
    comparison = Image.new('RGB', (width * 2, height))
    comparison.paste(img_original, (0, 0))
    comparison.paste(img, (width, 0))

    comparison.save(comparison_path)
    print(f"✓ Comparison image saved to: {comparison_path}")
    print(f"  (Original on left, Preprocessed on right)")

else:
    print(f"Test image not found at: {test_image_path}")
