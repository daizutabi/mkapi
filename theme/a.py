class A:
    def __init__(self):
        self.dict = {"a": 1}

    def __getattr__(self, key):
        return self.dict[key]


a = A()
hasattr(a, "b")
