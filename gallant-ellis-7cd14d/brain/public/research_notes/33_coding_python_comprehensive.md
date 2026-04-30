# Python Comprehensive Reference

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

> Sumber: Sintesis dari dokumentasi resmi Python, PEP documents, dan praktik industri.
> Relevan untuk: backend developers, data scientists, AI engineers, general programmers
> Tags: python, programming, oop, async, decorators, generators, typing, pytest, packaging

## Core Data Types and Operations

Python's type system is dynamic but has a rich set of built-in types. Understanding them deeply prevents most beginner bugs.

### Numeric Types
```python
# int: arbitrary precision
big = 10 ** 100  # no overflow
x = 0xFF   # hex literal = 255
y = 0b1010 # binary literal = 10

# float: IEEE 754 double precision
# Never use == for floats
from math import isclose
assert isclose(0.1 + 0.2, 0.3, rel_tol=1e-9)

# Decimal for exact decimal arithmetic (financial use)
from decimal import Decimal
price = Decimal("19.99")

# complex
z = 3 + 4j
abs(z)  # magnitude = 5.0
```

### Strings
```python
# Strings are immutable sequences of Unicode code points
name = "Fahmi"
greeting = f"Hello, {name}!"  # f-string (preferred since 3.6)

# Multiline
sql = """
    SELECT *
    FROM users
    WHERE active = true
"""

# String methods
"  hello  ".strip()          # "hello"
"hello".upper()              # "HELLO"
"a,b,c".split(",")           # ["a", "b", "c"]
",".join(["a", "b", "c"])    # "a,b,c"
"hello world".replace("world", "Python")

# Formatting
"{:.2f}".format(3.14159)     # "3.14"
f"{1_000_000:,}"             # "1,000,000"
```

### Lists, Tuples, Sets, Dicts
```python
# List: mutable, ordered, O(1) append, O(n) insert at arbitrary index
nums = [1, 2, 3]
nums.append(4)
nums.extend([5, 6])
nums.insert(0, 0)    # O(n)
nums.pop()           # remove last, O(1)
nums.pop(0)          # remove first, O(n) — use collections.deque for queues

# Tuple: immutable, can be used as dict keys
point = (3, 4)
x, y = point         # unpacking

# Set: unordered, unique elements, O(1) lookup
tags = {"python", "ai", "backend"}
tags.add("fastapi")
tags.discard("missing_ok")
a = {1, 2, 3}; b = {2, 3, 4}
a & b  # intersection {2, 3}
a | b  # union {1, 2, 3, 4}
a - b  # difference {1}

# Dict: ordered (Python 3.7+), O(1) average lookup
config = {"host": "localhost", "port": 8000}
config.get("missing", "default")
config.setdefault("debug", False)
{k: v for k, v in config.items() if v}  # dict comprehension
```

## Functions

### Signatures and Arguments
```python
def greet(name: str, greeting: str = "Hello") -> str:
    """Return a greeting string."""
    return f"{greeting}, {name}!"

# Positional-only (/) and keyword-only (*) parameters
def api(url: str, /, *, timeout: int = 30, retries: int = 3):
    # url must be positional; timeout and retries must be keyword
    pass

# *args and **kwargs
def log(*args, level: str = "INFO", **metadata):
    print(f"[{level}]", *args, metadata)

log("request started", level="DEBUG", user_id=42)
```

### Lambda, Map, Filter, Reduce
```python
square = lambda x: x ** 2
squares = list(map(square, range(10)))
evens = list(filter(lambda x: x % 2 == 0, range(10)))

from functools import reduce
product = reduce(lambda a, b: a * b, [1, 2, 3, 4, 5])  # 120
```

## List, Dict, Set Comprehensions

```python
# List comprehension
squares = [x**2 for x in range(10) if x % 2 == 0]

# Nested comprehension (flatten 2D list)
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
flat = [val for row in matrix for val in row]

# Dict comprehension
word_lengths = {word: len(word) for word in ["hello", "world", "python"]}

# Set comprehension
unique_lengths = {len(word) for word in ["hi", "hello", "hey"]}

# Walrus operator (:=) — Python 3.8+
import re
text = "Error: connection refused on port 5432"
if m := re.search(r"port (\d+)", text):
    print(f"Port found: {m.group(1)}")  # Port found: 5432

# Use walrus in comprehensions to avoid double computation
data = [1, -2, 3, -4, 5]
processed = [cleaned for x in data if (cleaned := abs(x)) > 2]
```

## Object-Oriented Programming

```python
from dataclasses import dataclass, field
from typing import ClassVar

class Animal:
    species_count: ClassVar[int] = 0  # class variable
    
    def __init__(self, name: str, sound: str):
        self.name = name
        self._sound = sound   # "protected" by convention
        Animal.species_count += 1
    
    def speak(self) -> str:
        return f"{self.name} says {self._sound}"
    
    def __repr__(self) -> str:
        return f"Animal(name={self.name!r})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Animal):
            return NotImplemented
        return self.name == other.name
    
    @classmethod
    def from_dict(cls, data: dict) -> "Animal":
        return cls(data["name"], data["sound"])
    
    @staticmethod
    def validate_name(name: str) -> bool:
        return bool(name and name.isalpha())


class Dog(Animal):
    def __init__(self, name: str, breed: str):
        super().__init__(name, "woof")
        self.breed = breed
    
    def speak(self) -> str:  # override
        return f"{super().speak()}! I'm a {self.breed}."


# Dataclass — clean boilerplate-free classes
@dataclass
class Point:
    x: float
    y: float
    label: str = ""
    history: list = field(default_factory=list)
    
    def distance_to(self, other: "Point") -> float:
        return ((self.x - other.x)**2 + (self.y - other.y)**2) ** 0.5
```

### Properties and Descriptors
```python
class Temperature:
    def __init__(self, celsius: float):
        self._celsius = celsius
    
    @property
    def celsius(self) -> float:
        return self._celsius
    
    @celsius.setter
    def celsius(self, value: float):
        if value < -273.15:
            raise ValueError("Temperature below absolute zero")
        self._celsius = value
    
    @property
    def fahrenheit(self) -> float:
        return self._celsius * 9/5 + 32
```

## Generators and Iterators

Generators are lazy sequences — they produce values on demand, using O(1) memory regardless of sequence size.

```python
# Generator function
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

fib = fibonacci()
first_10 = [next(fib) for _ in range(10)]

# Generator expression (like list comprehension but lazy)
big_squares = (x**2 for x in range(10**9))  # no memory issue

# send() and two-way communication
def accumulator():
    total = 0
    while True:
        value = yield total
        if value is None:
            break
        total += value

acc = accumulator()
next(acc)          # prime the generator
acc.send(10)       # total = 10
acc.send(20)       # total = 30

# itertools — essential generator utilities
import itertools
list(itertools.islice(fibonacci(), 10))          # first 10
list(itertools.chain([1,2], [3,4], [5,6]))       # flatten iterables
list(itertools.product("AB", repeat=2))           # cartesian product
groups = itertools.groupby([1,1,2,2,3], key=lambda x: x)
```

## Decorators

Decorators are functions that wrap other functions, adding behavior without modifying the source.

```python
import functools
import time
import logging

# Basic decorator
def timer(func):
    @functools.wraps(func)  # preserves func metadata
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper

# Decorator with arguments
def retry(max_attempts: int = 3, delay: float = 1.0):
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

# Class-based decorator
class cache:
    def __init__(self, func):
        self.func = func
        self.memo = {}
        functools.update_wrapper(self, func)
    
    def __call__(self, *args):
        if args not in self.memo:
            self.memo[args] = self.func(*args)
        return self.memo[args]

# functools.lru_cache — built-in memoization
@functools.lru_cache(maxsize=128)
def fibonacci(n: int) -> int:
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

@timer
@retry(max_attempts=3, delay=0.5)
def fetch_data(url: str):
    import urllib.request
    return urllib.request.urlopen(url).read()
```

## Context Managers

```python
# Using with statement
with open("file.txt", "r") as f:
    content = f.read()
# file is automatically closed even if exception occurs

# Creating context managers with contextlib
from contextlib import contextmanager, asynccontextmanager

@contextmanager
def timer_context(label: str):
    start = time.perf_counter()
    try:
        yield  # body of `with` block executes here
    finally:
        elapsed = time.perf_counter() - start
        print(f"{label}: {elapsed:.4f}s")

with timer_context("database query"):
    time.sleep(0.1)

# Class-based context manager
class DatabaseTransaction:
    def __init__(self, conn):
        self.conn = conn
    
    def __enter__(self):
        self.conn.begin()
        return self.conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        return False  # don't suppress exceptions
```

## Standard Library Highlights

### pathlib — Modern File System Operations
```python
from pathlib import Path

base = Path("/home/user/projects")
config = base / "config" / "settings.json"  # join paths with /

config.exists()
config.is_file()
config.suffix         # ".json"
config.stem           # "settings"
config.parent         # Path("/home/user/projects/config")
config.name           # "settings.json"

# Read/write
text = config.read_text(encoding="utf-8")
config.write_text('{"debug": true}', encoding="utf-8")
data = config.read_bytes()

# Glob
py_files = list(base.glob("**/*.py"))  # recursive
config.mkdir(parents=True, exist_ok=True)

# Iteration
for f in base.iterdir():
    if f.is_file():
        print(f.name)
```

### json — Serialization
```python
import json

data = {"name": "SIDIX", "version": 1, "tags": ["ai", "rag"]}
json_str = json.dumps(data, indent=2, ensure_ascii=False)
parsed = json.loads(json_str)

# File I/O
with open("config.json", "w") as f:
    json.dump(data, f, indent=2)

with open("config.json") as f:
    loaded = json.load(f)

# Custom serialization
from datetime import datetime

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

json.dumps({"ts": datetime.now()}, cls=DateTimeEncoder)
```

### re — Regular Expressions
```python
import re

# Compile for reuse
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

text = "Contact us at info@sidix.ai or support@example.com"
emails = EMAIL_RE.findall(text)  # ['info@sidix.ai', 'support@example.com']

# Groups
m = re.match(r"(\d{4})-(\d{2})-(\d{2})", "2024-01-15")
if m:
    year, month, day = m.groups()

# Named groups
m = re.search(r"(?P<year>\d{4})-(?P<month>\d{2})", "2024-01")
m.group("year")   # "2024"

# Substitution
clean = re.sub(r"\s+", " ", "hello   world\n\nbye")

# Splitting
parts = re.split(r"[,;\s]+", "a, b; c d")
```

### collections — Specialized Containers
```python
from collections import Counter, defaultdict, OrderedDict, deque, namedtuple

# Counter
words = "the quick brown fox jumps over the lazy dog the".split()
freq = Counter(words)
freq.most_common(3)  # [("the", 3), ...]

# defaultdict — no KeyError on missing key
graph = defaultdict(list)
graph["A"].append("B")  # works without init

# deque — O(1) append/pop from both ends
dq = deque([1, 2, 3], maxlen=5)
dq.appendleft(0)
dq.rotate(1)  # rotate right by 1

# namedtuple — lightweight immutable record
Point = namedtuple("Point", ["x", "y", "z"])
p = Point(1, 2, 3)
p.x  # 1
```

### datetime — Date and Time
```python
from datetime import datetime, date, timedelta, timezone

now = datetime.now(tz=timezone.utc)   # always use UTC internally
today = date.today()

# Arithmetic
tomorrow = today + timedelta(days=1)
next_week = now + timedelta(weeks=1)
diff = datetime(2025, 1, 1) - datetime(2024, 1, 1)
diff.days  # 366

# Formatting and parsing
iso = now.isoformat()                            # "2024-01-15T10:30:00+00:00"
formatted = now.strftime("%Y-%m-%d %H:%M:%S")
parsed = datetime.strptime("2024-01-15", "%Y-%m-%d")
```

## Virtual Environments and pip

```bash
# Create virtual environment
python -m venv .venv

# Activate
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate.bat       # Windows

# Install packages
pip install fastapi uvicorn
pip install -r requirements.txt

# Freeze dependencies
pip freeze > requirements.txt

# pip with extras
pip install "fastapi[all]"  # installs optional dependencies

# uv — modern, fast pip alternative
pip install uv
uv venv
uv pip install fastapi uvicorn
uv pip sync requirements.txt
```

## Type Hints

```python
from typing import Optional, Union, Any, Callable, TypeVar
from typing import List, Dict, Tuple, Set  # pre-3.9 style
# Python 3.9+ can use built-in generics: list[int], dict[str, int]

T = TypeVar("T")

def first(items: list[T]) -> T | None:  # union with | (3.10+)
    return items[0] if items else None

def process(
    data: dict[str, Any],
    callback: Callable[[str, int], bool],
    *,
    timeout: int | None = None,
) -> list[str]:
    ...

# TypedDict for dict with known keys
from typing import TypedDict

class UserConfig(TypedDict):
    name: str
    email: str
    age: int | None

# Protocol for structural subtyping (duck typing formalized)
from typing import Protocol

class Drawable(Protocol):
    def draw(self) -> None: ...

# Generic classes
class Stack(list[T]):
    def push(self, item: T) -> None:
        self.append(item)
    
    def pop_safe(self) -> T | None:
        return self.pop() if self else None
```

## Async / Await

```python
import asyncio
import aiohttp

# Basic coroutine
async def fetch(url: str, session: aiohttp.ClientSession) -> dict:
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.json()

# Run multiple requests concurrently
async def fetch_all(urls: list[str]) -> list[dict]:
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(url, session) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)

# Async context manager
class AsyncDB:
    async def __aenter__(self):
        self.conn = await asyncio.sleep(0)  # simulate connection
        return self
    
    async def __aexit__(self, *args):
        await asyncio.sleep(0)  # simulate cleanup

# Async generator
async def stream_lines(filename: str):
    async with aiofiles.open(filename) as f:
        async for line in f:
            yield line.strip()

# Timeouts
async def guarded_fetch(url: str) -> str:
    async with asyncio.timeout(5.0):
        async with aiohttp.ClientSession() as s:
            async with s.get(url) as r:
                return await r.text()

asyncio.run(fetch_all(["https://api.example.com/1", "https://api.example.com/2"]))
```

## Testing with pytest

```python
# test_math_utils.py
import pytest
from math_utils import divide, fibonacci

# Basic test
def test_divide_normal():
    assert divide(10, 2) == 5.0

def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError, match="division by zero"):
        divide(10, 0)

# Parametrize — run same test with different inputs
@pytest.mark.parametrize("n,expected", [
    (0, 0), (1, 1), (2, 1), (5, 5), (10, 55)
])
def test_fibonacci(n, expected):
    assert fibonacci(n) == expected

# Fixtures — reusable test setup
@pytest.fixture
def sample_user():
    return {"id": 1, "name": "Test User", "email": "test@example.com"}

@pytest.fixture
def db_session():
    # setup
    session = create_test_session()
    yield session  # provide to test
    # teardown
    session.rollback()
    session.close()

def test_create_user(db_session, sample_user):
    user = create_user(db_session, **sample_user)
    assert user.id is not None
    assert user.name == sample_user["name"]

# Mocking
from unittest.mock import patch, MagicMock

def test_send_email(sample_user):
    with patch("myapp.email.send_smtp") as mock_smtp:
        mock_smtp.return_value = True
        result = send_welcome_email(sample_user["email"])
        mock_smtp.assert_called_once_with(sample_user["email"], subject="Welcome!")
        assert result is True

# Run: pytest -v --tb=short --cov=myapp
```

## Packaging with pyproject.toml

```toml
# pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "sidix-tools"
version = "0.1.0"
description = "Utilities for the SIDIX platform"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [{name = "Fahmi", email = "fahmiwol@gmail.com"}]
dependencies = [
    "fastapi>=0.115",
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
]

[project.optional-dependencies]
dev = ["pytest", "pytest-cov", "mypy", "ruff"]
test = ["pytest", "pytest-asyncio", "httpx"]

[project.scripts]
sidix = "sidix.cli:main"

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W"]

[tool.mypy]
strict = true
python_version = "3.11"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

```bash
# Install in editable mode for development
pip install -e ".[dev]"

# Build distribution
pip install build
python -m build  # creates dist/*.whl and dist/*.tar.gz

# Publish to PyPI
pip install twine
twine upload dist/*
```

## Common Patterns and Best Practices

```python
# Singleton pattern
class Config:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

# Registry pattern
HANDLERS: dict[str, type] = {}

def register(name: str):
    def decorator(cls):
        HANDLERS[name] = cls
        return cls
    return decorator

@register("json")
class JsonHandler:
    def handle(self, data): return json.dumps(data)

# Null object pattern
class NullLogger:
    def info(self, *args): pass
    def error(self, *args): pass

def process(data, logger=None):
    logger = logger or NullLogger()
    logger.info("processing started")
```

## Referensi & Sumber Lanjut
- https://docs.python.org/3/
- https://peps.python.org/ (PEP 8 style, PEP 484 typing, PEP 572 walrus)
- https://docs.pytest.org/
- https://mypy.readthedocs.io/
- https://docs.astral.sh/ruff/ (fast linter/formatter)
- roadmap.sh/python
