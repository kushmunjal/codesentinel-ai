from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Type, TypeVar

T = TypeVar("T", bound=BaseModel)

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, schema: Type[T]) -> T:
        """Generates a response matching the given Pydantic schema."""
        pass
