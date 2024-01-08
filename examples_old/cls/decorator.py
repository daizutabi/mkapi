from functools import wraps


def deco_without_wraps(func):
    def _func(*args, **kwargs):
        return func(*args, **kwargs)

    return _func


def deco_with_wraps(func):
    @wraps(func)
    def _func(*args, **kwargs):
        return func(*args, **kwargs)

    return _func
