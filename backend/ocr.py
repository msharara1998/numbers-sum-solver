"""
OCR module for extracting puzzle grids from images using RapidOCR.

This module uses RapidOCR to detect and extract numbers from puzzle grid images.
"""

from typing import List, Tuple, Optional
from pathlib import Path
import re

from rapidocr_onnxruntime import RapidOCR

from .models import PuzzleGrid, GridCell, Constraint


class PuzzleOCRExtractor:
    """Extract puzzle grid data from images using OCR."""

    def __init__(self):
        """Initialize the OCR engine."""
        self.engine = RapidOCR()

    def extract_from_image(self, image_path: str) -> PuzzleGrid:
        """Extract puzzle grid from an image file.

        Args:
            image_path: Path to the image file.

        Returns:
            PuzzleGrid: Extracted puzzle grid with cells and constraints.

        Raises:
            ValueError: If the image cannot be processed or grid cannot be extracted.
        """
        # Run OCR on the image
        result, elapse = self.engine(image_path)

        if not result:
            raise ValueError("No text detected in image")

        # Extract text and bounding boxes
        texts_with_boxes = []
        for item in result:
            box, text, confidence = item
            texts_with_boxes.append({
                "text": text,
                "box": box,
                "confidence": confidence,
            })

        # Parse the detected text into grid structure
        grid = self._parse_grid_from_ocr(texts_with_boxes)

        return grid

    def extract_from_bytes(self, image_bytes: bytes) -> PuzzleGrid:
        """Extract puzzle grid from image bytes.

        Args:
            image_bytes: Image data as bytes.

        Returns:
            PuzzleGrid: Extracted puzzle grid with cells and constraints.

        Raises:
            ValueError: If the image cannot be processed or grid cannot be extracted.
        """
        # Run OCR on the image bytes
        result, elapse = self.engine(image_bytes)

        if not result:
            raise ValueError("No text detected in image")

        # Extract text and bounding boxes
        texts_with_boxes = []
        for item in result:
            box, text, confidence = item
            texts_with_boxes.append({
                "text": text,
                "box": box,
                "confidence": confidence,
            })

        # Parse the detected text into grid structure
        grid = self._parse_grid_from_ocr(texts_with_boxes)

        return grid

    def _parse_grid_from_ocr(
        self, texts_with_boxes: List[dict]
    ) -> PuzzleGrid:
        """Parse OCR results into a puzzle grid.

        This is a placeholder implementation that needs to be customized
        based on the actual puzzle image format.

        Args:
            texts_with_boxes: List of detected text with bounding boxes.

        Returns:
            PuzzleGrid: Parsed puzzle grid.

        Raises:
            ValueError: If grid structure cannot be determined.
        """
        # Extract numbers from detected text
        numbers = []
        for item in texts_with_boxes:
            text = item["text"].strip()
            # Try to extract number
            if text.isdigit():
                numbers.append({
                    "value": int(text),
                    "box": item["box"],
                    "confidence": item["confidence"],
                })

        if not numbers:
            raise ValueError("No numbers detected in image")

        # Sort numbers by position (top to bottom, left to right)
        numbers.sort(key=lambda x: (x["box"][0][1], x["box"][0][0]))

        # Determine grid dimensions
        # This is a simplified approach - in practice, you'd need more
        # sophisticated logic to determine the grid structure
        grid_size = self._estimate_grid_size(numbers)

        # Create cells
        cells = self._create_cells_from_numbers(numbers, grid_size)

        # Create constraints (placeholder - needs actual constraint detection)
        constraints = self._create_default_constraints(grid_size)

        return PuzzleGrid(cells=cells, constraints=constraints)

    def _estimate_grid_size(self, numbers: List[dict]) -> int:
        """Estimate the grid size from detected numbers.

        Args:
            numbers: List of detected numbers with positions.

        Returns:
            int: Estimated grid size (assumes square grid).
        """
        # Simple estimation: square root of number count
        import math

        count = len(numbers)
        size = int(math.sqrt(count))

        # Adjust if not perfect square
        if size * size < count:
            size += 1

        return size

    def _create_cells_from_numbers(
        self, numbers: List[dict], grid_size: int
    ) -> List[List[GridCell]]:
        """Create grid cells from detected numbers.

        Args:
            numbers: List of detected numbers.
            grid_size: Size of the grid.

        Returns:
            List[List[GridCell]]: 2D array of grid cells.
        """
        cells = []
        idx = 0

        for row in range(grid_size):
            row_cells = []
            for col in range(grid_size):
                if idx < len(numbers):
                    value = numbers[idx]["value"]
                    idx += 1
                else:
                    value = None

                cell = GridCell(
                    row=row,
                    col=col,
                    value=value,
                    isSelected=None,
                )
                row_cells.append(cell)

            cells.append(row_cells)

        return cells

    def _create_default_constraints(
        self, grid_size: int
    ) -> List[Constraint]:
        """Create default constraints for the grid.

        This is a placeholder that creates constraints with sum=0.
        In practice, you'd need to detect actual constraint values from the image.

        Args:
            grid_size: Size of the grid.

        Returns:
            List[Constraint]: List of constraints.
        """
        constraints = []

        # Add row constraints
        for i in range(grid_size):
            constraints.append(
                Constraint(
                    type="row",
                    index=i,
                    sum=0,  # Placeholder - needs actual detection
                    is_satisfied=False,
                )
            )

        # Add column constraints
        for i in range(grid_size):
            constraints.append(
                Constraint(
                    type="column",
                    index=i,
                    sum=0,  # Placeholder - needs actual detection
                    is_satisfied=False,
                )
            )

        return constraints


def extract_puzzle_from_image(image_path: str) -> PuzzleGrid:
    """Convenience function to extract puzzle from image.

    Args:
        image_path: Path to the image file.

    Returns:
        PuzzleGrid: Extracted puzzle grid.
    """
    extractor = PuzzleOCRExtractor()
    return extractor.extract_from_image(image_path)


def extract_puzzle_from_bytes(image_bytes: bytes) -> PuzzleGrid:
    """Convenience function to extract puzzle from image bytes.

    Args:
        image_bytes: Image data as bytes.

    Returns:
        PuzzleGrid: Extracted puzzle grid.
    """
    extractor = PuzzleOCRExtractor()
    return extractor.extract_from_bytes(image_bytes)
