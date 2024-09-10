"""Navigation Module for API Documentation.

Provide utility functions for managing and updating the
navigation structure of API documentation. Include functions to
retrieve module names, build navigation trees, and update navigation
entries dynamically.
"""

from __future__ import annotations

import re
from functools import partial
from typing import TYPE_CHECKING

from mkapi.utils import find_submodule_names, get_module_path, is_package

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from typing import Any


def get_apinav(
    name: str,
    depth: int,
    predicate: Callable[[str], bool] | None = None,
) -> list:
    """Retrieve a list of module names based on the specified module name and depth.

    Check if the given module name corresponds to a valid module path.
    If the module is not a package, return a list containing only the
    module name. If the module is a package, retrieve submodule names
    based on the specified depth.

    Args:
        name (str): The name of the module for which to retrieve the navigation.
        depth (int): The depth level for retrieving submodules:
            - 1: Return the module name and its immediate submodules.
            - 2: Return a flat list of the module and its submodules,
              including deeper levels.
            - 3: Return a nested dictionary structure representing the module
              and its submodules.
        predicate (Callable[[str], bool], optional): An optional predicate
            function to filter submodule names. If provided, only submodules
            that satisfy this predicate will be included in the result.

    Returns:
        list: A list of module names or a nested structure of module names
        based on the specified depth. Return an empty list if the module
        path is invalid.
    """
    if not get_module_path(name):
        return []

    if not is_package(name):
        return [name]

    find = partial(find_submodule_names, predicate=predicate)

    if depth == 1:
        return [name, *find(name)]

    if depth == 2:
        return _get_apinav_list(name, find)

    if depth == 3:
        return [_get_apinav_dict(name, find)]

    return [name]


def _get_apinav_list(name: str, find: Callable[[str], list[str]]) -> list[str]:
    names = [name]
    for subname in find(name):
        if is_package(subname):
            names.extend(_get_apinav_list(subname, find))
        else:
            names.append(subname)
    return names


def _get_apinav_dict(name: str, find: Callable[[str], list[str]]) -> dict[str, list]:
    names: list[str | dict] = [name]
    for subname in find(name):
        if is_package(subname):
            names.append(_get_apinav_dict(subname, find))
        else:
            names.append(subname)
    return {name: names}


def gen_apinav(
    nav: list,
    depth: int = 0,
) -> Generator[tuple[str, bool, int], Any, None]:
    """Yield tuples of (module name, is_section, depth).

    Iterate over the provided navigation list and yield tuples containing
    the name of each module or section, a boolean indicating whether the
    item is a section, and the depth of the item in the navigation
    hierarchy. Allow for dynamic modification of section names or
    navigation items based on the values sent back during iteration.

    Args:
        nav (list): A list representing the navigation structure,
            which can contain module names or nested dictionaries
            representing sections and their corresponding pages.
        depth (int, optional): The current depth in the navigation
            hierarchy. Defaults to 0.

    Yields:
        tuple[str, bool, int]: A tuple containing:

        - module name (str): The name of the module or section.
        - is_section (bool): True if the item is a section, False otherwise.
        - depth (int): The depth of the item in the navigation hierarchy.

    Examples:
        >>> nav_structure = ['module1', {'section1': ['module2', 'module3']}]
        >>> for name, is_section, depth in gen_apinav(nav_structure):
        ...     print(name, is_section, depth)
        module1 False 0
        section1 True 0
        module2 False 1
        module3 False 1

        >>> nav_structure = ['moduleA', {'sectionA': ['moduleB']}]
        >>> for name, is_section, depth in gen_apinav(nav_structure, 1):
        ...     print(name, is_section, depth)
        moduleA False 1
        sectionA True 1
        moduleB False 2
    """
    for k, page in enumerate(nav):
        if isinstance(page, str):
            page_ = yield page, False, depth
            if page_:
                nav[k] = page_
        elif isinstance(page, dict) and len(page) == 1:
            section, pages = next(iter(page.items()))
            section = yield section, True, depth
            if isinstance(section, str):
                page.clear()
                page[section] = pages
            yield from gen_apinav(pages, depth + 1)


def update_apinav(
    nav: list,
    page: Callable[[str, int], str | dict[str, str]],
    section: Callable[[str, int], str] | None = None,
) -> None:
    """Update the API navigation structure.

    Iterate over the provided navigation list and update it by generating
    page and section titles based on the provided callable functions.
    Utilize a generator to traverse the navigation structure, allowing for
    dynamic modification of section names and page titles.

    Args:
        nav (list): A list representing the navigation structure, which can
            contain module names, sections, and nested pages.
        page (Callable[[str, int], str | dict[str, str]]): A callable
            function that takes a module name and its depth as arguments
            and returns a string or a dictionary representing the page
            title or content.
        section (Callable[[str, int], str] | None, optional): A callable
            function that takes a section name and its depth as arguments
            and returns a string representing the section title. If None,
            the section name will remain unchanged. Defaults to None.

    Raises:
        StopIteration: If the generator completes without yielding any
            further values.

    Examples:
        >>> def page_title(name: str, depth: int) -> str:
        ...     return f"{name.upper()}.{depth}"
        >>> def section_title(name: str, depth: int) -> str:
        ...     return f"Section: {name}"
        >>> nav_structure = ["module1", {"section1": ["module2"]}]
        >>> update_apinav(nav_structure, page_title, section_title)
        >>> print(nav_structure)
        ['MODULE1.0', {'Section: section1': ['MODULE2.1']}]
    """
    it = gen_apinav(nav)
    try:
        name, is_section, depth = it.send(None)
    except StopIteration:
        return
    while True:
        if is_section:  # noqa: SIM108
            value = section(name, depth) if section else name
        else:
            value = page(name, depth)
        try:
            name, is_section, depth = it.send(value)
        except StopIteration:
            break


def build_apinav(
    nav: list,
    create_apinav: Callable[[str, str], list],
) -> list:
    """Build the API navigation structure.

    Construct a navigation structure for the API documentation by
    iterating over the provided navigation list. Process each item,
    checking for API entries and creating corresponding navigation entries
    using the provided `create_apinav` function. The resulting navigation
    structure can include both flat and nested entries based on the input.

    Args:
        nav (list): A list representing the initial navigation structure,
            which can contain module names, sections, and nested pages.
        create_apinav (Callable[[str, str], list]): A callable function
            that takes a module name and `src_uri` as arguments and returns
            a list of navigation entries for that module.

    Returns:
        list: A list representing the updated navigation structure, which
        includes the processed API entries and any nested structures.

    Examples:
        >>> def create_apinav(name: str, path: str) -> list:
        ...     return [f"{name}.md"]
        >>> nav_structure = ["$api/module1", {"section1": ["$api/module2"]}]
        >>> updated_nav = build_apinav(nav_structure, create_apinav)
        >>> print(updated_nav)
        ['module1.md', {'section1': ['module2.md']}]
    """
    nav_ = []
    for item in nav:
        if match := _match_api_entry(item):
            name, path = _split_name_path(match)
            nav_.extend(create_apinav(name, path))

        elif isinstance(item, dict) and len(item) == 1:
            key, value = next(iter(item.items()))

            if match := _match_api_entry(value):
                name, path = _split_name_path(match)
                value = create_apinav(name, path)

                if len(value) == 1 and isinstance(value[0], str):
                    value = value[0]
                elif len(value) == 1 and isinstance(value[0], dict):
                    value = next(iter(value[0].values()))

            elif isinstance(value, list):
                value = build_apinav(value, create_apinav)
            nav_.append({key: value})

        else:
            nav_.append(item)

    return nav_


API_URI_PATTERN = re.compile(r"^(?P<uri>\<.+\>|\$.+)/(?P<name>[^/]+)$")


def _match_api_entry(item: str | list | dict) -> re.Match | None:
    if not isinstance(item, str):
        return None
    return re.match(API_URI_PATTERN, item)


def _split_name_path(match: re.Match) -> tuple[str, str]:
    path, name = match.groups()
    path = path[1:-1] if path.startswith("<") else path[1:]
    return name, path


def split_name_depth(name: str) -> tuple[str, int]:
    """Split a nav entry into name and depth."""
    if m := re.match(r"^(.+?)\.(\*+)$", name):
        name, option = m.groups()
        return name, len(option)

    return name, 0


def update_nav(
    nav: list,
    create_page: Callable[[str, str], str],
    section_title: Callable[[str, int], str] | None = None,
    page_title: Callable[[str, int], str] | None = None,
    predicate: Callable[[str], bool] | None = None,
) -> None:
    """Update the navigation structure.

    Update the provided navigation list by constructing API entries and
    section titles based on the specified callable functions. Process
    each entry in the navigation list, creating pages and sections as
    needed, and modify the navigation structure in place.

    Args:
        nav (list): A list representing the navigation structure, which can
            contain module names, sections, and nested pages.
        create_page (Callable[[str, str, list[str]], str]): A callable
            function that takes a module name, path, and filters as
            arguments and returns a string representing the URI of the
            created page.
        section_title (Callable[[str, int], str] | None, optional): A
            callable function that takes a section name and its depth as
            arguments and returns a string representing the section title.
            If None, the section title will remain unchanged. Defaults to
            None.
        page_title (Callable[[str, int], str] | None, optional): A
            callable function that takes a page name and its depth as
            arguments and returns a string representing the page title.
            If None, the page title will remain unchanged. Defaults to
            None.
        predicate (Callable[[str], bool] | None, optional): An optional
            predicate function to filter the navigation entries. If provided,
            only entries that satisfy this predicate will be included in the
            updated navigation structure.

    Returns:
        None: This function modifies the `nav` list in place and does not
            return a value.
    """

    def _create_apinav(name: str, path: str) -> list:
        def page(name: str, depth: int) -> str | dict[str, str]:
            uri = create_page(name, path)

            if page_title:
                return {page_title(name, depth): uri}
            return uri

        name, depth = split_name_depth(name)
        nav = get_apinav(name, depth, predicate)
        update_apinav(nav, page, section_title)
        return nav

    nav[:] = build_apinav(nav, _create_apinav)
