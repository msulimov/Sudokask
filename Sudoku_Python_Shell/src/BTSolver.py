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

    def forwardChecking(self, last_assigned_vars: [Variable] = None) -> ({str: Domain}, bool):

        """
            This function will do both Constraint Propagation and check
            the consistency of the network

            (1) If a variable is assigned then eliminate that value from
                the square's neighbors.

            Note: remember to trail.push variables before you assign them
            Return: a tuple of a dictionary and a bool.
                The dictionary contains all MODIFIED variables, mapped to their MODIFIED domain.
                The bool is true if assignment is consistent, false otherwise.
        """

        output_dictionary = dict()
        assigned_vars = [v for v in last_assigned_vars] if last_assigned_vars is not None\
            else [v for v in self.network.getVariables() if v.isAssigned()]

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
                    output_dictionary[neighbor] = neighbor.getDomain()

                    # do some further O(1) checks to see if assignment consistent

                    # If the neighbor has no more values in domain, then it's inconsistent since it is unassigned still
                    if neighbor.domain.size() == 0:
                        return output_dictionary, False

                    # Arc consistency neighbor has only 1 value in domain, assign it and check consistency
                    # elif neighbor.domain.size() == 1:
                    #
                    #     self.trail.push(neighbor)  # push to trail so can backtrack later
                    #     neighbor.assignValue(neighbor.domain.values[0]) # assign the last remaining value for neighbor
                    #     if not self.forwardChecking(last_assigned_vars=[neighbor])[1]:  # perform recursive call
                    #         return output_dictionary, False

        return output_dictionary, self.assignmentsCheck()

    # =================================================================
    # Arc Consistency
    # =================================================================
    def arcConsistency(self, last_assigned_vars: [Variable] = None) -> bool:

        assigned_vars = []

        if last_assigned_vars is not None:
            for last_assigned_var in last_assigned_vars:
                assigned_vars.append(last_assigned_var)
        else:
            for v in self.network.getVariables():
                if v.isAssigned():
                    assigned_vars.append(v)

        while len(assigned_vars) != 0:
            assigned_var = assigned_vars.pop(0)
            for neighbor in self.network.getNeighborsOfVariable(assigned_var):
                if neighbor.isChangeable and not neighbor.isAssigned() and neighbor.getDomain().contains(
                        assigned_var.getAssignment()):
                    self.trail.push(neighbor)
                    neighbor.removeValueFromDomain(assigned_var.getAssignment())
                    if neighbor.domain.size() == 1:
                        self.trail.push(neighbor)
                        neighbor.assignValue(neighbor.domain.values[0])
                        assigned_vars.append(neighbor)
        return self.assignmentsCheck()

    def norvigCheck(self, last_assigned_vars: [Variable] = None) -> ({str: int}, bool):
        """
        This function will do both Constraint Propagation and check
        the consistency of the network
        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.
        (2) If a constraint has only one possible place for a value
            then put the value there.
        Returns: a pair of a dictionary and a bool. The dictionary contains all variables that were ASSIGNED during
            the whole NorvigCheck propagation, and mapped to the values that they were assigned.
            The bool is true if assignment is consistent, false otherwise.
        """

        output_dict = {}  # output the variables assigned by norvig's check for grading

        if not self.forwardChecking(last_assigned_vars=last_assigned_vars)[1]:
            return output_dict, False

        n = self.gameboard.N  # number of different values each variable can take
        value_freq = [0] * (n + 1)  # array of values to count up with frequencies

        for c in self.network.getConstraints():

            for value in range(1, n + 1):
                value_freq[value] = 0
            for var in c.vars:
                if not var.isAssigned():
                    for value in var.getValues():
                        value_freq[value] += 1  # adds elements in the domain

            for value, count in enumerate(value_freq[1:], start=1):
                if count == 1:

                    vars_to_assign = [var for var in c.vars if value in var.getValues()]

                    # another assigned var invalidated domain of var, but constraint still needs value
                    if len(vars_to_assign) == 0:
                        return output_dict, False
                    # single var found, assign and do a forward check on it
                    var = vars_to_assign[0]
                    if len(vars_to_assign) == 1 and not var.isAssigned():

                        self.trail.push(var)  # save original var to the trail for backtracking
                        var.assignValue(value)  # assign the value to the var
                        output_dict[var] = value  # save to output dict for grading

                        if not self.forwardChecking(last_assigned_vars=[var])[1]:
                            return output_dict, False

        return output_dict, True
    
    def hidden_pair_prune(self):
        """
            If a pair of candidates occurs in exactly two unit cells, and none
            of its members is a candidate in the other unit cells. Then,
            we can eliminate all of the other candidates in the two unit cells
        """
        n = self.gameboard.N  # number of different values each variable can take
        value_freq = [0] * (n + 1)  # array of values to count up with frequencies

                for c in self.network.getConstraints():
            variables_to_consider = dict()
            for value in range(1, n + 1):
                value_freq[value] = 0
            for var in c.vars:
                if not var.isAssigned():
                    for value in var.getValues():
                        value_freq[value] += 1  # adds elements in the domain

            for value in range(1, len(value_freq)):
                count = value_freq[value]
                if count == 2:  # If a value appears twice, could be a potential hidden pair
                    # There should be two variables in this list
                    variables_to_consider[value] = [var for var in c.vars if value in var.getValues()
                                                    and not var.isAssigned()]
                    # Iterate through the stored possible hidden pairs and sees if there is an actual hidden pair
                    for iter_value in variables_to_consider.keys():
                        if iter_value != value:
                            # There is apparently an error in the following if statement, index out of range error,
                            # This should have been fixed
                            if (variables_to_consider[iter_value][0] in variables_to_consider[value] and
                                    variables_to_consider[iter_value][1] in variables_to_consider[value]):
                                first_variable = variables_to_consider[value][0]
                                second_variable = variables_to_consider[value][1]
                                self.trail.push(first_variable)
                                first_variable.setDomain(Domain([value, iter_value]))

                                self.trail.push(second_variable)
                                second_variable.setDomain(Domain([value, iter_value]))

                                del variables_to_consider[iter_value]
                                del variables_to_consider[value]
                                # Update the counts again, since it would have changed
                                for value in range(1, n + 1):
                                    value_freq[value] = 0
                                for var in c.vars:
                                    if not var.isAssigned():
                                        for value in var.getValues():
                                            value_freq[value] += 1  # adds elements in the domain
                                break
    
    def naked_pair_pruning(self):
        """
        A pair is called naked if it is lonely in a cell.
        If a pair is naked in two unit cells, then it can be dropped from all the other unit cells.
        Following the same logic of hidden pairs.
        """
        n = self.gameboard.N  # number of different values each variable can take
        value_freq = [0] * (n + 1)  # array of values to count up with frequencies

        for c in self.network.getConstraints():
            pairs_to_consider = dict()
            for value in range(1, n + 1):
                value_freq[value] = 0
            for var in c.vars:
                if not var.isAssigned():
                    if len(var.getValues()) == 2:
                        try:
                            pairs_to_consider[tuple(var.getValues())] += 1
                        except KeyError:
                            pairs_to_consider[tuple(var.getValues())] = 1

            for key, value in pairs_to_consider.items():
                if value >= 2:  # There might be more than 2 which should result in an automatic backtrack
                    variables_to_consider = [var for var in c.vars if key == tuple(var.getValues())][0:2]
                    for var in c.vars:
                        if key[0] in var.getValues() and var not in variables_to_consider:
                            self.trail.push(var)
                            var.removeValueFromDomain(key[0])

                        if key[1] in var.getValues() and var not in variables_to_consider:
                            self.trail.push(var)
                            var.removeValueFromDomain(key[1])    
    
    def getTournCC(self, **kwargs):
        """
             TODO: Implement your own advanced Constraint Propagation

             Completing the three tourn heuristic will automatically enter
             your program into a tournament.
        """
        last_assigned_var = kwargs["last_assigned_var"] if "last_assigned_var" in kwargs else None

        if last_assigned_var is None:  # if initial board, perform arc-consistency
            if not self.arcConsistency():
                return False
        self.hidden_pair_prune()
        self.naked_pair_pruning()
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

    def getMRV(self):
        """
            Returns: The unassigned variable with the smallest domain or None if there are no more variables to assign
        """
        # returns the minimum var that is unassigned based on its domain size
        return min(
            (var for var in self.network.getVariables() if not var.isAssigned()),
            key=lambda x: x.size(),
            default=None
        )

    def MRVwithTieBreaker(self):
        """
           Returns: The unassigned variable with the smallest domain and affecting the  most unassigned neighbors.
                   If there are multiple variables that have the same smallest domain with the same number of unassigned
                   neighbors, add them to the list of Variables.

                   If there is only one variable, return the list of size 1 containing that variable.
        """
        mrv_variable = self.getMRV()
        if mrv_variable is None:
            return [None]

        minimum_remaining_var_domain_size = mrv_variable.size()
        min_remaining_value_vars = [var for var in self.network.getVariables() if
                                    (var.size() == minimum_remaining_var_domain_size and not var.isAssigned())]
        maximum_degree = \
            max(
                (sum((1 for neighbor in self.network.getNeighborsOfVariable(var) if not neighbor.isAssigned()), 0)
                 for var in min_remaining_value_vars))

        return [var for var in min_remaining_value_vars
                if sum((1 for neighbor in self.network.getNeighborsOfVariable(var) if not neighbor.isAssigned()), 0)
                == maximum_degree]

    def getTournVar(self):
        """
             Optional TODO: Implement your own advanced Variable Heuristic

             Completing the three tourn heuristic will automatically enter
             your program into a tournament.
        """
        return self.MRVwithTieBreaker()[0]

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

        return list(sorted(
            (value for value in var.getValues()), key=lambda x:
            sum(1 for neighbor in self.network.getNeighborsOfVariable(var)
                if not neighbor.isAssigned() and x in neighbor.getValues()
                )
        ))

    def getTournVal(self, v):
        """
             TODO: Implement your own advanced Value Heuristic

             Completing the three tourn heuristic will automatically enter
             your program into a tournament.
        """
        return self.getValuesLCVOrder(v)

    # ==================================================================
    # Engine Functions
    # ==================================================================

    def solve(self, time_left=600):
        if time_left <= 0:
            return -1

        start_time = time.time()
        if self.hassolution:
            return 0

        # Variable Selection
        v = self.selectNextVariable()

        # check if the assigment is complete
        if v is None:
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
            if self.checkConsistency(last_assigned_vars=[v]):  # add variable last assigned for optimized checking
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

    def checkConsistency(self, last_assigned_vars: [Variable] = None):

        if self.cChecks == "forwardChecking":
            return self.forwardChecking(last_assigned_vars=last_assigned_vars)[1]

        if self.cChecks == "norvigCheck":
            return self.norvigCheck(last_assigned_vars=last_assigned_vars)[1]

        if self.cChecks == "tournCC":
            return self.getTournCC(last_assigned_vars=last_assigned_vars)

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
