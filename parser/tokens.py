
# TYPES
NUMBER, STRING, BOOL, IDENTIFIER = (
    'NUMBER', 'STRING',  'BOOL', 'IDENTIFIER'
)

# BOOL
TRUE, FALSE = (
    'TRUE', 'FALSE'
)

# OPERATORS
EQ, NEQ, GT, LT, GTE, LTE = (
    'EQ', 'NEQ', 'GT', 'LT', 'GTE', 'LTE'
)

# PUNCTUATION
DOT, COMMA, LSQB, RSQB, EOF = (
    'DOT', 'COMMA', 'LSQB', 'RSQB', 'EOF'
)

# KEYWORDS
FROM, IN, JOIN, INNER, OUTER, LEFT, RIGHT, ON, EQUALS, WHERE, SELECT, GROUP, BY, INTO = (
    'FROM', 'IN', 'JOIN', 'INNER', 'OUTER', 'LEFT', 'RIGHT', 'ON', 'EQUALS', 'WHERE', 'SELECT', 'GROUP', 'BY', 'INTO'
)

KEYWORDS = [
    FROM,
    IN,
    JOIN,
    INNER,
    OUTER,
    LEFT,
    RIGHT,
    ON,
    EQUALS,
    WHERE,
    SELECT,
    GROUP,
    BY,
    INTO
]

class Token(object):
    def __init__(self, ttype: str, value, line: int, pos: int):
        self.type = ttype
        self.value = value
        self.line = line
        self.pos = pos

    def __str__(self):
        return "Token({0}, \"{1}\")".format(self.type, self.value)

    @property
    def location(self):
        return (self.line, self.pos)
