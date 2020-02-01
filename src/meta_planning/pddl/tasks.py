import numpy as np
from _collections import defaultdict


# def get_all_subtypes(the_type, all_types):
#    subtypes=[the_type]
#    for a_type in all_types:
#        if a_type.basetype_name == the_type:
#            subtypes.append(str(a_type.name))
#    return subtypes
#
# def generate_all_literals(predicates, objects, all_types, valuation=True):
#
#     all_literals = []
#     for p in predicates:
#         types_for_predicate = [get_all_subtypes(arg.type_name, all_types) for arg in p.arguments]
#         objects_for_predicate = [[o for o in objects if o.type_name in types] for types in types_for_predicate]
#
#         combinations = list(itertools.product(*objects_for_predicate))
#         for comb in combinations:
#             all_literals += [Literal(p.name, [o.name for o in comb], valuation)]
#
#     return all_literals

class Requirements(object):
    def __init__(self, requirements):
        self.requirements = requirements
        for req in requirements:
            assert req in (
              ":strips", ":adl", ":typing", ":negation", ":equality",
              ":negative-preconditions", ":disjunctive-preconditions",
              ":existential-preconditions", ":universal-preconditions",
              ":quantified-preconditions", ":conditional-effects",
              ":derived-predicates", ":action-costs"), req
    def __str__(self):
        return ", ".join(self.requirements)

    def __repr__(self):
        return "Requirements(requirements: %r)" % self.requirements


class Model(object):

    def __init__(self, domain_name, requirements,
                 types, predicates, functions,
                 schemata, axioms, use_cost=False):
        self.domain_name = domain_name
        self.requirements = requirements
        self.types = types
        self.predicates = predicates
        self.functions = functions
        self.schemata = schemata
        self.axioms = axioms
        self.axiom_counter = 0
        self.use_cost = use_cost


    def __str__(self):
        return self.pddl_encoding()


    def pddl_encoding(self):
        model_str = ""
        model_str += "(define (domain %s)\n" % (self.domain_name)
        model_str += "(:requirements %s)\n" % (self.requirements)
        model_str += "(:types %s)\n" % (" ".join(map(str,self.types)))
        model_str += "(:predicates\n"
        for p in self.predicates:
            model_str += "\t%s\n" % (p)
        model_str += ")\n\n"
        if self.use_cost:
            model_str += "(:functions (total-cost))\n\n"
        model_str += "%s" % ("\n\n".join(map(str, self.schemata)))
        model_str += ")"

        return model_str


    def propositional_encoding(self):
        propositions = []
        for scheme in self.schemata:
            propositions += scheme.propositional_encoding()

        return propositions

    def to_file(self, filename):
        with open(filename, 'w') as f:
            f.write(str(self))


    def observe(self, precondition_observability=0, effect_observability=0):
        observed_schemata = [s.observe(precondition_observability=precondition_observability, effect_observability=effect_observability) for s in self.schemata]

        return Model(self.domain_name, self.requirements, self.types, self.predicates, self.functions, observed_schemata, self.axioms)



class SensorModel(object):
    def __init__(self, mapping, probabilistic=False):

        self.probabilistic = probabilistic
        self.s_to_o = mapping # state to observation
        self.o_to_s = defaultdict(dict)

        for key, val in self.s_to_o.items():
            for subkey, subval in val.items():
                self.o_to_s[subkey][key] = subval


    def __initialize(self, initial_probabilities):
        # literals = generate_all_literals(self.model.predicates, self.objects, self.model.types)
        return {l:initial_probabilities for l in self.s_to_o.keys()}

    # def set_observability(self, predicates, objects, observability):
    #     literals = generate_all_literals(predicates, self.objects, self.model.types)
    #     o_names = set([o.name for o in objects])
    #     for l in literals:
    #         if len(l.args) == 0 or len(o_names.intersection(set(l.args))) != 0:
    #             self.observability_table[l] = observability

    def set_observability(self, mapping, observability):
        for k,v in mapping.items():
            self.s_to_o[k] = v

            self.observability_table[k] = observability


    def observe(self, literal):

        if literal in self.s_to_o.keys():
            observation = np.random.choice(list(self.s_to_o[literal].keys()), 1, p=list(self.s_to_o[literal].values()))
            return observation[0]
        else:
            return None


    def get_observable_fluents(self):
        return set(self.o_to_s.keys())

    def get_observable_variables(self, literal):
        return self.s_to_o[literal]

    def get_state_variables(self, observable):
        return self.o_to_s[observable]






class Problem(object):
    def __init__(self, problem_name, domain_name, objects, init, goal, use_metric=False):
        self.problem_name = problem_name
        self.domain_name = domain_name
        self.objects = objects
        self.init = init
        self.goal = goal
        self.use_metric = use_metric


    def __str__(self):

        problem_str = ""
        problem_str += "(define (problem %s)\n" % self.problem_name
        problem_str += "\t(:domain %s)\n" % self.domain_name
        problem_str += "\t(:objects %s)\n" % " ".join(map(str, self.objects))
        problem_str += "\t(:init \n"
        problem_str += "\t%s\n" % " ".join(map(str, self.init.to_close_world().literals))
        if self.use_metric:
            problem_str += "(= (total-cost) 0)\n"
        problem_str += "\t)\n"
        problem_str += "\t(:goal %s)\n" % self.goal
        if self.use_metric:
            problem_str += "(:metric minimize (total-cost))\n"
        problem_str += ")"


        return problem_str


    def to_file(self, filename):
        with open(filename, 'w') as f:
            f.write(str(self))



class Plan(object):
    def __init__(self, actions):
        self.actions = actions

    def __str__(self):
        plan_str = ""
        for i in range(len(self.actions)):
            plan_str += "%s : %s\n" % (str(i), self.actions[i])

        return plan_str

    def to_file(self, filename):
        with open(filename, 'w') as f:
            f.write(str(self))

    def clean(self, name):
        new_actions = []
        for a in self.actions:
            if name in a.name:
                continue
            else:
                new_actions.append(a)

        return Plan(new_actions)

    def diverseness(self, other):
        # count = 0
        # for i in range(len(self.actions)):
        #     if self.actions[i] != other.actions[i]:
        #         count += 1

        # return count / len(self.actions)


        ### Bag difference version
        self_minus_other = len([item for item in self.actions if item not in other.actions])
        other_minus_self = len([item for item in other.actions if item not in self.actions])

        sum_plans = len(self.actions) + len(other.actions)

        return self_minus_other/sum_plans + other_minus_self/sum_plans




