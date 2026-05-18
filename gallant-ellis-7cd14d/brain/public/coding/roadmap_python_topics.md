# Python Roadmap — Topic Index + Quick Reference

> Sumber: roadmap.sh/python (CC BY-SA 4.0)
> Referensi: https://roadmap.sh/python

## Python Fundamentals

### Data Types
```python
# Numeric
i = 42              # int (arbitrary precision)
f = 3.14            # float (64-bit)
c = 1 + 2j          # complex
n = 9999999999999999999  # int (no overflow)

# Text
s = "hello"         # str (immutable sequence of Unicode chars)
s = 'hello'         # single or double quotes
s = """multi
line"""              # triple-quoted
s = r"raw\nstring"  # raw string (backslash not escape)
s = f"name={name}"  # f-string (Python 3.6+)
s = b"bytes"        # bytes literal

# Boolean
True, False         # note: capital
bool(0) == False
bool([]) == False
bool("") == False
bool(None) == False

# None
x = None            # null/none value
x is None           # use 'is', not ==

# Type conversion
int("42")       # 42
float("3.14")   # 3.14
str(42)         # "42"
list("hello")   # ['h', 'e', 'l', 'l', 'o']
tuple([1, 2])   # (1, 2)
set([1, 1, 2])  # {1, 2}
```

### Strings
```python
s = "Hello, World!"

# Methods
s.upper()           # "HELLO, WORLD!"
s.lower()           # "hello, world!"
s.strip()           # remove leading/trailing whitespace
s.lstrip()          # left only
s.rstrip()          # right only
s.split(",")        # ['Hello', ' World!']
s.split(",", 1)     # ['Hello', ' World!'] (max 1 split)
",".join(["a", "b", "c"])  # "a,b,c"
s.replace("World", "SIDIX")
s.startswith("Hello")
s.endswith("!")
s.find("World")     # 7 (-1 if not found)
s.index("World")    # 7 (raises ValueError if not found)
s.count("l")        # 3
s.format(name="Fahmi")
"hello".center(11, "-")  # "---hello---"

# f-strings (most modern)
name = "Fahmi"
score = 95.7
f"Name: {name!r}"        # repr()
f"Score: {score:.2f}"    # 2 decimal places
f"Hex: {255:#010x}"      # 0x000000ff
f"List: {[1,2,3]!s}"     # str()

# String formatting (older)
"{} {}".format("hello", "world")
"%(name)s" % {"name": "Fahmi"}

# Slicing
s = "Hello"
s[1:3]    # "el"
s[:3]     # "Hel"
s[3:]     # "lo"
s[-2:]    # "lo"
s[::-1]   # "olleH" (reverse)
s[::2]    # "Hlo" (every 2nd char)
```

### Collections
```python
# List (mutable, ordered)
lst = [1, 2, 3, 4, 5]
lst.append(6)           # [1, 2, 3, 4, 5, 6]
lst.insert(0, 0)        # insert at index
lst.extend([7, 8])      # add multiple
lst.remove(3)           # remove first occurrence of value
lst.pop()               # remove and return last
lst.pop(1)              # remove and return at index
lst.sort()              # sort in-place
lst.sort(key=lambda x: -x)  # sort by key
lst.sort(reverse=True)
sorted(lst)             # returns new sorted list
lst.reverse()           # reverse in-place
lst.index(4)            # index of value
lst.count(2)            # count occurrences
lst.copy()              # shallow copy
lst.clear()             # empty list

# Comprehensions
squares = [x**2 for x in range(10)]
evens = [x for x in range(20) if x % 2 == 0]
flat = [x for row in matrix for x in row]

# Tuple (immutable, ordered)
t = (1, 2, 3)
t = 1, 2, 3          # parentheses optional
t = (1,)             # single-element tuple (note comma!)
a, b, c = t          # unpacking
a, *rest = t         # star unpacking: a=1, rest=[2,3]

# Set (mutable, unordered, unique)
s = {1, 2, 3}
s.add(4)
s.remove(2)          # raises KeyError if not found
s.discard(99)        # no error if not found
s.union({3, 4, 5})   # {1, 2, 3, 4, 5} — or s | other
s.intersection({2, 3})  # {2, 3} — or s & other
s.difference({2})    # {1, 3} — or s - other
s.symmetric_difference({2, 4})  # {1, 3, 4}
frozenset([1, 2])    # immutable set

# Dict (mutable, ordered since Python 3.7)
d = {"key": "value", "n": 42}
d["key"]             # access (KeyError if missing)
d.get("key")         # None if missing
d.get("key", "default")
d["new"] = "val"     # add/update
del d["key"]
d.pop("key")         # remove and return
d.pop("key", None)   # no error if missing
d.keys()             # dict_keys
d.values()           # dict_values
d.items()            # dict_items — (key, value) pairs
d.update({"a": 1})   # merge (updates existing)
{**d1, **d2}         # merge (Python 3.9+: d1 | d2)
d.setdefault("key", []).append(1)  # initialize if missing
d.copy()             # shallow copy

# defaultdict, Counter
from collections import defaultdict, Counter
dd = defaultdict(list)
dd["key"].append(1)   # no KeyError on missing key

counter = Counter("abracadabra")
counter.most_common(3)  # [('a', 5), ('b', 2), ('r', 2)]
counter["a"]            # 5

# Dict comprehension
{k: v**2 for k, v in items.items() if v > 0}
```

## Functions

```python
# Parameters
def func(pos, /, normal, *, kw_only):
    """/ means pos is positional-only; * means kw_only is keyword-only"""
    pass

def func(a, b, *args, **kwargs):
    print(a, b)             # positional
    print(args)             # tuple of extra positionals
    print(kwargs)           # dict of extra keyword args

func(1, 2, 3, 4, x=5, y=6)  # a=1 b=2 args=(3,4) kwargs={'x':5,'y':6}

# Unpacking in call
args = (1, 2)
kwargs = {"c": 3}
func(*args, **kwargs)

# Type hints (PEP 484, 526)
def greet(name: str, times: int = 1) -> str:
    return f"Hello, {name}! " * times

from typing import Optional, Union, List, Dict, Tuple, Any, Callable
def process(
    items: list[str],
    callback: Callable[[str], None],
    limit: int | None = None,   # Python 3.10+ union syntax
) -> dict[str, int]:
    ...

# Decorators
import functools
import time

def timer(func):
    @functools.wraps(func)   # preserves docstring, name
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} took {end-start:.4f}s")
        return result
    return wrapper

@timer
def slow_function():
    time.sleep(1)

# Decorator with arguments
def retry(max_attempts=3, delay=1.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator

@retry(max_attempts=5, delay=0.5)
def fetch_data():
    ...

# Generators
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

# Generator expressions (lazy)
squares = (x**2 for x in range(1000000))  # doesn't compute all
total = sum(x**2 for x in range(1000))

# functools
from functools import lru_cache, partial, reduce

@lru_cache(maxsize=128)
def fib(n):
    if n < 2: return n
    return fib(n-1) + fib(n-2)

double = partial(lambda x, y: x * y, 2)
double(5)  # 10
```

## Object-Oriented Programming

```python
class Animal:
    # Class variable (shared across instances)
    count = 0
    
    def __init__(self, name: str, sound: str):
        # Instance variables
        self.name = name
        self._sound = sound       # convention: "protected"
        self.__secret = "private" # name-mangled → _Animal__secret
        Animal.count += 1
    
    def speak(self) -> str:
        return f"{self.name} says {self._sound}"
    
    @classmethod
    def get_count(cls) -> int:
        return cls.count
    
    @staticmethod
    def is_valid_name(name: str) -> bool:
        return bool(name and name.strip())
    
    @property
    def sound(self) -> str:
        return self._sound
    
    @sound.setter
    def sound(self, value: str) -> None:
        if not value:
            raise ValueError("Sound cannot be empty")
        self._sound = value
    
    def __repr__(self) -> str:
        return f"Animal(name={self.name!r}, sound={self._sound!r})"
    
    def __str__(self) -> str:
        return self.name
    
    def __eq__(self, other) -> bool:
        return isinstance(other, Animal) and self.name == other.name
    
    def __hash__(self) -> int:
        return hash(self.name)

class Dog(Animal):
    def __init__(self, name: str, breed: str):
        super().__init__(name, "woof")
        self.breed = breed
    
    def speak(self) -> str:
        return f"{super().speak()}! I'm a {self.breed}."

# Dataclasses (Python 3.7+)
from dataclasses import dataclass, field

@dataclass
class Config:
    host: str = "localhost"
    port: int = 8765
    debug: bool = False
    tags: list[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.port < 1 or self.port > 65535:
            raise ValueError(f"Invalid port: {self.port}")

# Protocol (structural typing)
from typing import Protocol

class Drawable(Protocol):
    def draw(self) -> None: ...
    def get_area(self) -> float: ...

def render(item: Drawable) -> None:
    item.draw()  # any object with draw() method works
```

## Exceptions and Context Managers

```python
# Exception hierarchy
# BaseException
#   SystemExit, KeyboardInterrupt, GeneratorExit
#   Exception
#     ValueError, TypeError, KeyError, IndexError
#     FileNotFoundError, PermissionError (OSError subclasses)
#     RuntimeError, NotImplementedError
#     StopIteration

# try/except/else/finally
try:
    result = risky_operation()
except ValueError as e:
    print(f"Value error: {e}")
except (TypeError, KeyError) as e:
    print(f"Type or key error: {e}")
except Exception as e:
    raise RuntimeError("Unexpected error") from e  # chain exceptions
else:
    print("Success:", result)    # runs only if no exception
finally:
    cleanup()                    # always runs

# Custom exceptions
class AppError(Exception):
    def __init__(self, message: str, code: int = 0):
        super().__init__(message)
        self.code = code

class DatabaseError(AppError):
    pass

# Context managers
class DatabaseConnection:
    def __enter__(self):
        self.conn = connect()
        return self.conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.conn.rollback()
        else:
            self.conn.commit()
        self.conn.close()
        return False  # don't suppress exceptions

with DatabaseConnection() as conn:
    conn.execute("INSERT ...")

# contextlib
from contextlib import contextmanager, asynccontextmanager

@contextmanager
def timer(name: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        print(f"{name}: {elapsed:.3f}s")

with timer("database query"):
    results = db.query("SELECT ...")
```

## Modules and Packages

```python
# Importing
import os
import sys
import json
from pathlib import Path
from typing import Optional
from collections import defaultdict
from functools import lru_cache
import importlib

# Standard library highlights
import os
os.path.join("a", "b", "c")    # cross-platform path
os.path.exists(path)
os.getcwd()
os.environ.get("API_KEY")
os.makedirs(path, exist_ok=True)

from pathlib import Path
p = Path("/home/fahmi")
p / "projects" / "sidix"       # path joining with /
p.exists()
p.is_file()
p.is_dir()
p.stem                          # filename without extension
p.suffix                        # ".py"
p.parent
p.read_text()
p.write_text("content")
list(p.glob("**/*.py"))         # recursive glob
p.mkdir(parents=True, exist_ok=True)

import json
json.dumps({"key": "value"}, indent=2, ensure_ascii=False)
json.loads('{"key": "value"}')

import re
pattern = re.compile(r"\d+")
pattern.findall("abc 123 def 456")  # ['123', '456']
re.sub(r"\s+", " ", text)          # normalize whitespace
re.search(r"(\w+)@(\w+)", email)   # groups

from datetime import datetime, timedelta, timezone
now = datetime.now(timezone.utc)
now.isoformat()
now + timedelta(days=7)
datetime.fromisoformat("2026-04-17T12:00:00+00:00")

import logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)
logger.info("Server started on port %d", 8765)
logger.error("Failed to load model", exc_info=True)
```

## Async Programming

```python
import asyncio
import aiohttp
import aiofiles

# Basic async/await
async def fetch(session: aiohttp.ClientSession, url: str) -> dict:
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.json()

async def fetch_all(urls: list[str]) -> list[dict]:
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        return await asyncio.gather(*tasks)

# Run async code
results = asyncio.run(fetch_all(["https://api.example.com/1",
                                  "https://api.example.com/2"]))

# FastAPI (async web framework)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class GenerateRequest(BaseModel):
    prompt: str
    system: str = "You are SIDIX"
    max_tokens: int = 512

@app.post("/generate")
async def generate(req: GenerateRequest):
    try:
        text, mode = await asyncio.get_event_loop().run_in_executor(
            None, generate_sidix, req.prompt, req.system
        )
        return {"text": text, "mode": mode}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}

# Async file I/O
async def read_file(path: str) -> str:
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        return await f.read()

# Async generator
async def paginate_api(base_url: str):
    cursor = None
    async with aiohttp.ClientSession() as session:
        while True:
            url = f"{base_url}?cursor={cursor}" if cursor else base_url
            data = await fetch(session, url)
            for item in data["items"]:
                yield item
            if not data.get("next_cursor"):
                break
            cursor = data["next_cursor"]

async def main():
    async for item in paginate_api("https://api.example.com/items"):
        print(item)
```

## Testing

```python
# pytest
import pytest

def add(a: int, b: int) -> int:
    return a + b

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0

def test_add_type_error():
    with pytest.raises(TypeError):
        add("1", 2)

@pytest.mark.parametrize("a, b, expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
])
def test_add_parametrize(a, b, expected):
    assert add(a, b) == expected

# Fixtures
@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture(scope="session")
def db():
    conn = create_test_db()
    yield conn
    conn.close()

# Mocking
from unittest.mock import patch, MagicMock, AsyncMock

def test_with_mock():
    with patch("module.external_api") as mock_api:
        mock_api.return_value = {"status": "ok"}
        result = function_using_api()
        assert result == "ok"
        mock_api.assert_called_once_with(expected_arg)

@patch("module.async_function", new_callable=AsyncMock)
async def test_async(mock_func):
    mock_func.return_value = "mocked"
    result = await my_async_function()
    assert result == "mocked"
```

## Referensi Lanjut
- https://roadmap.sh/python
- https://docs.python.org/3/ — official documentation
- https://peps.python.org/ — Python Enhancement Proposals
- https://realpython.com/ — practical Python tutorials
- "Fluent Python" — Luciano Ramalho (advanced)
- "Effective Python" — Brett Slatkin
- https://pythonic.org/ — Pythonic code patterns
