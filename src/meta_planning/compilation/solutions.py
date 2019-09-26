import sys

class Solution(object):

    def __init__(self, solution_found):
        self.solution_found = solution_found

class FoundSolution(Solution):
    def __init__(self, solution_plan, learned_model, edit_distance, explanations):
        self.solution_found = True
        self.solution_plan = solution_plan
        self.learned_model = learned_model
        self.edit_distance = edit_distance
        self.explanations = explanations

class NoSolution(Solution):
    def __init__(self):
        self.solution_found = False
        self.edit_distance = -1


class ModelRecognitionSolution(object):
    def __init__(self, solutions, priors, model_space_size, edit_probability=0.2):
        self.solutions = solutions
        self.priors = priors
        self.model_space_size = model_space_size
        self.edit_probability=edit_probability
        self.conditionals = self.__compute_conditionals()
        self.posteriors = self.__compute_posteriors()
        self.normalized_posteriors = self.__normalize_posteriors()


    def __compute_conditionals(self):
        conditionals = []

        for s in self.solutions:
            if s.edit_distance == -1:
                conditionals += [0]
            else:
                conditionals += [self.edit_probability**s.edit_distance + (1-self.edit_probability)**(self.model_space_size-s.edit_distance)]

        return conditionals


    def __compute_posteriors(self):
        return [self.conditionals[i]*self.priors[i] for i in range(len(self.solutions))]


    def __normalize_posteriors(self):
        return [self.posteriors[i]/sum(self.posteriors) for i in range(len(self.posteriors))]

