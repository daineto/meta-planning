from .graph import transitive_closure
from .parsing_functions import parse_typed_list
from .pddl_parsing import parse_pddl_file

from ..pddl import Type, TypedObject, Literal, Requirements, Predicate, Model, Axiom, Scheme
from ..pddl import Effect, SimpleEffect, ConjunctiveEffect, CostEffect, UniversalEffect, ConditionalEffect
from ..pddl import Conjunction, Disjunction, UniversalCondition, ExistentialCondition, Truth

import sys


def set_supertypes(type_list):
    # TODO: This is a two-stage construction, which is perhaps
    # not a great idea. Might need more thought in the future.
    type_name_to_type = {}
    child_types = []
    for type in type_list:
        type.supertype_names = []
        type_name_to_type[type.name] = type
        if type.basetype_name:
            child_types.append((type.name, type.basetype_name))
    for (desc_name, anc_name) in transitive_closure(child_types):
        type_name_to_type[desc_name].supertype_names.append(anc_name)



def parse_condition(alist, type_dict, predicate_dict):
    condition = parse_condition_aux(alist, False, type_dict, predicate_dict)
    # TODO: The next line doesn't appear to do anything good,
    # since uniquify_variables doesn't modify the condition in place.
    # Conditions in actions or axioms are uniquified elsewhere, but
    # it looks like goal conditions are never uniquified at all
    # (which would be a bug).
    condition.uniquify_variables({})
    return condition


def parse_condition_aux(alist, negated, type_dict, predicate_dict):
    """Parse a PDDL condition. The condition is translated into NNF on the fly."""
    tag = alist[0]
    if tag in ("and", "or", "not", "imply"):
        args = list()
        for arg in alist[1:]:
            if arg[0] == "=":
                continue
            if arg[0] == "not" and arg[1][0] == "=":
                continue
            args.append(arg)
        if tag == "imply":
            assert len(args) == 2
        if tag == "not":
            assert len(args) == 1
            return parse_condition_aux(
                args[0], not negated, type_dict, predicate_dict)
    elif tag in ("forall", "exists"):
        parameters = parse_typed_list(alist[1])
        args = alist[2:]
        assert len(args) == 1
    else:
        return parse_literal(alist, type_dict, predicate_dict, negated=negated)

    if tag == "imply":
        parts = [parse_condition_aux(
                args[0], not negated, type_dict, predicate_dict),
                 parse_condition_aux(
                args[1], negated, type_dict, predicate_dict)]
        tag = "or"
    else:
        parts = [parse_condition_aux(part, negated, type_dict, predicate_dict) for part in args]

    if tag == "and" and not negated or tag == "or" and negated:
        return Conjunction(parts)
    elif tag == "or" and not negated or tag == "and" and negated:
        return Disjunction(parts)
    elif tag == "forall" and not negated or tag == "exists" and negated:
        return UniversalCondition(parameters, parts)
    elif tag == "exists" and not negated or tag == "forall" and negated:
        return ExistentialCondition(parameters, parts)


def parse_literal(alist, type_dict, predicate_dict, negated=False):
    if alist[0] == "not":
        assert len(alist) == 2
        alist = alist[1]
        negated = not negated

    pred_id, arity = _get_predicate_id_and_arity(
        alist[0], type_dict, predicate_dict)

    if arity != len(alist) - 1:
        raise SystemExit("predicate used with wrong arity: (%s)"
                         % " ".join(alist))

    if negated:
        return Literal(pred_id, alist[1:], False)
    else:
        return Literal(pred_id, alist[1:], True)


SEEN_WARNING_TYPE_PREDICATE_NAME_CLASH = False
def _get_predicate_id_and_arity(text, type_dict, predicate_dict):
    global SEEN_WARNING_TYPE_PREDICATE_NAME_CLASH

    the_type = type_dict.get(text)
    the_predicate = predicate_dict.get(text)

    if the_type is None and the_predicate is None:
        raise SystemExit("Undeclared predicate: %s" % text)
    elif the_predicate is not None:
        if the_type is not None and not SEEN_WARNING_TYPE_PREDICATE_NAME_CLASH:
            msg = ("Warning: name clash between type and predicate %r.\n"
                   "Interpreting as predicate in conditions.") % text
            print(msg, file=sys.stderr)
            SEEN_WARNING_TYPE_PREDICATE_NAME_CLASH = True
        return the_predicate.name, the_predicate.get_arity()
    else:
        assert the_type is not None
        return the_type.get_predicate_name(), 1


def parse_predicate(alist):
    name = alist[0]
    arguments = parse_typed_list(alist[1:], only_variables=True)
    return Predicate(name, arguments)


def add_effect(tmp_effect, result):
    """tmp_effect has the following structure:
       [ConjunctiveEffect] [UniversalEffect] [ConditionalEffect] SimpleEffect."""

    if isinstance(tmp_effect, ConjunctiveEffect):
        for effect in tmp_effect.effects:
            add_effect(effect, result)
        return
    else:
        parameters = []
        condition = Truth()
        if isinstance(tmp_effect, UniversalEffect):
            parameters = tmp_effect.parameters
            if isinstance(tmp_effect.effect, ConditionalEffect):
                condition = tmp_effect.effect.condition
                assert isinstance(tmp_effect.effect.effect, SimpleEffect)
                effect = tmp_effect.effect.effect.effect
            else:
                assert isinstance(tmp_effect.effect, SimpleEffect)
                effect = tmp_effect.effect.effect
        elif isinstance(tmp_effect, ConditionalEffect):
            condition = tmp_effect.condition
            assert isinstance(tmp_effect.effect, SimpleEffect)
            effect = tmp_effect.effect.effect
        else:
            assert isinstance(tmp_effect, SimpleEffect)
            effect = tmp_effect.effect
        # assert isinstance(effect, pddl.Literal)
        # Check for contradictory effects
        condition = condition.simplified()
        new_effect = Effect(parameters, condition, effect)
        contradiction = Effect(parameters, condition, effect.negate())

        ### REMOVED CONTRADICTION CHECK
        result.append(new_effect)

        # if not contradiction in result:
        #     result.append(new_effect)
        # else:
        #     # We use add-after-delete semantics, keep positive effect
        #     if isinstance(contradiction.literal, pddl.NegatedAtom):
        #         result.remove(contradiction)
        #         result.append(new_effect)


def parse_effect(alist, type_dict, predicate_dict):
    tag = alist[0]
    if tag == "and":
        return ConjunctiveEffect(
            [parse_effect(eff, type_dict, predicate_dict) for eff in alist[1:]])
    elif tag == "forall":
        assert len(alist) == 3
        parameters = parse_typed_list(alist[1])
        effect = parse_effect(alist[2], type_dict, predicate_dict)
        return UniversalEffect(parameters, effect)
    elif tag == "when":
        assert len(alist) == 3
        condition = parse_condition(
            alist[1], type_dict, predicate_dict)
        effect = parse_effect(alist[2], type_dict, predicate_dict)
        return ConditionalEffect(condition, effect)
    else:
        # We pass in {} instead of type_dict here because types must
        # be static predicates, so cannot be the target of an effect.
        return SimpleEffect(parse_literal(alist, {}, predicate_dict))


def parse_effects(alist, result, type_dict, predicate_dict):
    """Parse a PDDL effect (any combination of simple, conjunctive, conditional, and universal)."""
    tmp_effect = parse_effect(alist, type_dict, predicate_dict)
    normalized = tmp_effect.normalize()
    cost_eff, rest_effect = normalized.extract_cost()
    add_effect(rest_effect, result)
    if cost_eff:
        return cost_eff.effect
    else:
        return None


def parse_action(alist, type_dict, predicate_dict):
    iterator = iter(alist)
    action_tag = next(iterator)
    assert action_tag == ":action"
    name = next(iterator)
    parameters_tag_opt = next(iterator)
    if parameters_tag_opt == ":parameters":
        parameters = parse_typed_list(next(iterator),
                                      only_variables=True)
        precondition_tag_opt = next(iterator)
    else:
        parameters = []
        precondition_tag_opt = parameters_tag_opt
    if precondition_tag_opt == ":precondition":
        precondition_list = next(iterator)
        if not precondition_list:
            # Note that :precondition () is allowed in PDDL.
            precondition = Conjunction([])
        else:
            precondition = parse_condition(
                precondition_list, type_dict, predicate_dict)

            if isinstance(precondition, Literal):
                precondition = Conjunction([precondition])

            # precondition = precondition.simplified()
        effect_tag = next(iterator)
    else:
        precondition = Conjunction([])
        effect_tag = precondition_tag_opt
    assert effect_tag == ":effect"
    effect_list = next(iterator)
    eff = []
    if effect_list:
        try:
            cost = parse_effects(
                effect_list, eff, type_dict, predicate_dict)
        except ValueError as e:
            raise SystemExit("Error in Action %s\nReason: %s." % (name, e))
    for rest in iterator:
        assert False, rest
    # if eff:
    #     return pddl.Action(name, parameters, len(parameters),
    #                        precondition, eff, cost)
    # else:
    #     return None

    return Scheme(name, parameters, len(parameters),
                           precondition, eff, None)


def parse_axiom(alist, type_dict, predicate_dict):
    assert len(alist) == 3
    assert alist[0] == ":derived"
    predicate = parse_predicate(alist[1])
    condition = parse_condition(
        alist[2], type_dict, predicate_dict)
    return Axiom(predicate.name, predicate.arguments,
                      len(predicate.arguments), condition)



def parse_model(model_file):
    model_pddl = parse_pddl_file('model', model_file)

    iterator = iter(model_pddl)

    define_tag = next(iterator)
    assert define_tag == "define"
    domain_line = next(iterator)
    if domain_line[0] == "domain":
        assert domain_line[0] == "domain" and len(domain_line) == 2
    else:
        domain_line = ["domain", "unknown"]

    domain_name = domain_line[1]

    ## We allow an arbitrary order of the requirement, types, constants,
    ## predicates and functions specification. The PDDL BNF is more strict on
    ## this, so we print a warning if it is violated.
    requirements = Requirements([":strips"])
    the_types = [Type("object")]
    constants, the_predicates, the_functions = [], [], []
    correct_order = [":requirements", ":types", ":constants", ":predicates",
                     ":functions"]
    seen_fields = []
    first_action = None
    for opt in iterator:
        field = opt[0]
        if field not in correct_order:
            first_action = opt
            break
        if field in seen_fields:
            raise SystemExit("Error in domain specification\n" +
                             "Reason: two '%s' specifications." % field)
        if (seen_fields and
            correct_order.index(seen_fields[-1]) > correct_order.index(field)):
            msg = "\nWarning: %s specification not allowed here (cf. PDDL BNF)" % field
            print(msg, file=sys.stderr)
        seen_fields.append(field)
        if field == ":requirements":
            requirements = Requirements(opt[1:])
        elif field == ":types":
            the_types.extend(parse_typed_list(
                    opt[1:], constructor=Type))
        elif field == ":constants":
            constants = parse_typed_list(opt[1:])
        elif field == ":predicates":
            the_predicates = [parse_predicate(entry)
                              for entry in opt[1:]]
            # the_predicates += [pddl.Predicate("=",
            #                      [pddl.TypedObject("?x", "object"),
            #                       pddl.TypedObject("?y", "object")])]
    set_supertypes(the_types)

    type_dict = dict((type.name, type) for type in the_types)

    predicate_dict = dict((pred.name, pred) for pred in the_predicates)

    entries = []
    if first_action is not None:
        entries.append(first_action)
    entries.extend(iterator)

    the_axioms = []
    the_actions = []
    for entry in entries:
        if entry[0] == ":derived":
            axiom = parse_axiom(entry, type_dict, predicate_dict)
            the_axioms.append(axiom)
        else:
            action = parse_action(entry, type_dict, predicate_dict)
            if action is not None:
                the_actions.append(action)

    return Model(domain_name,requirements,the_types,the_predicates,the_functions,the_actions,the_axioms)