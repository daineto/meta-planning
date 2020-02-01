from ..observations import Trajectory, State
from ..pddl import Increase, Literal, Truth

import copy

def apply_action(model, action, state):

    for scheme in model.schemata:
        if scheme.name == action.name:
            lifted_action = scheme

    if len(action.arguments) != 0:
        grounded_action = lifted_action.instantiate(action.arguments)
    else:
        grounded_action = lifted_action

    #TODO: check applicability

    state_literals = set(state.literals)
    positive_effects = set()
    negative_effects = set()
    cost = 0

    if grounded_action.cost is not None:
        cost += grounded_action.cost.expression.value

    for effect in grounded_action.effects:

        if isinstance(effect.condition, Truth) or effect.condition in state_literals:

            if isinstance(effect.literal, Literal):
                if effect.literal.valuation:
                    positive_effects.add(effect.literal)
                else:
                    negative_effects.add(effect.literal)
            elif isinstance(effect.literal, Increase):
                cost += effect.literal.expression.value


    for effect in negative_effects:
        state_literals.remove(effect.positive())
        state_literals.add(effect)

    for effect in positive_effects:
        if effect.negate() in state_literals:
            state_literals.remove(effect.negate())
        state_literals.add(effect)

    return State(sorted(list(state_literals)), None), cost


def generate_trajectory(model, problem, plan):

    states = []
    cost = 0

    current_state = problem.init
    for action in plan.actions:
        current_state.next_action = action
        next_state, action_cost = apply_action(model, action, current_state)

        states.append(current_state)
        current_state = next_state
        cost += action_cost

    states.append(current_state)

    if cost == 0:
        cost = len(states)

    return Trajectory(problem.objects, states, cost=cost)


