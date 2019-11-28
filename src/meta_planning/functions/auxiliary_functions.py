from ..pddl import Literal

import itertools


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


def generate_all_literals(predicates, objects, all_types, valuation=True):

    all_literals = []
    for p in predicates:
        types_for_predicate = [get_all_subtypes(arg.type_name, all_types) for arg in p.arguments]
        objects_for_predicate = [[o for o in objects if o.type_name in types] for types in types_for_predicate]

        combinations = list(itertools.product(*objects_for_predicate))
        for comb in combinations:
            all_literals += [Literal(p.name, [o.name for o in comb], valuation)]

    return all_literals

def get_matching_literals(F, predicates, objects):
    matching_literals = []

    p_names = set([p.name for p in predicates])
    o_names = set([o.name for o in objects])
    for l in [f for f in F if f.predicate in p_names]:
        if len(l.args) == 0 or len(o_names.intersection(set(l.args))) != 0:
            matching_literals.append(l)

    return matching_literals


# def set_observability(self, predicates, objects, observability):
#     literals = generate_all_literals(predicates, self.objects, self.model.types)
#     o_names = set([o.name for o in objects])
#     for l in literals:
#         if len(l.args) == 0 or len(o_names.intersection(set(l.args))) != 0:
#             self.observability_table[l] = observability