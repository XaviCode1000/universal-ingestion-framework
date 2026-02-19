---
name: python-strict
description: Skill para validación estricta de código Python 3.12+ con type hints modernos, mypy --strict y mejores prácticas de tipado.
---

# PYTHON-STRICT: Validación Estricta de Python 3.12+

> Skill especializado en garantizar código Python con tipado estricto y validación mypy --strict.

## Disparadores (Triggers)

- Cuando se escribe código Python
- Cuando se solicita validación de tipos
- Cuando se mencionan: mypy, type hints, typing, validación
- Antes de commits de código Python

---

## TYPE HINTS PYTHON 3.12+

### Sintaxis Moderna (Obligatoria)
```python
# ✅ CORRECTO - Python 3.12+
def process(
    items: list[str],
    mapping: dict[str, int],
    unique: set[str],
    pairs: tuple[str, int],
) -> str | None:
    ...

# ❌ INCORRECTO - Legacy
from typing import List, Dict, Set, Tuple, Optional

def process(
    items: List[str],
    mapping: Dict[str, int],
    unique: Set[str],
    pairs: Tuple[str, int],
) -> Optional[str]:
    ...
```

### Union Types
```python
# ✅ CORRECTO - Python 3.10+
def parse(value: str | int | None) -> float:
    ...

# ❌ INCORRECTO
from typing import Union, Optional

def parse(value: Union[str, int, None]) -> Optional[float]:
    ...
```

### Generic Types
```python
from typing import TypeVar, Generic

T = TypeVar("T")

class Container(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value

    def get(self) -> T:
        return self.value
```

### Protocol (Structural Subtyping)
```python
from typing import Protocol


class Drawable(Protocol):
    def draw(self) -> None: ...


def render(obj: Drawable) -> None:
    obj.draw()
```

---

## MYPY -- STRICT COMPLIANCE

### Reglas Obligatorias

1. **Todos los argumentos tipados**
```python
# ✅ CORRECTO
def calculate(a: int, b: int) -> int:
    return a + b

# ❌ INCORRECTO
def calculate(a, b):  # Missing type hints
    return a + b
```

2. **Retorno explícito**
```python
# ✅ CORRECTO
def greet(name: str) -> str:
    return f"Hola, {name}"

def log(message: str) -> None:
    print(message)

# ❌ INCORRECTO
def greet(name: str):  # Missing return type
    return f"Hola, {name}"
```

3. **Never para funciones que no retornan**
```python
from typing import Never


def raise_error(message: str) -> Never:
    raise ValueError(message)
```

4. **override para métodos sobrescritos**
```python
from typing import override


class Child(Parent):
    @override
    def method(self) -> str:
        return "overridden"
```

---

## PATRONES DE TIPIADO

### Callable
```python
from collections.abc import Callable


def apply(
    func: Callable[[int, int], int],
    a: int,
    b: int,
) -> int:
    return func(a, b)
```

### Iterator / Generator
```python
from collections.abc import Iterator, Generator


def iterate(items: list[str]) -> Iterator[str]:
    return iter(items)


def generate(n: int) -> Generator[int, None, None]:
    for i in range(n):
        yield i
```

### TypeGuard
```python
from typing import TypeGuard, Any


def is_string_list(value: list[Any]) -> TypeGuard[list[str]]:
    return all(isinstance(x, str) for x in value)
```

### Self Type
```python
from typing import Self


class Builder:
    def __init__(self) -> None:
        self._value: int = 0

    def set_value(self, value: int) -> Self:
        self._value = value
        return self
```

---

## VALIDACIONES COMUNES

### Pydantic Models
```python
from pydantic import BaseModel, Field, HttpUrl, field_validator


class User(BaseModel):
    model_config = {"frozen": True}

    name: str
    email: str
    age: int = Field(ge=0, le=150)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("Invalid email")
        return v
```

### Async Functions
```python
from collections.abc import Coroutine
from typing import Any


async def fetch(url: str) -> str:
    ...


async def run_tasks(
    tasks: list[Coroutine[Any, Any, str]],
) -> list[str]:
    ...
```

---

## COMANDOS DE VALIDACIÓN

```bash
# Validación estricta
uv run mypy --strict src/

# Validación con reportes
uv run mypy --strict --html-report mypy-report src/

# Validación incremental
uv run mypy --strict --incremental src/

# Verificar solo errores
uv run mypy --strict --no-error-summary src/ 2>&1 | grep "error:"
```

---

## ERRORES COMUNES Y SOLUCIONES

### error: Incompatible return value type
```python
# ❌ INCORRECTO
def get_value() -> int:
    return "string"  # Error!

# ✅ CORRECTO
def get_value() -> int:
    return 42
```

### error: Argument missing
```python
# ❌ INCORRECTO
def process(data: dict[str, Any]) -> None:
    value = data["key"]  # Could be missing

# ✅ CORRECTO
def process(data: dict[str, Any]) -> None:
    value = data.get("key")
    if value is None:
        return
```

### error: Need type annotation
```python
# ❌ INCORRECTO
items = []  # Error!

# ✅ CORRECTO
items: list[str] = []
```

---

## CHECKLIST MYPY STRICT

- [ ] Todos los argumentos tienen type hints
- [ ] Todos los retornos tienen type hints
- [ ] Uso de `|` en lugar de `Union`
- [ ] Uso de `list[]`, `dict[]`, `set[]` nativos
- [ ] `None` explícito en funciones sin retorno
- [ ] `@override` en métodos sobrescritos
- [ ] `Never` para funciones que lanzan excepciones
- [ ] Variables inicializadas con tipo explícito si es necesario
