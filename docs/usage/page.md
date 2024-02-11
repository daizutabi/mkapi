# Page mode

MkAPI provides Page mode to construct a comprehensive
API documentation for your Python project.

## Navigation setting

Use of the Page mode is very simple.
Just add a single line to `nav` section in `mkdocs.yml`:

```yaml title="mkdocs.yml"
nav:
  - index.md  # normal page.
  - $api/package.module  # MkAPI page with a special syntax.
```

Here, a leading `$` is a marker to indicate that
this page should be processed by MkAPI to generate API
documentation.
A text between the leading `$` and the last `/`
is used as a name of API directory
as well as the prefix of URI.
In this case, MkAPI creates a new API directory `api`
in a `docs` directory.
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
    - You can change the name `api` as long as it is a valid
      directory name and it does not exist.
    - A `src` directory is also created to locate source codes.
      The name `src` is configured by the plugin setting.
      See [Configuration](config.md).
    - Both `api` and `src` directories will be removed after
      building documentation by MkDocs.

In the above example, just one `api/package/module.md` file
will be created.
In order to obtain a collection of subpackages/submodules,
you can use `*` symbols.
Consider next directory structure:

```sh
package/
├─ subpackage1/
│  ├─ __init__.py
│  ├─ module_11.py
│  └─ module_12.py
├─ subpackage2/
│  ├─ __init__.py
│  ├─ module_21.py
│  └─ module_22.py
├─ __init__.py
├─ module1.py
└─ module2.py
```

There are three ways to collect modules:

=== "package.*"

    - Modules under a `package` directory are collected.
    - The `nav` section is extended *vertically*.

    Example:

    ```yaml
    nav:
      - index.md
      - $api/package.*
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

=== "package.**"

    - Modules under a `package` directory and its
    subdirectories are collected, recursively.
    - The `nav` section is extended *vertically*
    in flat structure.
    - Optionally, a section title can be set, for example, `API`.

    Example:

    ```yaml
    nav:
      - index.md
      - API: $api/package.**
      - other.md
    ```

    will be converted into

    ```yaml
    nav:
      - index.md
      - API:
        - package: api/package/README.md
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

=== "package.***"

    - Modules under a `package` directory and its
    subdirectories are collected, recursively.
    - The `nav` section is extended to have the same tree structure as the package.
    - Optionally, a top section title can be set, for example, `API`.

    Example:

    ```yaml
    nav:
      - index.md
      - API: $api/package.***
      - other.md
    ```

    will be converted into

    ```yaml
    nav:
      - index.md
      - API:
        - package: api/package/README.md
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
    - `README.md` is an index page for packages. It corresponds to `__init__.py`.
    - Section and page titles can be configured programatically.
      See [Configuration](config.md).

## Example API documentations

To demonstrate the Page mode, try some libraries.
For example, MkAPI is tested using following libraries:

- [Schemdraw](https://schemdraw.readthedocs.io/en/stable/)
  － "Schemdraw is a Python package for producing high-quality
  electrical circuit schematic diagrams."
- [Polars](https://docs.pola.rs/)
  － "Polars is a blazingly fast DataFrame library for manipulating
  structured data."
- [Altair](https://altair-viz.github.io/)
  － "Vega-Altair is a declarative visualization library for Python."

Use the following `nav` section in your `mkdocs.yml`
if you want to check the output of MkAPI.

```yaml title="mkdocs.yml"
nav:
  - index.md
  - API: $api/mkapi.**  # API documentation of MkAPI itself
  - Schemdraw: $api/schemdraw.***
  - Polars: $api/polars.***
  - Altair: $api/altair.***
```

<!-- Click section tabs at the top bar or buttons below to see the API documentation.

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
</div> -->
