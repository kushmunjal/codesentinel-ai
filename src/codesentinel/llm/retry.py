import time
from typing import Callable, Type, TypeVar
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

def generate_with_retry(
    provider_generate_func: Callable[..., T],
    system_prompt: str,
    user_prompt: str,
    schema: Type[T],
    max_retries: int = 3
) -> T:
    """Wrapper that retries on ValidationError or transient failures with exponential backoff."""
    attempt = 0
    last_exception = None
    
    while attempt < max_retries:
        try:
            return provider_generate_func(system_prompt, user_prompt, schema)
        except ValidationError as e:
            last_exception = e
            # On validation error, append the error to the prompt to ask the LLM to fix it
            user_prompt += f"\n\nYour previous JSON failed validation. Error: {e.errors()}\nPlease fix the JSON and try again."
        except Exception as e:
            last_exception = e
            time.sleep(2 ** attempt)
        attempt += 1
        
    raise RuntimeError(f"Failed to generate valid output after {max_retries} attempts. Last error: {last_exception}")
