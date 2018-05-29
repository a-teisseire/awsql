import jmespath
from enum import Enum
from .utils import JMESPathFunctions

class JoinType(Enum):
    INNER = 0
    OUTER = 1

class JoinDirection(Enum):
    LEFT = 0
    RIGHT = 1

class Query(object):
    def __init__(self):
        self.result = None
        pass

    def From(self, source):
        self.result = list(source)
        return self

    def Where(self, predicate):
        self.result = list(filter(predicate, self.result))
        return self

    def Join(self, rhs, lhs_selector, rhs_selector, result_func, join_type=JoinType.INNER, direction=JoinDirection.LEFT):
        new_result = []

        if join_type == JoinType.OUTER and direction == JoinDirection.RIGHT:
            outer = rhs
            inner = self.result
            outer_selector = rhs_selector
            inner_selector = lhs_selector
        else:
            outer = self.result
            inner = rhs
            outer_selector = lhs_selector
            inner_selector = rhs_selector

        found = False
        for o in outer:
            o_key = outer_selector(o)

            for i in inner:
                if o_key == inner_selector(i):
                    new_result.append(result_func(o, i))
                    found = True

            if not found and join_type == JoinType.OUTER:
                new_result.append(result_func(o, {}))

        self.result = new_result
        return self

    def Path(self, expr):
        self.result = jmespath.search(expr, self.result, options=jmespath.Options(custom_functions=JMESPathFunctions()))
        return self

    def Result(self):
        return self.result

