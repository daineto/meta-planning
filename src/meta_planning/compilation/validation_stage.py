from ..pddl import Predicate, TypedObject, Literal, Effect, Scheme
from ..pddl import Truth, Conjunction

from .basic import get_all_subtypes
from .problem import generate_domain_objects

import itertools



def generate_all_literals(predicates, objects, all_types, valuation=True):

    all_literals = []
    for p in predicates:
        types_for_predicate = [get_all_subtypes(arg.type_name, all_types) for arg in p.arguments]
        objects_for_predicate = [[o for o in objects if o.type_name in types] for types in types_for_predicate]

        combinations = list(itertools.product(*objects_for_predicate))
        for comb in combinations:
            all_literals += [Literal(p.name, [o.name for o in comb], valuation)]

    return all_literals


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

    return Scheme("validate_" + str(count), [], 0, Conjunction(pre), eff, 0)



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
        eff += [Effect([], Truth(), l.negate()) for l in all_literals if l not in init_literals and l.negate() not in literals] # delete the goal state of the last observation

        if observation.states[0].next_action != None:
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

            if state.next_action != None:
                new_actions += [state.next_action]

    validation_action = generate_validation_action(literals, new_actions, old_actions, states_seen,
                                                   observations_contain_actions, additional_preconditions=pre,
                                                   additional_effects=eff)
    validation_actions += [validation_action]




    return validation_actions