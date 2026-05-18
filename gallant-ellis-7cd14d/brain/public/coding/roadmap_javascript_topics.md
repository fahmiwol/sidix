# JavaScript Roadmap — Topic Index + Quick Reference

> Sumber: roadmap.sh/javascript (CC BY-SA 4.0)
> Referensi: https://roadmap.sh/javascript

## Foundations

### How JavaScript Works
- **Single-threaded**: one call stack, one thing at a time
- **Interpreted / JIT compiled**: V8 (Chrome/Node), SpiderMonkey (Firefox), JavaScriptCore (Safari)
- **Dynamically typed**: types are checked at runtime, not compile time
- **Prototype-based OOP**: inheritance via prototype chain (not class-based at the core)
- **Event-driven**: code responds to events; event loop runs continuously

### JavaScript Engines
- V8 (Google): Chrome, Node.js, Deno
- SpiderMonkey: Firefox
- JavaScriptCore (Nitro): Safari, React Native

### Running JavaScript
- Browser: `<script>` tag, browser console, DevTools
- Node.js: `node file.js`, `node --watch file.js`
- Deno: `deno run file.ts`
- Bun: `bun run file.ts`

## Variables, Scoping, Hoisting

```javascript
// var — function scoped, hoisted (but value not hoisted, just declaration)
console.log(x); // undefined (not ReferenceError — var is hoisted)
var x = 5;

// let and const — block scoped, not hoisted (Temporal Dead Zone)
// console.log(y); // ReferenceError: Cannot access 'y' before initialization
let y = 5;

// Scope types
// Global scope — accessible everywhere
// Function scope — inside a function (var)
// Block scope — inside {} (let, const)
// Module scope — inside ES module

// Closure — function retains access to outer scope after outer function returns
function outer() {
    let count = 0;
    return function inner() {
        return ++count;
    };
}
const increment = outer();
increment(); // 1
increment(); // 2

// IIFE (Immediately Invoked Function Expression)
(function() {
    const private = "not accessible outside";
})();
```

## Data Types

```javascript
// Primitives (7 types)
typeof 42          // "number"
typeof 3.14        // "number" (no integer/float distinction)
typeof NaN         // "number" (NaN is a number!)
typeof "hello"     // "string"
typeof true        // "boolean"
typeof undefined   // "undefined"
typeof null        // "object" (historical bug in JS)
typeof Symbol()    // "symbol"
typeof 9007199254740992n  // "bigint"

// Reference types
typeof {}          // "object"
typeof []          // "object"
typeof function(){} // "function"

// Type coercion (implicit)
"5" + 3    // "53" (string concat — + with string = concat)
"5" - 3    // 2   (arithmetic — converts string to number)
"5" * 2    // 10
true + 1   // 2
null + 1   // 1
undefined + 1 // NaN

// Comparison
1 == "1"    // true  (loose equality — type coercion)
1 === "1"   // false (strict equality — no coercion)
null == undefined  // true
null === undefined // false
NaN === NaN        // false (NaN is not equal to itself!)
Object.is(NaN, NaN) // true

// Falsy values (all others are truthy)
// false, 0, -0, 0n, "", null, undefined, NaN

// Nullish values (null and undefined only)
// Use ?? to handle these specifically

// Type conversion
Number("3.14")  // 3.14
Number("")      // 0
Number(null)    // 0
Number(undefined) // NaN
Number("abc")   // NaN
parseInt("3.7") // 3
parseFloat("3.7abc") // 3.7
String(42)      // "42"
Boolean(0)      // false
Boolean("")     // false
Boolean(null)   // false
Boolean({})     // true (objects are always truthy)
```

## Functions

```javascript
// Function declaration (hoisted)
function add(a, b) { return a + b; }

// Function expression (not hoisted)
const multiply = function(a, b) { return a * b; };

// Arrow function (no own this, arguments, super)
const square = (x) => x * x;
const greet = name => `Hello, ${name}!`;
const multi = (a, b) => {
    const result = a * b;
    return result;
};

// Default parameters
function fetchData(url, method = "GET", timeout = 5000) { ... }

// Rest parameters
function sum(...nums) {
    return nums.reduce((total, n) => total + n, 0);
}
sum(1, 2, 3, 4); // 10

// Arguments object (not available in arrow functions)
function legacy() {
    return Array.from(arguments).reduce((a, b) => a + b, 0);
}

// Higher-order functions (functions that take/return functions)
const double = (fn) => (x) => fn(x) * 2;
const addDouble = double(n => n + 1);
addDouble(5); // 12

// Currying
const add = (a) => (b) => a + b;
const add5 = add(5);
add5(3); // 8

// Function composition
const compose = (...fns) => x => fns.reduceRight((acc, fn) => fn(acc), x);
const pipe = (...fns) => x => fns.reduce((acc, fn) => fn(acc), x);

const transform = pipe(
    x => x * 2,
    x => x + 1,
    x => x.toString()
);
transform(5); // "11"
```

## Arrays

```javascript
const arr = [1, 2, 3, 4, 5];

// Iteration
arr.forEach(x => console.log(x));

// Transformation
arr.map(x => x * 2);              // [2, 4, 6, 8, 10] — new array
arr.filter(x => x % 2 === 0);     // [2, 4] — keep matching
arr.reduce((acc, x) => acc + x, 0); // 15 — fold to single value
arr.flatMap(x => [x, x * 2]);     // [1, 2, 2, 4, 3, 6, ...] — map + flatten

// Search
arr.find(x => x > 3);             // 4 — first match
arr.findIndex(x => x > 3);        // 3 — index of first match
arr.findLast(x => x < 4);         // 3 — last match
arr.includes(3);                  // true
arr.some(x => x > 4);             // true — at least one matches
arr.every(x => x > 0);            // true — all match
arr.indexOf(3);                   // 2 (-1 if not found)

// Mutating methods (modify original)
arr.push(6);                      // add to end, returns new length
arr.pop();                        // remove from end, returns element
arr.unshift(0);                   // add to start
arr.shift();                      // remove from start
arr.splice(2, 1, 99);             // at index 2, remove 1, insert 99
arr.sort((a, b) => a - b);        // sort ascending (mutates!)
arr.reverse();                    // reverse (mutates!)
arr.fill(0, 2, 4);                // fill indices 2-4 with 0

// Non-mutating methods
arr.slice(1, 3);                  // [2, 3] — copy portion
arr.concat([6, 7]);               // new combined array
arr.flat();                       // flatten one level
arr.flat(Infinity);               // flatten completely
[...arr].sort((a, b) => a - b);  // sort without mutation (spread first)

// Spread and destructuring
const [first, second, ...rest] = [1, 2, 3, 4, 5];
const copy = [...arr];
const merged = [...arr1, ...arr2];

// Array.from
Array.from({length: 5}, (_, i) => i);  // [0, 1, 2, 3, 4]
Array.from("hello");                   // ['h', 'e', 'l', 'l', 'o']
Array.from(new Set([1, 1, 2]));        // [1, 2] — dedup

// Array.of
Array.of(1, 2, 3);  // [1, 2, 3]

// at() method — negative indices
arr.at(-1);   // last element
arr.at(-2);   // second to last
```

## Objects

```javascript
// Object creation
const user = { id: 1, name: "Fahmi", active: true };

// Property access
user.name          // dot notation
user["name"]       // bracket notation (use when key is dynamic)
const key = "name";
user[key]          // "Fahmi"

// Shorthand
const name = "Fahmi";
const obj = { name, age: 30 }; // { name: "Fahmi", age: 30 }

// Computed property names
const prefix = "user_";
const dynamic = { [prefix + "id"]: 1, [`${prefix}name`]: "Fahmi" };

// Methods
const counter = {
    count: 0,
    increment() { this.count++; },
    reset: function() { this.count = 0; },
    // Don't use arrow functions for methods — they don't have their own 'this'
};

// Object methods
Object.keys(obj)          // ["id", "name"]
Object.values(obj)        // [1, "Fahmi"]
Object.entries(obj)       // [["id", 1], ["name", "Fahmi"]]
Object.assign(target, source)  // shallow merge
Object.freeze(obj)        // prevent modification (shallow)
Object.create(proto)      // create with specified prototype
Object.hasOwn(obj, "key") // check own property (modern)

// Spread / destructuring
const { name, age = 25, ...rest } = user;
const merged = { ...defaults, ...overrides };
const copy = { ...original };

// Optional chaining
user?.address?.city
users?.[0]?.name
obj?.method?.()

// Nullish coalescing
const port = config.port ?? 3000;

// Symbols as property keys (unique, non-enumerable by default)
const id = Symbol("id");
obj[id] = 123;
Object.keys(obj); // does NOT include Symbol keys

// Object.fromEntries (reverse of entries)
const map = [["a", 1], ["b", 2]];
Object.fromEntries(map); // { a: 1, b: 2 }

// Property descriptors
Object.defineProperty(obj, "id", {
    value: 42,
    writable: false,
    enumerable: true,
    configurable: false,
});
```

## Promises and Async

```javascript
// Creating a Promise
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));
const fetchData = (url) => new Promise((resolve, reject) => {
    setTimeout(() => {
        if (url.startsWith("https://")) resolve({ data: "ok" });
        else reject(new Error("HTTP only"));
    }, 1000);
});

// Consuming Promises
fetchData("https://api.example.com")
    .then(response => response.data)
    .then(data => console.log(data))
    .catch(err => console.error(err))
    .finally(() => console.log("done"));

// async/await
async function loadUser(id) {
    try {
        const response = await fetch(`/api/users/${id}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const user = await response.json();
        return user;
    } catch (err) {
        console.error("Failed:", err.message);
        return null;
    }
}

// Promise combinators
Promise.all([p1, p2, p3])          // all resolve or first reject
Promise.allSettled([p1, p2, p3])   // wait for all, get all results
Promise.race([p1, p2, p3])         // first to settle (resolve or reject)
Promise.any([p1, p2, p3])          // first to resolve (ignore rejects)
Promise.resolve(value)             // already-resolved promise
Promise.reject(error)              // already-rejected promise

// Parallel vs sequential
// Sequential (slow — waits for each)
const a = await fetchA();
const b = await fetchB();

// Parallel (fast — both run simultaneously)
const [a, b] = await Promise.all([fetchA(), fetchB()]);

// Async generators
async function* paginate(url) {
    let cursor = null;
    while (true) {
        const { items, next } = await fetch(`${url}?cursor=${cursor}`).then(r => r.json());
        yield* items;
        if (!next) break;
        cursor = next;
    }
}
for await (const item of paginate("/api/items")) {
    console.log(item);
}
```

## ES Modules

```javascript
// Named exports
export const PI = 3.14159;
export function add(a, b) { return a + b; }
export class EventBus { ... }

// Default export
export default class App { ... }

// Re-exports
export { add, PI } from "./math.js";
export * from "./utils.js";
export { default as App } from "./App.js";

// Imports
import { add, PI } from "./math.js";
import { add as sum } from "./math.js";
import * as math from "./math.js";
import App from "./App.js";
import App, { helper } from "./App.js";

// Dynamic import (lazy loading)
const { processData } = await import("./heavy.js");
button.onclick = async () => {
    const module = await import("./feature.js");
    module.init();
};

// Import assertions (JSON modules)
import data from "./config.json" assert { type: "json" };
```

## Error Handling

```javascript
// try/catch/finally
try {
    const result = JSON.parse(invalidJson);
} catch (err) {
    if (err instanceof SyntaxError) {
        console.error("Invalid JSON:", err.message);
    } else {
        throw err; // re-throw unexpected errors
    }
} finally {
    cleanup();
}

// Custom errors
class ValidationError extends Error {
    constructor(field, message) {
        super(message);
        this.name = "ValidationError";
        this.field = field;
    }
}

class NetworkError extends Error {
    constructor(status, message) {
        super(message);
        this.name = "NetworkError";
        this.status = status;
    }
}

// Error types
// Error, TypeError, RangeError, ReferenceError, SyntaxError
// URIError, EvalError

// Result pattern (avoid throw for expected errors)
function parseAge(str) {
    const n = parseInt(str, 10);
    if (isNaN(n) || n < 0 || n > 150) {
        return { ok: false, error: "Invalid age" };
    }
    return { ok: true, value: n };
}

const result = parseAge(input);
if (!result.ok) {
    showError(result.error);
} else {
    useAge(result.value);
}
```

## Browser APIs

```javascript
// DOM Manipulation
const el = document.querySelector(".user-card");
const els = document.querySelectorAll(".item");
const el2 = document.getElementById("main");
const el3 = document.createElement("div");

el.textContent = "New text";
el.innerHTML = "<strong>bold</strong>";   // XSS risk!
el.setAttribute("data-id", "123");
el.classList.add("active");
el.classList.remove("hidden");
el.classList.toggle("open");
el.classList.contains("active");
el.style.color = "red";
el.dataset.id;              // reads data-id attribute

// DOM events
el.addEventListener("click", (event) => {
    event.preventDefault();  // prevent default (e.g. form submit)
    event.stopPropagation(); // stop event bubbling up
    console.log(event.target, event.currentTarget);
});

// Event delegation (handle events on parent)
document.querySelector(".list").addEventListener("click", (e) => {
    if (e.target.matches(".item")) {
        handleItemClick(e.target);
    }
});

// Fetch API
const response = await fetch("/api/data", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ key: "value" }),
});
const data = await response.json();

// Web Storage
localStorage.setItem("key", JSON.stringify(value));
const value = JSON.parse(localStorage.getItem("key"));
localStorage.removeItem("key");
localStorage.clear();

sessionStorage.setItem("token", token); // clears when tab closes

// URL / History API
const url = new URL(window.location.href);
url.searchParams.get("q");
url.searchParams.set("page", "2");
history.pushState({ page: 2 }, "", `?page=2`);
window.addEventListener("popstate", (e) => console.log(e.state));

// Intersection Observer (lazy loading, infinite scroll)
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            loadMore();
        }
    });
}, { threshold: 0.1 });
observer.observe(document.querySelector(".sentinel"));
```

## Modern JavaScript Patterns

```javascript
// Iterator protocol
const range = {
    from: 1, to: 5,
    [Symbol.iterator]() {
        let current = this.from;
        const last = this.to;
        return {
            next() {
                if (current <= last) return { value: current++, done: false };
                return { value: undefined, done: true };
            }
        };
    }
};
for (const n of range) console.log(n); // 1 2 3 4 5

// Generator functions
function* fibonacci() {
    let [a, b] = [0, 1];
    while (true) {
        yield a;
        [a, b] = [b, a + b];
    }
}
const fib = fibonacci();
fib.next().value; // 0
fib.next().value; // 1
fib.next().value; // 1

// WeakMap / WeakSet (garbage collection friendly)
const privateData = new WeakMap();
class Person {
    constructor(name) {
        privateData.set(this, { name });
    }
    getName() { return privateData.get(this).name; }
}

// Proxy
const handler = {
    get(target, key) {
        return key in target ? target[key] : `Property ${key} not found`;
    },
    set(target, key, value) {
        if (typeof value !== "number") throw new TypeError("Must be number");
        target[key] = value;
        return true;
    }
};
const proxy = new Proxy({}, handler);
```

## Referensi Lanjut
- https://roadmap.sh/javascript
- https://javascript.info/ — comprehensive modern JS guide
- https://developer.mozilla.org/en-US/docs/Web/JavaScript
- https://tc39.es/ecma262/ — ECMAScript specification
- "You Don't Know JS" — Kyle Simpson (free on GitHub)
