import jmespath
import itertools

class LazyList(object):
    def __init__(self):
        self.loaded = False
        self.data = []

    def load(self):
        raise NotImplementedError()

    def __next__(self):
        if not self.loaded:
            self.load()
            self.loaded = True

        for x in self.data:
            yield x

    def __iter__(self):
        return next(self)

class LazyListFetcher(LazyList):
    def __init__(self, provider_func):
        self.provider_func = provider_func
        super().__init__()

    def load(self):
        self.data = self.provider_func()

def create_list(func, path):
    return LazyListFetcher(lambda: jmespath.search(path, func()))

def create_paginated_list(client, action, path):
    paginator = client.get_paginator(action)
    return LazyListFetcher(lambda: list(paginator.paginate().search(path)))
    #return LazyListFetcher(lambda: itertools.chain.from_iterable([jmespath.search(path, x) for x in paginator.paginate()))
