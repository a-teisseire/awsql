from jmespath import functions


class JMESPathFunctions(functions.Functions):
    @functions.signature({'types': ['object']}, {'types': ['string']})
    def _func_get_tag(self, data, key):
        try:
            tags = data["Tags"]
            for t in tags:
                if t["Key"] == key:
                    return t["Value"]
        except Exception:
            pass
        
        return None


class InterpreterError(Exception):
    def __init__(self, message, loc):
        super().__init__(message)
        self.loc = loc

    @property
    def lineno(self):
        return self.loc[0]

    @property
    def offset(self):
        return self.loc[1]


def grab(data, path, default=None, raiser=False):
    if isinstance(path, str):
        keys = path.split(".")
    else:
        keys = path

    obj = data
    for k in keys:
        if k not in obj:
            if raiser:
                raise IndexError("Error while resolving path: {0}, {1} doesn't exist".format(path, k))

            return default

        obj = obj[k]
    else:
        return obj

