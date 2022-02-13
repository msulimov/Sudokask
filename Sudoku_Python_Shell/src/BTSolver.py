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
        assigned_values = list()

        last_assigned_var = kwargs["last_assigned_var"] if "last_assigned_var" in kwargs else None

        if last_assigned_var is not None:
            # if called after assigning a var, do forward checking on its neighbors only
            assigned_values.append(last_assigned_var)

        else:
            # if initial call where board uninitialized, forward check on all assigned vars
            for v in self.network.getVariables():
                if v.isAssigned():
                    assigned_values.append(v)

        for assigned_value in assigned_values:

            # loop through all the neighbors of assigned vars
            for neighbor in self.network.getNeighborsOfVariable(assigned_value):

                # if neighbor not an initial variable on sudoku board
                # and the neighbor is not yet assigned
                # and neighbor's domain contains the newly assigned variable's value
                if neighbor.isChangeable and not neighbor.isAssigned() and \
                        neighbor.getDomain().contains(assigned_value.getAssignment()):
                    # Remove the assigned variable's value from the domain of the neighbor and check its domain after

                    self.trail.push(neighbor)  # push to trail revert neighbor when backtracking

                    # remove assigned variable's value value from neighbor
                    neighbor.removeValueFromDomain(assigned_value.getAssignment())

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

        return ({}, False)

    """
         Optional TODO: Implement your own advanced Constraint Propagation

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """

    def getTournCC(self, **kwargs):

        last_assigned_var = kwargs["last_assigned_var"] if "last_assigned_var" in kwargs else None

        return False

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

        return min((var for var in self.network.getConstraints() if not var.isAssigned()), key=lambda x: x.size())

        # for v in self.network.getVariables():  # loop through all the constraints
        #     if not v.isAssigned() and v.size() < min_values:
        #         min_var = v
        #         min_values = v.size()
        # return min_var

    """
        Part 2 TODO: Implement the Minimum Remaining Value Heuristic
                       with Degree Heuristic as a Tie Breaker

        Return: The unassigned variable with the smallest domain and affecting the  most unassigned neighbors.
                If there are multiple variables that have the same smallest domain with the same number of unassigned neighbors, add them to the list of Variables.
                If there is only one variable, return the list of size 1 containing that variable.
    """

    def MRVwithTieBreaker(self):
        number_domain_values = list()
        for c in self.network.getConstraints():
            for v in c.vars:
                if not v.isAssigned():
                    number_domain_values.append((v, v.size()))
        number_domain_values.sort(key=lambda x: x[1])
        smallest_domain = number_domain_values[0][1]
        largest_unassigned_neighbor_count = 0
        variable_to_choose = number_domain_values[0][0]
        for variable, domain_size in number_domain_values:
            if domain_size == smallest_domain:
                unassigned_count = 0
                for neighbor in self.network.getNeighborsOfVariable(variable):
                    if not neighbor.isAssigned():
                        unassigned_count += 1
                if unassigned_count > largest_unassigned_neighbor_count:
                    largest_unassigned_neighbor_count = unassigned_count
                    variable_to_choose = variable
            else:
                break
        return variable_to_choose

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

    def getValuesLCVOrder(self, v):
        return None

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
            return self.MRVwithTieBreaker()[0]

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
