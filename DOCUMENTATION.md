# Numbers Sum Solver - Complete Documentation

## Overview

The Numbers Sum Solver is a constraint satisfaction problem (CSP) solver designed to solve number-selection puzzles. Given a grid of numbers and sum constraints for rows and columns, the solver determines which numbers should be selected to satisfy all constraints.

## Problem Definition

### Input
- **Grid**: 2D array of cells, each containing a number
- **Constraints**: Target sums for each row and column

### Goal
For each cell, determine if it should be:
- **Selected** (`isSelected = True`): Included in the sum
- **Deselected** (`isSelected = False`): Not included in the sum
- **Undecided** (`isSelected = None`): Cannot be determined yet

### Success Criteria
All constraints are satisfied when the sum of selected cells in each row/column equals the target sum.

---

## Architecture

### Directory Structure
```
numbers-sum-solver/
├── backend/
│   ├── models.py          # Data models (Pydantic)
│   ├── utils.py           # Utility functions
│   ├── solver.py          # Core solving algorithms
│   └── tests/             # Backend unit tests
├── tests/                 # Integration tests
└── DOCUMENTATION.md       # This file
```

---

## API Endpoints

The backend provides three main API endpoints for image processing, puzzle solving, and real-time progress streaming.

### 1. Process Image

**Endpoint:** `POST /api/process-image`

**Description:** Accepts an image file containing a Numbers Sum puzzle grid, processes it using AI/OCR to extract the grid structure, numbers, and constraints.

**Request:**
- **Content-Type:** `multipart/form-data`
- **Body Parameters:**
  - `image` (File, required): The puzzle image file (JPG, PNG, JPEG)

**Response:**
- **Status Code:** `200 OK`
- **Content-Type:** `application/json`
- **Body:**
```json
{
  "grid": {
    "cells": [
      [
        {
          "value": 5,
          "isSelected": null,
          "row": 0,
          "col": 0
        },
        {
          "value": null,
          "isSelected": null,
          "row": 0,
          "col": 1
        }
      ]
    ],
    "constraints": [
      {
        "type": "row",
        "index": 0,
        "sum": 15,
        "is_satisfied": false
      },
      {
        "type": "column",
        "index": 0,
        "sum": 20,
        "is_satisfied": false
      }
    ]
  }
}
```

**Error Responses:**
- `400 Bad Request`: Invalid image format or unreadable image
- `422 Unprocessable Entity`: Image does not contain a valid puzzle grid
- `500 Internal Server Error`: Server processing error

---

### 2. Solve Puzzle

**Endpoint:** `POST /api/solve`

**Description:** Initiates the solving process for a given puzzle grid. Returns a solving session ID that can be used to stream progress updates.

**Request:**
- **Content-Type:** `application/json`
- **Body:** PuzzleGrid object (same format as process-image response)

**Response:**
- **Status Code:** `200 OK`
- **Content-Type:** `application/json`
- **Body:**
```json
{
  "solvingId": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid grid format
- `422 Unprocessable Entity`: Puzzle is unsolvable or has invalid constraints
- `500 Internal Server Error`: Server processing error

---

### 3. Stream Solving Progress

**Endpoint:** `GET /api/solve-stream/:solvingId`

**Description:** Server-Sent Events (SSE) endpoint that streams real-time updates as the puzzle is being solved.

**Request:**
- **Method:** `GET`
- **Path Parameters:**
  - `solvingId` (string, required): The solving session ID from `/api/solve`

**Response:**
- **Content-Type:** `text/event-stream`
- **Stream Format:** Server-Sent Events (SSE)

**Event Types:**

1. **Progress Update Event**
```
data: {"type":"progress","cells":[[{"value":5,"isSelected":true,"row":0,"col":0}]]}
```

2. **Completion Event**
```
data: {"type":"complete","cells":[[{"value":5,"isSelected":true,"row":0,"col":0}]]}
```

3. **Error Event**
```
data: {"type":"error","message":"Puzzle is unsolvable with given constraints"}
```

**Connection Behavior:**
- Stream remains open until puzzle is solved or error occurs
- Progress updates sent at reasonable intervals
- Stream automatically closes after "complete" or "error" event
- Frontend handles reconnection if connection is lost

---

### API Integration Flow

1. User uploads image via `POST /api/process-image`
2. Backend processes image and returns extracted grid
3. User reviews grid and clicks "Solve"
4. Frontend sends grid to `POST /api/solve`
5. Backend returns `solvingId`
6. Frontend establishes SSE connection to `GET /api/solve-stream/:solvingId`
7. Backend streams progress updates as it solves
8. Frontend updates UI in real-time with each event
9. Backend sends "complete" event when solved
10. Connection closes automatically

---

### Security Considerations

- Limit file upload sizes (max 10MB recommended)
- Validate image formats and sanitize inputs
- Implement rate limiting on API endpoints
- Set appropriate CORS headers
- Use authentication for production deployment

---

## Data Models

### `GridCell`
Represents a single cell in the puzzle grid.

**Attributes:**
- `value: Optional[int]` - The number in the cell (None if empty)
- `isSelected: Optional[bool]` - Selection state (True/False/None)
- `row: int` - Zero-based row index
- `col: int` - Zero-based column index

### `Constraint`
Represents a sum constraint for a row or column.

**Attributes:**
- `type: Literal["row", "column"]` - Constraint type
- `index: int` - Zero-based row/column index
- `sum: int` - Target sum
- `is_satisfied: bool` - Whether constraint is satisfied (default: False)

### `PuzzleGrid`
Complete puzzle representation.

**Attributes:**
- `cells: List[List[GridCell]]` - 2D array of cells
- `constraints: List[Constraint]` - List of sum constraints

---

## Core Algorithms

### 1. Combination Finding: `sums_composite`

**Purpose**: Find all combinations of numbers that sum to a target.

**Algorithm**: Backtracking with pruning
- Sorts candidates for efficient pruning
- Handles duplicate values correctly (treats each position as distinct)
- Skips duplicate combinations at same recursion level
- Cached with LRU cache for performance

**Example:**
```python
sums_composite(10, (1, 2, 3, 4, 5, 5, 7))
# Returns: [[2, 3, 5], [3, 7], [5, 5], [1, 4, 5], [1, 2, 7], [1, 2, 3, 4]]
```

**Complexity**: O(2^n) worst case, but heavily optimized with pruning

---

### 2. Essential Value Detection: `get_essential_values_with_counts`

**Purpose**: Identify values that MUST be selected based on frequency analysis.

**Algorithm**:
1. Count frequency of each value in available cells
2. Count frequency of each value in each possible combination
3. A value is essential if:
   - It appears with the SAME frequency in ALL combinations, AND
   - That frequency equals the available count

**Why This Matters - The Duplicate Problem:**

Consider: `[5, 5, 5]` with target sum 10
- Possible combinations: `[[5, 5]]`
- We have 3 instances of 5, but only need 2
- **Problem**: Which two 5s should we select?
- **Solution**: Don't select any - leave as undecided (None)

The algorithm prevents incorrect selections by checking if we need ALL available instances.

**Examples:**

✅ **Can Select:**
```python
combos = [[5, 5]]
available = [5, 5]  # Exactly 2 instances
# Result: {5: 2} - Both 5s are essential
```

❌ **Cannot Select:**
```python
combos = [[5, 5]]
available = [5, 5, 5]  # 3 instances, only need 2
# Result: {} - Not essential (ambiguous)
```

---

### 3. Elimination and Selection: `solve_by_elimination_and_selection`

**Purpose**: Main solving strategy that processes each constraint.

**Algorithm Flow:**

For each unsatisfied constraint:

1. **Calculate remaining sum**
   ```python
   known_sum = sum of already selected cells
   remaining_sum = target_sum - known_sum
   ```

2. **Check if constraint is satisfied**
   ```python
   if remaining_sum <= 0:
       mark constraint as satisfied
       deselect all remaining cells
       continue to next constraint
   ```

3. **Find possible combinations**
   ```python
   combos = sums_composite(remaining_sum, remaining_cell_values)
   ```

4. **Identify essential values**
   ```python
   essential_values = get_essential_values_with_counts(combos, available_values)
   ```

5. **Apply selection/deselection**
   ```python
   for each cell:
       if value is essential:
           select cell
       if value not in any combination:
           deselect cell
   ```

6. **Mark constraint as satisfied if complete**
   ```python
   if selected_sum == target_sum and no undecided cells:
       mark constraint as satisfied
   ```

**Why Step 6 is Important:**
- **Performance**: Avoids unnecessary iterations
- **Early termination**: Solver can stop as soon as all constraints satisfied
- **Accuracy**: Properly tracks which constraints are solved

---

### 4. Iterative Solver: `main_solver`

**Purpose**: Repeatedly apply solving strategy until grid is solved or stuck.

**Algorithm:**
```python
iteration = 0
while iteration < max_iterations:
    # Check if all constraints satisfied
    if is_grid_solved(grid):
        break
    
    # Save state to detect progress
    grid_before = grid.copy()
    
    # Apply solving strategy
    grid = solve_by_elimination_and_selection(grid)
    
    # Check if we made progress
    if not has_grid_changed(grid_before, grid):
        break  # Stuck - no more progress possible
    
    iteration += 1

return grid
```

**Termination Conditions:**
1. **Success**: All constraints satisfied (`is_grid_solved()` returns True)
2. **Stuck**: No cells changed state (solver can't make progress)
3. **Safety**: Max iterations reached (default: 100)

**Design Decision - No `is_solved` Attribute:**

Instead of adding `is_solved` to the model, we compute it:
- ✅ **Single source of truth**: Derived from constraint satisfaction
- ✅ **No synchronization**: Can't have inconsistent state
- ✅ **Cleaner model**: Separates data from computed state
- ✅ **Always accurate**: Computed on-demand from actual data

---

## Utility Functions

### Grid State Management

#### `is_grid_solved(grid: PuzzleGrid) -> bool`
Checks if all constraints are satisfied.

#### `has_grid_changed(grid_before, grid_after) -> bool`
Detects if any cell's selection state changed between two grids.

#### `get_cells_of(constraint, grid) -> List[GridCell]`
Returns all cells belonging to a constraint (row or column).

---

## Algorithm Complexity Analysis

### Time Complexity

**Per Iteration:**
- For each constraint (c constraints):
  - Get cells: O(n) where n = grid dimension
  - Find combinations: O(2^k) where k = remaining cells
  - Essential value detection: O(m × k) where m = combinations
  - Apply selections: O(k)
- **Total per iteration**: O(c × 2^k)

**Full Solve:**
- Typical: 1-5 iterations
- Worst case: O(max_iterations × c × 2^k)

### Space Complexity

- Grid storage: O(n²)
- Combinations: O(2^k) worst case
- State snapshot: O(n²)
- **Total**: O(n² + 2^k)

### Optimizations

1. **LRU Cache**: `sums_composite` results cached
2. **Early termination**: Stop when constraints satisfied
3. **Pruning**: Skip impossible combinations early
4. **Constraint satisfaction tracking**: Avoid reprocessing solved constraints

---

## Usage Examples

### Basic Usage

```python
from backend.models import PuzzleGrid, GridCell, Constraint
from backend.solver import main_solver

# Create grid
cells = [
    [GridCell(row=0, col=0, value=1, isSelected=None),
     GridCell(row=0, col=1, value=2, isSelected=None)],
    [GridCell(row=1, col=0, value=3, isSelected=None),
     GridCell(row=1, col=1, value=4, isSelected=None)]
]

# Define constraints
constraints = [
    Constraint(type="row", index=0, sum=3),     # Row 0: 1+2=3
    Constraint(type="row", index=1, sum=7),     # Row 1: 3+4=7
    Constraint(type="column", index=0, sum=4),  # Col 0: 1+3=4
    Constraint(type="column", index=1, sum=6)   # Col 1: 2+4=6
]

grid = PuzzleGrid(cells=cells, constraints=constraints)

# Solve
result = main_solver(grid)

# Check results
from backend.utils import is_grid_solved
if is_grid_solved(result):
    print("Solved!")
else:
    print("Partial solution")
```

### Handling Results

```python
# Iterate through results
for i, row in enumerate(result.cells):
    for j, cell in enumerate(row):
        if cell.isSelected is True:
            print(f"Cell ({i},{j}): {cell.value} ✓ SELECTED")
        elif cell.isSelected is False:
            print(f"Cell ({i},{j}): {cell.value} ✗ DESELECTED")
        else:
            print(f"Cell ({i},{j}): {cell.value} ? UNDECIDED")
```

---

## Edge Cases and Limitations

### Handled Edge Cases

1. **Duplicate Values**: Correctly handles multiple instances of same number
2. **Ambiguous Cases**: Leaves cells undecided when can't determine selection
3. **Empty Combinations**: Handles cases with no valid combinations
4. **Already Satisfied**: Skips constraints that are already satisfied

### Current Limitations

1. **Single Strategy**: Only uses elimination/selection (no backtracking)
2. **Stuck Detection**: May leave some cells undecided if logic insufficient
3. **No Heuristics**: Doesn't prioritize constraints by difficulty

### When Solver Gets Stuck

The solver may not fully solve a puzzle if:
- Multiple valid solutions exist
- Advanced techniques required (e.g., trial and error)
- Constraints are contradictory

In these cases, the solver returns a partial solution with some cells still `None`.

---

## Testing

### Test Coverage

**Unit Tests** (`tests/test_utility_functions.py`):
- `sums_composite` function
- `get_essential_values_with_counts` function
- Edge cases and boundary conditions

**Integration Tests** (`tests/test_duplicate_handling.py`):
- Duplicate value handling
- Exact match scenarios
- Mixed values with duplicates
- Selection and deselection logic

**Solver Tests** (`tests/test_iterative_solver.py`):
- Multi-iteration solving
- Stuck detection
- Complex grid solving
- Constraint satisfaction

### Running Tests

```bash
# Run all tests
python3 tests/test_utility_functions.py
python3 tests/test_duplicate_handling.py
python3 tests/test_iterative_solver.py

# Or with pytest
pytest tests/
```

---

## Performance Characteristics

### Best Case
- Simple grids with unique solutions
- Few constraints
- Small number of cells per constraint
- **Time**: O(c × n) - linear in constraints and cells

### Average Case
- Typical puzzle grids (7x7 to 10x10)
- Multiple iterations needed
- Some ambiguous cells
- **Time**: O(i × c × 2^k) where i ≈ 3-5 iterations

### Worst Case
- Large grids with many possibilities
- Highly ambiguous constraints
- Solver gets stuck early
- **Time**: O(max_iterations × c × 2^k)

---

## Future Enhancements

### Potential Improvements

1. **Backtracking**: Try different selections when stuck
2. **Constraint Propagation**: More advanced CSP techniques
3. **Heuristics**: Prioritize easier constraints first
4. **Parallel Processing**: Process independent constraints simultaneously
5. **Solution Validation**: Verify final solution correctness
6. **Multiple Solutions**: Find all possible solutions

### Extensibility

The modular design allows easy addition of:
- New solving strategies
- Different constraint types
- Custom heuristics
- Progress callbacks
- Visualization hooks

---

## Conclusion

The Numbers Sum Solver uses a combination of:
- **Backtracking** for finding combinations
- **Frequency analysis** for handling duplicates
- **Iterative refinement** for progressive solving
- **Constraint satisfaction tracking** for efficiency

The design prioritizes:
- ✅ **Correctness**: Handles edge cases properly
- ✅ **Efficiency**: Caching and early termination
- ✅ **Maintainability**: Clean, modular code
- ✅ **Testability**: Comprehensive test coverage

The solver is production-ready for typical puzzle grids and can be extended with additional strategies for more complex scenarios.
