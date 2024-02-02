def on_config(config, mkapi):
    return config


def page_title(name: str, depth: int) -> str:
    return name
    # return ".".join(module_name.split(".")[depth:])


def section_title(name: str, depth: int) -> str:
    return name
    # return ".".join(package_name.split(".")[depth:])
