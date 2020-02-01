from .compilation import generate_model_representation_fluents
from .compilation import generate_programming_actions
from .compilation import generate_auxiliary_programming_fluents
from .compilation import generate_programmable_action
from .compilation import generate_extended_action

from .compilation import generate_test_fluents
from .compilation import generate_plan_fluents
from .compilation import generate_validation_actions
from .compilation import generate_sense_actions

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

    def __init__(self, initial_model, observations, allow_insertions=False, allow_deletions=False, compile_known=True, use_cost=False, sensor_model=None):
        self.initial_model = initial_model
        self.observations = observations

        self.allow_insertions=allow_insertions
        self.allow_deletions=allow_deletions
        self.compile_known = compile_known

        self.use_cost = use_cost
        self.sensor_model = sensor_model

        self.compiled_model = self.__compile_model()
        self.compiled_problem = self.__compile_problem()

    def __compile_model(self):
        compiled_model = copy.deepcopy(self.initial_model)
        compiled_model.schemata = []

        if self.use_cost:
            compiled_model.use_cost = self.use_cost

        observations_contain_actions = any([o.has_actions() for o in self.observations])
        all_states_observed = all([o.all_states_observed for o in self.observations])
        all_actions_observed = all([o.all_actions_observed for o in self.observations])


        if all_states_observed:
            alternate = True
        else:
            alternate = False

        # if all_states_observed or self.sensor_model is not None:
        #     alternate = True
        # else:
        #     alternate = False

        NUM_OBSERVATIONS = len(self.observations)
        NUM_OBSERVED_STATES = sum([o.number_of_states for o in self.observations])
        MAX_OBSERVED_ACTIONS = max([o.number_of_actions for o in self.observations])

        initial_model_propositional_encoding = self.initial_model.propositional_encoding()


        # Programming

        for scheme in self.initial_model.schemata:

            if self.compile_known:
                scheme_model_representation_fluents = generate_model_representation_fluents(scheme, self.initial_model.predicates, self.initial_model.types)
                compiled_model.predicates += scheme_model_representation_fluents

                programming_actions = generate_programming_actions(scheme, self.initial_model.predicates, self.initial_model.types, initial_model_propositional_encoding, allow_insertions=self.allow_insertions, allow_deletions=self.allow_deletions)
                compiled_model.schemata += programming_actions

                programmable_action = generate_programmable_action(scheme, self.initial_model.predicates, self.initial_model.types, alternate, observations_contain_actions, all_actions_observed)
                if self.use_cost:
                    programmable_action.cost = scheme.cost

                compiled_model.schemata += [programmable_action]

            else:
                extended_action = generate_extended_action(scheme, alternate, observations_contain_actions, all_actions_observed)
                if self.use_cost:
                    extended_action.cost = scheme.cost

                compiled_model.schemata += [extended_action]

        auxiliary_programming_fluents = generate_auxiliary_programming_fluents()
        compiled_model.predicates += auxiliary_programming_fluents

        # effects_programming_action = generate_effects_programming_action()
        # compiled_model.schemata += [effects_programming_action]



        # Validation

        if self.sensor_model is None:

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

        else:

            if observations_contain_actions:
                step_type = generate_step_type()
                compiled_model.types += [step_type]

                step_predicates = generate_step_predicates()
                compiled_model.predicates += step_predicates

                plan_fluents = generate_plan_fluents(self.initial_model.schemata)
                compiled_model.predicates += plan_fluents

            test_fluents = generate_test_fluents(NUM_OBSERVED_STATES, NUM_OBSERVATIONS)
            compiled_model.predicates += test_fluents

            sense_actions = generate_sense_actions(self.observations, self.sensor_model, observations_contain_actions)

            compiled_model.schemata += sense_actions

        return compiled_model


    def __compile_problem(self):

        observations_contain_actions = any([o.has_actions() for o in self.observations])

        NUM_OBSERVATIONS = len(self.observations)
        NUM_OBSERVED_STATES = sum([o.number_of_states for o in self.observations])
        MAX_OBSERVED_ACTIONS = max([o.number_of_actions for o in self.observations])


        if self.compile_known:
            initial_model_propositional_encoding = self.initial_model.propositional_encoding()
        else:
            initial_model_propositional_encoding = []
        init = generate_initial_state(MAX_OBSERVED_ACTIONS, initial_model_propositional_encoding)

        goal = generate_goal(NUM_OBSERVED_STATES, NUM_OBSERVATIONS)

        objects = generate_domain_objects(self.observations)

        if observations_contain_actions:
            step_objects = generate_step_objects(MAX_OBSERVED_ACTIONS)
            objects += step_objects

        return Problem("compiled_problem", self.initial_model.domain_name, objects, init, goal, use_metric=self.use_cost)


    def validate(self, clean=True, parallel=True, planner="madagascar", t=3000):
        problem_file = 'compiled_problem'
        domain_file = 'compiled_domain'
        solution_file = 'solution_plan'
        log_file = "planner_out"

        self.compiled_model.to_file(domain_file)
        self.compiled_problem.to_file(problem_file)

        initial_model_propositional_encoding = self.initial_model.propositional_encoding()

        if planner == "madagascar":
            planner_path =  os.path.join(os.path.dirname(__file__), 'util/planners/madagascar/M')

            min_horizon = sum([max(o.number_of_states*2 - 1, o.number_of_states+o.number_of_actions) for o in self.observations]) - len(self.observations) + 1
            max_horizon = min_horizon

            if self.allow_insertions or self.allow_deletions:
                max_horizon += 2

            cmd_args = [planner_path, domain_file, problem_file, "-S 1", "-Q", "-o %s" % solution_file, "-F %s" % min_horizon]

            if not parallel:
                cmd_args += ["-P 0"]

            if parallel and all(o.bounded for o in self.observations):
                cmd_args += ["-T %s" % max_horizon]

            cmd_args += ["> %s" % log_file]

        elif planner == "downward":
            planner_path = "/home/dieaigar/PhD/downward/fast-downward.py"

            cmd_args = [planner_path, '--plan-file %s' % solution_file, domain_file, problem_file, '--search "astar(lmcut())"']

        elif planner == "metric-ff":
            planner_path = os.path.join(os.path.dirname(__file__), 'util/planners/metric-FF/ff')

            cmd_args = [planner_path, "-E", "-O", "-g 1", "-h 0", "-o %s" % domain_file, "-f %s" % problem_file, "-s %s" % solution_file]


        cmd = " ".join(cmd_args)
        cmd = "ulimit -t %d; " % t + cmd

        print(cmd)
        os.system(cmd)

        solution = parse_solution(solution_file, self.initial_model, self.observations,
                                  initial_model_propositional_encoding)


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
        solutions = [t.validate(parallel=False) for t in self.tasks]
        model_space_size = get_model_space_size(self.models[0])

        return ModelRecognitionSolution(solutions, self.priors, model_space_size)
