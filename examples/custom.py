def on_config(config, mkapi):
    print("Called with config and mkapi.")
    return config


def page_title(module_name: str, depth: int, ispackage: bool) -> str:
    return ".".join(module_name.split(".")[depth:])


def section_title(package_name: str, depth: int) -> str:
    return ".".join(package_name.split(".")[depth:])
