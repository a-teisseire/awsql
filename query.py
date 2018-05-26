import jmespath

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

    def Join(self, inner, outer_selector, inner_selector, result_func):
        new_result = []
        for a in self.result:
            a_key = outer_selector(a)

            for b in inner:
                if a_key == inner_selector(b):
                    new_result.append(result_func(a, b))

        self.result = new_result
        return self

    def Path(self, expr):
        self.result = jmespath.search(expr, self.result)
        return self

    def Result(self):
        return self.result

