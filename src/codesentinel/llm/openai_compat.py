import os
import requests
import json
from typing import Type, TypeVar, Optional
from pydantic import BaseModel
from .base import LLMProvider
from codesentinel.observability.metrics import (
    LLM_REQUESTS_TOTAL, LLM_TOKENS_TOTAL, LLM_COST_DOLLARS_TOTAL
)

T = TypeVar('T', bound=BaseModel)

class OpenAICompatProvider(LLMProvider):
    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        fallback_model: Optional[str] = None
    ):
        cfg = None
        try:
            from codesentinel.config import load_config
            cfg = load_config()
        except Exception:
            pass

        self.model = model or os.environ.get('MODEL') or (cfg.model if cfg else 'qwen/qwen3.8-27b')
        self.fallback_model = fallback_model or os.environ.get('FALLBACK_MODEL') or (cfg.fallback_model if cfg else 'openai/gpt-oss-120b')
        self.api_key = api_key or os.environ.get('API_KEY') or (cfg.api_key if cfg else None)
        self.base_url = base_url or os.environ.get('BASE_URL') or (cfg.base_url if cfg else 'https://api.openai.com/v1')
        if not self.base_url:
            self.base_url = 'https://api.openai.com/v1'
        if not self.api_key:
            raise ValueError('API_KEY must be set.')
            
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
        
        # Token and cost tracking
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.total_cost_usd = 0.0

    def generate(self, system_prompt: str, user_prompt: str, schema: Type[T]) -> T:
        schema_json = json.dumps(schema.model_json_schema())
        messages = [
            {'role': 'system', 'content': f'{system_prompt}\n\nYou must respond ONLY with valid JSON matching this schema: {schema_json}'},
            {'role': 'user', 'content': user_prompt}
        ]
        
        payload = {
            'model': self.model,
            'messages': messages,
            'response_format': {'type': 'json_object'}
        }
        
        url = f'{self.base_url.rstrip("/")}/chat/completions'
        active_model = self.model
        resp = self.session.post(url, json=payload)

        # Check for 429 or 5xx to fall back to fallback_model
        status_code = getattr(resp, "status_code", 200)
        if isinstance(status_code, int) and (status_code == 429 or (500 <= status_code < 600)):
            if self.fallback_model and self.fallback_model != self.model:
                print(f"Warning: Primary model {self.model} returned HTTP {status_code}. Falling back to {self.fallback_model}...")
                active_model = self.fallback_model
                payload['model'] = active_model
                resp = self.session.post(url, json=payload)

        if not resp.ok:
            print(f'API Error: {resp.status_code} {resp.text}')
            try:
                LLM_REQUESTS_TOTAL.labels(model=active_model, status="error").inc()
            except Exception:
                pass
            resp.raise_for_status()

        data = resp.json()
        content = data['choices'][0]['message']['content']

        # Track token usage and costs
        usage = data.get('usage', {}) if isinstance(data, dict) else {}
        prompt_tokens = usage.get('prompt_tokens', len(system_prompt + user_prompt) // 4)
        completion_tokens = usage.get('completion_tokens', len(content) // 4)
        call_tokens = prompt_tokens + completion_tokens
        call_cost = (call_tokens / 1_000_000) * 0.50

        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_tokens += call_tokens
        self.total_cost_usd += call_cost

        try:
            LLM_REQUESTS_TOTAL.labels(model=active_model, status="success").inc()
            LLM_TOKENS_TOTAL.labels(model=active_model, direction="prompt").inc(prompt_tokens)
            LLM_TOKENS_TOTAL.labels(model=active_model, direction="completion").inc(completion_tokens)
            LLM_COST_DOLLARS_TOTAL.labels(model=active_model).inc(call_cost)
        except Exception:
            pass

        return schema.model_validate_json(content)
