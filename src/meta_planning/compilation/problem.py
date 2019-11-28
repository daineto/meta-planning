from ..pddl import TypedObject, Literal, Conjunction
from ..observations import State

def generate_goal(number_of_states, number_of_observations):

    num_validate_actions = number_of_states - number_of_observations

    return Conjunction([Literal("test" + str(num_validate_actions), [], True), Literal("disabled", [], False)])


def generate_domain_objects(observations):
    objects = []
    for observation in observations:
        objects += observation.objects
    objects = list(set(objects))

    return objects


def generate_step_objects(max_actions):

    return [TypedObject("i" + str(i), "step") for i in range(max_actions+1)]


def generate_initial_state(max_actions, known_model):

    init = [Literal("modeProg", [], True)]

    init += known_model

    if max_actions != 0:
        init += [Literal("inext", ["i" + str(i), "i" + str(i+1)], True) for i in range(max_actions)]

    return State(init, None)

