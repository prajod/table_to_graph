import pytest

from table_to_graph.registry import Registry


class DummyComponent:
    pass


class AnotherComponent:
    pass


def test_registry_register_and_get():
    reg = Registry[type]("test")
    reg.register("dummy", DummyComponent)
    assert reg.get("dummy") == DummyComponent


def test_registry_get_missing():
    reg = Registry[type]("test")
    with pytest.raises(KeyError, match="not found in registry 'test'"):
        reg.get("missing")


def test_registry_available():
    reg = Registry[type]("test")
    reg.register("a", DummyComponent)
    reg.register("b", AnotherComponent)
    assert sorted(reg.available()) == ["a", "b"]


def test_registry_has():
    reg = Registry[type]("test")
    reg.register("dummy", DummyComponent)
    assert reg.has("dummy") is True
    assert reg.has("missing") is False


def test_registry_decorator():
    reg = Registry[type]("test")

    @reg.decorator("decorated")
    class DecoratedComponent:
        pass

    assert reg.get("decorated") == DecoratedComponent


def test_registry_type_safety():
    # This is mostly for mypy, but we can verify at runtime it holds instances
    class Base:
        pass

    class Sub1(Base):
        pass

    reg = Registry[Base]("typed")
    reg.register("sub", Sub1)
    assert issubclass(reg.get("sub"), Base)
