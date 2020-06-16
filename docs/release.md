# Release Notes

## Version 1.0.1 (2020-06-16)

* Add `title` attribute to [DOCS] and [SOURCE] link to display the object id.
* Add `hasattr` for `_ast.Str` because Python 3.8 does not provide the attribute.

## Version 1.0.0 (2020-06-15)

### Additions to Version 1.0.0

* Add support for NumPy docstring style ([#1](https://github.com/daizutabi/mkapi/issues/1)).
* Document only a specific method from a class ([#5](https://github.com/daizutabi/mkapi/issues/5)).
* Add support for magic/dunder methods ([#7](https://github.com/daizutabi/mkapi/issues/7)).
* Include methods defined in different file ([#9](https://github.com/daizutabi/mkapi/issues/9)).
* Display inheritance of class ([#10](https://github.com/daizutabi/mkapi/issues/10)).
* Add `on_config` option to allow users to run custom script ([#11](https://github.com/daizutabi/mkapi/issues/11)).
