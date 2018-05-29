from .utils import grab, InterpreterError
from .lexer import Lexer
from .query import Query, JoinType, JoinDirection
from .tokens import *

class LValue(object):
    def __init__(self, value=None, path=None, loc=None):
        self.value = value
        self.path = path
        self.loc = loc

    def resolve(self, ctx):
        if self.value is not None:
            return self.value
        else:
            try:
                return grab(ctx, self.path, raiser=True)
            except IndexError as e:
                raise InterpreterError(str(e), self.loc)

class Interpreter(object):
    def __init__(self, content: str):
        self.lexer = Lexer(content)
        self.content = content
        self.tokens = self.lexer.tokens()
        self.cur_token = next(self.tokens)
        self.locals = {}
        self.query = Query()
        self.query_items = []

    def error(self, message, loc=None):
        if loc is None:
            loc = (self.cur_token.line, self.cur_token.pos)

        return InterpreterError(message, loc)

    @property
    def current_location(self):
        return (self.cur_token.line, self.cur_token.pos)

    def add_local(self, key, data):
        self.locals[key] = data

    def eat(self, ttype):
        if self.cur_token.type == ttype:
            self.cur_token = next(self.tokens)
        else:
            raise self.error("Expected {0}, got {1}".format(ttype, self.cur_token.type))
            #raise SyntaxError("Expected {0}, got {1}".format(ttype, self.cur_token.type))

    def var_access(self):
        token = self.cur_token
        path = ""
        
        self.eat(IDENTIFIER)   
        path += token.value     

        if self.cur_token.type == DOT:
            self.eat(DOT)
            path += ".{0}".format(self.var_access())

        return path

    def lvalue(self):
        token = self.cur_token

        if token.type == NUMBER or token.type == STRING or token.type == BOOL:
            val = token.value
            self.eat(token.type)
            return LValue(value=val, loc=token.location)
        else:
            val = self.var_access()
            return LValue(path=val, loc=token.location)

    def condition(self):
        left = self.lvalue()

        token = self.cur_token
        if token.type == EQ:
            self.eat(EQ)
            right = self.lvalue()
            return lambda x: left.resolve(x) == right.resolve(x)
        elif token.type == NEQ:
            self.eat(NEQ)
            right = self.lvalue()
            return lambda x: left.resolve(x) != right.resolve(x)
        elif token.type == GT:
            self.eat(GT)
            right = self.lvalue()
            return lambda x: left.resolve(x) > right.resolve(x)
        elif token.type == LT:
            self.eat(LT)
            right = self.lvalue()
            return lambda x: left.resolve(x) < right.resolve(x)
        elif token.type == GTE:
            self.eat(GTE)
            right = self.lvalue()
            return lambda x: left.resolve(x) >= right.resolve(x)
        elif token.type == LTE:
            self.eat(LTE)
            right = self.lvalue()
            return lambda x: left.resolve(x) <= self.lvalue().resolve(x)
        else:
            raise self.error("Expected operator, got {0}".format(token.type))

    def from_stmt(self):
        self.eat(FROM)

        token = self.cur_token
        self.eat(IDENTIFIER)
        alias = token.value

        self.eat(IN)
        collection = self.lvalue()

        self.query_items.append(alias)
        self.query.From([{alias: x} for x in list(collection.resolve(self.locals))])

    def where_stmt(self):
        self.eat(WHERE)

        cond = self.condition()
        self.query.Where(cond)

    def select_stmt(self):
        self.eat(SELECT)

        path = self.lvalue()
        self.query.Path("[*].{0}".format(path.resolve({})))

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
        
        self.query.Join(
            [{alias: x} for x in collection.resolve(self.locals)], 
            lambda x: outer_selector.resolve(x), 
            lambda x: inner_selector.resolve(x),
            lambda x, y: {**x, **y},
            join_type=join_type,
            direction=join_dir
            )

    def statement(self):
        if self.cur_token.type == FROM:
            self.from_stmt()
        elif self.cur_token.type == WHERE:
            self.where_stmt()
        elif self.cur_token.type == JOIN:
            self.join_stmt()
        elif self.cur_token.type == SELECT:
            self.select_stmt()
        else:
            raise self.error("Expected valid statement, got {0}: {1}".format(self.cur_token.type, self.cur_token.value))

    def rquery(self):
        self.from_stmt()

        while self.cur_token.type != EOF:
            self.statement()

    def run(self):
        try:
            self.rquery()
        except InterpreterError as e:
            print(e)
            print("At line {0}, position {1}".format(e.lineno, e.offset))
            print(self.content.splitlines()[e.lineno - 1])
            print(' ' * e.offset + "^")
            return None

        return self.query.Result()
