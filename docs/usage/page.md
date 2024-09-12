# Page mode

Unlock the full potential of your Python project with MkAPI's Page mode,
designed to create comprehensive and user-friendly API documentation.

## Simple navigation setup

Getting started with Page mode is a breeze!
Just add a single line to the `nav` section of your `mkdocs.yml` file:

```yaml title="mkdocs.yml"
nav:
  - index.md  # normal page.
  - $api/package.module  # MkAPI page with a special syntax.
```

The leading `$` acts as a marker, indicating that this page should be
processed by MkAPI to generate dynamic API documentation.
The text between the `$` and the last `/` specifies
the name of the API path and serves as the URI prefix.
Module pages will be organized under this path seamlessly.

In the example above, only one `api/package/module.md` file
for documentation and one `src/package/module.md` file
for source code will be created.
To gather a collection of subpackages or submodules,
you can use the `*` symbol.
Consider the following directory structure:

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

There are three effective ways to collect modules:

=== "package.*"

    - Collects all modules under the `package` directory.
    - The `nav` section is extended *vertically*.

    Example:

    ```yaml
    nav:
      - index.md
      - $api/package.*
      - other.md
    ```

    This will be transformed into:

    ```yaml
    nav:
      - index.md
      - package: api/package/README.md
      - module_1: api/package/module_1.md
      - module_2: api/package/module_2.md
      - other.md
    ```

=== "package.**"

    - Collects modules under the `package` directory and
      its subdirectories recursively.
    - The `nav` section is extended *vertically* in a flat structure.
    - Optionally, you can set a section title, such as `API`.


    Example:

    ```yaml
    nav:
      - index.md
      - API: $api/package.**
      - other.md
    ```

    This will be transformed into:

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

    - Collects modules under the `package` directory and
      its subdirectories recursively.
    - The `nav` section is extended to maintain the same
      tree structure as the package.
    - Optionally, you can set a top section title, such as `API`.


    Example:

    ```yaml
    nav:
      - index.md
      - API: $api/package.***
      - other.md
    ```

    This will be transformed into:

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
    - `README.md` serves as an index page for packages,
      corresponding to `__init__.py`.
    - Section and page titles can be configured programmatically.
      See [Configuration](config.md).
