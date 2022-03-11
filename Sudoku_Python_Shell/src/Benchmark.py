#!/usr/bin/env python3

import sys
import SudokuBoard
import BTSolver
from Trail import Trail
import time

from Sudoku_Python_Shell.src import Variable


def main():
    # args = sys.argv
    #
    # # Important Variables
    # variable_heuristic = ""
    # value_heuristic = ""
    # consistency_check = ""
    #
    # for arg in [args[i] for i in range(1, len(args))]:
    #     if arg == "MRV":
    #         variable_heuristic = "MinimumRemainingValue"
    #
    #     elif arg == "MAD":
    #         variable_heuristic = "MRVwithTieBreaker"
    #
    #     elif arg == "LCV":
    #         value_heuristic = "LeastConstrainingValue"
    #
    #     elif arg == "FC":
    #         consistency_check = "forwardChecking"
    #
    #     elif arg == "NOR":
    #         consistency_check = "norvigCheck"
    #
    #     elif arg == "TOURN":
    #         variable_heuristic = "tournVar"
    #         value_heuristic = "tournVal"
    #         consistency_check = "tournCC"

    solver_settings = {
        "FC": ("forwardChecking", "", ""),
        "NOR": ("norvigCheck", "", ""),
        "FC LCV": ("forwardChecking", "", "LeastConstrainingValue"),
        "NOR LCV": ("norvigCheck", "", "LeastConstrainingValue"),
        "FC MRV": ("forwardChecking", "MinimumRemainingValue", ""),
        "NOR MRV": ("norvigCheck", "MinimumRemainingValue", ""),
        "FC MAD": ("forwardChecking", "MRVwithTieBreaker", ""),
        "NOR MAD": ("norvigCheck", "MRVwithTieBreaker", ""),
        "FC MRV LCV": ("forwardChecking", "MinimumRemainingValue", "LeastConstrainingValue"),
        "NOR MRV LCV": ("norvigCheck", "MinimumRemainingValue", "LeastConstrainingValue"),
        "FC MAD LCV": ("forwardChecking", "MRVwithTieBreaker", "LeastConstrainingValue"),
        "NOR MAD LCV": ("norvigCheck", "MRVwithTieBreaker", "LeastConstrainingValue"),
        "TOURNAMENT1": ("tournCC", "tournVar", "tournVal")

    }

    # p rows, q cols, m values given initially
    easy_config = (3, 3, 7)
    intermediate_config = (3, 4, 11)
    hard_config = (4, 4, 20)
    expert_config = (5, 5, 30)

    num_easy_trials = 1
    num_intermediate_trials = 1
    num_hard_trials = 500
    num_expert_trials = 1

    trial_settings = (
        ("Easy", easy_config, num_easy_trials),
        ("Intermediate", intermediate_config, num_intermediate_trials),
        ("Hard", hard_config, num_hard_trials),
        ("Expert", expert_config, num_expert_trials),
    )

    solvers_to_benchmark = ["NOR MAD LCV", "TOURNAMENT1"]

    for trial_name, difficulty_config, num_trials in trial_settings:

        boards = [SudokuBoard.SudokuBoard(*difficulty_config) for _ in range(num_trials)]

        print()
        print(f"-" * 80)
        print(
            f"Starting {trial_name} with {num_trials} trials comparing: "
            f"{' vs. '.join(solver_name for solver_name in solvers_to_benchmark)}"
        )
        print(f"-" * 80)

        solver_backtrack_scores = {solver_name: 0 for solver_name in solvers_to_benchmark}
        solver_backtrack_counts = {solver_name: 0 for solver_name in solvers_to_benchmark}
        solver_last_backtrack_count = {solver_name: 0 for solver_name in solvers_to_benchmark}
        solver_total_time_elapsed = {solver_name: 0 for solver_name in solvers_to_benchmark}
        solver_time_scores = {solver_name: 0 for solver_name in solvers_to_benchmark}
        solver_last_time_elapsed = {solver_name: 0 for solver_name in solvers_to_benchmark}
        solver_failures = {solver_name: 0 for solver_name in solvers_to_benchmark}

        current_solver_index = 0
        current_solver_name = solvers_to_benchmark[current_solver_index]
        progress_bar_prefix = [current_solver_name]
        progress_bar_suffix = ["Last backtrack winner: N/A, Last time winner: N/A"]

        for i in print_progress_bar(range(num_trials * len(solvers_to_benchmark)), len(solvers_to_benchmark),
                                    prefix=progress_bar_prefix,
                                    suffix=progress_bar_suffix,
                                    length=150
                                    ):

            trial_number = i // len(solvers_to_benchmark)
            Trail.numPush = 0
            Trail.numUndo = 0
            trail = Trail()
            Variable.STATIC_NAMING_COUNTER = 1
            sudoku_board = boards[trial_number]

            consistency_check, variable_heuristic, value_heuristic = solver_settings[current_solver_name]
            solver = BTSolver.BTSolver(sudoku_board, trail, value_heuristic, variable_heuristic, consistency_check)

            current_time = time.time()
            solver.checkConsistency()
            solver.solve()
            end_time = time.time()
            time_taken = end_time - current_time
            solver_total_time_elapsed[current_solver_name] += time_taken
            solver_last_time_elapsed[current_solver_name] = time_taken

            if solver.hassolution:

                solver_backtrack_counts[current_solver_name] += trail.getUndoCount()
                solver_last_backtrack_count[current_solver_name] = trail.getUndoCount()

            else:
                solver_last_backtrack_count[current_solver_name] = -1
                solver_failures[current_solver_name] += 1

            current_solver_index += 1
            if current_solver_index == len(solvers_to_benchmark):
                current_solver_index = 0
                time_winner = min(
                    (solver_name for solver_name in solvers_to_benchmark),
                    key=lambda x: solver_last_time_elapsed[x]
                )
                solver_time_scores[time_winner] += 1
                backtrack_winner = min(
                    (solver_name for solver_name in solvers_to_benchmark
                     if solver_last_backtrack_count[solver_name] != -1),
                    key=lambda x: solver_last_backtrack_count[x], default="All Failed"
                )
                if backtrack_winner != "All Failed":
                    solver_backtrack_scores[backtrack_winner] += 1
                progress_bar_suffix[0] = \
                    "Last backtrack winner: " + str(backtrack_winner) + \
                    ", Last time winner: " + str(time_winner)

            current_solver_name = solvers_to_benchmark[current_solver_index]
            progress_bar_prefix[0] = current_solver_name

        print('-' * 80)

        print(f"Time stats between {', '.join(solver_name for solver_name in solvers_to_benchmark)}")
        for solver_name in solvers_to_benchmark:
            print(f"{solver_name} Number of wins: {solver_time_scores[solver_name]}, "
                  f"average time per trial: {solver_total_time_elapsed[solver_name] / num_trials} seconds, "
                  f"total time taken: {solver_total_time_elapsed[solver_name]} seconds")

        print('-'*80)

        print(f"Backtrack stats between {', '.join(solver_name for solver_name in solvers_to_benchmark)}")
        for solver_name in solvers_to_benchmark:
            print(f"{solver_name} Number of wins: {solver_backtrack_scores[solver_name]}, "
                  f"average backtracks per trial: {solver_backtrack_counts[solver_name] / num_trials} backtracks"
                  )

        print(f"-" * 80)

        print(f"Failure stats between {', '.join(solver_name for solver_name in solvers_to_benchmark)}")
        for solver_name in solvers_to_benchmark:
            print(f"{solver_name} failures: {solver_failures[solver_name]} failures")

        print('-' * 80)


def print_progress_bar(iterable, num_solvers, prefix, suffix, length):
    # src: https://stackoverflow.com/questions/3173320/text-progress-bar-in-terminal-with-block-characters

    fill = '█'
    total = len(iterable)

    # Progress Bar Printing Function
    def printProgressBar(iteration):
        trial = iteration // num_solvers
        percent = f"{iteration}/{total}"
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)

        current_solver_fixed_str = "{0: <15}".format(f"{prefix[0]}\'s turn")

        print(f"\r{current_solver_fixed_str}, board #{trial}"
              f" |{bar}| {percent} {suffix[0]}", end='')

    # Initial Call
    printProgressBar(0)
    # Update Progress Bar
    for i, item in enumerate(iterable):
        yield item
        printProgressBar(i + 1)
    # Print New Line on Complete
    print()


main()
