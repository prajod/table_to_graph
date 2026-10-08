from collections.abc import Callable
from typing import Generic, TypeVar

T = TypeVar("T")


class Registry(Generic[T]):
    """Type-safe component registry, independent of interface inheritance."""

    def __init__(self, name: str) -> None:
        self._name = name
        self._items: dict[str, type[T]] = {}

    def register(self, name: str, component: type[T]) -> None:
        """Register a component class under a specific name."""
        self._items[name] = component

    def get(self, name: str) -> type[T]:
        """Retrieve a registered component class by name."""
        if name not in self._items:
            available = ", ".join(self.available())
            raise KeyError(
                f"Component '{name}' not found in registry '{self._name}'. Available: {available}"
            )
        return self._items[name]

    def available(self) -> list[str]:
        """Get a list of all registered component names."""
        return list(self._items.keys())

    def has(self, name: str) -> bool:
        """Check if a component name is registered."""
        return name in self._items

    def decorator(self, name: str) -> Callable[[type[T]], type[T]]:
        """Class decorator for convenient component registration.

        Example:
            @extractor_registry.decorator("pdfplumber")
            class PdfPlumberExtractor:
                ...
        """

        def wrapper(cls: type[T]) -> type[T]:
            self.register(name, cls)
            return cls

        return wrapper


# Provide concrete type hints later when initialized,
# for now they are instantiated in __init__.py to prevent circular dependencies.
