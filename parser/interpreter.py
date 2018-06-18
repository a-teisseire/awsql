from .tree import Node, Context
from typing import List

class BaseInterpreter(object):
    """BaseInterpreter provides the basic features set for running the instructions."""

    def __init__(self, steps: List[Node]):
        self.steps = steps

    def run(self, context: Context):
        for s in self.steps:
            s.resolve(context)

        return context.query.Result()
