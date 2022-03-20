# Sudokask
Sudoku puzzle solver that models the sudoku problem as a Constraint
Satisfaction Problem, utilizing custom heuristics and consistency
checks to efficiently find a solution to the puzzle. Can solve 
**monster** sudoku puzzles up to 25 X 25 in size in just a few 
seconds!  

Includes a benchmark script to analyze the time and backtracking 
performance of various heuristic combinations. You can define the 
board parameters such as size as well as the number of trials to
perform. Allows comparing a solver using any consistency check, 
variable selection and value selection heuristic combination 
against any other custom defined solvers to identify their 
strengths and weaknesses on different problem sizes. For better
stat comparison between solvers, each trial corresponds to the 
same pre-generated board so that all solvers solve the same board.
This allows a direct comparison of their stats on the same board.

# Features
### Consistency Checks:
1. Forward Checking
2. Arc Consistency
3. Norvig's Check

### Variable Selection Heuristics:

1. **M**inimum **R**emaining **V**ariable (smallest domain)
2. MRV with **L**argest **D**egree as Tie Breaker
3. MRV SD (smallest degree) Largest Value Frequency as second Tie Breaker

### Value Selection Heuristics:

1. Variable's values in least constraining (on neighbors) order 
2. Values in descending frequency order as currently assigned on the board

# Requirements
Python 3.7+

# How to Use


## Specifying a Single Board
1. Create a txt file representing the board in the following the sample_board.txt format:  
The first two positive ints represent the number of rows and cols in each of the blocks 
on the board  
The values in each row correspond to the sudoku board's values seperated by a space. 
There should be (rows * cols) values per row and rows specified.

2. Run Main.py and enter the location of the text file representing the sample board as
a parameter.

## Specifying Multiple Boards

1. Create a directory that will store all the board txt files. Make sure there are no other
files in this directory.
2. Follow the _Specifying a Single Board_ instructions above to create a txt file for each
board you would like to solve
3. Run Main.py and enter the location of the directory containing the boards as a parameter.

## Solving a random, classic 9 x 9 board

1. Run the Main.py script with no arguments specified to generate a random board and then
solve it

# How to Benchmark

Benchmark script is found in **Benchmark.py**  

The benchmark works by having a certain number of trials for each board difficulty level. 
Harder boards are larger in size and only have a few values given, balancing 
underconstraining and overconstraining the CSP. During every trial, each solver tries to solve
the board and records its stats. At the end of all the trials for a particular board difficulty 
level, the average stats are printed. You can see the realtime time and backtrack winners to the 
right of the dynamic progress bar. Remember that there are (num solvers * num trials) boards to 
solve for each difficulty level.

See the comments in the code for the exact format for the following parameters you can change:
1. Add/Edit custom solvers by creating a key value pair in the _solver_settings_ dict
2. Change the board size and initial values given in the \[_difficulty_\]__config_ variables.
3. Change the number of trials to perform for each difficulty level in the 
_num__\[_difficulty_\]__config_. Remember, harder difficulties take much longer to solve!
4. Edit the list of names of solvers to compare during each trial in the _solvers_to_benchmark_ 
list.
