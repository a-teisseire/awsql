def grab(data, keys, default=None, raiser=False):
    if isinstance(keys, str):
        keys = keys.split(".")

    obj = data
    for k in keys:
        if k not in obj:
            if raiser:
                raise IndexError()

            return default

        obj = obj[k]
    else:
        return obj


class Buffer(object):
    def __init__(self, content: str):
        self.content = content
        self.csize = len(content)
        self.pos = 0

    def string(self) -> str:
        return self.content[self.pos:]

    def seek(self, pos: int):
        self.pos = pos

    def inc(self, pos: int = 1):
        self.pos += pos

    def get(self) -> str:
        c = self.peek()
        self.pos += 1
        return c

    @property
    def next(self) -> str:
        return self.peek()

    @property
    def current(self) -> str:
        if self.pos >= self.csize:
            return None

        return self.content[self.pos]

    @property
    def prev_char(self) -> str:
        if self.pos == 0:
            return None

        return self.content[self.pos - 1]

    def peek(self) -> str:
        peek_pos = self.pos + 1
        if peek_pos > self.csize - 1:
            return None
        else:
            return self.content[peek_pos]

    def __next__(self) -> str:
        c = self.get()
        if c is None:
            raise StopIteration()
        
        return c
