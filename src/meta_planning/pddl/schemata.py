import copy
from random import random
from . import conditions
from .effects import Effect
from .pddl_types import TypedObject



class Scheme(object):
    def __init__(self, name, parameters, num_external_parameters,
                 precondition, effects, cost):
        assert 0 <= num_external_parameters <= len(parameters)
        self.name = name
        self.parameters = parameters
        # num_external_parameters denotes how many of the parameters
        # are "external", i.e., should be part of the grounded action
        # name. Usually all parameters are external, but "invisible"
        # parameters can be created when compiling away existential
        # quantifiers in conditions.
        self.num_external_parameters = num_external_parameters
        self.precondition = precondition
        self.effects = effects
        self.cost = cost
        # self.uniquify_variables() # TODO: uniquify variables in cost?

    def __repr__(self):
        return "Scheme(name: %r, parameters: %r, precondition: %r, effects: %r" % (self.name, self.parameters, self.precondition, self.effects)

    def __str__(self):
        scheme_str = "(:action %s\n" % (self.name)
        scheme_str += "\t:parameters (%s)\n" % (' '.join(map(str, self.parameters)))
        scheme_str += "\t:precondition %s\n" % (self.precondition)
        scheme_str += "\t:effect (and \n"
        for e in self.effects:
            scheme_str += "\t\t%s\n" % (e)
        if self.cost is not None:
            scheme_str += "\t\t%s\n" % (self.cost)
        scheme_str += "\t)\n)"
        return scheme_str


    def propositional_preconditions(self):

        propositions = []

        vars = {self.parameters[i].name: "var" + str(i + 1) for i in range(len(self.parameters))}

        preconditions = self.precondition.parts
        for pre in preconditions:
            pre_vars = [vars[arg] for arg in pre.args]
            propositions += [conditions.Literal("pre_" + "_".join([self.name] + [pre.predicate] + pre_vars), [], True)]

        return propositions


    def propositional_effects(self):

        propositions = []

        vars = {self.parameters[i].name: "var" + str(i + 1) for i in range(len(self.parameters))}

        for eff in self.effects:
            literal = eff.literal
            eff_vars = [vars[arg] for arg in literal.args]
            propositions += [
                conditions.Literal("eff_" + "_".join([self.name] + [literal.predicate] + eff_vars), [], True)]

        return propositions


    def propositional_encoding(self):

        return self.propositional_preconditions() + self.propositional_effects()


    def observe(self, precondition_observability=1, effect_observability=1):

        preconditions = self.precondition.parts

        pre = [p for p in preconditions if random() <= precondition_observability]

        eff = [e for e in self.effects if random() <= effect_observability]

        return Scheme(self.name, self.parameters, self.num_external_parameters, conditions.Conjunction(pre), eff, self.cost)


    def reform(self, ordering):
        new_pres = []
        new_effs = []
        new_params = [self.parameters[i] for i in ordering]

        parameter_names = [p.name for p in self.parameters]

        for pre in self.precondition.parts:
            args_indices = [parameter_names.index(arg) for arg in pre.args]

            new_args = [parameter_names[i] for i in args_indices]
            new_pres += [conditions.Literal(pre.predicate, new_args, pre.valuation)]

        for eff in self.effects:
            args_indices = [parameter_names.index(arg) for arg in eff.literal.args]

            new_args = [parameter_names[i] for i in args_indices]
            new_effs += [Effect(eff.parameters, eff.condition, conditions.Literal(eff.literal.predicate, new_args, eff.literal.valuation))]

        return Scheme(self.name, new_params, self.num_external_parameters, conditions.Conjunction(new_pres), new_effs, self.cost)


    def instantiate(self, objects):
        new_pres = []
        new_effs = []

        objects = [o for o in objects if o != ""]

        new_params = [TypedObject(objects[i], self.parameters[i].type_name) for i in range(len(self.parameters))]

        parameter_names = [p.name for p in self.parameters]

        for pre in self.precondition.parts:
            args_indices = [parameter_names.index(arg) for arg in pre.args]

            new_args = [objects[i] for i in args_indices]
            new_pres += [conditions.Literal(pre.predicate, new_args, pre.valuation)]

        for eff in self.effects:
            if not isinstance(eff.literal, conditions.Literal):
                continue
            args_indices = [parameter_names.index(arg) for arg in eff.literal.args]

            new_args = [objects[i] for i in args_indices]
            new_effs += [Effect(eff.parameters, eff.condition, conditions.Literal(eff.literal.predicate, new_args, eff.literal.valuation))]
            pass

        return Scheme(self.name, new_params, self.num_external_parameters, conditions.Conjunction(new_pres), new_effs, self.cost)


    def uniquify_variables(self):
        self.type_map = dict([(par.name, par.type_name)
                              for par in self.parameters])
        self.precondition = self.precondition.uniquify_variables(self.type_map)
        for effect in self.effects:
            effect.uniquify_variables(self.type_map)

    def untyped(self):
        # We do not actually remove the types from the parameter lists,
        # just additionally incorporate them into the conditions.
        # Maybe not very nice.
        result = copy.copy(self)
        parameter_atoms = [par.to_untyped_strips() for par in self.parameters]
        new_precondition = self.precondition.untyped()
        result.precondition = conditions.Conjunction(parameter_atoms + [new_precondition])
        result.effects = [eff.untyped() for eff in self.effects]
        return result


class Action(object):

    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments

    def __str__(self):
        action_str = "(%s %s)" % (self.name, " ".join(self.arguments))
        return action_str

    def __eq__(self, other):
        if self.name != other.name:
            return False
        else:
            return all([self.arguments[i] == other.arguments[i] for i in range(len(self.arguments))])


