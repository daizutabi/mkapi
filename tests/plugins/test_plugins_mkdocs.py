import os
import shutil
import subprocess
from pathlib import Path

import pytest
from mkdocs.config import load_config
from mkdocs.structure.files import get_files
from mkdocs.structure.nav import get_navigation

import mkapi


@pytest.fixture(scope="module")
def config_file():
    root = Path(mkapi.__file__).parent.parent
    config_file = root / "mkdocs.yml"
    return os.path.normpath(config_file)


@pytest.fixture(scope="module")
def config(config_file):
    config = load_config(config_file)
    plugin = config["plugins"]["mkapi"]
    return plugin.on_config(config)


@pytest.fixture(scope="module")
def plugin(config):
    return config["plugins"]["mkapi"]


@pytest.fixture(scope="module")
def env(config):
    return config["theme"].get_env()


@pytest.fixture(scope="module")
def files(config, plugin, env):
    files = get_files(config)
    files.add_files_from_theme(env, config)
    return plugin.on_files(files, config)


@pytest.fixture(scope="module")
def nav(config, files):
    return get_navigation(files, config)


def test_plugins_mkdocs_config_file(config_file):
    assert Path(config_file).exists()


def test_plugins_mkdocs_config(config):
    assert "mkapi" in config["plugins"]


def test_plugins_mkdocs_build():
    def run(command: str):
        args = command.split()
        assert subprocess.run(args, check=False).returncode == 0  # noqa: S603

    if Path("docs/api").exists():
        shutil.rmtree("docs/api")
    run("mkdocs build")
