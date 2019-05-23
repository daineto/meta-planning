from ..pddl import Predicate, Type, TypedObject


def get_all_subtypes(the_type, all_types):
   subtypes=[the_type]
   for a_type in all_types:
       if a_type.basetype_name == the_type:
           subtypes.append(str(a_type.name))
   return subtypes


def is_possible_predicate_for_scheme(predicate, scheme, tup, types):
    if (len(predicate.arguments) > len(scheme.parameters)):
        return False

    scheme_types = [set([scheme.parameters[int(tup[i])-1].type_name]) for i in range(len(tup))]
    predicate_types = [set(get_all_subtypes(x.type_name, types)) for x in predicate.arguments]

    fits = [len(scheme_types[i].intersection(predicate_types[i])) >= 1 for i in range(len(scheme_types))]
    return all(fits)


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

