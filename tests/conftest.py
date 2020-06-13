import sys

import pytest

sys.path.insert(0, "examples")

import google_style as example  # isort:skip


@pytest.fixture(scope="session")
def module():
    return example


@pytest.fixture(scope="session")
def add():
    return example.add


@pytest.fixture(scope="session")
def gen():
    return example.gen


@pytest.fixture(scope="session")
def ExampleClass():
    return example.ExampleClass


@pytest.fixture(scope="session")
def ExampleDataClass():
    return example.ExampleDataClass
