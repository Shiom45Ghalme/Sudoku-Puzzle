from flask import Flask, render_template, request
import json
import copy

app = Flask(__name__)

def is_valid(board, row, col, num):
    # Check row and column
    for i in range(9):
        if board[row][i] == num or board[i][col] == num:
            return False
    
    # Check 3x3 box
    start_row, start_col = 3 * (row // 3), 3 * (col // 3)
    for i in range(3):
        for j in range(3):
            if board[start_row + i][start_col + j] == num:
                return False
    
    return True

def solve_sudoku_with_steps(board):
    steps = []
    if solve_sudoku_step(board, steps):
        return True, steps
    return False, []

def solve_sudoku_step(board, steps):
    # Find an empty cell
    empty_cell = find_empty(board)
    if not empty_cell:
        return True  # Puzzle is solved
    
    row, col = empty_cell
    
    # Try each number 1-9
    for num in range(1, 10):
        if is_valid(board, row, col, num):
            # Place the number
            board[row][col] = num
            
            # Record this step
            steps.append({"row": row, "col": col, "value": num})
            
            # Recursively try to solve the rest
            if solve_sudoku_step(board, steps):
                return True
            
            # If we get here, this number didn't work
            # Remove the step
            steps.pop()
            
            # Backtrack
            board[row][col] = 0
    
    return False

def find_empty(board):
    for i in range(9):
        for j in range(9):
            if board[i][j] == 0:
                return (i, j)
    return None

def find_multiple_solutions(board, max_solutions=10):
    solutions = []
    find_all_solutions(copy.deepcopy(board), solutions, max_solutions)
    return solutions

def find_all_solutions(board, solutions, max_solutions):
    if len(solutions) >= max_solutions:
        return
    
    steps = []
    board_copy = copy.deepcopy(board)
    
    if find_solution_recursive(board_copy, steps):
        solution = {
            "board": copy.deepcopy(board_copy),
            "steps": steps
        }
        
        # Check if this is a unique solution
        is_unique = True
        for existing_solution in solutions:
            if boards_equal(existing_solution["board"], board_copy):
                is_unique = False
                break
        
        if is_unique:
            solutions.append(solution)
            
            # Find another solution by altering the first filled cell
            if len(solutions) < max_solutions:
                find_another_solution(board, solutions, max_solutions)

def find_solution_recursive(board, steps):
    empty_cell = find_empty(board)
    if not empty_cell:
        return True
    
    row, col = empty_cell
    
    for num in range(1, 10):
        if is_valid(board, row, col, num):
            board[row][col] = num
            steps.append({"row": row, "col": col, "value": num})
            
            if find_solution_recursive(board, steps):
                return True
            
            steps.pop()
            board[row][col] = 0
    
    return False

def find_another_solution(original_board, solutions, max_solutions):
    # Make a copy of the original board
    board = copy.deepcopy(original_board)
    
    # Find the first filled cell from the last solution
    if not solutions:
        return
    
    last_solution = solutions[-1]
    if not last_solution["steps"]:
        return
    
    # Try a different approach - block one of the solutions
    first_step = last_solution["steps"][0]
    row, col, value = first_step["row"], first_step["col"], first_step["value"]
    
    # Temporarily block this value at this position
    board[row][col] = -1  # Mark as blocked
    
    # Find new solutions
    steps = []
    board_copy = copy.deepcopy(board)
    if find_solution_with_blocked(board_copy, steps, row, col, value):
        solution = {
            "board": copy.deepcopy(board_copy),
            "steps": steps
        }
        
        # Check if this is a unique solution
        is_unique = True
        for existing_solution in solutions:
            if boards_equal(existing_solution["board"], board_copy):
                is_unique = False
                break
        
        if is_unique:
            solutions.append(solution)
            
            # Find more solutions
            if len(solutions) < max_solutions:
                find_another_solution(original_board, solutions, max_solutions)

def find_solution_with_blocked(board, steps, blocked_row, blocked_col, blocked_value):
    empty_cell = find_empty(board)
    if not empty_cell:
        return True
    
    row, col = empty_cell
    
    # Reset blocked cell if we encounter it
    if board[row][col] == -1:
        board[row][col] = 0
    
    for num in range(1, 10):
        # Skip the blocked value at the specific cell
        if row == blocked_row and col == blocked_col and num == blocked_value:
            continue
            
        if is_valid(board, row, col, num):
            board[row][col] = num
            steps.append({"row": row, "col": col, "value": num})
            
            if find_solution_with_blocked(board, steps, blocked_row, blocked_col, blocked_value):
                return True
            
            steps.pop()
            board[row][col] = 0
    
    return False

def boards_equal(board1, board2):
    for i in range(9):
        for j in range(9):
            if board1[i][j] != board2[i][j]:
                return False
    return True

@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    step_by_step = 0
    check_multiple = 1
    original_board = None
    solution_steps = None
    multiple_solutions = None
    
    if request.method == "POST":
        if 'play_again' in request.form:
            return render_template("index.html", 
                                  board=[[0]*9 for _ in range(9)], 
                                  message="",
                                  step_by_step=int(request.form.get('step_by_step', 0)),
                                  check_multiple=int(request.form.get('check_multiple', 1)))
        
        # Parse step-by-step and check-multiple flags
        step_by_step = int(request.form.get('step_by_step', 0))
        check_multiple = int(request.form.get('check_multiple', 1))
        
        # Parse the board
        board = []
        for i in range(9):
            row = []
            for j in range(9):
                val = request.form.get(f'cell-{i}-{j}')
                row.append(int(val) if val and val.isdigit() else 0)
            board.append(row)
        
        # Save original board for display
        original_board = copy.deepcopy(board)
        
        # Check for multiple solutions if requested
        if check_multiple:
            solutions = find_multiple_solutions(original_board, max_solutions=5)
            if len(solutions) > 1:
                return render_template("index.html", 
                                      board=original_board,
                                      original_board=original_board,
                                      message="This puzzle has multiple solutions.",
                                      step_by_step=step_by_step,
                                      check_multiple=check_multiple,
                                      multiple_solutions=json.dumps(solutions))
            elif len(solutions) == 1:
                # If there's only one solution, use it
                solved_board = solutions[0]["board"]
                solution_steps = solutions[0]["steps"]
                message = "Puzzle solved successfully!"
                return render_template("index.html",
                                      board=solved_board,
                                      original_board=original_board,
                                      message=message,
                                      step_by_step=step_by_step,
                                      check_multiple=check_multiple,
                                      solution_steps=json.dumps(solution_steps))
        
        # Try to solve directly
        solved, steps = solve_sudoku_with_steps(board)
        if solved:
            message = "Puzzle solved successfully!"
            solution_steps = steps
        else:
            message = "No solution exists for this puzzle."
        
        return render_template("index.html", 
                              board=board,
                              original_board=original_board,
                              message=message,
                              step_by_step=step_by_step,
                              check_multiple=check_multiple,
                              solution_steps=json.dumps(steps) if solved else None)
    
    # Initial empty board for GET request
    board = [[0 for _ in range(9)] for _ in range(9)]
    return render_template("index.html", 
                          board=board, 
                          message=message,
                          step_by_step=step_by_step,
                          check_multiple=check_multiple)

if __name__ == "__main__":
    app.run(debug=True)