from .pddl_parsing import parse_pddl_file
from .parsing_functions import parse_typed_list, parse_condition, parse_assignment, parse_state

from ..pddl import Problem
from ..pddl import Requirements, Literal
from ..pddl import NumericConstant

from ..functions import generate_all_literals

def check_atom_consistency(literal, same_truth_value, other_truth_value, atom_is_true=True):
    if literal in other_truth_value:
        raise SystemExit("Error in initial state specification\n" +
                         "Reason: %s is true and false." %  literal)
    if literal in same_truth_value:
        if not atom_is_true:
            literal = literal.negate()
        print("Warning: %s is specified twice in initial state specification" % literal)


def parse_problem(problem_file, model):
    problem_pddl = parse_pddl_file('problem', problem_file)

    type_dict = dict((type.name, type) for type in model.types)
    predicate_dict = dict((pred.name, pred) for pred in model.predicates)


    iterator = iter(problem_pddl)

    define_tag = next(iterator)
    assert define_tag == "define"
    problem_line = next(iterator)
    assert problem_line[0] == "problem" and len(problem_line) == 2
    problem_name = problem_line[1]
    domain_line = next(iterator)
    assert domain_line[0] == ":domain" and len(domain_line) == 2
    domain_name = domain_line[1]

    requirements_opt = next(iterator)
    if requirements_opt[0] == ":requirements":
        requirements = requirements_opt[1:]
        objects_opt = next(iterator)
    else:
        requirements = []
        objects_opt = requirements_opt
    requirements = Requirements(requirements)

    if objects_opt[0] == ":objects":
        objects = parse_typed_list(objects_opt[1:])
        init = next(iterator)
    else:
        objects = []
        init = objects_opt


    all_literals = set(generate_all_literals(model.predicates, objects, model.types))


    assert init[0] == ":init"
    initial = parse_state(init[1:], all_literals)
    # initial = initial.to_close_world()


    goal = next(iterator)
    assert goal[0] == ":goal" and len(goal) == 2
    goal = parse_condition(goal[1], type_dict, predicate_dict)

    use_metric = False
    for entry in iterator:
        if entry[0] == ":metric":
            if entry[1]=="minimize" and entry[2][0] == "total-cost":
                use_metric = True
            else:
                assert False, "Unknown metric."

    for entry in iterator:
        assert False, entry

    return Problem(problem_name, domain_name, objects, initial, goal, use_metric=use_metric)