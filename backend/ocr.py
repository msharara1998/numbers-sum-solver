"""
OCR module for extracting puzzle grids from images using RapidOCR.

This module uses RapidOCR to detect and extract numbers from puzzle grid images.
"""

from typing import List, Tuple, Optional
from pathlib import Path
import re

from rapidocr import RapidOCR
from rapidocr.utils.output import RapidOCROutput
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
        ocr_result = self.engine(image_path)

        if not isinstance(ocr_result, RapidOCROutput):
            raise ValueError("Unexpected OCR output format")

        if not ocr_result or len(ocr_result) == 0:
            raise ValueError("No text detected in image")

        # Extract text and bounding boxes from RapidOCROutput
        texts_with_boxes = []
        if ocr_result.boxes is not None and ocr_result.txts is not None and ocr_result.scores is not None:
            for box, text, confidence in zip(ocr_result.boxes, ocr_result.txts, ocr_result.scores):
                texts_with_boxes.append({
                    "text": text,
                    "box": box,
                    "confidence": confidence,
                })

        if not texts_with_boxes:
            raise ValueError("No text detected in image")

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
        ocr_result = self.engine(image_bytes)

        if not isinstance(ocr_result, RapidOCROutput):
            raise ValueError("Unexpected OCR output format")

        if not ocr_result or len(ocr_result) == 0:
            raise ValueError("No text detected in image")

        # Extract text and bounding boxes from RapidOCROutput
        texts_with_boxes = []
        if ocr_result.boxes is not None and ocr_result.txts is not None and ocr_result.scores is not None:
            for box, text, confidence in zip(ocr_result.boxes, ocr_result.txts, ocr_result.scores):
                texts_with_boxes.append({
                    "text": text,
                    "box": box,
                    "confidence": confidence,
                })

        if not texts_with_boxes:
            raise ValueError("No text detected in image")

        # Parse the detected text into grid structure
        grid = self._parse_grid_from_ocr(texts_with_boxes)

        return grid

    def _parse_grid_from_ocr(
        self, texts_with_boxes: List[dict]
    ) -> PuzzleGrid:
        """Parse OCR results into a puzzle grid.

        Args:
            texts_with_boxes: List of detected text with bounding boxes.

        Returns:
            PuzzleGrid: Parsed puzzle grid.

        Raises:
            ValueError: If grid structure cannot be determined.
        """
        # Extract numbers from detected text with bounding box info
        numbers = []
        for item in texts_with_boxes:
            text = item["text"].strip()
            # Try to extract number
            if text.isdigit():
                # Get bounding box dimensions
                box = item["box"]
                top_left_x = float(box[0][0]) if hasattr(box[0], '__getitem__') else float(box[0])
                top_left_y = float(box[0][1]) if hasattr(box[0], '__getitem__') else float(box[1])
                bottom_right_x = float(box[2][0]) if hasattr(box[2], '__getitem__') else float(box[4])
                bottom_right_y = float(box[2][1]) if hasattr(box[2], '__getitem__') else float(box[5])
                
                # Calculate bounding box area
                width = abs(bottom_right_x - top_left_x)
                height = abs(bottom_right_y - top_left_y)
                area = width * height
                
                numbers.append({
                    "value": int(text),
                    "box": item["box"],
                    "confidence": item["confidence"],
                    "top_left_x": top_left_x,
                    "top_left_y": top_left_y,
                    "width": width,
                    "height": height,
                    "area": area,
                })

        if not numbers:
            raise ValueError("No numbers detected in image")

        # Filter out small corner annotations by comparing bbox areas
        numbers = self._filter_small_annotations(numbers)

        if not numbers:
            raise ValueError("No valid numbers detected after filtering")

        # Sort numbers by position (top to bottom, left to right)
        numbers.sort(key=lambda x: (x["top_left_y"], x["top_left_x"]))

        # Separate constraints from grid cells
        # First row = column constraints, first column = row constraints
        grid_with_constraints = self._separate_constraints_and_grid(numbers)

        return grid_with_constraints

    def _filter_small_annotations(self, numbers: List[dict]) -> List[dict]:
        """Filter out small corner annotations by comparing bounding box areas.

        Args:
            numbers: List of detected numbers with bbox information.

        Returns:
            List of numbers with small annotations removed.
        """
        if len(numbers) < 3:
            return numbers

        # Calculate median area
        areas = [n["area"] for n in numbers]
        areas_sorted = sorted(areas)
        median_area = areas_sorted[len(areas_sorted) // 2]

        # Filter out numbers with area less than 30% of median
        # These are likely small corner annotations
        threshold = median_area * 0.3
        filtered = [n for n in numbers if n["area"] >= threshold]

        return filtered if filtered else numbers

    def _separate_constraints_and_grid(self, numbers: List[dict]) -> PuzzleGrid:
        """Separate constraint sums from grid cells.

        Assumes first row contains column constraints and first column contains row constraints.

        Args:
            numbers: Sorted list of detected numbers.

        Returns:
            PuzzleGrid with properly separated constraints and cells.

        Raises:
            ValueError: If grid structure cannot be determined.
        """
        # Group numbers by rows using y-coordinate clustering
        rows = self._cluster_into_rows(numbers)

        if len(rows) < 2:
            raise ValueError("Not enough rows detected for valid grid")

        # Sort each row by x-coordinate
        grid_2d = []
        for row_numbers in rows:
            row_numbers_sorted = sorted(row_numbers, key=lambda x: x["top_left_x"])
            grid_2d.append(row_numbers_sorted)
        
        # Find the column with most numbers (this should be the actual grid width)
        max_cols = max(len(row) for row in grid_2d)
        
        # The first row should contain column constraints
        # If first row has fewer elements than max, we need to identify which row is actually the constraint row
        # by finding the row with largest average height (constraint numbers are typically larger)
        if len(grid_2d[0]) < max_cols:
            # Find row with largest average height
            row_heights = []
            for row_idx, row in enumerate(grid_2d):
                if len(row) > 0:
                    avg_height = sum(n["height"] for n in row) / len(row)
                    row_heights.append((row_idx, avg_height, len(row)))
            
            # Sort by height (descending) to find constraint row
            row_heights.sort(key=lambda x: x[1], reverse=True)
            
            # The row with largest average height and at least max_cols-1 elements is likely the constraint row
            constraint_row_idx = 0
            for idx, height, length in row_heights:
                if length >= max_cols - 1:  # Allow for 1 missing element
                    constraint_row_idx = idx
                    break
            
            # If constraint row is not first, swap it to first position
            if constraint_row_idx != 0:
                grid_2d[0], grid_2d[constraint_row_idx] = grid_2d[constraint_row_idx], grid_2d[0]

        # Determine the expected number of columns (should be number of elements in first row)
        # This represents the column constraint count
        expected_cols = len(grid_2d[0])
        
        # Pad all other rows to match the expected column count
        for i in range(1, len(grid_2d)):
            if len(grid_2d[i]) < expected_cols:
                # Pad with None placeholders
                grid_2d[i] = grid_2d[i] + [None] * (expected_cols - len(grid_2d[i]))
            elif len(grid_2d[i]) > expected_cols:
                # Trim to expected size
                grid_2d[i] = grid_2d[i][:expected_cols]

        # Extract constraints: first row = column sums, first column = row sums
        col_constraints = []
        row_constraints = []

        # First row = column constraints (all numbers in first row)
        for col_idx, num_item in enumerate(grid_2d[0]):
            if num_item is not None:
                col_constraints.append(Constraint(
                    type="column",
                    index=col_idx,
                    sum=num_item["value"],
                    is_satisfied=False,
                ))

        # First column = row constraints (skip first row since it's already used for column constraints)
        for row_idx in range(1, len(grid_2d)):
            num_item = grid_2d[row_idx][0]
            if num_item is not None:
                row_constraints.append(Constraint(
                    type="row",
                    index=row_idx - 1,
                    sum=num_item["value"],
                    is_satisfied=False,
                ))

        # Extract grid cells (skip first row and first column)
        cells = []
        for row_idx in range(1, len(grid_2d)):
            row_cells = []
            for col_idx in range(1, len(grid_2d[row_idx])):
                num_item = grid_2d[row_idx][col_idx]
                cell = GridCell(
                    row=row_idx - 1,
                    col=col_idx - 1,
                    value=num_item["value"] if num_item is not None else None,
                    isSelected=None,
                )
                row_cells.append(cell)
            cells.append(row_cells)

        constraints = row_constraints + col_constraints

        return PuzzleGrid(cells=cells, constraints=constraints)

    def _cluster_into_rows(self, numbers: List[dict]) -> List[List[dict]]:
        """Cluster numbers into rows based on y-coordinates.

        Args:
            numbers: List of numbers with position information.

        Returns:
            List of rows, where each row is a list of numbers.
        """
        if not numbers:
            return []

        # Sort by y-coordinate
        sorted_numbers = sorted(numbers, key=lambda x: x["top_left_y"])

        # Use median height as threshold for row separation
        heights = [n["height"] for n in sorted_numbers]
        median_height = sorted(heights)[len(heights) // 2]
        row_threshold = median_height * 0.6  # Increased threshold for more robust clustering

        rows = []
        current_row = [sorted_numbers[0]]

        for num in sorted_numbers[1:]:
            # Calculate average y-coordinate of current row for more accurate clustering
            current_avg_y = sum(n["top_left_y"] for n in current_row) / len(current_row)
            
            # If y-coordinate is close to current row average, add to current row
            if abs(num["top_left_y"] - current_avg_y) < row_threshold:
                current_row.append(num)
            else:
                # Start new row
                rows.append(current_row)
                current_row = [num]

        # Add last row
        if current_row:
            rows.append(current_row)

        return rows




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
