from .buffer import Buffer
from typing import Iterable
from .tokens import *

class Lexer(object):
    def __init__(self, text):
        self.buf = Buffer(text)
        self.cur_line = 1
        self.line_pos = 0
        self.token_begin = 0

    def make_token(self, ttype, value) -> Token:
        return Token(ttype, value, self.cur_line, self.line_pos - self.token_begin)

    def identifier(self) -> str:
        ident = ""
        while self.buf.current is not None and (self.buf.current.isalnum() or self.buf.current == '_'):
            ident += self.buf.current
            self.buf.inc()

        return ident

    def number(self) -> str:
        num = ""
        while self.buf.current is not None and (self.buf.current.isdigit() or self.buf.current == '.'):
            num += self.buf.current
            self.buf.inc()

        return num
        #return float(num) if '.' in num else int(num)

    def string(self) -> str:
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

    def tokens(self) -> Iterable[Token]:
        while True:
            t = self.get_next_token()
            yield t

            if t.type == EOF:
                raise StopIteration()


    def get_next_token(self) -> Token:
        while self.buf.current is not None:
            c = self.buf.current

            self.token_begin = self.buf.pos

            # IDENTIFIER or Keyword
            if c.isalpha():
                ident = self.identifier()

                if ident.upper() in KEYWORDS:
                    return self.make_token(ident.upper(), ident)
                elif ident.upper() in [TRUE, FALSE]:
                    return self.make_token(BOOL, ident.upper() == TRUE)
                else:
                    return self.make_token(IDENTIFIER, ident)

            # NUMBER
            elif c.isdigit():
                return self.make_token(NUMBER, self.number())

            # STRING
            elif c == '"' or c == "'":
                return self.make_token(STRING, self.string())

            # Operators
            elif c == "=" and self.buf.next == "=":
                self.buf.inc(2)
                return self.make_token(EQ, "==")

            elif c == "!" and self.buf.next == "=":
                self.buf.inc(2)
                return self.make_token(NEQ, "!=")

            elif c == ">":
                if self.buf.next == "=":
                    self.buf.inc(2)
                    return self.make_token(GTE, ">=")
                else:
                    self.buf.inc()
                    return self.make_token(GT, ">")

            elif c == "<":
                if self.buf.next == "=":
                    self.buf.inc(2)
                    return self.make_token(LTE, "<=")
                else:
                    self.buf.inc()
                    return self.make_token(LT, "<")

            # Punctuation
            elif c == '.':
                self.buf.inc()
                return self.make_token(DOT, '.')

            elif c == '[':
                self.buf.inc()
                return self.make_token(LSQB, '[')

            elif c == ']':
                self.buf.inc()
                return self.make_token(RSQB, ']')

            elif c == ',':
                self.buf.inc()
                return self.make_token(COMMA, ',')

            # Skip spaces
            elif c.isspace():
                while self.buf.current is not None and self.buf.current.isspace():
                    if self.buf.current == '\n':
                        self.cur_line += 1
                        self.line_pos = self.buf.pos

                    self.buf.inc()

            else:
                raise Exception("Unknown token: {0}".format(self.buf.string()))
        
        return self.make_token(EOF, "EOF")
