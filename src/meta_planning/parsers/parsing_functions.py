from ..pddl import TypedObject

import copy

def parse_typed_list(alist, only_variables=False,
                     constructor=TypedObject,
                     default_type="object"):
    aux = copy.deepcopy(alist)
    alist = []
    for item in aux:
        if item.startswith("-") and not item == "-":
            alist.append("-")
            alist.append(item[1:])
        else:
            alist.append(item)
    result = []
    while alist:
        try:
            separator_position = alist.index("-")
            pass
        except ValueError:
            items = alist
            _type = default_type
            alist = []
        else:
            items = alist[:separator_position]
            _type = alist[separator_position + 1]
            alist = alist[separator_position + 2:]
        for item in items:
            assert not only_variables or item.startswith("?"), \
                "Expected item to be a variable: %s in (%s)" % (
                    item, " ".join(items))
            entry = constructor(item, _type)
            result.append(entry)
    return result