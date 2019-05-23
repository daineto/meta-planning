from random import random, randint, seed
from .state import State
from ..pddl import Action

class Trajectory(object):
    def __init__(self, objects, states):
        self.objects = objects
        self.states = states
        self.length = len(states)

    def __str__(self):
        return "(trajectory\n\n(:objects %s)\n\n%s)" % (' '.join(map(str, self.objects)), "\n\n".join(map(str, self.states)))

    def __repr__(self):
        return "Trajectory(objects: %r, states: %r)" % (self.objects, self.states)

    def to_close_world(self):
        new_states = [s.to_close_world() for s in self.states]
        return Trajectory(self.objects, new_states)

    def observe(self, state_observability, action_observability=1., goal_observability=1., keep_every_state=False, positive_goal_literals=False):
        seed(123)
        new_states = []

        if state_observability == 1 or keep_every_state:
            all_states_observed = True
        else:
            all_states_observed = False

        if action_observability == 1:
            all_actions_observed = True
        else:
            all_actions_observed = False

        # First state
        current_literals = self.states[0].literals
        current_action = None
        if random() < action_observability:
            current_action = self.states[0].next_action

        if current_literals != [] and current_action != None:
            new_states.append(State(current_literals, current_action))
            current_literals = []
            current_action = None

        for s in self.states[1:-1]:
            new_literals = [l for l in s.literals if random() < state_observability]
            if new_literals == [] and keep_every_state:
                new_literals = [s.literals[randint(0, len(s.literals)-1)]]
            if new_literals != []:
                if current_literals != []:
                    new_states.append(State(current_literals, None))
                current_literals = new_literals

            new_action = None
            if random() < action_observability:
                new_action = s.next_action
            if new_action != None:
                if current_action != None:
                    new_states.append(State([], current_action))
                current_action = new_action

            if current_literals != [] and current_action != None:
                new_states.append(State(current_literals, current_action))
                current_literals = []
                current_action = None

        if current_literals != []:
            new_states.append(State(current_literals, None))
        elif current_action != None:
            new_states.append(State([], current_action))

        new_literals = [l for l in self.states[-1].literals if random() < goal_observability]
        if new_literals == []:
            new_literals = [self.states[-1].literals[randint(0, len(self.states[-1].literals) - 1)]]
        new_states.append(State(new_literals, None))

        return Observation(self.objects, new_states, all_states_observed, all_actions_observed)


class Observation(object):
    def __init__(self, objects, states, all_states_observed, all_actions_observed):
        self.objects = objects
        self.states = states
        self.all_states_observed = all_states_observed
        self.all_actions_observed = all_actions_observed
        self.bounded = all_states_observed or all_actions_observed
        self.length = len(states)
        self.number_of_states = self.get_number_of_states()
        self.number_of_actions = self.get_number_of_actions()


    def __str__(self):
        return "(observation\n\n(:objects %s)\n\n%s)" % (' '.join(map(str, self.objects)), "\n\n".join(map(str, self.states)))

    def __repr__(self):
        return "Observation(objects: %r, states: %r, bounded: %r)" % (self.objects, self.states, self.bounded)

    def has_actions(self):
        return any([s.next_action != None for s in self.states])

    def get_number_of_states(self):
        num_states = 0
        for s in self.states:
            if s.literals != []:
                num_states += 1
        return num_states

    def get_number_of_actions(self):
        num_actions = 0
        for s in self.states:
            if s.next_action != None:
                num_actions += 1
        return num_actions