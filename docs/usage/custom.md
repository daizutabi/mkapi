# Customization

## Customization 'on_config'.

MkAPI has an option `on_config` to allow users to configure MkDocs/MkAPI or
user system environment. Here is an example directory structure and the corresponding `mkdocs.yml`:

~~~yml
# Directory structure
myproject:
  - docs:
    - index.md
  - examples:
    - custom.py
  - mkdocs.yml
~~~

~~~yml
# mkdocs.yml
plugins:
  - search
  - mkapi:
      src_dirs: [examples]
      on_config: custom.on_config
~~~

Customization script is defined in `examples/custom.py`:

#File examples/custom.py {%=/examples/custom.py%}

Let's build the documentation.

~~~bash
$ mkdocs build
INFO    -  [MkAPI] Calling user 'on_config' with []
Called.
INFO    -  Cleaning site directory
...
~~~

`on_config()` can take `config` and/or `mkapi` arguments.

~~~yml
# mkdocs.yml
plugins:
  - search
  - mkapi:
      src_dirs: [examples]
      on_config: custom.on_config_with_config
~~~

~~~bash
$ mkdocs build
INFO    -  [MkAPI] Calling user 'on_config' with ['config']
Called with config.
C:\Users\daizu\Documents\github\mkapi\docs
INFO    -  Cleaning site directory
...
~~~

~~~yml
# mkdocs.yml
plugins:
  - search
  - mkapi:
      src_dirs: [examples]
      on_config: custom.on_config_with_mkapi
~~~

~~~bash
$ mkdocs build
INFO    -  [MkAPI] Calling user 'on_config' with ['config', 'mkapi']
Called with config and mkapi.
C:\Users\daizu\Documents\github\mkapi\docs
<mkapi.plugins.mkdocs.MkapiPlugin object at 0x000001DF712D0F08>
INFO    -  Cleaning site directory
...
~~~
