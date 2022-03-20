import sys
import os
from Sudoku_Board import SudokuBoard, Trail
from Solver.BTSolver import BTSolver

# Main driver file, which is responsible for interfacing with the
# command line and properly starting the backtracking solver.

if __name__ == "__main__":
    args = sys.argv

    file = None

    print(os.getcwd())

    if len(args) == 2:
        file = args[1]

    if file is None:  # solve a random sample_board.txt of size 3x3 with 7 values specified

        sudokudata = SudokuBoard.SudokuBoard(3, 3, 7)
        trail = Trail.Trail()
        print(sudokudata)

        solver = BTSolver(sudokudata, trail, "tournVal", "tournVar", "tournCC")
        solver.checkConsistency()
        solver.solve()

        if solver.hassolution:
            print(solver.getSolution())
            print("Trail Pushes: " + str(trail.getPushCount()))
            print("Backtracks: " + str(trail.getUndoCount()))

        else:
            print("Failed to find a solution")
        exit(0)

    elif os.path.isfile(file):

        sudokudata = SudokuBoard.SudokuBoard(filepath=os.path.abspath(file))
        trail = Trail.Trail()
        print(sudokudata)

        solver = BTSolver(sudokudata, trail, "tournVal", "tournVar", "tournCC")
        solver.checkConsistency()
        solver.solve()

        if solver.hassolution:
            print(solver.getSolution())
            print("Trail Pushes: " + str(trail.getPushCount()))
            print("Backtracks: " + str(trail.getUndoCount()))

        else:
            print("Failed to find a solution")

    elif os.path.isdir(file):
        listOfBoards = None

        try:
            listOfBoards = os.listdir(file)
        except:
            print("[ERROR] Failed to open directory.")
            exit(1)

        numSolutions = 0
        for f in listOfBoards:
            print("Running board: " + str(f))
            trail = Trail.Trail()
            sudokudata = SudokuBoard.SudokuBoard(filepath=os.path.join(file, f))

            print(sudokudata)
            solver = BTSolver(sudokudata, trail, "tournVal", "tournVar", "tournCC")
            solver.checkConsistency()
            solver.solve()

            if solver.hassolution:
                print(solver.getSolution())
                print("Trail Pushes: " + str(trail.getPushCount()))
                print("Backtracks: " + str(trail.getUndoCount()))
                numSolutions += 1

            else:
                print("Failed to find a solution")

    else:
        print("Invalid parameters.\n"
              "To solve a random board, run with no command line arguments\n"
              "To solve a specific board, enter the board's file location\n"
              "To solve a set of boards, enter the directory containing the board files\n"
              )

