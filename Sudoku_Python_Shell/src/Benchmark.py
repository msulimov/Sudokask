#!/usr/bin/env python3

import sys
import SudokuBoard
import BTSolver
from Trail import Trail
import time

from Sudoku_Python_Shell.src import Variable


def main():
    args = sys.argv

    # Important Variables
    variable_heuristic = ""
    value_heuristic = ""
    consistency_check = ""

    for arg in [args[i] for i in range(1, len(args))]:
        if arg == "MRV":
            variable_heuristic = "MinimumRemainingValue"

        elif arg == "MAD":
            variable_heuristic = "MRVwithTieBreaker"

        elif arg == "LCV":
            value_heuristic = "LeastConstrainingValue"

        elif arg == "FC":
            consistency_check = "forwardChecking"

        elif arg == "NOR":
            consistency_check = "norvigCheck"

        elif arg == "TOURN":
            variable_heuristic = "tournVar"
            value_heuristic = "tournVal"
            consistency_check = "tournCC"

    # p rows, q cols, m values given initially
    easy_config = (3, 3, 7)
    intermediate_config = (3, 4, 11)
    hard_config = (4, 4, 20)
    expert_config = (5, 5, 30)

    num_easy_trials = 500
    num_intermediate_trials = 100
    num_hard_trials = 50
    num_expert_trials = 20

    trial_settings = (
        ("Easy", easy_config, num_easy_trials),
        ("Intermediate", intermediate_config, num_intermediate_trials),
        ("Hard", hard_config, num_hard_trials),
        ("Expert", expert_config, num_expert_trials)
    )

    for trial_name, difficulty_config, num_trials in trial_settings:

        time_taken = 0
        num_backtracks = 0
        num_pushed = 0
        num_failures = 0
        print(f"-"*80)
        print(f"Starting {trial_name} with {num_trials} trials")
        for _ in print_progress_bar(range(num_trials), prefix=f"Progress", suffix="Trials Done", length=250):

            Trail.numPush = 0
            Trail.numUndo = 0
            trail = Trail()
            Variable.STATIC_NAMING_COUNTER = 1
            sudoku_board = SudokuBoard.SudokuBoard(*difficulty_config)
            solver = BTSolver.BTSolver(sudoku_board, trail, value_heuristic, variable_heuristic, consistency_check)

            current_time = time.time()
            solver.checkConsistency()
            solver.solve()
            end_time = time.time()
            time_taken += end_time - current_time

            if solver.hassolution:
                num_backtracks += trail.getUndoCount()
                num_pushed += trail.getPushCount()

            else:
                num_failures += 1

        print(
            f"Total time taken for {num_trials} trials: {time_taken} seconds\n"
            f"Average time taken per trial: {time_taken/num_trials} seconds\n"
            f"Average backtracks for successful solution: {num_backtracks/num_trials} backtracks\n"
            f"Average trail pushes for successful solution: {num_pushed/num_trials} pushes\n"
            f"Failure rate: {num_failures}/{num_trials}\n"
        )


def print_progress_bar(iterable, prefix='', suffix='', decimals=1, length=100, fill='█', print_end="\r"):
    # src: https://stackoverflow.com/questions/3173320/text-progress-bar-in-terminal-with-block-characters
    """
    Call in a loop to create terminal progress bar
    @params:
        iterable    - Required  : iterable object (Iterable)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    total = len(iterable)

    # Progress Bar Printing Function
    def printProgressBar(iteration):
        percent = f"{iteration}/{total}"
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print(f'\rTrial #{iteration} |{bar}| {percent} {suffix}', end='')

    # Initial Call
    printProgressBar(0)
    # Update Progress Bar
    for i, item in enumerate(iterable):
        yield item
        printProgressBar(i + 1)
    # Print New Line on Complete
    print()


main()
