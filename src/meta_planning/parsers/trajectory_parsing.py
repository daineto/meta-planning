from ..pddl import Literal, Action
from ..observations import State, Trajectory

from .pddl_parsing import parse_pddl_file
from .parsing_functions import parse_typed_list

from ..compilation import generate_all_literals

import random
import itertools



def check_state_consistency(literal, same_truth_value, other_truth_value):
    if literal in other_truth_value:
        raise SystemExit("Error in initial state specification\n" +
                         "Reason: %s is true and false." %  literal)
    if literal in same_truth_value:
        print("Warning: %s is specified twice in initial state specification" % literal)


def parse_state(new_state, all_literals, autocomplete=True):
    state = []
    state_true = set()
    state_false = set()
    for fact in new_state:
        if fact[0] == "not":
            literal = Literal(fact[1][0], fact[1][1:], False)
            check_state_consistency(literal, state_false, state_true)
            state_false.add(literal)
        else:
            literal = Literal(fact[0], fact[1:], True)
            check_state_consistency(literal, state_true, state_false)
            state_true.add(literal)

    state.extend(state_true)

    if autocomplete:
        for literal in all_literals.difference(state_true):
            state.append(Literal(literal.predicate, literal.args, False))
    else:
        state.extend(state_false)

    return sorted(state)


def parse_trajectory(trajectory_file, model):

    predicates = model.predicates
    types = model.types

    trajectory_pddl = parse_pddl_file('trajectory', trajectory_file)

    random.seed(123)

    iterator = iter(trajectory_pddl)

    tag = next(iterator)
    assert tag == "trajectory"

    objects_opt = next(iterator)
    assert objects_opt[0] == ":objects"
    object_list = parse_typed_list(objects_opt[1:])

    all_literals = set(generate_all_literals(predicates, object_list, types))


    states = []


    init = next(iterator)
    assert init[0] == ":init"
    state_literals = parse_state(init[1:], all_literals)
    next_action = None

    for token in iterator:
        if token[0] == ':state':
            state_literals = parse_state(token[1:], all_literals)
        elif token[0] == ':action':
            next_action = Action(token[1][0], token[1][1:])

            new_state = State(state_literals, next_action)
            states.append(new_state)

            state_literals = []
            next_action = None

    last_state = State(state_literals, next_action)
    states.append(last_state)


    return Trajectory(object_list, states)