# Renamed from types.py to avoid clash with stdlib module.
# In the future, use explicitly relative imports or absolute
# imports as a better solution.

import itertools


class Type(object):
    def __init__(self, name, basetype_name=None):
        self.name = name
        self.basetype_name = basetype_name

    def __str__(self):
        if self.basetype_name != None:
            return "%s - %s" % (self.name, self.basetype_name)
        else:
            return self.name

    def __repr__(self):
        return "Type(%s, %s)" % (self.name, self.basetype_name)


class TypedObject(object):
    def __init__(self, name, type_name):
        self.name = name
        self.type_name = type_name

    def __hash__(self):
        return hash((self.name, self.type_name))

    def __eq__(self, other):
        return self.name == other.name and self.type_name == other.type_name

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return "%s - %s" % (self.name, self.type_name)

    def __repr__(self):
        return "TypedObject(name: %r, type_name: %r)" % (self.name, self.type_name)

    def uniquify_name(self, type_map, renamings):
        if self.name not in type_map:
            type_map[self.name] = self.type_name
            return self
        for counter in itertools.count(1):
            new_name = self.name + str(counter)
            if new_name not in type_map:
                renamings[self.name] = new_name
                type_map[new_name] = self.type_name
                return TypedObject(new_name, self.type_name)
