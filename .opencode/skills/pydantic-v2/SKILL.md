---
name: pydantic-v2
description: Pydantic V2 patterns for UIF - frozen models, validators, and type hints
---

## Use this when

- Creating Pydantic models for data validation
- Designing schemas for SQLite persistence
- Building APIs with type-safe request/response models

## MANDATORY: Frozen Models

All models MUST be immutable:

```python
from pydantic import BaseModel, Field, HttpUrl


class ScrapingResult(BaseModel):
    """Esquema inmutable para resultados de extracción."""
    model_config = {"frozen": True}

    url: HttpUrl
    content_md: str
    metadata: dict[str, str] = Field(default_factory=dict)
```

## Field Validators

```python
from pydantic import BaseModel, field_validator


class UrlConfig(BaseModel):
    model_config = {"frozen": True}

    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v
```

## Type Hints (Python 3.12+)

```python
# CORRECT - Modern type hints
class MyModel(BaseModel):
    items: list[str]
    mapping: dict[str, int]
    optional: str | None = None

# INCORRECT - Legacy type hints
class MyModel(BaseModel):
    items: List[str]  # Don't use typing.List
    mapping: Dict[str, int]  # Don't use typing.Dict
```

## Model Config Options

```python
class Config(BaseModel):
    model_config = {
        "frozen": True,  # Immutability
        "str_strip_whitespace": True,  # Auto-strip strings
        "validate_assignment": True,  # Validate on attribute set
    }
```

## Common Patterns

### URL with HttpUrl
```python
from pydantic import HttpUrl

url: HttpUrl  # Validates URL format
```

### Path sanitization
```python
from slugify import slugify

safe_path = f"data/{slugify(domain)}/{slugify(filename)}.jsonl"
```

### JSON serialization
```python
model.model_dump()  # dict
model.model_dump_json()  # JSON string
```
