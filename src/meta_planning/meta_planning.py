from .compilation import generate_model_representation_fluents
from .compilation import generate_programming_actions
from .compilation import generate_auxiliary_programming_fluents
from .compilation import generate_programmable_action

from .compilation import generate_test_fluents
from .compilation import generate_plan_fluents
from .compilation import generate_validation_actions

from .compilation import generate_step_type
from .compilation import generate_step_predicates

from .compilation import generate_goal
from .compilation import generate_initial_state
from .compilation import generate_domain_objects
from .compilation import generate_step_objects

from .compilation import get_model_space_size

from .compilation import ModelRecognitionSolution

from .pddl import Problem

from .parsers import parse_solution

import copy
import os



class ValidationTask(object):

    def __init__(self, initial_model, observations, allow_insertions=False, allow_deletions=False):
        self.initial_model = initial_model
        self.observations = observations

        self.allow_insertions=allow_insertions
        self.allow_deletions=allow_deletions

        self.compiled_model = self.__compile_model()
        self.compiled_problem = self.__compile_problem()

    def __compile_model(self):
        compiled_model = copy.deepcopy(self.initial_model)
        compiled_model.schemata = []

        observations_contain_actions = any([o.has_actions() for o in self.observations])
        all_states_observed = all([o.all_states_observed for o in self.observations])
        all_actions_observed = all([o.all_actions_observed for o in self.observations])

        NUM_OBSERVATIONS = len(self.observations)
        NUM_OBSERVED_STATES = sum([o.number_of_states for o in self.observations])
        MAX_OBSERVED_ACTIONS = max([o.number_of_actions for o in self.observations])

        initial_model_propositional_encoding = self.initial_model.propositional_encoding()


        # Programming

        for scheme in self.initial_model.schemata:

            scheme_model_representation_fluents = generate_model_representation_fluents(scheme, self.initial_model.predicates, self.initial_model.types)
            compiled_model.predicates += scheme_model_representation_fluents

            programming_actions = generate_programming_actions(scheme, self.initial_model.predicates, self.initial_model.types, initial_model_propositional_encoding, allow_insertions=self.allow_insertions, allow_deletions=self.allow_deletions)
            compiled_model.schemata += programming_actions

            programmable_action = generate_programmable_action(scheme, self.initial_model.predicates, self.initial_model.types, observations_contain_actions, all_states_observed, all_actions_observed)
            compiled_model.schemata += [programmable_action]

        auxiliary_programming_fluents = generate_auxiliary_programming_fluents()
        compiled_model.predicates += auxiliary_programming_fluents

        # effects_programming_action = generate_effects_programming_action()
        # compiled_model.schemata += [effects_programming_action]



        # Validation

        if observations_contain_actions:
            step_type = generate_step_type()
            compiled_model.types += [step_type]

            step_predicates = generate_step_predicates()
            compiled_model.predicates += step_predicates

            plan_fluents = generate_plan_fluents(self.initial_model.schemata)
            compiled_model.predicates += plan_fluents

        test_fluents = generate_test_fluents(NUM_OBSERVED_STATES, NUM_OBSERVATIONS)
        compiled_model.predicates += test_fluents

        validation_actions = generate_validation_actions(self.observations, observations_contain_actions, self.initial_model.predicates, self.initial_model.types)
        compiled_model.schemata += validation_actions

        return compiled_model


    def __compile_problem(self):

        observations_contain_actions = any([o.has_actions() for o in self.observations])

        NUM_OBSERVATIONS = len(self.observations)
        NUM_OBSERVED_STATES = sum([o.number_of_states for o in self.observations])
        MAX_OBSERVED_ACTIONS = max([o.number_of_actions for o in self.observations])

        initial_model_propositional_encoding = self.initial_model.propositional_encoding()

        init = generate_initial_state(MAX_OBSERVED_ACTIONS, initial_model_propositional_encoding)

        goal = generate_goal(NUM_OBSERVED_STATES, NUM_OBSERVATIONS)

        objects = generate_domain_objects(self.observations)

        if observations_contain_actions:
            step_objects = generate_step_objects(MAX_OBSERVED_ACTIONS)
            objects += step_objects

        return Problem("compiled_problem", self.initial_model.domain_name, objects, init, goal)


    def validate(self, clean=True):
        problem_file = 'compiled_problem'
        domain_file = 'compiled_domain'
        solution_file = 'solution_plan'
        log_file = "planner_out"

        self.compiled_model.to_file(domain_file)
        self.compiled_problem.to_file(problem_file)

        initial_model_propositional_encoding = self.initial_model.propositional_encoding()

        planner_path =  os.path.join(os.path.dirname(__file__), 'util/planners/madagascar/M')

        min_horizon = sum([max(o.number_of_states*2 - 1, o.number_of_states+o.number_of_actions) for o in self.observations]) - len(self.observations) + 1
        max_horizon = min_horizon

        if self.allow_insertions or self.allow_deletions:
            max_horizon += 2

        cmd_args = [planner_path, domain_file, problem_file, "-S 1", "-Q", "-o %s" % solution_file, "-F %s" % min_horizon]

        if all(o.bounded for o in self.observations):
            cmd_args += ["-T %s" % max_horizon]

        cmd_args += ["> %s" % log_file]

        cmd = " ".join(cmd_args)

        print(cmd)
        os.system(cmd)

        solution  = parse_solution(solution_file, self.initial_model, self.observations, initial_model_propositional_encoding)

        if clean:
            cmd = "rm %s; rm %s; rm %s; rm %s" % (domain_file, problem_file, solution_file, log_file)
            os.system(cmd)

        return solution


class LearningTask(ValidationTask):

    def __init__(self, initial_model, observations, allow_insertions=False, allow_deletions=False):
        ValidationTask.__init__(self, initial_model, observations, allow_insertions=True)

    def learn(self, clean=True):
        return self.validate(clean=clean)


class ModelRecognitionTask(object):

    def __init__(self, models, observations, priors):
        self.models = models
        self.observations = observations
        self.priors = priors
        self.tasks = [ValidationTask(m, observations, allow_insertions=True, allow_deletions=True) for m in models]


    def recognize(self):
        solutions = [t.validate() for t in self.tasks]
        model_space_size = get_model_space_size(self.models[0])

        return ModelRecognitionSolution(solutions, self.priors, model_space_size)
