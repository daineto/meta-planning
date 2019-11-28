class State(object):
    def __init__(self, literals, next_action, assignments=[]):
        self.literals = literals
        self.assignments = assignments
        self.next_action = next_action

    def __str__(self):
        state_str = "(:state %s)" % (' '.join(map(str, self.literals)))
        if self.next_action is not None:
            state_str += "\n\n(:action %s)" % self.next_action
        # else:
        #     state_str += "\n\n(:action )"
        return state_str

    def __repr__(self):
        return "State(literals: % r, applied_action: % r)" % (self.literals, self.next_action)

    def to_close_world(self):
        return State([l for l in self.literals if l.valuation == True], self.next_action)
