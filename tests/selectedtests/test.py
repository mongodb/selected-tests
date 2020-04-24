import inject
import pytest


class Greeter:
    def greet(self, thing: str) -> str:
        return f'Hello, {thing}!'


@inject.autoparams()
def handle_with_greeter_1(thing: str, greeter: Greeter):
    return greeter.greet(thing)


@inject.autoparams("greeter")
def handle_with_greeter_2(thing: str, greeter: Greeter):
    return greeter.greet(thing)


@inject.autoparams()
def handle_with_greeter_3(greeter: Greeter, thing: str):
    return greeter.greet(thing)


@inject.autoparams("greeter")
def handle_with_greeter_4(greeter: Greeter, thing: str):
    return greeter.greet(thing)


@pytest.fixture()
def greeter():
    return Greeter()


@pytest.fixture(autouse=True)
def configure_inject(greeter):
    def dependencies(binder: inject.Binder):
        binder.bind(Greeter, greeter)

    inject.clear_and_configure(dependencies, bind_in_runtime=False)


def test_1():
    assert handle_with_greeter_1("World") == "Hello, World!"


def test_2():
    assert handle_with_greeter_2("World") == "Hello, World!"


def test_3():
    assert handle_with_greeter_3("World") == "Hello, World!"


def test_4():
    assert handle_with_greeter_4("World") == "Hello, World!"
