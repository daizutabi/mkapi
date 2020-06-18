# Changelog

## [Unreleased]
### Changed
- Delete prefix if an object has qualifide name with `.`.

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

- BugFix: Correct parameter names for `*args` and `**kwargs`.

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
