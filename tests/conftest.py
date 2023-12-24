import pytest

import mkapi.examples.styles.google as example


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
def ExampleClass():  # noqa: N802
    return example.ExampleClass


@pytest.fixture(scope="session")
def ExampleDataClass():  # noqa: N802
    return example.ExampleDataClass
