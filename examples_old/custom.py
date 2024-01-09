def on_config(config, mkapi):
    print("Called with config and mkapi.")
    return config


def page_title(modulename: str, depth: int, ispackage: bool) -> str:
    return ".".join(modulename.split(".")[depth:])


def section_title(package_name: str, depth: int) -> str:
    return ".".join(package_name.split(".")[depth:])
