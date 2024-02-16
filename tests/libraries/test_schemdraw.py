from mkapi.globals import get_globals
from mkapi.utils import get_by_name


def test_get_globals():
    from schemdraw.elements.cables import Element2Term, Segment  # type: ignore

    x = get_globals("schemdraw.elements.cables")
    n = get_by_name(x.names, "Segment")
    assert n
    a = f"{Segment.__module__}.{Segment.__name__}"
    assert n.fullname == a
    n = get_by_name(x.names, "Element2Term")
    assert n
    a = f"{Element2Term.__module__}.{Element2Term.__name__}"
    assert n.fullname == a


# schemdraw.elements.intcircuits.Ic
# IcDIP
# Keyword args
