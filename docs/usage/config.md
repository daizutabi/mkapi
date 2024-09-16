# Configuration for MkAPI

Customize the behavior of the MkAPI plugin with the
configuration settings outlined below.
<!-- This guide will help you tailor the plugin to
meet your specific documentation needs. -->

## Excluding Modules

You can exclude the generation of documentation for
specific modules using the plugin's `exclude` setting.
This feature is particularly useful for omitting
test modules, unnecessary components, or large modules
that may clutter your documentation.

```yaml title="mkdocs.yml"
plugins:
  - mkapi:
      exclude:
        - package.module_to_exclude
```

In the example above, the `package.module_to_exclude` module
is excluded from the documentation generation.

The `exclude` setting supports the use of shell-style wildcards
for package/module names. For example, you can exclude all modules
starting with `test_` by using the pattern `package.subpackage.test_*`.

!!! note
    Module names starting with `_` are always excluded.

<!--

## Configuration script

You can further customize the plugin's behavior
using the `config` setting in your configuration file.
This allows you to define your own functions to enhance
the documentation process.

```yaml title="mkdocs.yml"
plugins:
  - mkapi:
      config: config.py
```

Ensure that the `config.py` script file is located
in the same directory as your `mkdocs.yml`, as shown below:

``` sh
.
├─ docs/
│  └─ index.md
├─ config.py
└─ mkdocs.yml
```

!!! Note
    - You can change the script name if needed.
    - If the config file is a module and importable,
      you can specify it as `config: modulename` without
      the `.py` extension.

Currently, five functions can be called from the MkAPI plugin.
You can define your own functions to customize plugin behaviors
or set navigation titles for sections, pages, and/or the table of contents.

### Function Overview

- **before_on_config**: This function is called before the `on_config` event of the MkAPI plugin, allowing you to set up your environment.
- **after_on_config**: This function is executed after the `on_config` event, enabling you to make final adjustments.
- **page_title**: Returns a user-friendly title for a page, enhancing navigation.
- **section_title**: Generates a clear title for a section, improving organization.
- **toc_title**: Creates a concise title for the table of contents.

By leveraging these functions, you can create a more tailored and user-friendly documentation experience with MkAPI.

The following is an example of `config.py`.

```python title="config.py"
"""Config functions."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig

    from mkapi.plugins import MkApiPlugin

def before_on_config(config: MkDocsConfig, plugin: MkApiPlugin) -> None:
    """Called before `on_config` event of MkAPI plugin."""

def after_on_config(config: MkDocsConfig, plugin: MkApiPlugin) -> None:
    """Called after `on_config` event of MkAPI plugin."""

def page_title(name: str, depth: int) -> str:
    """Return a page title."""
    return name

def section_title(name: str, depth: int) -> str:
    """Return a section title."""
    return name

def toc_title(name: str, depth: int) -> str:
    """Return a toc title."""
    return name.split(".")[-1]  # Remove prefix. Default behavior.
```

-->

## Features setting

MkAPI can be used with any MkDocs theme.
However, we suggest considering the
[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
theme as one of the options due to its exceptional
navigation features and user-friendly design.

Below are some settings that can enhance your
documentation experience if you choose to use
this theme:

<div class="annotate" markdown="1">

```yaml title="mkdocs.yml"
theme:
  name: material (1)
  features:
    - content.tooltips (2)
    - navigation.expand (3)
    - navigation.indexes (4)
    - navigation.sections (5)
    - navigation.tabs (6)
```

</div>

1. **Material theme**: Using the
[Material theme](https://squidfunk.github.io/mkdocs-material/getting-started/)
provides a sleek and modern interface for your documentation.

2. **Improved tooltips**: With the `content.tooltips` feature, MkAPI displays object
full names as tooltips, enhancing user experience by providing
additional context without cluttering the interface. See
[Improved tooltips](https://squidfunk.github.io/mkdocs-material/reference/tooltips/?h=too#improved-tooltips)
for more information.

3. **Navigation expansion**: The `navigation.expand` feature automatically
expands subpackages or submodules, making it easier for users to
navigate through your documentation. Learn more about
[Navigation expansion](https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/?h=navigation#navigation-expansion).

4. **Section index pages**: The `navigation.indexes` feature allows package
sections to have their own summary or overview pages, providing a
clearer structure. Check out
[Section index pages](https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/?h=navigation#section-index-pages)
for details.

5. **Navigation sections**: With the `navigation.sections` feature,
packages are rendered as groups in the sidebar, improving
organization and accessibility. More information can be found in
[Navigation sections](https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/?h=navigation#navigation-sections).

6. **Navigation tabs**: The `navigation.tabs` feature allows the API
section to be placed in a menu layer, making it easily accessible.
Discover more about
[Navigation tabs](https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/?h=navigation#navigation-tabs).

By considering these features, you can create a more intuitive
and visually appealing documentation experience that encourages
users to explore and utilize your library effectively.

!!! warning "Instant loading"
    Enabling the `navigation.instant` feature will cause links to source
    pages to function improperly, and the **[-]**/**[+]** buttons will
    be disabled.
