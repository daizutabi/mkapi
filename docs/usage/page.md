# Page mode

```yaml
nav:
  - <api>/package
  - <api>/package.module
```

```yaml
nav:
  - Package: <api>/package.*
  - Module: <api>/package.module.**
```

```yaml
nav:
  - Package: <api>/package.***
```

- [Schemdraw](https://schemdraw.readthedocs.io/en/stable/)
  － Schemdraw is a Python package for producing high-quality
  electrical circuit schematic diagrams.
- [Polars](https://docs.pola.rs/)
  － Polars is a blazingly fast DataFrame library for manipulating
  structured data.
- [Altair](https://altair-viz.github.io/)
  － Vega-Altair is a declarative visualization library for Python.

```yaml
nav:
  - index.md
  - Usage:
    - usage/embed.md
    - usage/page.md
  - Examples: <api>/examples.**
  - Schemdraw: <api>/schemdraw.***
  - Polars: <api>/polars.***
  - Altair: <api>/altair.***
```

```yaml
plugins:
  - mkapi:
      config: config.py
      exclude:
        - altair.vegalite
```

```python
"""Config functions."""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig

    from mkapi.plugins import MkAPIPlugin


def before_on_config(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:
    """Called before `on_config` event of MkAPI plugin."""


def after_on_config(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:
    """Called after `on_config` event of MkAPI plugin."""


def page_title(name: str, depth: int) -> str:
    """Return a page title."""
    return name


def section_title(name: str, depth: int) -> str:
    """Return a section title."""
    return name


def toc_title(name: str, depth: int) -> str:
    """Return a toc title."""
    return name.split(".")[-1]  # Remove prefix.
```
