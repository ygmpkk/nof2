"""Lightweight Pydantic AI inspired helpers for structured agent logic.

This module implements a very small subset of the public API provided by the
`pydantic-ai` project so that the trading agent can express its reasoning using
strongly typed models without requiring an internet connection to install the
real dependency.  Only the functionality that is needed by the tests is
implemented here.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Generic, Iterable, Optional, Type, TypeVar


class ValidationError(ValueError):
    """Raised when data cannot be converted into a model."""


T = TypeVar("T", bound="BaseModel")


class BaseModel:
    """Very small subset of Pydantic's ``BaseModel``.

    The implementation focuses on predictable, explicit data validation.  It
    supports required and optional annotated attributes as well as default
    values defined directly on the subclass.  The goal is to provide a typed
    structure for the trading agent's reasoning rather than replicating the
    full feature set of Pydantic.
    """

    __slots__ = ("__dict__",)

    def __init__(self, **data: Any) -> None:
        annotations = getattr(self.__class__, "__annotations__", {})
        values: Dict[str, Any] = {}

        for name, annotation in annotations.items():
            if name in data:
                values[name] = data.pop(name)
            elif hasattr(self.__class__, name):
                values[name] = getattr(self.__class__, name)
            else:
                raise ValidationError(f"Missing field '{name}' for {self.__class__.__name__}")

        # Allow optional extra data by storing it as attributes.  This mirrors
        # Pydantic's ability to keep ``extra`` fields when configured to do so.
        values.update(data)
        self.__dict__.update(values)

    @classmethod
    def model_validate(cls: Type[T], data: Any) -> T:
        if isinstance(data, cls):
            return data
        if not isinstance(data, dict):
            raise ValidationError(
                f"{cls.__name__} expects a mapping, received {type(data).__name__}"
            )
        return cls(**data)

    def model_dump(self) -> Dict[str, Any]:
        annotations = getattr(self.__class__, "__annotations__", {})
        return {name: getattr(self, name) for name in annotations}

    def __repr__(self) -> str:  # pragma: no cover - representation helper
        fields = ", ".join(f"{k}={v!r}" for k, v in self.model_dump().items())
        return f"{self.__class__.__name__}({fields})"


I = TypeVar("I", bound=BaseModel)
O = TypeVar("O", bound=BaseModel)


def ensure_model(model_type: Type[T], value: Any) -> T:
    """Convert ``value`` into ``model_type`` if required."""
    if isinstance(value, model_type):
        return value
    return model_type.model_validate(value)


class Tool(BaseModel):
    """Description of a callable tool for use with :class:`Agent`."""

    name: str
    description: str
    function: Callable[..., Any]


class Agent(Generic[I, O]):
    """Minimal structured agent implementation.

    The agent receives a callable ``planner`` that produces an output model from
    an input model.  The callable can perform deterministic logic (as done in
    this project) but the typed wrapper allows the calling code to remain close
    to the ergonomics offered by the real Pydantic AI library.
    """

    def __init__(
        self,
        *,
        name: str,
        input_model: Type[I],
        output_model: Type[O],
        planner: Callable[[I], O | Dict[str, Any]],
        tools: Optional[Iterable[Tool]] = None,
        description: str | None = None,
    ) -> None:
        self.name = name
        self.input_model = input_model
        self.output_model = output_model
        self.planner = planner
        self.tools = list(tools or [])
        self.description = description or ""

    def add_tool(self, tool: Tool) -> None:
        self.tools.append(tool)

    def run(self, data: I | Dict[str, Any]) -> O:
        """Execute the planner for the provided data."""
        input_obj = ensure_model(self.input_model, data)
        result = self.planner(input_obj)
        return ensure_model(self.output_model, result)


__all__ = [
    "Agent",
    "BaseModel",
    "Tool",
    "ValidationError",
]
