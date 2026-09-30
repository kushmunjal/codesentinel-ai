import os
import requests
import json
from typing import Type, TypeVar
from pydantic import BaseModel, ValidationError
from .base import LLMProvider

T = TypeVar("T", bound=BaseModel)

class OpenAICompatProvider(LLMProvider):
    def __init__(self, model: str = None, api_key: str = None, base_url: str = None):
        self.model = model or os.environ.get("MODEL", "gpt-4")
        self.api_key = api_key or os.environ.get("API_KEY")
        self.base_url = base_url or os.environ.get("BASE_URL", "https://api.openai.com/v1")
        if not self.api_key:
            raise ValueError("API_KEY must be set.")
            
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })

    def generate(self, system_prompt: str, user_prompt: str, schema: Type[T]) -> T:
        # Ask the LLM to output JSON matching the schema schema.model_json_schema()
        # For simplicity, we just pass the schema in the prompt.
        schema_json = json.dumps(schema.model_json_schema())
        messages = [
            {"role": "system", "content": f"{system_prompt}\n\nYou must respond ONLY with valid JSON matching this schema: {schema_json}"},
            {"role": "user", "content": user_prompt}
        ]
        
        payload = {
            "model": self.model,
            "messages": messages,
            "response_format": {"type": "json_object"}
        }
        
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        resp = self.session.post(url, json=payload)
        resp.raise_for_status()
        
        content = resp.json()["choices"][0]["message"]["content"]
        return schema.model_validate_json(content)
