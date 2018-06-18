from .query import Query
from .tokens import EQ, NEQ, LT, GT, LTE, GTE
from .utils import grab, InterpreterError

class Context:
    """Context is used by the Query Runner and contains the global/local variables."""

    def __init__(self, local_vars=None):
        if local_vars is None:
            self.locals = {}
        else:
            self.locals = local_vars

        self.query = Query()

    def set_var(self, name, value):
        """Set a variable in the current context."""
        self.locals[name] = value

    def var(self, path, default=None, raiser=False):
        """Get a variable in the current context."""
        return grab(self.locals, path, default=default, raiser=raiser)

class Node(object):
    def __init__(self):
        self.loc = None

    def resolve(self, context: Context):
        raise NotImplementedError()

class VarConstNode(object):
    def __init__(self, value):
        self.value = value

    def resolve(self, context: Context):
        return self.value

class VarAccessNode(object):
    def __init__(self, path):
        self.path = path

    def resolve(self, context: Context):
        # Support local resolves like in inner joins
        if isinstance(context, dict):
            return grab(context, self.path)
        else:
            return context.var(self.path)

class FromNode(object):
    def __init__(self, alias, collection):
        self.alias = alias
        self.collection = collection

    def resolve(self, context: Context):
        coll = self.collection.resolve(context)
        context.query.From([{self.alias: x} for x in list(coll)])

class ConditionNode(object):
    def __init__(self, lhs, op, rhs):
        self.lhs = lhs
        self.op = op
        self.rhs = rhs

    def resolve(self, x: Context):
        if self.op == EQ:
            return lambda x: self.lhs.resolve(x) == self.rhs.resolve(x)
        elif self.op == NEQ:
            return lambda x: self.lhs.resolve(x) != self.rhs.resolve(x)
        elif self.op == GT:
            return lambda x: self.lhs.resolve(x) > self.rhs.resolve(x)
        elif self.op == LT:
            return lambda x: self.lhs.resolve(x) < self.rhs.resolve(x)
        elif self.op == GTE:
            return lambda x: self.lhs.resolve(x) >= self.rhs.resolve(x)
        elif self.op == LTE:
            return lambda x: self.lhs.resolve(x) <= self.rhs.resolve(x)
        else:
            raise Exception("Unknown operation: {0}".format(self.op))

class WhereNode(object):
    def __init__(self, condition):
        self.condition = condition

    def resolve(self, context: Context):
        func = self.condition.resolve(context)
        context.query.Where(func)

class JoinNode(object):
    def __init__(self, alias, collection, outer_selector, inner_selector, join_type, join_dir):
        self.alias = alias
        self.collection = collection
        self.outer_selector = outer_selector
        self.inner_selector = inner_selector
        self.join_type = join_type
        self.join_dir = join_dir

    def resolve(self, context: Context):
        context.query.Join(
            [{self.alias: x} for x in self.collection.resolve(context)], 
            lambda x: self.outer_selector.resolve(x), 
            lambda x: self.inner_selector.resolve(x),
            lambda x, y: {**x, **y},
            join_type=self.join_type,
            direction=self.join_dir
            )

class GroupByNode(object):
    def __init__(self, alias, key_selectors, key_aliases):
        self.alias = alias
        self.key_selectors = key_selectors
        self.key_aliases = key_aliases

    def resolve(self, context: Context):
        context.query.GroupBy(self.key_selectors, lambda x, y: {self.alias: { **dict(zip(self.key_aliases, list(x))), "group": y}})

class SelectNode(object):
    def __init__(self, path):
        self.path = path

    def resolve(self, context: Context):
        context.query.Path("[*].{0}".format(self.path.resolve(context)))


        