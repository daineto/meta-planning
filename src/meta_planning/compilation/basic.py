from ..pddl import Predicate, Type, TypedObject

def generate_auxiliary_programming_fluents():
    auxiliary_fluents = []

    # Define "modeProg" predicate
    auxiliary_fluents += [Predicate("modeProg", [])]
    # auxiliary_fluents += [Predicate("modeProg2", [])]
    # Define "disabled" predicate
    auxiliary_fluents += [Predicate("disabled", [])]
    # Define "action_applied" predicate
    auxiliary_fluents += [Predicate("action_applied", [])]

    return auxiliary_fluents


def generate_step_type():
    # Define "step" domain type
    return Type("step", "None")


def generate_step_predicates():
    step_predicates = []

    # Define "current" predicate. Example (current ?i - step)
    step_predicates += [Predicate("current", [TypedObject("?i", "step")])]

    # Define "inext" predicate. Example (inext ?i1 - step ?i2 - step)
    step_predicates += [Predicate("inext", [TypedObject("?i1", "step"), TypedObject("?i2", "step")])]

    return step_predicates
