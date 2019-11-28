from ..pddl import TypedObject, Literal
from ..pddl import Conjunction, Disjunction, UniversalCondition, ExistentialCondition, Truth
from ..pddl import PrimitiveNumericExpression, NumericConstant, Assign, Increase

from ..observations import State

import copy
import sys

def parse_typed_list(alist, only_variables=False,
                     constructor=TypedObject,
                     default_type="object"):
    aux = copy.deepcopy(alist)
    alist = []
    for item in aux:
        if item.startswith("-") and not item == "-":
            alist.append("-")
            alist.append(item[1:])
        else:
            alist.append(item)
    result = []
    while alist:
        try:
            separator_position = alist.index("-")
            pass
        except ValueError:
            items = alist
            _type = default_type
            alist = []
        else:
            items = alist[:separator_position]
            _type = alist[separator_position + 1]
            alist = alist[separator_position + 2:]
        for item in items:
            assert not only_variables or item.startswith("?"), \
                "Expected item to be a variable: %s in (%s)" % (
                    item, " ".join(items))
            entry = constructor(item, _type)
            result.append(entry)
    return result


def parse_expression(exp):
    if isinstance(exp, list):
        functionsymbol = exp[0]
        return PrimitiveNumericExpression(functionsymbol, exp[1:])
    elif exp.replace(".", "").isdigit():
        return NumericConstant(float(exp))
    elif exp[0] == "-":
        raise ValueError("Negative numbers are not supported")
    else:
        return PrimitiveNumericExpression(exp, [])


def parse_assignment(alist):
    assert len(alist) == 3
    op = alist[0]
    head = parse_expression(alist[1])
    exp = parse_expression(alist[2])
    if op == "=":
        return Assign(head, exp)
    elif op == "increase":
        return Increase(head, exp)
    else:
        assert False, "Assignment operator not supported."


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
    assignments = []

    initial_assignments = dict()

    for fact in new_state:
        if fact[0] == "=":
            try:
                assignment = parse_assignment(fact)
            except ValueError as e:
                raise SystemExit("Error in initial state specification\n" +
                                 "Reason: %s." %  e)
            if not isinstance(assignment.expression,
                              NumericConstant):
                raise SystemExit("Illegal assignment in initial state " +
                    "specification:\n%s" % assignment)
            if assignment.fluent in initial_assignments:
                prev = initial_assignments[assignment.fluent]
                if assignment.expression == prev.expression:
                    print("Warning: %s is specified twice" % assignment,
                          "in initial state specification")
                else:
                    raise SystemExit("Error in initial state specification\n" +
                                     "Reason: conflicting assignment for " +
                                     "%s." %  assignment.fluent)
            else:
                initial_assignments[assignment.fluent] = assignment
                assignments.append(assignment)
        elif fact[0] == "not":
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

    return State(sorted(state), None, assignments=sorted(assignments))