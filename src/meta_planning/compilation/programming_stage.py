from ..pddl import Predicate, Literal, Scheme, Effect, Truth, Conjunction, Type, TypedObject
from ..functions import is_possible_predicate_for_scheme

import itertools


# def generate_model_representation_fluents(scheme, predicates, types):
#
#     model_representation_fluents = []
#
#     var_ids = []
#     for i in range(scheme.num_external_parameters):
#         var_ids += ["" + str(i + 1)]
#     for p in predicates:
#         for tup in itertools.product(var_ids, repeat=(len(p.arguments))):
#             if is_possible_predicate_for_scheme(p, scheme, tup, types):
#                 vars = ["var" + str(t) for t in tup]
#
#                 model_representation_fluents.append(Predicate("pre_" + "_".join([scheme.name] + [p.name] + vars), []))
#                 model_representation_fluents.append(Predicate("eff_" + "_".join([scheme.name] + [p.name] + vars), []))
#
#     return model_representation_fluents


def get_model_space_size(model):

    schemata_sizes = [len(generate_model_representation_fluents(scheme, model.predicates, model.types)) for scheme in model.schemata]
    size = sum(schemata_sizes)

    return size




def generate_model_representation_fluents(scheme, predicates, types):

    model_representation_fluents = []

    var_ids = []
    for i in range(scheme.num_external_parameters):
        var_ids += ["" + str(i + 1)]
    for p in predicates:
        for tup in itertools.product(var_ids, repeat=(len(p.arguments))):
            if is_possible_predicate_for_scheme(p, scheme, tup, types):
                vars = ["var" + str(t) for t in tup]

                model_representation_fluents.append(Predicate("pre_" + "_".join([scheme.name] + [p.name] + vars), []))
                model_representation_fluents.append(Predicate("eff_" + "_".join([scheme.name] + [p.name] + vars), []))

    return model_representation_fluents


def generate_all_possible_propositions(scheme, predicates, types):
    pre_propositions = []
    eff_propositions = []

    var_ids = []
    for i in range(scheme.num_external_parameters):
        var_ids += ["" + str(i + 1)]
    for p in predicates:
        for tup in itertools.product(var_ids, repeat=len(p.arguments)):
            if is_possible_predicate_for_scheme(p, scheme, tup, types):
                vars = ["var" + str(t) for t in tup]

                pre_propositions += [Literal("pre_" + "_".join([scheme.name] + [p.name] + vars), [], True)]
                eff_propositions += [Literal("eff_" + "_".join([scheme.name] + [p.name] + vars), [], True)]

    return pre_propositions, eff_propositions




def generate_programming_actions(scheme, predicates, types, known_model, allow_insertions=False, allow_deletions=False):
    programming_actions = []

    pre_propositions, eff_propositions = generate_all_possible_propositions(scheme, predicates, types)



    if allow_insertions:

        # Action for inserting a precondition

        for proposition in [prop for prop in pre_propositions if prop not in known_model]:

            pre = []
            pre += [Literal("modeProg", [], True)]
            pre += [proposition.negate()]

            eff = [Effect([], Truth(), proposition)]

            programming_actions += [ Scheme("insert_" + proposition.predicate, [],
                                    0, Conjunction(pre), eff, None) ]


        # Action for inserting an effect

        for proposition in [prop for prop in eff_propositions if prop not in known_model]:

            pre = []
            pre += [Literal("modeProg", [], True)]
            pre += [proposition.negate()]

            eff = [Effect([], Truth(), proposition)]

            programming_actions += [Scheme("insert_" + proposition.predicate, [],
                                           0, Conjunction(pre), eff, None)]

    if allow_deletions:

        # Action for inserting a precondition

        for proposition in [prop for prop in pre_propositions if prop in known_model]:
            pre = []
            pre += [Literal("modeProg", [], True)]
            pre += [proposition]

            eff = [Effect([], Truth(), proposition.negate())]

            programming_actions += [Scheme("delete_" + proposition.predicate, [],
                                           0, Conjunction(pre), eff, None)]

        # Action for inserting an effect

        for proposition in [prop for prop in eff_propositions if prop in known_model]:
            pre = []
            pre += [Literal("modeProg", [], True)]
            pre += [proposition]

            eff = [Effect([], Truth(), proposition.negate())]

            programming_actions += [Scheme("delete_" + proposition.predicate, [],
                                           0, Conjunction(pre), eff, None)]


    return programming_actions


# def generate_effects_programming_action():
#     pre = [Literal("modeProg1", [], True)]
#     eff = [Effect([], Truth(), Literal("modeProg1", [], False))]
#     eff += [Effect([], Truth(), Literal("modeProg2", [], True))]
#
#     effects_programming_action = Scheme("effects_programming", [], 0, Conjunction(pre), eff, 0)
#
#     return effects_programming_action



def generate_extended_action(scheme, alternate, observations_contain_actions, all_actions_observed):
    # Original domain actions
    params = [par for par in scheme.parameters]

    pre = [p for p in scheme.precondition.parts]

    pre += [Literal("disabled", [], False)]

    if alternate:
        pre += [Literal("action_applied", [], False)]

    eff = scheme.effects

    # action_applied predicate
    eff += [Effect([], Truth(), Literal("action_applied", [], True))]

    # Add "step" parameters to the original actions
    # This will allow to reproduce the input traces
    if observations_contain_actions:
        params += [TypedObject("?i1", "step")]
        params += [TypedObject("?i2", "step")]

    # Add "modeProg" precondition
    pre += [Literal("modeProg", [], False)]

    # Define action validation condition
    # Example (and (plan-pickup ?i1 ?o1) (current ?i1) (inext ?i1 ?i2))
    if observations_contain_actions:
        validation_condition = [Literal("current", ["?i1"], True)]
        validation_condition += [Literal("inext", ["?i1", "?i2"], True)]

        pre += validation_condition

        plan_fluent = Literal("plan-" + scheme.name, ["?i1"] + ["?o" + str(i + 1) for i in range(scheme.num_external_parameters)], True)

        if all_actions_observed:
            pre += [plan_fluent]
            eff += [Effect([], Truth(), Literal("current", ["?i1"], False))]
            eff = eff + [Effect([], Truth(), Literal("current", ["?i2"], True))]
        else:
            eff += [Effect([], Conjunction([plan_fluent]), Literal("current", ["?i1"], False))]
            eff = eff + [Effect([], Conjunction([plan_fluent]), Literal("current", ["?i2"], True))]


    return  Scheme(scheme.name, params, len(params), Conjunction(pre), eff, None)


def generate_programmable_action(scheme, predicates, types, alternate, observations_contain_actions, all_actions_observed):
    # Original domain actions
    original_params = [par.name for par in scheme.parameters]
    params = [TypedObject("?o" + str(i + 1), scheme.parameters[i].type_name) for i in
              range(scheme.num_external_parameters)]

    pre = []

    pre += [Literal("disabled", [], False)]

    if alternate:
        pre += [Literal("action_applied", [], False)]

    eff = []

    # action_applied predicate
    eff += [Effect([], Truth(), Literal("action_applied", [], True))]

    # Add "step" parameters to the original actions
    # This will allow to reproduce the input traces
    if observations_contain_actions:
        params += [TypedObject("?i1", "step")]
        params += [TypedObject("?i2", "step")]

    # Add "modeProg" precondition
    pre += [Literal("modeProg", [], False)]
    # pre += [Literal("modeProg2", [], False)]

    # Add all possible preconditions
    var_ids = []
    for i in range(scheme.num_external_parameters):
        var_ids = var_ids + ["" + str(i + 1)]
    for p in predicates:
        for tup in itertools.product(var_ids, repeat=(len(p.arguments))):
            if is_possible_predicate_for_scheme(p, scheme, tup, types):
                vars = ["var" + str(t) for t in tup]
                condition = Conjunction(
                    [Literal("pre_" + "_".join([scheme.name] + [p.name] + vars), [], True),
                     Literal(p.name, ["?o" + str(t) for t in tup], False)])
                eff = eff + [Effect([], condition, Literal("disabled", [], True))]

    # Define action validation condition
    # Example (and (plan-pickup ?i1 ?o1) (current ?i1) (inext ?i1 ?i2))
    if observations_contain_actions:
        validation_condition = [Literal("current", ["?i1"], True)]
        validation_condition += [Literal("inext", ["?i1", "?i2"], True)]

        pre += validation_condition

        plan_fluent = Literal("plan-" + scheme.name, ["?i1"] + ["?o" + str(i + 1) for i in range(scheme.num_external_parameters)], True)

        if all_actions_observed:
            pre += [plan_fluent]
            eff += [Effect([], Truth(), Literal("current", ["?i1"], False))]
            eff = eff + [Effect([], Truth(), Literal("current", ["?i2"], True))]
        else:
            eff += [Effect([], Conjunction([plan_fluent]), Literal("current", ["?i1"], False))]
            eff = eff + [Effect([], Conjunction([plan_fluent]), Literal("current", ["?i2"], True))]


    # Add all possible effects as conditional effects
    # Example (when (and (del_ontable_put-down_var1 ))(not (ontable ?o1)))
    var_ids = []
    for i in range(scheme.num_external_parameters):
        var_ids = var_ids + ["" + str(i + 1)]
    for p in predicates:
        for tup in itertools.product(var_ids, repeat=len(p.arguments)):
            if is_possible_predicate_for_scheme(p, scheme, tup, types):
                vars = ["var" + str(t) for t in tup]
                # del effects
                condition = Conjunction(
                    [Literal("pre_" + "_".join([scheme.name] + [p.name] + vars), [], True),
                     Literal("eff_" + "_".join([scheme.name] + [p.name] + vars), [], True)])
                eff = eff + [
                    Effect([], condition, Literal(p.name, ["?o" + str(t) for t in tup], False))]
                # add effects
                condition = Conjunction(
                    [Literal("pre_" + "_".join([scheme.name] + [p.name] + vars), [], False),
                     Literal("eff_" + "_".join([scheme.name] + [p.name] + vars), [], True)])
                eff = eff + [Effect([], condition, Literal(p.name, ["?o" + str(t) for t in tup], True))]


    return  Scheme(scheme.name, params, len(params), Conjunction(pre), eff, None)

