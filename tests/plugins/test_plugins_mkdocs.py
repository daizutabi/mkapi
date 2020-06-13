import os
import shutil
import subprocess

import pytest
from mkdocs.config import load_config
from mkdocs.structure.files import get_files
from mkdocs.structure.nav import get_navigation

import mkapi


@pytest.fixture(scope="module")
def config_file():
    root = os.path.join(mkapi.__file__, "../..")
    config_file = os.path.join(root, "mkdocs.yml")
    config_file = os.path.normpath(config_file)
    return config_file


@pytest.fixture(scope="module")
def config(config_file):
    config = load_config(config_file)
    plugin = config["plugins"]["mkapi"]
    config = plugin.on_config(config)
    return config


@pytest.fixture(scope="module")
def plugin(config):
    plugin = config["plugins"]["mkapi"]
    return plugin


@pytest.fixture(scope="module")
def env(config):
    env = config["theme"].get_env()
    return env


@pytest.fixture(scope="module")
def files(config, plugin, env):
    files = get_files(config)
    files.add_files_from_theme(env, config)
    files = plugin.on_files(files, config)
    return files


@pytest.fixture(scope="module")
def nav(config, plugin, files):
    nav = get_navigation(files, config)
    return nav


def test_plugins_mkdocs_config_file(config_file):
    assert os.path.exists(config_file)


def test_plugins_mkdocs_config(config):
    assert "mkapi" in config["plugins"]


def test_plugins_mkdocs_build():
    def run(command):
        assert subprocess.run(command.split()).returncode == 0

    if os.path.exists('docs/api'):
        shutil.rmtree('docs/api')
    run("mkdocs build")
