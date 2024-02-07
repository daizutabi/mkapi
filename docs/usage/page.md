# Page mode

MkAPI provides Page mode to construct a comprehensive
API documentation for your project.

## Navigation setting

The use of Page mode is very simple.
Just add a single line to `nav` section in `mkdocs.yml`

```yaml
nav:
  - index.md  # normal page.
  - <api>/package.module  # MkAPI page with a special syntax.
```

Here, a __bracket__ (`<...>`) is a marker to indicate that
this page should be processed by MkAPI to generate API
documentation.
The text in the bracket is used as a name of API directory.
In this case, a new API directory `api` is created
in the `docs` directory by MkAPI.
Module page(s) will be located under this directory automatically:

``` sh
.
├─ docs/
│  ├─ api/
│  │  └─ package
│  │     └─ module.md
│  ├─ src/
│  └─ index.md
└─ mkdocs.yml
```

!!! note
    - You can change the name `api` as long as it is a valid URI or
      directory name and it does not exist.
    - A `src` directory is also created to locate source codes.
      The name `src` is configured by the plugin setting.
      See [Configuration](config.md).

In the above example, just one `pakcge.module` page is created.
In order to obtain a collection of subpackages/submodules,
you can use `*` symbols.
There are three ways:

=== "1. package.*"

    - Modules under `package` directory are collected.
    - `nav` section is extended *vertically*.

    ```yaml
    nav:
      - index.md
      - <api>/package.*
      - other.md
    ```

    will be converted into

    ```yaml
    nav:
      - index.md
      - package: api/package/README.md
      - module_1: api/package/module_1.md
      - module_2: api/package/module_2.md
      - other.md
    ```

=== "2. package.**"

    - Modules under `package` directory and its
    subdirectories are collected, recursively.
    - `nav` section is extended *vertically*
    in flat structure.

    ```yaml
    nav:
      - index.md
      - <api>/package.**
      - other.md
    ```

    will be converted into

    ```yaml
    nav:
      - index.md
      - package: api/package/READ.md
      - subpackage_1: api/package/subpackage_1/README.md
      - module_11: api/package/subpackage_1/module_11.md
      - module_21: api/package/subpackage_1/module_12.md
      - subpackage_2: api/package/subpackage_2/README.md
      - module_21: api/package/subpackage_2/module_21.md
      - module_22: api/package/subpackage_2/module_22.md
      - module_1: api/package/module_1.md
      - module_2: api/package/module_2.md
      - other.md
    ```

=== "3. package.***"

    - Modules under `package` directory and its
    subdirectories are collected, recursively.
    - `nav` section is extended to have the same tree structure as the package.
    - The top section title can be set, for example, `API`.

    ```yaml
    nav:
      - index.md
      - API: <api>/package.**
      - other.md
    ```

    will be converted into

    ```yaml
    nav:
      - index.md
      - API:
        - package: api/package/READ.md
          - subpackage_1:
            - subpackage_1: api/package/subpackage_1/README.md
            - module_11: api/package/subpackage_1/module_11.md
            - module_12: api/package/subpackage_1/module_12.md
          - subpackage_2:
            - subpackage_2: api/package/subpackage_2/README.md
            - module_21: api/package/subpackage_2/module_21.md
            - module_22: api/package/subpackage_2/module_22.md
        - module_1: api/package/module_1.md
        - module_2: api/package/module_2.md
      - other.md
    ```

!!! note
    - `README.md` is a index page for packages. Actually it corresponds to `__init__.py`
    - Section and page titles can be configured programatically.
      See [Configuration](config.md).
    - You can set the top setion title as
      `<section>`: `<api>/package.[***]` like the last case.

## Example API pages

To demonstrate the Page mode. This MkAPI documentation ships with
some libraries reference:

- [Schemdraw](https://schemdraw.readthedocs.io/en/stable/)
  － Schemdraw is a Python package for producing high-quality
  electrical circuit schematic diagrams.
- [Polars](https://docs.pola.rs/)
  － Polars is a blazingly fast DataFrame library for manipulating
  structured data.
- [Altair](https://altair-viz.github.io/)
  － Vega-Altair is a declarative visualization library for Python.

Click section tabs at the top bar or buttons below to see the API documentation.

<style type="text/css">
.mkapi-center {
  display: flex;
  justify-content: center;
}
</style>

<div class="mkapi-center" markdown="1">
[Schemdraw][schemdraw]{.md-button .md-button--primary}
[Polars][polars]{.md-button .md-button--primary}
[Altair][altair]{.md-button .md-button--primary}
</div>

__Note that MkAPI processed the docstrings of
these libraries without any modification.__

Here is the actual `nav` section in `mkdocs.yml` of this documentation.
Use this to reproduce the similar navigation structure for your project if you like.

```yaml
nav:
  - index.md
  - Usage:  # Actual MkAPI documentation
    - usage/object.md
    - usage/page.md
    - usage/config.md
  - Examples: <api>/examples.**  # for Object mode description
  - Schemdraw: <api>/schemdraw.***  # for Page mode demonstration
  - Polars: <api>/polars.***  # for Page mode demonstration
  - Altair: <api>/altair.***  # for Page mode demonstration
```
