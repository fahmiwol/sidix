# Data Structures & Algorithms — Topic Index + Quick Reference

> Sumber: roadmap.sh/datastructures-and-algorithms (CC BY-SA 4.0)
> Referensi: https://roadmap.sh/datastructures-and-algorithms

## Programming Fundamentals
- Language Syntax, Control Structures, Functions
- OOP Basics, Pseudo Code

## Basic Data Structures

### Array (List)
- Ordered collection, O(1) index access, O(n) search/insert/delete
- Python: `arr = [1, 2, 3]`, `arr.append(x)`, `arr[i]`

### Linked Lists
- Singly linked (node → node → None)
- Doubly linked (prev ↔ node ↔ next)
- O(1) insert at head, O(n) search

### Stacks (LIFO)
- push, pop, peek — O(1)
- Python: `stack = []`, `stack.append(x)`, `stack.pop()`
- Use: undo/redo, function call stack, balanced parentheses

### Queues (FIFO)
- enqueue, dequeue — O(1) with deque
- Python: `from collections import deque; q = deque()`
- Use: BFS, task scheduling, message queue

### Hash Tables / Dict
- O(1) average get/set/delete
- Python: `d = {}`, `d[key] = val`, `d.get(key)`
- Collision resolution: chaining, open addressing

## Algorithmic Complexity

### Time vs Space Complexity
- Time: how long does it take? Space: how much memory?

### Common Runtimes (Best → Worst)
| Notation | Name | Example |
|---|---|---|
| O(1) | Constant | Array index access |
| O(log n) | Logarithmic | Binary search |
| O(n) | Linear | Linear scan |
| O(n log n) | Linearithmic | Merge sort, Heap sort |
| O(n²) | Polynomial | Bubble sort, nested loops |
| O(2^n) | Exponential | Recursive Fibonacci naive |
| O(n!) | Factorial | Permutations |

### Asymptotic Notation
- Big-O: worst case (O(n))
- Big-Theta (Θ): tight bound (exact growth)
- Big-Omega (Ω): best case

## Sorting Algorithms

| Algorithm | Best | Average | Worst | Space | Stable |
|---|---|---|---|---|---|
| Bubble Sort | O(n) | O(n²) | O(n²) | O(1) | Yes |
| Insertion Sort | O(n) | O(n²) | O(n²) | O(1) | Yes |
| Selection Sort | O(n²) | O(n²) | O(n²) | O(1) | No |
| Merge Sort | O(n log n) | O(n log n) | O(n log n) | O(n) | Yes |
| Quick Sort | O(n log n) | O(n log n) | O(n²) | O(log n) | No |
| Heap Sort | O(n log n) | O(n log n) | O(n log n) | O(1) | No |

```python
# Merge Sort — Python
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    return result + left[i:] + right[j:]

# Quick Sort — Python
def quick_sort(arr, lo=0, hi=None):
    if hi is None: hi = len(arr) - 1
    if lo < hi:
        p = partition(arr, lo, hi)
        quick_sort(arr, lo, p - 1)
        quick_sort(arr, p + 1, hi)

def partition(arr, lo, hi):
    pivot = arr[hi]
    i = lo - 1
    for j in range(lo, hi):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    arr[i+1], arr[hi] = arr[hi], arr[i+1]
    return i + 1
```

## Search Algorithms

```python
# Linear Search — O(n)
def linear_search(arr, target):
    for i, x in enumerate(arr):
        if x == target: return i
    return -1

# Binary Search — O(log n) — requires sorted array
def binary_search(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target: return mid
        elif arr[mid] < target: lo = mid + 1
        else: hi = mid - 1
    return -1
```

## Tree Data Structures

### Tree Traversal
```python
class Node:
    def __init__(self, val, left=None, right=None):
        self.val = val; self.left = left; self.right = right

def inorder(root):    # Left → Root → Right (sorted for BST)
    if root: inorder(root.left); print(root.val); inorder(root.right)

def preorder(root):   # Root → Left → Right
    if root: print(root.val); preorder(root.left); preorder(root.right)

def postorder(root):  # Left → Right → Root
    if root: postorder(root.left); postorder(root.right); print(root.val)
```

### Tree Types
- **Binary Tree**: max 2 children
- **Binary Search Tree (BST)**: left < node < right, O(log n) average search
- **AVL Tree**: self-balancing BST, height diff ≤ 1
- **Heap (Min/Max)**: complete binary tree; parent ≤ children (min-heap)
- **B-Tree**: multi-way search tree; used in databases (PostgreSQL, MySQL)

## Graph Data Structures

```python
# BFS — Breadth First Search
from collections import deque
def bfs(graph, start):
    visited = set([start])
    queue = deque([start])
    while queue:
        node = queue.popleft()
        print(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

# DFS — Depth First Search (recursive)
def dfs(graph, node, visited=None):
    if visited is None: visited = set()
    visited.add(node)
    print(node)
    for neighbor in graph[node]:
        if neighbor not in visited:
            dfs(graph, neighbor, visited)
```

### Graph Algorithms
- **BFS**: shortest path (unweighted), level-order traversal
- **DFS**: cycle detection, topological sort, connected components
- **Dijkstra's**: shortest path (weighted, non-negative)
- **Bellman-Ford**: shortest path (handles negative weights)
- **Prim's / Kruskal's**: Minimum Spanning Tree

## Dynamic Programming

Key insight: break problem into overlapping subproblems, store results (memoization).

```python
# Fibonacci — O(n) with memoization
from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n):
    if n <= 1: return n
    return fib(n-1) + fib(n-2)

# 0/1 Knapsack
def knapsack(weights, values, capacity):
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            dp[i][w] = dp[i-1][w]
            if weights[i-1] <= w:
                dp[i][w] = max(dp[i][w], dp[i-1][w - weights[i-1]] + values[i-1])
    return dp[n][capacity]

# Longest Common Subsequence
def lcs(a, b):
    m, n = len(a), len(b)
    dp = [[0]*(n+1) for _ in range(m+1)]
    for i in range(1, m+1):
        for j in range(1, n+1):
            if a[i-1] == b[j-1]: dp[i][j] = dp[i-1][j-1] + 1
            else: dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    return dp[m][n]
```

## Problem Solving Techniques
- **Brute Force**: try all possibilities
- **Backtracking**: explore + prune (N-Queens, Sudoku)
- **Greedy**: local optimum → global (Activity Selection, Huffman)
- **Divide and Conquer**: split → solve → combine (Merge Sort, FFT)
- **Dynamic Programming**: overlapping subproblems + optimal substructure
- **Two Pointer**: sorted arrays, pair problems (O(n) vs O(n²))
- **Sliding Window**: contiguous subarray/substring problems

## Advanced Data Structures
- **Trie**: prefix tree; O(m) search where m = word length; used in autocomplete
- **Segment Tree**: range queries + updates; O(log n)
- **Fenwick Tree (BIT)**: prefix sums; O(log n) update + query
- **Disjoint Set (Union-Find)**: detect cycle, connected components; near O(1) with path compression
- **Skip List**: probabilistic sorted list; O(log n) average

## Platforms untuk Latihan
- LeetCode: https://leetcode.com
- Edabit: https://edabit.com
- HackerRank, Codeforces, AtCoder

## Referensi
- https://roadmap.sh/datastructures-and-algorithms
- https://visualgo.net (visualisasi algoritma)
- Big-O Cheat Sheet: https://bigocheatsheet.com
