from ..pddl import Literal, Action
from ..observations import State, Trajectory

from .pddl_parsing import parse_pddl_file
from .parsing_functions import parse_typed_list, parse_state

from ..functions import generate_all_literals

import random
import itertools







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
    new_state = parse_state(init[1:], all_literals)


    for token in iterator:
        if token[0] == ':state':
            new_state = parse_state(token[1:], all_literals)
        elif token[0] == ':action':
            next_action = Action(token[1][0], token[1][1:])
            new_state.next_action = next_action

            states.append(new_state)


    states.append(new_state)


    return Trajectory(object_list, states)