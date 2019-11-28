from ..observations import Trajectory, State
from ..pddl import Action

import copy

def apply_action(model, action, state):

    for scheme in model.schemata:
        if scheme.name == action.name:
            lifted_action = scheme

    grounded_action = lifted_action.instantiate(action.arguments)

    #TODO: check applicability

    state_literals = set(state.literals)
    positive_effects = set()
    negative_effects = set()

    for effect in grounded_action.effects:
        if effect.literal.valuation:
            positive_effects.add(effect.literal)
        else:
            negative_effects.add(effect.literal)

    for effect in negative_effects:
        state_literals.remove(effect.positive())
        state_literals.add(effect)

    for effect in positive_effects:
        state_literals.remove(effect.negate())
        state_literals.add(effect)

    return State(sorted(list(state_literals)), None)

def generate_trajectory(model, problem, plan):

    states = []

    current_state = problem.init
    for action in plan.actions:
        current_state.next_action = action
        next_state = apply_action(model, action, current_state)

        states.append(current_state)
        current_state = next_state

    states.append(current_state)

    return Trajectory(problem.objects, states)


