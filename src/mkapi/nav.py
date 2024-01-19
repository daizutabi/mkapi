"""Navivgation utility functions."""
from __future__ import annotations

import re
from functools import partial
from typing import TYPE_CHECKING, TypeGuard

from mkapi.utils import find_submodule_names, get_module_path, is_package, split_filters

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from typing import Any


def get_apinav(name: str, predicate: Callable[[str], bool] | None = None) -> list:
    """Return list of module names."""
    if m := re.match(r"^(.+?)\.(\*+)$", name):
        name, option = m.groups()
        n = len(option)
    else:
        n = 0
    if not get_module_path(name):
        return []
    if not is_package(name):
        return [name]
    find = partial(find_submodule_names, predicate=predicate)
    if n == 1:
        return [name, *find(name)]
    if n == 2:
        return _get_apinav_list(name, find)
    if n == 3:
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
    """Yield tuple of (module name, is_section).

    Sent value is used to modify section names or nav items.
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
    """Update API navigation."""
    it = gen_apinav(nav)
    name, is_section, depth = it.send(None)
    while True:
        if is_section:
            value = section(name, depth) if section else name
        else:
            value = page(name, depth)
        try:
            name, is_section, depth = it.send(value)
        except StopIteration:
            break


def create_nav(nav: list, create_apinav: Callable[[str, str, list[str]], list]) -> list:
    """Create navigation."""
    nav_ = []
    for item in nav:
        if match := _match_api_entry(item):
            name, path, filters = _split_name_path_filters(match)
            nav_.extend(create_apinav(name, path, filters))
        elif isinstance(item, dict) and len(item) == 1:
            key, value = next(iter(item.items()))
            if match := _match_api_entry(value):
                name, path, filters = _split_name_path_filters(match)
                value = create_apinav(name, path, filters)
                if len(value) == 1 and isinstance(value[0], str):
                    value = value[0]
                elif len(value) == 1 and isinstance(value[0], dict):
                    value = next(iter(value[0].values()))
            elif isinstance(value, list):
                value = create_nav(value, create_apinav)
            nav_.append({key: value})
        else:
            nav_.append(item)
    return nav_


API_URI_PATTERN = re.compile(r"^\<(.+)\>/(.+)$")


def _match_api_entry(item: str | list | dict) -> re.Match | None:
    if not isinstance(item, str):
        return None
    return re.match(API_URI_PATTERN, item)


def _split_name_path_filters(match: re.Match) -> tuple[str, str, list[str]]:
    path, name_filters = match.groups()
    name, filters = split_filters(name_filters)
    return name, path, filters


def update_nav(
    nav: list,
    create_page: Callable[[str, str, list[str], int], str | None],
    section: Callable[[str, int], str] | None = None,
    predicate: Callable[[str], bool] | None = None,
) -> None:
    """Update navigation."""

    def create_apinav(name: str, api_path: str, filters: list[str]) -> list:
        def page(name: str, depth: int) -> str | dict[str, str]:
            path = f"{api_path}/{name}.md"
            title = create_page(name, path, filters, depth)
            return {title: path} if title else path

        nav = get_apinav(name, predicate)
        update_apinav(nav, page, section)
        return nav

    nav[:] = create_nav(nav, create_apinav)
