from ..functions import generate_all_literals

from ..pddl import Predicate, TypedObject, Literal, Effect, Scheme
from ..pddl import Truth, Conjunction
from ..pddl import Increase, PrimitiveNumericExpression, NumericConstant

from .problem import generate_domain_objects

import numpy as np


def generate_test_fluents(num_observed_states, num_observations):
    test_fluents = [Predicate("test" + str(i), []) for i in range(num_observed_states - num_observations + 1)]
    return test_fluents


def generate_plan_fluents(schemata):
    # Define action validation predicates
    # Example (plan-pickup ?i - step ?x - block)

    plan_fluents = []
    for scheme in schemata:
        plan_fluents += [Predicate("plan-" + scheme.name, [TypedObject("?i", "step")] + scheme.parameters)]

    return plan_fluents


def generate_validation_action(literals, new_actions, old_actions, count, observations_contain_actions, additional_effects=[], additional_preconditions=[]):
    pre = additional_preconditions
    eff = additional_effects

    pre += literals

    pre += [Literal("disabled", [], False)]

    if count != 0:
        pre += [Literal("test"+ str(count-1), [], True)]
        eff += [Effect([], Truth(), Literal("test"+ str(count-1), [], False))]

    eff += [Effect([], Truth(), Literal("test" + str(count), [], True))]

    if observations_contain_actions:
        if count != 0:
            pre += [Literal("current", ["i"+str(len(old_actions))], True)]
        eff += [Effect([], Truth(), Literal("current", ["i"+str(len(old_actions))], False))]
        eff += [Effect([], Truth(), Literal("current", ["i0"], True))]

    for i in range(len(new_actions)):
        action = new_actions[i]
        eff += [Effect([], Truth(), Literal("plan-" + action.name, ["i" + str(i)] + action.arguments, True))]

    for i in range(len(old_actions)):
        action = old_actions[i]
        eff += [Effect([], Truth(), Literal("plan-" + action.name, ["i" + str(i)] + action.arguments, False))]

    return Scheme("validate_" + str(count), [], 0, Conjunction(pre), eff, None)



def generate_validation_actions(observations, observations_contain_actions, predicates, types):
    validation_actions = []

    all_objects = generate_domain_objects(observations)
    all_literals = generate_all_literals(predicates, all_objects, types)

    last_state_validations = []
    # First validate action
    pre = [Literal("modeProg", [], True)]
    eff = [Effect([], Truth(), Literal("modeProg", [], False))]
    # eff += [Effect([], Truth(), l) for l in observations[0].states[0].literals if l.valuation]


    old_actions = []
    new_actions = []
    states_seen = 0
    literals = []

    for observation in observations:

        init_literals = observation.states[0].literals
        eff += [Effect([], Truth(), l) for l in init_literals if l.valuation and l not in literals] # add the literals of the initial state
        # eff += [Effect([], Truth(), l.negate()) for l in all_literals if l not in init_literals and l.negate() not in literals] # delete the goal state of the last observation
        eff += [Effect([], Truth(), l.negate()) for l in all_literals if
                l.valuation and l not in init_literals and l in literals]


        if observation.states[0].next_action is not None:
            new_actions += [observation.states[0].next_action]


        for state in observation.states[1:]:
            if state.literals != []:
                validation_action = generate_validation_action(literals, new_actions, old_actions, states_seen, observations_contain_actions, additional_preconditions=pre, additional_effects=eff)
                validation_actions += [validation_action]

                states_seen += 1
                literals = state.literals
                old_actions = new_actions
                new_actions = []
                pre = []
                eff = []

                pre += [Literal("action_applied", [], True)]
                eff += [Effect([], Truth(), Literal("action_applied", [], False))]

            if state.next_action is not None:
                new_actions += [state.next_action]

    validation_action = generate_validation_action(literals, new_actions, old_actions, states_seen,
                                                   observations_contain_actions, additional_preconditions=pre,
                                                   additional_effects=eff)
    validation_actions += [validation_action]




    return validation_actions


def generate_sense_action(observed_literals, new_actions, old_actions, count, observations_contain_actions, sensor_model, additional_effects=[], additional_preconditions=[]):
    pre = additional_preconditions
    eff = additional_effects

    pre += [Literal("disabled", [], False)]

    if count != 0:
        pre += [Literal("test"+ str(count-1), [], True)]
        eff += [Effect([], Truth(), Literal("test"+ str(count-1), [], False))]

    eff += [Effect([], Truth(), Literal("test" + str(count), [], True))]

    for observable in observed_literals:
        for s_literal,probability in sensor_model.get_state_variables(observable).items():

            if probability == 0:
                eff += [
                    Effect([], s_literal, Literal("disabled", [], True))]
            elif sensor_model.probabilistic and probability > 0 and probability < 1:
                cost = -round(np.log(probability) * 100)
                eff += [
                    Effect([], s_literal, Increase(PrimitiveNumericExpression("total-cost", []), NumericConstant(cost)))]


    if observations_contain_actions:
        if count != 0:
            pre += [Literal("current", ["i"+str(len(old_actions))], True)]
        eff += [Effect([], Truth(), Literal("current", ["i"+str(len(old_actions))], False))]
        eff += [Effect([], Truth(), Literal("current", ["i0"], True))]

    for i in range(len(new_actions)):
        action = new_actions[i]
        eff += [Effect([], Truth(), Literal("plan-" + action.name, ["i" + str(i)] + action.arguments, True))]

    for i in range(len(old_actions)):
        action = old_actions[i]
        eff += [Effect([], Truth(), Literal("plan-" + action.name, ["i" + str(i)] + action.arguments, False))]

    return Scheme("sense" + str(count), [], 0, Conjunction(pre), eff, None)


def generate_sense_missing_action(sensor_model):
    pre = []
    eff = []

    pre += [Literal("disabled", [], False)]

    pre += [Literal("action_applied", [], True)]
    eff += [Effect([], Truth(), Literal("action_applied", [], False))]

    o_to_s = sensor_model.get_o_to_s()

    for literal in sensor_model.get_observable_fluents():
        s_literal = o_to_s[literal]
        # Missing
        probability = sensor_model.observability_table[s_literal][2]
        if probability == 0:
            eff += [
                Effect([], s_literal, Literal("disabled", [], True))]
        elif probability > 0 and probability < 1:
            cost = -round(np.log(probability) * 100)
            eff += [
                Effect([], s_literal, Increase(PrimitiveNumericExpression("total-cost", []), NumericConstant(cost)))]
            # eff += [
            #     Effect([], s_literal.negate(),
            #            Increase(PrimitiveNumericExpression("total-cost", []), NumericConstant(cost)))]

    return Scheme("sense_missing", [], 0, Conjunction(pre), eff, None)


def generate_sense_actions(observations, sensor_model, observations_contain_actions):
    sense_actions = []

    all_literals = sensor_model.o_to_s.keys()

    last_state_validations = []
    # First validate action
    pre = [Literal("modeProg", [], True)]
    eff = [Effect([], Truth(), Literal("modeProg", [], False))]


    old_actions = []
    new_actions = []
    states_seen = 0
    literals = []

    for observation in observations:

        init_literals = observation.states[0].literals
        eff += [Effect([], Truth(), l) for l in init_literals if l.valuation and l not in literals] # add the literals of the initial state
        # eff += [Effect([], Truth(), l.negate()) for l in all_literals if l.valuation and l not in init_literals and l.negate() not in literals] # delete the goal state of the last observation
        eff += [Effect([], Truth(), l.negate()) for l in all_literals if
                l.valuation and l not in init_literals and l in literals]

        if observation.states[0].next_action is not None:
            new_actions += [observation.states[0].next_action]

        first=True
        for state in observation.states[1:]:
            if state.literals != []:
                if first:
                    sense_action = generate_validation_action(literals, new_actions, old_actions, states_seen,
                                                         observations_contain_actions,
                                                         additional_preconditions=pre, additional_effects=eff)
                    first = False
                else:
                    sense_action = generate_sense_action(literals, new_actions, old_actions, states_seen,
                                                         observations_contain_actions, sensor_model,
                                                         additional_preconditions=pre, additional_effects=eff)
                sense_actions += [sense_action]

                states_seen += 1
                literals = state.literals
                old_actions = new_actions
                new_actions = []
                pre = []
                eff = []

                pre += [Literal("action_applied", [], True)]
                eff += [Effect([], Truth(), Literal("action_applied", [], False))]

            if state.next_action is not None:
                new_actions += [state.next_action]

    sense_action = generate_validation_action(literals, new_actions, old_actions, states_seen,
                                                   observations_contain_actions, additional_preconditions=pre,
                                                   additional_effects=eff)
    sense_actions += [sense_action]


    # Sense missing
    # sense_action = generate_sense_missing_action(sensor_model)
    # sense_actions += [sense_action]



    return sense_actions