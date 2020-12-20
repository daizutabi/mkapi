# Changelog

## [Unreleased]
### Added
- Short filter (`nav_short`) for nav items in page mode ([#41](https://github.com/daizutabi/mkapi/issues/41)).

## [1.0.13] - 2020-08-03
### Fixed
- Handle parsing empty line ([#23](https://github.com/daizutabi/mkapi/pull/23)). Thanks to [tony](https://github.com/tony).
- Typo ([#24](https://github.com/daizutabi/mkapi/pull/24)). Thanks to [tony](https://github.com/tony).
- Add a slash at the end of URL ([#25](https://github.com/daizutabi/mkapi/issues/25)).


## [1.0.12] - 2020-07-29
### Changed
- Ensure compatibility with future MkDocs versions ([#20](https://github.com/daizutabi/mkapi/pull/20)). Thanks to [timvink](https://github.com/timvink).

## [1.0.11] - 2020-07-07
### Fixed
- TypeError in `<metaclass>.mro()` ([#19](https://github.com/daizutabi/mkapi/issues/19)).

## [1.0.10] - 2020-06-28
### Added
- Global filters and page filters.

### Fixed
- Delete prefix in nav menu for heading mode.

## [1.0.9] - 2020-06-28
### Added
- *Abstract* prefix for abstract class and method.

### Changed
- *readonly_property* -> *readonly property* and *readwrite_property* -> *readwrite property*.

### Fixed
- Detect classmethods on abstract base class ([#18](https://github.com/daizutabi/mkapi/issues/18)).

## [1.0.8] - 2020-06-20
### Added
- `short` filter to remove the prefix from an object name ([#16](https://github.com/daizutabi/mkapi/pull/16)). Thanks to [Ahrak](https://github.com/Ahrak).

## [1.0.7] - 2020-06-19
### Changed
- Top level object style.
- Hide `function` prefix by `display: none;` in CSS.

## [1.0.6] - 2020-06-19
### Changed
- Object type style: Bold upper case -> italic lower case, as in the readthedocs.
- Hide `method` prefix by `display: none;` in CSS.

### Fixed
- `type: description` style docstring is interpreted as a pair of return type and description only if the object is a property ([#17](https://github.com/daizutabi/mkapi/issues/17)).

## [1.0.5] - 2020-06-18
### Changed
- Use theme's admonition for Note[s] and Warning[s] sections.
- Update CSS ([#8](https://github.com/daizutabi/mkapi/issues/8)). Thanks to [Ahrak](https://github.com/Ahrak).

### Fixed
- Attribute inspection from docstring.
- Display base class in non-strict mode.
- Catch `NameError` in resolving `typing.ForwardRef` ([#14](https://github.com/daizutabi/mkapi/issues/14)).
- Delete unrelated members in a decorated function.
- Inspect type of decorated functions correctly.
- Skip multiple assignments per line during attribute inspection ([#15](https://github.com/daizutabi/mkapi/issues/15)).

## [1.0.4] - 2020-06-16
### Added
- `all` filter for package or module to display all of the members and add links to them.
- Link from table of contents to source.

### Fixed
- Include decorated functions if decorator uses `functools.wraps()`.

## [1.0.3] - 2020-06-16
### Added
- Link from property to source vice versa.
- reStructuredText type link like `Object_`.
- Support of string type annotation like `ForwardRef`.

### Fixed
- Include functions decorated by Pytest ([#14](https://github.com/daizutabi/mkapi/issues/14)).

## [1.0.2] -  2020-06-16
### Fixed
- Correct parameter names for `*args` and `**kwargs`.

## [1.0.1] - 2020-06-16
### Added
- `title` attribute to [DOCS] and [SOURCE] link to display the object id.
- `hasattr` for `_ast.Str` because Python 3.8 does not provide the attribute.

## [1.0.0] - 2020-06-15
### Added
- Support for NumPy docstring style ([#1](https://github.com/daizutabi/mkapi/issues/1)).
- Document only a specific method from a class ([#5](https://github.com/daizutabi/mkapi/issues/5)).
- Support for magic/dunder methods ([#7](https://github.com/daizutabi/mkapi/issues/7)).
- Include methods defined in different file ([#9](https://github.com/daizutabi/mkapi/issues/9)).
- Display inheritance of class ([#10](https://github.com/daizutabi/mkapi/issues/10)).
- `on_config` option to allow users to run custom script ([#11](https://github.com/daizutabi/mkapi/issues/11)).
