import sys

import SudokuBoard
from Variable import Variable
from Domain import Domain
import Trail
import Constraint
import ConstraintNetwork
import time
import random


class BTSolver:

    # ==================================================================
    # Constructors
    # ==================================================================

    def __init__(self, gb, trail, val_sh, var_sh, cc):
        self.network = ConstraintNetwork.ConstraintNetwork(gb)
        self.hassolution = False
        self.gameboard = gb
        self.trail = trail

        self.varHeuristics = var_sh
        self.valHeuristics = val_sh
        self.cChecks = cc

    # ==================================================================
    # Consistency Checks
    # ==================================================================

    # Basic consistency check, no propagation done
    def assignmentsCheck(self):
        for c in self.network.getConstraints():
            if not c.isConsistent():
                return False
        return True

    """
        Part 1 TODO: Implement the Forward Checking Heuristic

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        Note: remember to trail.push variables before you assign them
        Return: a tuple of a dictionary and a bool. 
            The dictionary contains all MODIFIED variables, mapped to their MODIFIED domain.
            The bool is true if assignment is consistent, false otherwise.
    """

    def forwardChecking(self, **kwargs) -> ({str: Domain}, bool):
        output_dictionary = dict()
        assigned_vars = list()

        last_assigned_var = kwargs["last_assigned_var"] if "last_assigned_var" in kwargs else None

        if last_assigned_var is not None:
            # if called after assigning a var, do forward checking on its neighbors only
            assigned_vars.append(last_assigned_var)

        else:
            # if initial call where board uninitialized, forward check on all assigned vars
            for v in self.network.getVariables():
                if v.isAssigned():
                    assigned_vars.append(v)

        for assigned_var in assigned_vars:

            # loop through all the neighbors of assigned vars
            for neighbor in self.network.getNeighborsOfVariable(assigned_var):

                # if neighbor not an initial variable on sudoku board
                # and the neighbor is not yet assigned
                # and neighbor's domain contains the newly assigned variable's value
                if neighbor.isChangeable and not neighbor.isAssigned() and \
                        neighbor.getDomain().contains(assigned_var.getAssignment()):
                    # Remove the assigned variable's value from the domain of the neighbor and check its domain after

                    self.trail.push(neighbor)  # push to trail revert neighbor when backtracking

                    # remove assigned variable's value value from neighbor
                    neighbor.removeValueFromDomain(assigned_var.getAssignment())

                    # update output dictionary with new neighbor's domain for grading
                    output_dictionary[neighbor.getName()] = neighbor.getDomain()

                    # do some further O(1) checks to see if assignment consistent

                    # If the neighbor has no more values in domain, then it's inconsistent since it is unassigned still
                    if neighbor.domain.size() == 0:
                        return output_dictionary, False

                    # If neighbor has only 1 value in domain, assign it and check consistency
                    elif neighbor.domain.size() == 1:

                        self.trail.push(neighbor)  # push to trail so can backtrack later
                        neighbor.assignValue(neighbor.domain.values[0])  # assign the last remaining value for neighbor
                        if not self.checkConsistency(last_assigned_var=neighbor):  # perform recursive call
                            return output_dictionary, False

        return output_dictionary, self.assignmentsCheck()

    # =================================================================
    # Arc Consistency
    # =================================================================
    def arcConsistency(self):
        assignedVars = []
        for c in self.network.constraints:
            for v in c.vars:
                if v.isAssigned():
                    assignedVars.append(v)
        while len(assignedVars) != 0:
            av = assignedVars.pop(0)
            for neighbor in self.network.getNeighborsOfVariable(av):
                if neighbor.isChangeable and not neighbor.isAssigned() and neighbor.getDomain().contains(
                        av.getAssignment()):
                    neighbor.removeValueFromDomain(av.getAssignment())
                    if neighbor.domain.size() == 1:
                        neighbor.assignValue(neighbor.domain.values[0])
                        assignedVars.append(neighbor)
        return self.assignmentsCheck()

    """
        Part 2 TODO: Implement both of Norvig's Heuristics

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        (2) If a constraint has only one possible place for a value
            then put the value there.

        Note: remember to trail.push variables before you assign them
        Return: a pair of a dictionary and a bool. The dictionary contains all variables 
		        that were ASSIGNED during the whole NorvigCheck propagation, and mapped to the values that they were assigned.
                The bool is true if assignment is consistent, false otherwise.
    """

    def norvigCheck(self, **kwargs):
        """
        Building on forward checking, also checks that any values that appear n-1 times in the board can have
        the nth value assigned without being inconsistent
        """

        last_assigned_var = kwargs["last_assigned_var"] if "last_assigned_var" in kwargs else None
        output_dict = {}

        if not self.forwardChecking(**kwargs)[1]:  # first Norvig check which is Forward Checking
            return output_dict, False

        n = self.gameboard.n  # number of different values each variable can take
        value_freq = {}  # dict of values to count up with frequencies

        if last_assigned_var is None:  # only check the most recently assigned variable's value
            value_freq.update(((i, 0) for i in range(1, n + 1)))
        else:  # if from board initialization, check all the values
            value_freq[last_assigned_var.getDomain()[0]] = 0

        for var in self.network.getVariables():  # count up values from variables that have been assigned
            if var.isAssigned():
                value_freq[var.getDomain()[0]] += 1

        for value, count in value_freq:
            if count == n - 1:  # if there is a value that needs to be assigned to one more spot
                for var in self.network.getVariables():  # assign it to the var with the value in its domain
                    if value in var.getDomain():
                        self.trail.push(var)  # save original var to the trail for backtracking
                        var.assign_value(value)  # assign the value to the var
                        output_dict[var.getName()] = value  # save to output dict for grading
                        # don't need to update neighbors since no other variables contain value in their domain
        return output_dict, self.checkConsistency()

    """
         Optional TODO: Implement your own advanced Constraint Propagation

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """

    def getTournCC(self, **kwargs):

        last_assigned_var = kwargs["last_assigned_var"] if "last_assigned_var" in kwargs else None

        if last_assigned_var is None: # if initial board, perform arc-consistency
            if not self.checkConsistency():
                return False

        return self.norvigCheck(**kwargs)[1]

    # ==================================================================
    # Variable Selectors
    # ==================================================================

    # Basic variable selector, returns first unassigned variable
    def getfirstUnassignedVariable(self):
        for v in self.network.variables:
            if not v.isAssigned():
                return v

        # Everything is assigned
        return None

    """
        Part 1 TODO: Implement the Minimum Remaining Value Heuristic

        Return: The unassigned variable with the smallest domain
    """

    def getMRV(self):
        minimum_size = None
        smallest_domain_variable = None

        for v in self.network.getVariables():
            if not v.isAssigned() and (minimum_size is None or v.size() < minimum_size):
                minimum_size = v.size()
                smallest_domain_variable = v
        return smallest_domain_variable  # supposed to return none if nothing left to assign
        # return min((var for var in self.network.getConstraints() if not var.isAssigned()), key=lambda x: x.size())



    """
        Part 2 TODO: Implement the Minimum Remaining Value Heuristic
                       with Degree Heuristic as a Tie Breaker

        Return: The unassigned variable with the smallest domain and affecting the  most unassigned neighbors.
                If there are multiple variables that have the same smallest domain with the same number of unassigned neighbors, add them to the list of Variables.
                If there is only one variable, return the list of size 1 containing that variable.
    """

    def MRVwithTieBreaker(self):

        mrv_variable = self.getMRV()
        if mrv_variable is None:
            return None

        minimum_remaining_value = mrv_variable.size()
        min_remaining_value_vars = [var for var in self.network.getVariables() if (var.size() == minimum_remaining_value and not var.isAssigned())]
        maximum_degree = max(
            max(1 for neighbor in self.network.getNeighborsOfVariable(var) if not neighbor.isAssigned()) for var in
            min_remaining_value_vars)
        # I know it says to return a list, but that doesn't make sense as it can return none when there is no variables left to assign
        return [var for var in min_remaining_value_vars
                if max(1 for neighbor in self.network.getNeighborsOfVariable(var) if not neighbor.isAssigned()) == maximum_degree][0]

    """
         Optional TODO: Implement your own advanced Variable Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """

    def getTournVar(self):
        return None

    # ==================================================================
    # Value Selectors
    # ==================================================================

    # Default Value Ordering
    def getValuesInOrder(self, v):
        values = v.domain.values
        return sorted(values)

    """
        Part 1 TODO: Implement the Least Constraining Value Heuristic

        The Least constraining value is the one that will knock the least
        values out of it's neighbors domain.

        Return: A list of v's domain sorted by the LCV heuristic
                The LCV is first and the MCV is last
    """

    def getValuesLCVOrder(self, var):

        return sorted(
            (value for value in var.getValues()), key=lambda x:
            sum(1 for neighbor in self.network.getNeighborsOfVariable(var)
                if not neighbor.isAssigned() and x in neighbor.getValues()
                )
        )

    """
         Optional TODO: Implement your own advanced Value Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """

    def getTournVal(self, v):
        return None

    # ==================================================================
    # Engine Functions
    # ==================================================================

    def solve(self, time_left=600):
        if time_left <= 60:
            return -1

        start_time = time.time()
        if self.hassolution:
            return 0

        # Variable Selection
        v = self.selectNextVariable()

        # check if the assigment is complete
        if (v == None):
            # Success
            self.hassolution = True
            return 0

        # Attempt to assign a value
        for i in self.getNextValues(v):

            # Store place in trail and push variable's state on trail
            self.trail.placeTrailMarker()  # makes undo backtrack to this position in the trail
            self.trail.push(v)

            # Assign the value
            v.assignValue(i)

            # Propagate constraints, check consistency, recur
            if self.checkConsistency(last_assigned_var=v):  # add variable last assigned for optimized checking
                elapsed_time = time.time() - start_time
                new_start_time = time_left - elapsed_time
                if self.solve(time_left=new_start_time) == -1:
                    return -1

            # If this assignment succeeded, return
            if self.hassolution:
                return 0

            # Otherwise backtrack
            self.trail.undo()

        return 0

    def checkConsistency(self, **kwargs):

        last_assigned_var = kwargs["last_assigned_var"] if "last_assigned_var" in kwargs else None

        if self.cChecks == "forwardChecking":
            return self.forwardChecking(last_assigned_var=last_assigned_var)[1]

        if self.cChecks == "norvigCheck":
            return self.norvigCheck(last_assigned_var=last_assigned_var)[1]

        if self.cChecks == "tournCC":
            return self.getTournCC(last_assigned_var=last_assigned_var)

        else:
            return self.assignmentsCheck()

    def selectNextVariable(self):
        if self.varHeuristics == "MinimumRemainingValue":
            return self.getMRV()

        if self.varHeuristics == "MRVwithTieBreaker":
            return self.MRVwithTieBreaker()

        if self.varHeuristics == "tournVar":
            return self.getTournVar()

        else:
            return self.getfirstUnassignedVariable()

    def getNextValues(self, v):
        if self.valHeuristics == "LeastConstrainingValue":
            return self.getValuesLCVOrder(v)

        if self.valHeuristics == "tournVal":
            return self.getTournVal(v)

        else:
            return self.getValuesInOrder(v)

    def getSolution(self):
        return self.network.toSudokuBoard(self.gameboard.p, self.gameboard.q)
