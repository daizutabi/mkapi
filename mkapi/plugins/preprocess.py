import os
import shutil


def collect(top):
    base = os.path.basename(top)
    for root, dirs, files in os.walk(top):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                middle = root[len(top) :].replace("/", ".").replace("\\", ".")
                yield ".".join([base + middle, file[:-3]])
        for x in dirs:
            if x.startswith("__"):
                dirs.remove(x)


def make_pages(root: str, api_dir: str):
    if os.path.exists(api_dir):
        shutil.rmtree(api_dir)
    os.mkdir(api_dir)
    api_base = os.path.basename(api_dir)
    nav = []
    for module in collect(root):
        markdown = f"[mkapi]({module})\n"
        path = os.path.join(api_dir, module + ".md")
        with open(path, "w") as f:
            f.write(markdown)
        nav.append({module: "/".join([api_base, module + ".md"])})
    return nav
