"""Filter functions."""


def split_filters(name: str) -> tuple[str, list[str]]:
    """Split filters written after `|`s.

    Examples:
        >>> split_filters("a.b.c")
        ('a.b.c', [])
        >>> split_filters("a.b.c|upper|strict")
        ('a.b.c', ['upper', 'strict'])
        >>> split_filters("|upper|strict")
        ('', ['upper', 'strict'])
        >>> split_filters("")
        ('', [])
    """
    index = name.find("|")
    if index == -1:
        return name, []
    name, filters = name[:index], name[index + 1 :]
    return name, filters.split("|")


def update_filters(org: list[str], update: list[str]) -> list[str]:
    """Update filters.

    Examples:
        >>> update_filters(['upper'], ['lower'])
        ['lower']
        >>> update_filters(['lower'], ['upper'])
        ['upper']
        >>> update_filters(['long'], ['short'])
        ['short']
        >>> update_filters(['short'], ['long'])
        ['long']
    """
    filters = org + update
    for x, y in [["lower", "upper"], ["long", "short"]]:
        if x in org and y in update:
            del filters[filters.index(x)]
        if y in org and x in update:
            del filters[filters.index(y)]

    return filters
