# JavaScript & TypeScript

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

> Sumber: Sintesis dari ECMAScript specification, TypeScript Handbook, React documentation, dan MDN Web Docs.
> Relevan untuk: frontend developers, full-stack engineers, Node.js developers
> Tags: javascript, typescript, react, hooks, async, promises, closures, generics, node, es2024

## JavaScript Fundamentals

### Variables and Scope
```javascript
// var: function-scoped, hoisted, avoid in modern code
// let: block-scoped, not hoisted to value, reassignable
// const: block-scoped, must be initialized, binding is immutable (object contents can change)

const name = "SIDIX";
let count = 0;

// Temporal Dead Zone (TDZ) — let/const can't be accessed before declaration
// console.log(x); // ReferenceError: Cannot access 'x' before initialization
// let x = 1;

// Block scope
{
    const local = "only here";
}
// console.log(local); // ReferenceError
```

### Closures
A closure is a function that "closes over" its surrounding scope — it retains access to variables from the enclosing function even after that function has returned.

```javascript
function makeCounter(initial = 0) {
    let count = initial; // closed-over variable
    return {
        increment() { return ++count; },
        decrement() { return --count; },
        value() { return count; },
    };
}

const counter = makeCounter(10);
counter.increment(); // 11
counter.increment(); // 12
counter.value();     // 12 — count is private, only accessible via the returned API

// Classic closure pitfall with loops (var)
for (var i = 0; i < 3; i++) {
    setTimeout(() => console.log(i), 100); // prints 3, 3, 3 — all share same i
}

// Fix 1: use let (block-scoped)
for (let i = 0; i < 3; i++) {
    setTimeout(() => console.log(i), 100); // prints 0, 1, 2
}

// Fix 2: IIFE (old style)
for (var i = 0; i < 3; i++) {
    ((captured) => setTimeout(() => console.log(captured), 100))(i);
}

// Memoization using closure
function memoize(fn) {
    const cache = new Map();
    return function(...args) {
        const key = JSON.stringify(args);
        if (cache.has(key)) return cache.get(key);
        const result = fn.apply(this, args);
        cache.set(key, result);
        return result;
    };
}
```

### Prototypes and Inheritance
```javascript
// Every object has a [[Prototype]] (internal, accessed via __proto__ or Object.getPrototypeOf())
// Functions have a .prototype property used when called with new

function Animal(name) {
    this.name = name;
}
Animal.prototype.speak = function() {
    return `${this.name} makes a sound.`;
};

const dog = new Animal("Rex");
dog.speak(); // works via prototype chain

// Modern class syntax (syntactic sugar over prototypes)
class Animal {
    #sound; // private field (ES2022)
    
    constructor(name, sound) {
        this.name = name;
        this.#sound = sound;
    }
    
    speak() {
        return `${this.name} says ${this.#sound}`;
    }
    
    static create(name, sound) {
        return new Animal(name, sound);
    }
}

class Dog extends Animal {
    constructor(name, breed) {
        super(name, "woof"); // must call super before using this
        this.breed = breed;
    }
    
    speak() {
        return `${super.speak()}! I'm a ${this.breed}.`;
    }
}
```

### Promises and Async/Await
```javascript
// Promise states: pending → fulfilled | rejected
const promise = new Promise((resolve, reject) => {
    setTimeout(() => resolve("data"), 1000);
});

// Chaining
promise
    .then(data => data.toUpperCase())
    .then(upper => console.log(upper))
    .catch(err => console.error("Error:", err))
    .finally(() => console.log("Always runs"));

// async/await — syntactic sugar over promises
async function fetchUser(id) {
    try {
        const response = await fetch(`/api/users/${id}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return await response.json();
    } catch (err) {
        console.error("Failed to fetch user:", err);
        throw err; // re-throw so caller can handle
    }
}

// Parallel execution
async function fetchAll(ids) {
    const promises = ids.map(id => fetchUser(id));
    const users = await Promise.all(promises); // parallel, fails if any fail
    return users;
}

// Promise.allSettled — wait for all, don't fail on individual errors
const results = await Promise.allSettled([
    fetch("/api/a"),
    fetch("/api/b"),
    fetch("/api/error"),
]);
results.forEach(r => {
    if (r.status === "fulfilled") console.log(r.value);
    else console.error(r.reason);
});

// Promise.race — first to settle wins
const firstResult = await Promise.race([
    fetchUser(1),
    new Promise((_, reject) => setTimeout(() => reject(new Error("Timeout")), 5000)),
]);

// Promise.any — first to fulfill wins (ignores rejections)
const fastest = await Promise.any([mirror1.get(), mirror2.get(), mirror3.get()]);
```

### The Event Loop
JavaScript is single-threaded with a non-blocking event loop.
```
Call Stack       — currently executing code
Web APIs         — browser: setTimeout, fetch, DOM events
Task Queue       — macrotasks: setTimeout, setInterval callbacks
Microtask Queue  — promises, queueMicrotask; runs BEFORE next macrotask

Execution order:
1. Run all synchronous code (call stack drains)
2. Run ALL microtasks (promise .then callbacks)
3. Render (browser only)
4. Run one macrotask (setTimeout callback)
5. Repeat from step 2
```

```javascript
console.log("1");
setTimeout(() => console.log("2"), 0);
Promise.resolve().then(() => console.log("3"));
console.log("4");
// Output: 1, 4, 3, 2
// Reason: sync runs first (1, 4), then microtask promise (3), then macrotask setTimeout (2)
```

### ES2020+ Modern Patterns
```javascript
// Optional chaining — safely access deeply nested properties
const city = user?.address?.city; // undefined if any link is null/undefined
const first = users?.[0]?.name;   // works on arrays too
const result = obj?.method?.();   // works for method calls

// Nullish coalescing — ?? returns right side only when left is null or undefined
const port = config.port ?? 3000; // not 0 (which is falsy but valid)
const name = user.name || "Guest"; // returns "Guest" for "" or 0 too (usually wrong)
const name2 = user.name ?? "Guest"; // returns "Guest" only for null/undefined

// Nullish assignment
user.score ??= 0; // only assigns if score is null/undefined
user.count ||= 1; // only assigns if count is falsy
user.max &&= user.max * 2; // only assigns if max is truthy

// Destructuring
const { name, age, role = "user" } = userObj; // with default
const { name: userName, ...rest } = userObj;   // rename + rest

const [first, second, ...others] = array;
const [, , third] = array; // skip elements

// Destructuring in function params
function display({ name, age = 25, address: { city } = {} } = {}) {
    console.log(`${name}, ${age}, ${city}`);
}

// Spread operator
const merged = { ...defaults, ...overrides }; // rightmost wins
const copy = [...originalArray, newItem];
const args = [1, 2, 3];
Math.max(...args);

// Template literal tags
function highlight(strings, ...values) {
    return strings.reduce((result, str, i) =>
        result + str + (values[i] ? `<mark>${values[i]}</mark>` : ""), "");
}
const html = highlight`Hello ${name}, you have ${count} messages.`;

// Logical OR assignment, AND assignment
x ||= defaultValue;
x &&= transform(x);
x ??= fallback;

// Array methods chaining
const result = data
    .filter(x => x.active)
    .map(x => ({ id: x.id, label: x.name.toUpperCase() }))
    .sort((a, b) => a.label.localeCompare(b.label))
    .slice(0, 10);
```

### Modules (ESM)
```javascript
// Named exports
export const PI = 3.14159;
export function add(a, b) { return a + b; }
export class Vector { ... }

// Default export (one per file)
export default class App { ... }

// Imports
import { add, PI } from "./math.js";
import { add as sum } from "./math.js"; // rename
import * as math from "./math.js";      // namespace import
import App from "./App.js";             // default import
import App, { helper } from "./App.js"; // both

// Dynamic import (lazy loading)
const module = await import("./heavy-module.js");
const { processData } = await import("./utils.js");
```

## TypeScript

### Basic Types and Interfaces
```typescript
// Primitive types
let name: string = "SIDIX";
let count: number = 42;
let active: boolean = true;
let data: unknown;           // type-safe any — must narrow before use
let legacy: any;             // bypass type checking (avoid)
let nothing: void;           // function returns nothing
let impossible: never;       // function never returns (throws or infinite loop)

// Arrays and tuples
const nums: number[] = [1, 2, 3];
const matrix: number[][] = [[1, 2], [3, 4]];
const pair: [string, number] = ["hello", 42]; // tuple: fixed length and types

// Object types with interface
interface User {
    id: number;
    name: string;
    email: string;
    age?: number;        // optional
    readonly createdAt: Date; // immutable after creation
}

// Type alias (more flexible than interface)
type Status = "active" | "inactive" | "pending"; // union literal type
type ID = string | number;
type Point = { x: number; y: number };
type Callback = (event: MouseEvent) => void;

// Intersection types
type AdminUser = User & { role: "admin"; permissions: string[] };
```

### Generics
```typescript
// Generic function
function identity<T>(value: T): T {
    return value;
}

function first<T>(arr: T[]): T | undefined {
    return arr[0];
}

// Generic with constraint
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
    return obj[key];
}

const user = { name: "Fahmi", age: 30 };
getProperty(user, "name"); // string
getProperty(user, "age");  // number
// getProperty(user, "email"); // TypeError — "email" not in keyof User

// Generic class
class Stack<T> {
    private items: T[] = [];
    
    push(item: T): void { this.items.push(item); }
    pop(): T | undefined { return this.items.pop(); }
    peek(): T | undefined { return this.items[this.items.length - 1]; }
    isEmpty(): boolean { return this.items.length === 0; }
}

const numberStack = new Stack<number>();
const stringStack = new Stack<string>();

// Generic with multiple type parameters
function zip<A, B>(a: A[], b: B[]): [A, B][] {
    return a.map((item, i) => [item, b[i]]);
}
```

### Utility Types
```typescript
interface User {
    id: number;
    name: string;
    email: string;
    age: number;
}

// Partial — all fields optional
type UserUpdate = Partial<User>;  // { id?: number; name?: string; ... }

// Required — all fields required (opposite of Partial)
type RequiredUser = Required<UserUpdate>;

// Pick — select subset of fields
type UserPreview = Pick<User, "id" | "name">; // { id: number; name: string }

// Omit — exclude fields
type UserWithoutId = Omit<User, "id">;

// Readonly — all fields immutable
type ImmutableUser = Readonly<User>;

// Record — object type with known key-value types
type RolePermissions = Record<"admin" | "editor" | "viewer", string[]>;

// ReturnType — extract return type from function type
async function fetchUser(): Promise<User> { ... }
type UserResult = Awaited<ReturnType<typeof fetchUser>>; // User

// Parameters — extract parameter types
type FetchParams = Parameters<typeof fetchUser>; // []

// Conditional types
type IsArray<T> = T extends any[] ? true : false;
type UnpackArray<T> = T extends (infer U)[] ? U : T;
type UnpackedUser = UnpackArray<User[]>; // User
```

### Decorators (TypeScript / JavaScript Stage 3)
```typescript
// Class decorator
function sealed(constructor: Function) {
    Object.seal(constructor);
    Object.seal(constructor.prototype);
}

// Property decorator
function validate(min: number, max: number) {
    return function(target: any, propertyKey: string) {
        let value: number;
        Object.defineProperty(target, propertyKey, {
            get() { return value; },
            set(v: number) {
                if (v < min || v > max) throw new RangeError(`${propertyKey} must be between ${min} and ${max}`);
                value = v;
            }
        });
    };
}

// Method decorator
function log(target: any, key: string, descriptor: PropertyDescriptor) {
    const original = descriptor.value;
    descriptor.value = function(...args: any[]) {
        console.log(`Calling ${key} with`, args);
        const result = original.apply(this, args);
        console.log(`${key} returned`, result);
        return result;
    };
    return descriptor;
}

@sealed
class Person {
    @validate(0, 150)
    age: number;
    
    @log
    greet(name: string): string {
        return `Hello, ${name}!`;
    }
}
```

## React Hooks

### useState and useEffect
```typescript
import React, { useState, useEffect, useCallback, useMemo, useRef } from "react";

function UserProfile({ userId }: { userId: number }) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    
    useEffect(() => {
        let cancelled = false;
        
        async function fetchUser() {
            setLoading(true);
            setError(null);
            try {
                const data = await api.getUser(userId);
                if (!cancelled) setUser(data);
            } catch (err) {
                if (!cancelled) setError(err instanceof Error ? err.message : "Unknown error");
            } finally {
                if (!cancelled) setLoading(false);
            }
        }
        
        fetchUser();
        
        return () => { cancelled = true; }; // cleanup — prevents state update on unmounted component
    }, [userId]); // re-run when userId changes
    
    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error}</div>;
    if (!user) return null;
    
    return <div>{user.name}</div>;
}
```

### useCallback and useMemo
```typescript
// useCallback — memoize a function reference (prevents child re-render)
// useMemo — memoize a computed value (expensive calculations)

function SearchPage() {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState<Result[]>([]);
    
    // Without useCallback: new function reference on every render → child re-renders
    const handleSearch = useCallback(async (q: string) => {
        const data = await api.search(q);
        setResults(data);
    }, []); // empty deps: function never changes
    
    // useMemo: only recompute when results changes
    const sortedResults = useMemo(
        () => [...results].sort((a, b) => b.score - a.score),
        [results]
    );
    
    const stats = useMemo(() => ({
        total: results.length,
        avgScore: results.reduce((sum, r) => sum + r.score, 0) / results.length,
    }), [results]);
    
    return (
        <div>
            <SearchBar onSearch={handleSearch} />
            <StatsPanel stats={stats} />
            <ResultList items={sortedResults} />
        </div>
    );
}

// useRef — mutable value that doesn't trigger re-render
function Timer() {
    const [time, setTime] = useState(0);
    const intervalRef = useRef<NodeJS.Timeout | null>(null);
    const countRef = useRef(0); // doesn't cause re-render when changed
    
    const start = useCallback(() => {
        intervalRef.current = setInterval(() => {
            countRef.current += 1;
            setTime(countRef.current);
        }, 1000);
    }, []);
    
    const stop = useCallback(() => {
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
        }
    }, []);
    
    useEffect(() => {
        return () => stop(); // cleanup on unmount
    }, [stop]);
    
    return <div>Time: {time}s <button onClick={start}>Start</button><button onClick={stop}>Stop</button></div>;
}
```

### Custom Hooks
```typescript
// Custom hook — extract and reuse stateful logic
function useFetch<T>(url: string) {
    const [data, setData] = useState<T | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<Error | null>(null);
    
    const refetch = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const json: T = await response.json();
            setData(json);
        } catch (err) {
            setError(err instanceof Error ? err : new Error("Unknown error"));
        } finally {
            setLoading(false);
        }
    }, [url]);
    
    useEffect(() => { refetch(); }, [refetch]);
    
    return { data, loading, error, refetch };
}

// useLocalStorage hook
function useLocalStorage<T>(key: string, initialValue: T) {
    const [value, setValue] = useState<T>(() => {
        try {
            const stored = window.localStorage.getItem(key);
            return stored ? JSON.parse(stored) : initialValue;
        } catch {
            return initialValue;
        }
    });
    
    const setStoredValue = useCallback((newValue: T | ((prev: T) => T)) => {
        setValue(prev => {
            const resolved = newValue instanceof Function ? newValue(prev) : newValue;
            window.localStorage.setItem(key, JSON.stringify(resolved));
            return resolved;
        });
    }, [key]);
    
    return [value, setStoredValue] as const;
}

// useDebounce
function useDebounce<T>(value: T, delay: number): T {
    const [debounced, setDebounced] = useState(value);
    useEffect(() => {
        const timer = setTimeout(() => setDebounced(value), delay);
        return () => clearTimeout(timer);
    }, [value, delay]);
    return debounced;
}

// Usage
function SearchInput() {
    const [query, setQuery] = useState("");
    const debouncedQuery = useDebounce(query, 300);
    const { data: results, loading } = useFetch<Result[]>(
        debouncedQuery ? `/api/search?q=${debouncedQuery}` : ""
    );
    ...
}
```

## Node.js Basics

```javascript
// Node.js-specific globals
process.env.NODE_ENV      // "development" | "production" | "test"
process.argv              // command line arguments
process.cwd()             // current working directory
process.exit(0)           // exit with code 0 (success)

// File system (use promises API)
const fs = require("fs/promises");
// or ESM:
import { readFile, writeFile, readdir, mkdir, stat } from "fs/promises";

async function processFiles(dir) {
    const entries = await readdir(dir, { withFileTypes: true });
    for (const entry of entries) {
        if (entry.isFile() && entry.name.endsWith(".json")) {
            const content = await readFile(`${dir}/${entry.name}`, "utf-8");
            const data = JSON.parse(content);
            // process data...
        }
    }
}

// HTTP server (low level)
import { createServer } from "http";
const server = createServer(async (req, res) => {
    const url = new URL(req.url, `http://${req.headers.host}`);
    if (url.pathname === "/health") {
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ status: "ok" }));
    }
});
server.listen(3000, () => console.log("Server on :3000"));

// EventEmitter — built-in pub/sub
import { EventEmitter } from "events";
class JobQueue extends EventEmitter {
    add(job) {
        this.emit("job:added", job);
        // process job...
        this.emit("job:done", { jobId: job.id, result: "success" });
    }
}
const queue = new JobQueue();
queue.on("job:done", ({ jobId }) => console.log(`Job ${jobId} done`));

// Streams — handle large data without loading all into memory
import { createReadStream, createWriteStream } from "fs";
import { createGzip } from "zlib";

createReadStream("large-file.txt")
    .pipe(createGzip())
    .pipe(createWriteStream("large-file.txt.gz"))
    .on("finish", () => console.log("Compressed!"));
```

## TypeScript Configuration

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,          // enables all strict type checks
    "noUncheckedIndexedAccess": true,  // arr[i] returns T | undefined
    "exactOptionalPropertyTypes": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist"]
}
```

## Referensi & Sumber Lanjut
- https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide
- https://www.typescriptlang.org/docs/handbook/
- https://react.dev/reference/react
- https://nodejs.org/en/docs/
- https://javascript.info/ — excellent in-depth JS resource
- roadmap.sh/javascript
- roadmap.sh/typescript
- roadmap.sh/react
