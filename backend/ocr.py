"""
OCR module for extracting puzzle grids from images using RapidOCR.

This module uses RapidOCR to detect and extract numbers from puzzle grid images.
"""

from typing import List, Tuple, Optional, Union
from pathlib import Path
import re
import io

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from rapidocr import RapidOCR
from rapidocr.utils.output import RapidOCROutput
from .models import PuzzleGrid, GridCell, Constraint


class PuzzleOCRExtractor:
    """Extract puzzle grid data from images using OCR."""

    def __init__(self, enable_preprocessing: bool = True):
        """Initialize the OCR engine.
        
        Args:
            enable_preprocessing: Whether to apply image preprocessing before OCR.
        """
        self.engine = RapidOCR()
        self.enable_preprocessing = enable_preprocessing

    def _preprocess_image(self, image: Union[str, bytes, Image.Image]) -> bytes:
        """Preprocess image to improve OCR accuracy.
        
        Applies contrast enhancement, sharpening, and binarization.
        
        Args:
            image: Image file path, bytes, or PIL Image object.
            
        Returns:
            Preprocessed image as bytes.
        """
        # Load image
        if isinstance(image, str):
            img = Image.open(image)
        elif isinstance(image, bytes):
            img = Image.open(io.BytesIO(image))
        elif isinstance(image, Image.Image):
            img = image
        else:
            raise ValueError("Image must be a file path, bytes, or PIL Image")
        
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 1. Increase contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(3)  # Increase contrast by 80%
        
        # 2. Increase sharpness
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.5)  # Double the sharpness
        
        # 3. Apply unsharp mask for additional sharpening
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        
        # 4. Convert to grayscale
        img = img.convert('L')
        
        # 5. Apply auto-contrast
        img_array = np.array(img)
        img = Image.fromarray(img_array)
        img = ImageOps.autocontrast(img, cutoff=2)
        
        # Convert back to RGB for OCR engine
        img = img.convert('RGB')
        
        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()

    def extract_from_image(self, image_path: str) -> PuzzleGrid:
        """Extract puzzle grid from an image file.

        Args:
            image_path: Path to the image file.

        Returns:
            PuzzleGrid: Extracted puzzle grid with cells and constraints.

        Raises:
            ValueError: If the image cannot be processed or grid cannot be extracted.
        """
        # Preprocess image if enabled
        if self.enable_preprocessing:
            image_data = self._preprocess_image(image_path)
            ocr_result = self.engine(image_data)
        else:
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
        # Preprocess image if enabled
        try:
            if self.enable_preprocessing:
                image_data = self._preprocess_image(image_bytes)
                ocr_result = self.engine(image_data)
            else:
                ocr_result = self.engine(image_bytes)
        except Exception as e:
            raise ValueError(f"Failed to process image: {str(e)}")

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

        # Filter out numbers with area less than 50% of median
        # These are likely small corner annotations
        threshold = median_area * 0.5
        filtered = [n for n in numbers if n["area"] >= threshold]

        return filtered if filtered else numbers

    def _separate_constraints_and_grid(self, numbers: List[dict]) -> PuzzleGrid:
        """Separate constraint sums from grid cells.

        Identifies column constraints as cells in the top row (lowest y values with margin),
        and row constraints as cells in the leftmost column (lowest x values with margin).

        Args:
            numbers: Sorted list of detected numbers.

        Returns:
            PuzzleGrid with properly separated constraints and cells.

        Raises:
            ValueError: If grid structure cannot be determined.
        """
        if len(numbers) < 3:
            raise ValueError("Not enough numbers detected for valid grid")

        # Calculate median height and width for margin of error
        heights = [n["height"] for n in numbers]
        widths = [n["width"] for n in numbers]
        median_height = sorted(heights)[len(heights) // 2]
        median_width = sorted(widths)[len(widths) // 2]
        
        # Use median height/width as margin of error for grouping
        # Increased margins to account for slight variations in OCR detection
        y_margin = median_height * 0.6
        x_margin = median_width * 0.6

        # Find minimum y-coordinate (top row) by getting average of lowest y values
        y_coords = sorted([n["top_left_y"] for n in numbers])
        # Take average of first few cells to get the top row baseline
        min_y = sum(y_coords[:7]) / 7  # Average of first 7 (likely the column constraints)
        
        # Find minimum x-coordinate (leftmost column) by getting average of lowest x values
        x_coords = sorted([n["top_left_x"] for n in numbers])
        # Take average of first few cells to get the left column baseline
        min_x = sum(x_coords[:7]) / 7  # Average of first 7 (likely the row constraints)

        # Identify column constraints: cells with y-coordinate within margin of min_y
        col_constraint_cells = []
        col_constraint_ids = set()
        for num in numbers:
            if abs(num["top_left_y"] - min_y) <= y_margin:
                col_constraint_cells.append(num)
                col_constraint_ids.add(id(num))

        # Identify row constraint cells: cells with x-coordinate within margin of min_x
        # BUT exclude cells that are already column constraints
        row_constraint_cells = []
        for num in numbers:
            if abs(num["top_left_x"] - min_x) <= x_margin:
                # Check if this cell is not already a column constraint
                if id(num) not in col_constraint_ids:
                    row_constraint_cells.append(num)

        # Grid cells are all other cells (not in constraints)
        constraint_set = set(id(c) for c in col_constraint_cells + row_constraint_cells)
        grid_cells_flat = [n for n in numbers if id(n) not in constraint_set]

        if not col_constraint_cells:
            raise ValueError("No column constraints detected")
        
        if not row_constraint_cells:
            raise ValueError("No row constraints detected")

        # Sort column constraints by x-coordinate (left to right)
        col_constraint_cells.sort(key=lambda x: x["top_left_x"])
        
        # Sort row constraints by y-coordinate (top to bottom)
        row_constraint_cells.sort(key=lambda x: x["top_left_y"])

        # Create constraint objects
        col_constraints = []
        for col_idx, num_item in enumerate(col_constraint_cells):
            col_constraints.append(Constraint(
                type="column",
                index=col_idx,
                sum=num_item["value"],
                is_satisfied=False,
            ))

        row_constraints = []
        for row_idx, num_item in enumerate(row_constraint_cells):
            row_constraints.append(Constraint(
                type="row",
                index=row_idx,
                sum=num_item["value"],
                is_satisfied=False,
            ))

        # Organize grid cells into 2D structure
        # Cluster grid cells by rows using y-coordinate
        grid_rows = self._cluster_into_rows(grid_cells_flat)
        
        # Sort each row by x-coordinate
        for row in grid_rows:
            row.sort(key=lambda x: x["top_left_x"])

        # Determine expected dimensions
        expected_rows = len(row_constraints)
        expected_cols = len(col_constraints)

        # Build cells matrix
        cells = []
        for row_idx in range(expected_rows):
            row_cells = []
            if row_idx < len(grid_rows):
                for col_idx in range(expected_cols):
                    if col_idx < len(grid_rows[row_idx]):
                        num_item = grid_rows[row_idx][col_idx]
                        cell = GridCell(
                            row=row_idx,
                            col=col_idx,
                            value=num_item["value"],
                            isSelected=None,
                        )
                    else:
                        cell = GridCell(
                            row=row_idx,
                            col=col_idx,
                            value=None,
                            isSelected=None,
                        )
                    row_cells.append(cell)
            else:
                # Fill missing rows with None cells
                for col_idx in range(expected_cols):
                    row_cells.append(GridCell(
                        row=row_idx,
                        col=col_idx,
                        value=None,
                        isSelected=None,
                    ))
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
