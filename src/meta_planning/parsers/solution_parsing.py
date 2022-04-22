from ..pddl import Scheme, Effect, Literal, Truth, Conjunction, Plan, Action
from ..compilation import FoundSolution, NoSolution
from ..compilation import Explanation
from ..observations import State, Trajectory

import copy

def build_model(pres, effs, initial_model):

    learned_model = copy.deepcopy(initial_model)
    learned_model.schemata = []

    for scheme in initial_model.schemata:
        name = scheme.name

        pre = []
        eff = []

        for p in pres[name]:
            p = list(p)
            pre += [Literal(p[0], [scheme.parameters[int(arg.replace("var", "")) - 1].name for arg in p[1:]], True)]

        for e in effs[name]:
            if e in pres[name]:
                valuation = False
            else:
                valuation = True

            eff += [Effect([], Truth(), Literal(e[0],[scheme.parameters[int(arg.replace("var", "")) - 1].name for arg in e[1:]], valuation))]

        learned_model.schemata += [Scheme(scheme.name, scheme.parameters, len(scheme.parameters), Conjunction(pre), eff, None)]


    return learned_model


def build_explanations(actions, cuts, observations, learned_model):

    explanations = []
    effects_dict = {scheme.name: scheme.effects for scheme in learned_model.schemata}
    parameters_dict = {scheme.name: scheme.parameters for scheme in learned_model.schemata}

    for i in range(len(cuts) - 1):
        init = set(observations[i].states[0].literals)
        lifted_inferred_trajectory = [init]
        subplan = actions[cuts[i]:cuts[i + 1]]

        for a in subplan:
            pre_state = []

            for literal in lifted_inferred_trajectory[-1]:
                if set(literal.args).issubset(set(a.arguments)):
                    args_indices = []

                    for arg in literal.args:
                        indices = [parameters_dict[a.name][j].name for j in range(len(a.arguments)) if a.arguments[j] == arg]
                        args_indices.append(indices)

                    for tup in itertools.product(*args_indices):
                        pre_state.append(Literal(literal.predicate, list(tup), literal.valuation))

            pre_state = State(pre_state, a)
            effects = copy.deepcopy(effects_dict[a.name])

            for j in range(len(a.arguments)):
                arg = a.arguments[j]
                par = parameters_dict[a.name][j].name

                for effect in effects:
                    effect.literal = effect.literal.rename_variables({x: arg for x in effect.literal.args if x == par})

            new_state = lifted_inferred_trajectory[-1]
            new_state = new_state.difference({effect.literal.flip() for effect in effects})
            new_state = new_state.union({effect.literal for effect in effects})
            lifted_inferred_trajectory[-1] = pre_state
            lifted_inferred_trajectory.append(new_state)

        lifted_inferred_trajectory[-1] = State(list(lifted_inferred_trajectory[-1]), None)
        lifted_inferred_trajectory = Trajectory(observations[i].objects, lifted_inferred_trajectory)
        explanations += [Explanation(Plan(subplan), observations[i], lifted_inferred_trajectory)]

    return explanations


def parse_plan(plan_file):

    actions = []

    f = open(plan_file, "r")
    lines = f.readlines()
    f.close()

    for line in lines:

        if ";" in line:
            continue
        line = line.lower()
        splitted_line = line.split(":")
        if len(splitted_line) == 2:
            raw_action = splitted_line[1]
        else:
            raw_action = splitted_line[0]

        cleaned_action = raw_action.strip().replace("(","").replace(")","").split(" ")
        actions += [Action(cleaned_action[0], cleaned_action[1:])]

    return Plan(actions)



def parse_solution(solution_file, initial_model, observations, known_model, lifted_inferred_trajectories= None):

    observations_contain_actions = any([o.has_actions() for o in observations])

    pres = dict()
    effs = dict()


    for scheme in initial_model.schemata:
        pres[scheme.name] = set()
        effs[scheme.name] = set()


    for proposition in known_model:
        pre_eff = proposition.predicate.split("_")
        name = pre_eff[1]
        if pre_eff[0] == "pre":
            pres[name].add(tuple(pre_eff[2:]))
        elif pre_eff[0] == "eff":
            effs[name].add(tuple(pre_eff[2:]))

    edition_distance = 0
    solution_plan = ""
    explanations = []

    regular_actions = []
    num_validate_actions = 0
    current_observation = 0
    cuts = [0]


    try:
        plan = parse_plan(solution_file)
    except:
        return NoSolution()


    for action in plan.actions:

        splitted_action = action.name.split("_")
        action_type = splitted_action[0]

        if action_type == "insert":
            action_name = splitted_action[2]
            pre_eff = tuple(splitted_action[3:])

            if splitted_action[1] == 'pre':
                pres[action_name].add(pre_eff)
            elif splitted_action[1] == 'eff':
                effs[action_name].add(pre_eff)

            edition_distance += 1

        elif action_type == "delete":
            action_name = splitted_action[2]
            pre_eff = tuple(splitted_action[3:])

            if splitted_action[1] == 'pre':
                pres[action_name].remove(pre_eff)
            elif splitted_action[1] == 'eff':
                effs[action_name].remove(pre_eff)

            edition_distance += 1

        elif action_type == "validate":
            num_validate_actions += 1
            if num_validate_actions == observations[current_observation].number_of_states:
                cuts += [len(regular_actions)]
                num_validate_actions = 1
                current_observation += 1

        else:
            if observations_contain_actions:
                regular_action = Action(action.name, action.arguments[:-2])
            else:
                regular_action = action
            regular_actions += [regular_action]

    learned_model = build_model(pres, effs, initial_model)

    explanations += build_explanations(regular_actions, cuts, observations, learned_model)
    
    if lifted_inferred_trajectories is None:
        lifted_inferred_trajectories = []

    lifted_inferred_trajectories = lifted_inferred_trajectories + [explanation.lifted_inferred_trajectory for explanation in explanations]
    pre_states = {}

    for lifted_inferred_trajectory in lifted_inferred_trajectories:
        for pre_state in lifted_inferred_trajectory.states:
            action = pre_state.next_action

            if action is not None:
                pre_states_list = pre_states.get(action.name, [])
                pre_states_list.append(set(pre_state.literals))
                pre_states[action.name] = pre_states_list

    action_names = [a.name for a in learned_model.schemata]

    for k, v in pre_states.items():
        new_preconditions = v[0]

        for pre_state in v[1:]:
            new_preconditions = new_preconditions.intersection(pre_state)

        if len(new_preconditions) > 0:
            new_preconditions = sorted(new_preconditions)
            indexa = action_names.index(k)
            learned_pres = list(learned_model.schemata[indexa].precondition.parts)
            new_preconditions = [pre for pre in new_preconditions if pre not in learned_pres]

            if len(new_preconditions) > 0:
                learned_model.schemata[indexa].precondition = Conjunction(learned_pres + new_preconditions)
                edition_distance += len(new_preconditions)

    return FoundSolution(plan, learned_model, edition_distance, explanations)
