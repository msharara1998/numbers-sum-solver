"""
Test suite for the API endpoints.

Tests all API endpoints including solving, validation, and mock endpoints.
"""

from fastapi.testclient import TestClient

from backend.api import app


# Create test client
client = TestClient(app)


def test_process_image_not_implemented():
    """Test that process-image endpoint returns 501 Not Implemented."""
    print("\nTest: Process image not implemented")

    # Create a dummy file
    files = {"image": ("test.jpg", b"fake image data", "image/jpeg")}

    response = client.post("/api/process-image", files=files)

    assert response.status_code == 501
    assert "not implemented" in response.json()["detail"].lower()

    print("✓ Process image not implemented test passed")


def test_mock_process_image():
    """Test mock process-image endpoint returns valid grid."""
    print("\nTest: Mock process image")

    response = client.post("/api/test/mock-process")

    assert response.status_code == 200
    data = response.json()

    # Check structure
    assert "grid" in data
    assert "cells" in data["grid"]
    assert "constraints" in data["grid"]

    # Check it's a 2x2 grid
    assert len(data["grid"]["cells"]) == 2
    assert len(data["grid"]["cells"][0]) == 2

    # Check constraints exist
    assert len(data["grid"]["constraints"]) == 4

    # Verify cell structure
    first_cell = data["grid"]["cells"][0][0]
    assert "value" in first_cell
    assert "isSelected" in first_cell
    assert "row" in first_cell
    assert "col" in first_cell

    print("✓ Mock process-image test passed")


def test_solve_puzzle_valid_grid():
    """Test solving a valid puzzle grid."""
    print("\nTest: Solve valid puzzle grid")

    # Create a simple 2x2 grid
    grid_data = {
        "cells": [
            [
                {"value": 1, "isSelected": None, "row": 0, "col": 0},
                {"value": 2, "isSelected": None, "row": 0, "col": 1},
            ],
            [
                {"value": 3, "isSelected": None, "row": 1, "col": 0},
                {"value": 4, "isSelected": None, "row": 1, "col": 1},
            ],
        ],
        "constraints": [
            {"type": "row", "index": 0, "sum": 3, "is_satisfied": False},
            {"type": "row", "index": 1, "sum": 7, "is_satisfied": False},
            {"type": "column", "index": 0, "sum": 4, "is_satisfied": False},
            {"type": "column", "index": 1, "sum": 6, "is_satisfied": False},
        ],
    }

    response = client.post("/api/solve", json=grid_data)

    assert response.status_code == 200
    data = response.json()

    # Check solving ID is returned
    assert "solvingId" in data
    assert len(data["solvingId"]) > 0

    # Verify it's a valid UUID format
    solving_id = data["solvingId"]
    parts = solving_id.split("-")
    assert len(parts) == 5  # UUID format: 8-4-4-4-12

    print("✓ Solve puzzle test passed")


def test_solve_puzzle_empty_grid():
    """Test solving with empty grid returns error."""
    print("\nTest: Empty grid validation")

    grid_data = {
        "cells": [],
        "constraints": [],
    }

    response = client.post("/api/solve", json=grid_data)

    assert response.status_code == 400
    assert "cells and constraints" in response.json()["detail"]

    print("✓ Empty grid validation test passed")


def test_solve_puzzle_missing_constraints():
    """Test solving with missing constraints returns error."""
    print("\nTest: Missing constraints validation")

    grid_data = {
        "cells": [
            [
                {"value": 1, "isSelected": None, "row": 0, "col": 0},
            ]
        ],
        "constraints": [],
    }

    response = client.post("/api/solve", json=grid_data)

    assert response.status_code == 400

    print("✓ Missing constraints validation test passed")


def test_solve_puzzle_missing_cells():
    """Test solving with missing cells returns error."""
    print("\nTest: Missing cells validation")

    grid_data = {
        "cells": [],
        "constraints": [
            {"type": "row", "index": 0, "sum": 10, "is_satisfied": False},
        ],
    }

    response = client.post("/api/solve", json=grid_data)

    assert response.status_code == 400

    print("✓ Missing cells validation test passed")


def test_solve_stream_invalid_session():
    """Test streaming with invalid session ID returns 404."""
    print("\nTest: Invalid session ID")

    response = client.get("/api/solve-stream/invalid-uuid-12345")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

    print("✓ Invalid session test passed")


def test_mock_solve():
    """Test mock solve endpoint."""
    print("\nTest: Mock solve")

    grid_data = {
        "cells": [[{"value": 1, "isSelected": None, "row": 0, "col": 0}]],
        "constraints": [{"type": "row", "index": 0, "sum": 1, "is_satisfied": False}],
    }

    response = client.post("/api/test/mock-solve", json=grid_data)

    assert response.status_code == 200
    data = response.json()

    assert "solvingId" in data
    assert len(data["solvingId"]) > 0

    print("✓ Mock solve test passed")


def test_solve_multiple_grids():
    """Test solving multiple grids creates different sessions."""
    print("\nTest: Multiple grid sessions")

    grid_data = {
        "cells": [[{"value": 5, "isSelected": None, "row": 0, "col": 0}]],
        "constraints": [{"type": "row", "index": 0, "sum": 5, "is_satisfied": False}],
    }

    # Solve first grid
    response1 = client.post("/api/solve", json=grid_data)
    assert response1.status_code == 200
    solving_id1 = response1.json()["solvingId"]

    # Solve second grid
    response2 = client.post("/api/solve", json=grid_data)
    assert response2.status_code == 200
    solving_id2 = response2.json()["solvingId"]

    # IDs should be different
    assert solving_id1 != solving_id2

    print("✓ Multiple grid sessions test passed")


def test_grid_with_various_constraint_types():
    """Test grid with both row and column constraints."""
    print("\nTest: Mixed constraint types")

    grid_data = {
        "cells": [
            [
                {"value": 1, "isSelected": None, "row": 0, "col": 0},
                {"value": 2, "isSelected": None, "row": 0, "col": 1},
            ]
        ],
        "constraints": [
            {"type": "row", "index": 0, "sum": 3, "is_satisfied": False},
            {"type": "column", "index": 0, "sum": 1, "is_satisfied": False},
            {"type": "column", "index": 1, "sum": 2, "is_satisfied": False},
        ],
    }

    response = client.post("/api/solve", json=grid_data)

    assert response.status_code == 200
    assert "solvingId" in response.json()

    print("✓ Mixed constraint types test passed")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Testing API Endpoints")
    print("=" * 60)

    test_process_image_not_implemented()
    test_mock_process_image()
    test_solve_puzzle_valid_grid()
    test_solve_puzzle_empty_grid()
    test_solve_puzzle_missing_constraints()
    test_solve_puzzle_missing_cells()
    test_solve_stream_invalid_session()
    test_mock_solve()
    test_solve_multiple_grids()
    test_grid_with_various_constraint_types()

    print("\n" + "=" * 60)
    print("All API tests passed! ✓")
    print("=" * 60 + "\n")
