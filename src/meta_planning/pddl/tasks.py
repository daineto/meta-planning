
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
                 schemata, axioms):
        self.domain_name = domain_name
        self.requirements = requirements
        self.types = types
        self.predicates = predicates
        self.functions = functions
        self.schemata = schemata
        self.axioms = axioms
        self.axiom_counter = 0


    def __str__(self):
        return self.pddl_encoding()


    def pddl_encoding(self):
        model_str = ""
        model_str += "(define (domain %s)\n" % (self.domain_name)
        model_str += "(:requirements %s)\n" % (self.requirements)
        model_str += "(:predicates\n"
        for p in self.predicates:
            model_str += "\t%s\n" % (p)
        model_str += ")\n\n"
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


class Problem(object):
    def __init__(self, problem_name, domain_name, objects, init, goal):
        self.problem_name = problem_name
        self.domain_name = domain_name
        self.objects = objects
        self.init = init
        self.goal = goal


    def __str__(self):

        problem_str = ""
        problem_str += "(define (problem %s)\n" % self.problem_name
        problem_str += "\t(:domain %s)\n" % self.domain_name
        problem_str += "\t(:objects %s)\n" % " ".join(map(str, self.objects))
        problem_str += "\t(:init %s)\n" % " ".join(map(str, self.init))
        problem_str += "\t(:goal %s)\n)" % self.goal

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
