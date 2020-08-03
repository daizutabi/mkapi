from mkapi.core.base import Section
from mkapi.core.docstring import get_docstring


def func():
    """Internal link examples.

    * [Section]() --- Imported object.
    * [](get_docstring) --- Imported object.
    * [Section.set_html]() --- Member of imported object.
    * [Section definition](Section) --- Alternative text.
    * Section_  --- reStructuredText style.
    """
    return Section(), get_docstring(None)
