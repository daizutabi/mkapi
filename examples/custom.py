def on_config(config, mkapi):
    return config


def page_title(name: str, depth: int) -> str:
    return f"{name}-p{depth}"
    # return ".".join(module_name.split(".")[depth:])


def section_title(name: str, depth: int) -> str:
    return f"{name}-s{depth}"
    # return ".".join(package_name.split(".")[depth:])
