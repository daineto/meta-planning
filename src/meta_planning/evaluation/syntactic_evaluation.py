
import  sys
import numpy as np
import itertools

from ..pddl import Literal
from .scores import Score

class bcolors:
    MISSING = '\033[94m'
    EXTRA = '\033[91m'
    ENDC = '\033[0m'

    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Matching(object):
    def __init__(self, original_scheme, matched_scheme, parameters_ordering):
        self.original_scheme = original_scheme
        self.matched_scheme = matched_scheme
        self.parameters_ordering = parameters_ordering

    def __repr__(self):
        return "Matching(original_scheme: %r, matched_scheme: %r, parameters_ordering: %r" % (self.original_scheme, self.matched_scheme, self.parameters_ordering)

    def __str__(self):
        return "Matching(%s, %s, %r)" % (self.original_scheme.name, self.matched_scheme.name, self.parameters_ordering)



class SynEvaluator(object):
    def __init__(self, learned_model, reference_model, reformulation=True, initial_model=None):
        self.learned_model = learned_model
        self.reference_model = reference_model
        self.reformulation = reformulation
        self.initial_model = initial_model

    def evaluate(self):
        schemata_matchings = self.__generate_matchings()

        best_f1 = -1
        best_score = None
        for schemata_matching in schemata_matchings:
            score = self.__evaluate_matchings(schemata_matching)
            if score.f1_score > best_f1:
                best_f1 = score.f1_score
                best_score = score


        self.__compare(best_score.matchings)

        print(best_score)


    def __compare(self, matchings):

        for matching in matchings:
            reference = matching.original_scheme.reform(matching.parameters_ordering)
            evaluated = matching.matched_scheme

            ref_preconditions = set(reference.precondition.parts)
            ref_effects = set(reference.effects)

            eva_preconditions = set(evaluated.precondition.parts)
            eva_effects = set(evaluated.effects)


            print("(:action %s" % evaluated.name)
            print("\t:parameters (%s)" % (' '.join(map(str, evaluated.parameters))))
            print("\t:precondition (and")
            for pre in eva_preconditions.intersection(ref_preconditions):
                print("\t\t%s" % pre)
            for pre in eva_preconditions.difference(ref_preconditions):
                print(bcolors.EXTRA + "\t\t%s" % pre + bcolors.ENDC)
            for pre in ref_preconditions.difference(eva_preconditions):
                print(bcolors.MISSING + "\t\t%s" % pre + bcolors.ENDC)

            print("\t)")
            print("\t:effects (and")
            for eff in eva_effects.intersection(ref_effects):
                print("\t\t%s" % eff)
            for eff in eva_effects.difference(ref_effects):
                print(bcolors.EXTRA + "\t\t%s" % eff + bcolors.ENDC)
            for eff in ref_effects.difference(eva_effects):
                print(bcolors.MISSING + "\t\t%s" % eff + bcolors.ENDC)

            print("\t)")
            print(")")
            print()





    def __evaluate_matchings(self, matchings):
        ref_pres = set()
        eva_pres = set()
        ref_adds = set()
        eva_adds = set()
        ref_dels = set()
        eva_dels = set()

        for matching in matchings:
            evaluated_scheme = matching.original_scheme.name

            ref_pres.update((evaluated_scheme, literal) for literal in matching.original_scheme.precondition.parts)

            for effect in matching.original_scheme.effects:
                if effect.literal.valuation:
                    ref_adds.add((evaluated_scheme, effect.literal))
                else:
                    ref_dels.add((evaluated_scheme, effect.literal))


            reformulated_scheme = matching.matched_scheme.reform(matching.parameters_ordering)

            eva_pres.update(
                (evaluated_scheme, literal) for literal in reformulated_scheme.precondition.parts)

            for effect in reformulated_scheme.effects:
                if effect.literal.valuation:
                    eva_adds.add((evaluated_scheme, effect.literal))
                else:
                    eva_dels.add((evaluated_scheme, effect.literal))


        pres_deletions = len(eva_pres) - len(ref_pres.intersection(eva_pres))
        adds_deletions = len(eva_adds) - len(ref_adds.intersection(eva_adds))
        dels_deletions = len(eva_dels) - len(ref_dels.intersection(eva_dels))

        # Compute precision and recall
        precision_pres = np.nan_to_num(np.float64(len(eva_pres) - pres_deletions) / len(eva_pres))
        recall_pres = np.nan_to_num(np.float64(len(eva_pres) - pres_deletions) / len(ref_pres))
        precision_adds = np.nan_to_num(np.float64(len(eva_adds) - adds_deletions) / len(eva_adds))
        recall_adds = np.nan_to_num(np.float64(len(eva_adds) - adds_deletions) / len(ref_adds))
        precision_dels = np.nan_to_num(np.float64(len(eva_dels) - dels_deletions) / len(eva_dels))
        recall_dels = np.nan_to_num(np.float64(len(eva_dels) - dels_deletions) / len(ref_dels))


        # Micro average
        avg_precision = np.nan_to_num(np.float64(
            len(eva_pres) + len(eva_adds) + len(eva_dels) - pres_deletions - adds_deletions - dels_deletions) / (
                                                  len(eva_pres) + len(eva_adds) + len(eva_dels)))
        avg_recall = np.nan_to_num(
            np.float64(
                len(eva_pres) + len(eva_adds) + len(eva_dels) - pres_deletions - adds_deletions - dels_deletions) / (
                    len(ref_pres) + len(ref_adds) + len(ref_dels)))

        if avg_precision + avg_recall > 0:
            f1_score = 2 * (avg_precision * avg_recall) / (avg_precision + avg_recall)
        else:
            f1_score = 0.0

        return Score(f1_score, precision_pres, recall_pres, precision_adds, recall_adds, precision_dels, recall_dels,
                     avg_precision, avg_recall, matchings)


    def __generate_matchings(self):
        reference_schemata = self.reference_model.schemata
        learned_schemata = self.learned_model.schemata


        matchings_by_scheme = {s.name:[] for s in reference_schemata}
        for r_scheme in reference_schemata:
            reference_parameters = [p.type_name for p in r_scheme.parameters]
            for l_scheme in learned_schemata:
                learned_parameters = [p.type_name for p in l_scheme.parameters]

                if sorted(reference_parameters) == sorted(learned_parameters):
                    orderings = list(itertools.permutations(range(len(reference_parameters))))
                    valid_orderings = [ordering for ordering in orderings if self.__is_valid_ordering(ordering, reference_parameters, learned_parameters)]
                    matchings_by_scheme[r_scheme.name] += [Matching(r_scheme, l_scheme, ordering) for ordering in valid_orderings]

        all_schemata_matchings = list(itertools.product(*[v for k,v in matchings_by_scheme.items()]))
        valid_schemata_matchings = [m for m in all_schemata_matchings if set([m[i].original_scheme.name for i in range(len(m))]) == set([m[i].matched_scheme.name for i in range(len(m))])]

        return valid_schemata_matchings


    def __is_valid_ordering(self, ordering, reference_parameters, learned_parameters):
        return all([reference_parameters[i] == learned_parameters[ordering[i]] for i in range(len(ordering))])