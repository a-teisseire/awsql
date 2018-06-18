from .utils import grab, InterpreterError
from .lexer import Lexer
from .tree import *
from .query import JoinDirection, JoinType
from .tokens import *
from typing import Tuple, List


class Parser(object):
    def __init__(self, content: str):
        self.lexer = Lexer(content)
        self.content = content
        self.tokens = self.lexer.tokens()
        self.cur_token = next(self.tokens)
        self.steps = []

    def error(self, message, loc=None) -> InterpreterError:
        if loc is None:
            loc = self.current_location

        return InterpreterError(message, loc)

    def add_step(self, step):
        self.steps.append(step)

    @property
    def current_location(self) -> Tuple[int, int]:
        return (self.cur_token.line, self.cur_token.pos)

    def eat(self, ttype):
        """Advance the token pointer by one and assert that the current token is of the expected type."""
        if self.cur_token.type == ttype:
            self.cur_token = next(self.tokens)
        else:
            raise self.error("Expected {0}, got {1}".format(ttype, self.cur_token.type))

    def var_access(self) -> str:
        token = self.cur_token
        path = ""
        
        self.eat(IDENTIFIER)   
        path += token.value     

        if self.cur_token.type == DOT:
            self.eat(DOT)
            path += ".{0}".format(self.var_access())

        return path

    def lvalue(self) -> Node:
        token = self.cur_token

        if token.type == NUMBER or token.type == STRING or token.type == BOOL:
            val = token.value
            self.eat(token.type)
            return VarConstNode(val)
        else:
            val = self.var_access()
            return VarAccessNode(val)

    def condition(self) -> Node:
        left = self.lvalue()

        optoken = self.cur_token
        if optoken.type in [EQ, NEQ, LT, GT, LTE, GTE]:
            self.eat(optoken.type)
            right = self.lvalue()

            return ConditionNode(left, optoken.type, right)
        else:
            raise self.error("Expected operator, got {0}".format(optoken.type))

    def from_stmt(self):
        self.eat(FROM)

        token = self.cur_token
        self.eat(IDENTIFIER)
        alias = token.value

        self.eat(IN)
        collection = self.lvalue()

        self.add_step(FromNode(alias, collection))

    def where_stmt(self):
        self.eat(WHERE)
        condition = self.condition()
        self.add_step(WhereNode(condition))

    def select_stmt(self):
        self.eat(SELECT)
        path = self.lvalue()
        self.add_step(SelectNode(path))

    def join_stmt(self):
        join_type = JoinType.INNER
        join_dir = None

        self.eat(JOIN)

        if self.cur_token.type == OUTER:
            join_type = JoinType.OUTER
            self.eat(OUTER)

            if self.cur_token.type == LEFT:
                join_dir = JoinDirection.LEFT
                self.eat(LEFT)
            elif self.cur_token.type == RIGHT:
                join_dir = JoinDirection.RIGHT
                self.eat(RIGHT)

        elif self.cur_token.type == INNER:
            self.eat(INNER)

        token = self.cur_token
        self.eat(IDENTIFIER)
        alias = token.value

        self.eat(IN)
        collection = self.lvalue()
        self.eat(ON)
        outer_selector = self.lvalue()
        self.eat(EQUALS)
        inner_selector = self.lvalue()
        
        self.add_step(JoinNode(alias, collection, outer_selector, inner_selector, join_type, join_dir))

    def group_stmt(self):
        self.eat(GROUP)
        self.eat(BY)

        key_selectors = []
        key_paths = []
        while self.cur_token.type == IDENTIFIER:
            key_val = self.lvalue()
            key_paths.append(key_val)
            key_selectors.append(lambda x: key_val.resolve(x))

            if self.cur_token.type != COMMA:
                break
            else:
                self.eat(COMMA)

        self.eat(INTO)
        token = self.cur_token
        self.eat(IDENTIFIER)
        alias = token.value

        key_aliases = [x.path.split('.')[-1] for x in key_paths]
        self.add_step(GroupByNode(alias, key_selectors, key_aliases))

    def statement(self):
        if self.cur_token.type == FROM:
            self.from_stmt()
        elif self.cur_token.type == WHERE:
            self.where_stmt()
        elif self.cur_token.type == JOIN:
            self.join_stmt()
        elif self.cur_token.type == GROUP:
            self.group_stmt()
        elif self.cur_token.type == SELECT:
            self.select_stmt()
        else:
            raise self.error("Expected valid statement, got {0}: {1}".format(self.cur_token.type, self.cur_token.value))


    def parse(self) -> List[Node]:
        while self.cur_token.type != EOF:
            self.statement()

        return self.steps

"""
    def run(self):
        try:
            self.rquery()
        except InterpreterError as e:
            print(e)
            print("At line {0}, position {1}".format(e.lineno, e.offset))
            print(self.content.splitlines()[e.lineno - 1])
            print(' ' * e.offset + "^")
            return None
"""