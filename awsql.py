import boto3
from query import Query
from utils import grab, Buffer

class Lexer(object):
    def __init__(self, text):
        self.buf = Buffer(text)

    def identifier(self):
        ident = ""
        while self.buf.current is not None and (self.buf.current.isalnum() or self.buf.current == '_'):
            ident += self.buf.current
            self.buf.inc()

        return ident

    def number(self):
        num = ""
        while self.buf.current is not None and (self.buf.current.isdigit() or self.buf.current == '.'):
            num += self.buf.current
            self.buf.inc()

        return float(num) if '.' in num else int(num)

    def string(self):
        val = ""
        ignore_next = False

        # Get the string opening symbol and inc the buffer
        q = self.buf.current
        self.buf.inc()
        while self.buf.current is not None:
            if ignore_next:
                ignore_next = False
            else:
                if self.buf.current == q:
                    self.buf.inc()
                    break

                if self.buf.current == '\\':
                    ignore_next = True

            val += self.buf.current
            self.buf.inc()

        return val

    def tokens(self):
        while True:
            t = self.get_next_token()
            yield t

            if t.type == EOF:
                raise StopIteration()


    def get_next_token(self):
        while self.buf.current is not None:
            c = self.buf.current

            # IDENTIFIER or Keyword
            if c.isalpha():
                ident = self.identifier()

                if ident.upper() in KEYWORDS:
                    return Token(ident.upper(), ident)
                else:
                    return Token(IDENTIFIER, ident)

            # NUMBER
            elif c.isdigit():
                return Token(NUMBER, self.number())

            # STRING
            elif c == '"' or c == "'":
                return Token(STRING, self.string())

            # Operators
            elif c == "=" and self.buf.next == "=":
                self.buf.inc(2)
                return Token(EQ, "==")

            elif c == "!" and self.buf.next == "=":
                self.buf.inc(2)
                return Token(NEQ, "!=")

            elif c == ">":
                if self.buf.next == "=":
                    self.buf.inc(2)
                    return Token(GTE, ">=")
                else:
                    self.buf.inc()
                    return Token(GT, ">")

            elif c == "<":
                if self.buf.next == "=":
                    self.buf.inc(2)
                    return Token(LTE, "<=")
                else:
                    self.buf.inc()
                    return Token(LT, "<")

            # Punctuation
            elif c == '.':
                self.buf.inc()
                return Token(DOT, '.')

            # Skip spaces
            elif c.isspace():
                while self.buf.current is not None and self.buf.current.isspace():
                    self.buf.inc()

            else:
                raise Exception("Unknown token: {0}".format(self.buf.string()))
        
        return Token(EOF, "EOF")

# TYPES
NUMBER, STRING, IDENTIFIER = (
    'NUMBER', 'STRING', 'IDENTIFIER'
)

# OPERATORS
EQ, NEQ, GT, LT, GTE, LTE = (
    'EQ', 'NEQ', 'GT', 'LT', 'GTE', 'LTE'
)

# PUNCTUATION
DOT, EOF = (
    'DOT', 'EOF'
)

# KEYWORDS
FROM, IN, JOIN, ON, EQUALS, WHERE, PATH = (
    'FROM', 'IN', 'JOIN', 'ON', 'EQUALS', 'WHERE', 'PATH'
)

KEYWORDS = [
    FROM,
    IN,
    JOIN,
    ON,
    EQUALS,
    WHERE,
    PATH
]

class Token(object):
    def __init__(self, ttype: str, value):
        self.type = ttype
        self.value = value

    def __str__(self):
        return "Token({0}, \"{1}\")".format(self.type, self.value)

class LValue(object):
    def __init__(self, value=None, path=None):
        self.value = value
        self.path = path

    def resolve(self, ctx):
        if self.value is not None:
            return self.value
        else:
            return grab(ctx, self.path, raiser=True)

class Interpreter(object):
    def __init__(self, content: str):
        self.lexer = Lexer(content)
        self.tokens = self.lexer.tokens()
        self.cur_token = next(self.tokens)
        self.locals = {}
        self.query = Query()
        self.query_items = []

    def add_local(self, key, data):
        self.locals[key] = data

    def eat(self, ttype):
        if self.cur_token.type == ttype:
            self.cur_token = next(self.tokens)
        else:
            raise SyntaxError("Expected {0}, got {1}".format(ttype, self.cur_token.type))

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
        if self.cur_token.type == NUMBER or self.cur_token.type == STRING:
            val = self.cur_token.value
            self.eat(self.cur_token.type)
            return LValue(value=val)
        else:
            val = self.var_access()
            return LValue(path=val)

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
            raise SyntaxError("Expected operator, got {0}".format(token.type))

    def from_stmt(self):
        self.eat(FROM)

        token = self.cur_token
        self.eat(IDENTIFIER)
        alias = token.value

        self.eat(IN)
        collection = self.lvalue()

        self.query_items.append(alias)
        self.query.From([{alias: x} for x in collection.resolve(self.locals)])

    def where_stmt(self):
        self.eat(WHERE)

        cond = self.condition()
        self.query.Where(cond)

    def path_stmt(self):
        self.eat(PATH)

        path = self.lvalue()
        self.query.Path(path.resolve({}))

    def join_stmt(self):
        self.eat(JOIN)

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
            lambda x, y: {**x, **y}
            )

    def statement(self):
        if self.cur_token.type == FROM:
            self.from_stmt()
        elif self.cur_token.type == WHERE:
            self.where_stmt()
        elif self.cur_token.type == JOIN:
            self.join_stmt()
        elif self.cur_token.type == PATH:
            self.path_stmt()
        else:
            raise SyntaxError("Expected valid statement, got {0}".format(self.cur_token.type))

    def rquery(self):
        self.from_stmt()

        while self.cur_token.type != EOF:
            self.statement()

    def run(self):
        self.rquery()

        return self.query.Result()
