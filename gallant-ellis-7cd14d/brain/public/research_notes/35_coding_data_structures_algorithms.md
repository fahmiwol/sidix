# Data Structures & Algorithms

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

> Sumber: Sintesis dari CLRS (Introduction to Algorithms), LeetCode patterns, dan dokumentasi Python.
> Relevan untuk: software engineers, competitive programmers, technical interview candidates, CS students
> Tags: algorithms, data-structures, big-o, sorting, searching, graphs, dynamic-programming, python, interviews

## Big-O Notation and Complexity Analysis

Big-O notation describes the **upper bound** of an algorithm's growth rate as input size n approaches infinity. We drop constants and lower-order terms.

```
O(1)        — Constant: dict lookup, array index, stack push/pop
O(log n)    — Logarithmic: binary search, balanced BST operations
O(n)        — Linear: linear scan, simple sum
O(n log n)  — Linearithmic: efficient sorting (merge sort, heap sort, Timsort)
O(n²)       — Quadratic: nested loops, bubble/insertion sort
O(2ⁿ)       — Exponential: brute-force subsets
O(n!)       — Factorial: brute-force permutations
```

### Space vs Time Trade-offs
- Hash maps trade O(n) space for O(1) lookup (instead of O(n) scan)
- Memoization trades O(n) space for avoiding redundant computation
- In-place algorithms use O(1) space but often have worse time complexity

### Amortized Analysis
An operation's cost averaged over a sequence. Example: Python list `append` is O(1) amortized even though it occasionally triggers an O(n) resize — because resize doubles capacity, so n appends take O(n) total → O(1) each.

## Arrays and Lists

```python
# Python list — dynamic array under the hood
arr = [1, 2, 3, 4, 5]

# Operations complexity
arr[i]              # O(1) — random access
arr.append(x)       # O(1) amortized
arr.insert(0, x)    # O(n) — shifts all elements
arr.pop()           # O(1) — remove last
arr.pop(i)          # O(n) — shifts elements after i
x in arr            # O(n) — linear scan
arr.index(x)        # O(n)
arr.sort()          # O(n log n) — Timsort (stable)
len(arr)            # O(1)

# Two-pointer technique — O(n) for many array problems
def two_sum_sorted(nums: list[int], target: int) -> tuple[int, int] | None:
    """Find indices of two numbers that sum to target in sorted array."""
    left, right = 0, len(nums) - 1
    while left < right:
        s = nums[left] + nums[right]
        if s == target:
            return left, right
        elif s < target:
            left += 1
        else:
            right -= 1
    return None

# Sliding window — O(n) for subarray problems
def max_sum_subarray(nums: list[int], k: int) -> int:
    """Maximum sum of subarray of length k."""
    window = sum(nums[:k])
    best = window
    for i in range(k, len(nums)):
        window += nums[i] - nums[i - k]
        best = max(best, window)
    return best

# Prefix sum — O(1) range sum queries after O(n) preprocessing
def build_prefix(nums: list[int]) -> list[int]:
    prefix = [0] * (len(nums) + 1)
    for i, v in enumerate(nums):
        prefix[i + 1] = prefix[i] + v
    return prefix

def range_sum(prefix: list[int], l: int, r: int) -> int:
    return prefix[r + 1] - prefix[l]
```

## Hash Maps / Dictionaries

Python `dict` uses open addressing with a hash table. Average O(1) for get/set/delete; O(n) worst case with many collisions (rare with good hash functions).

```python
# Frequency count — classic hash map pattern
from collections import Counter, defaultdict

def top_k_frequent(nums: list[int], k: int) -> list[int]:
    counts = Counter(nums)
    return [x for x, _ in counts.most_common(k)]

# Anagram detection
def are_anagrams(s: str, t: str) -> bool:
    return Counter(s) == Counter(t)

# Two-sum with hash map — O(n) time, O(n) space
def two_sum(nums: list[int], target: int) -> tuple[int, int] | None:
    seen: dict[int, int] = {}  # value → index
    for i, v in enumerate(nums):
        complement = target - v
        if complement in seen:
            return seen[complement], i
        seen[v] = i
    return None

# Group anagrams
def group_anagrams(words: list[str]) -> list[list[str]]:
    groups: dict[tuple, list[str]] = defaultdict(list)
    for word in words:
        key = tuple(sorted(word))
        groups[key].append(word)
    return list(groups.values())

# LRU Cache from scratch using OrderedDict
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int):
        self.cap = capacity
        self.cache: OrderedDict[int, int] = OrderedDict()
    
    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)  # mark as recently used
        return self.cache[key]
    
    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.cap:
            self.cache.popitem(last=False)  # evict oldest
```

## Stacks and Queues

```python
from collections import deque

# Stack — LIFO — use list or deque
stack: list[int] = []
stack.append(3)   # push
stack.pop()       # pop O(1)
stack[-1]         # peek

# Queue — FIFO — use deque for O(1) both ends
queue: deque[int] = deque()
queue.append(3)       # enqueue right
queue.popleft()       # dequeue left O(1)
# list.pop(0) is O(n) — never use for queues

# Monotonic stack — classic pattern for "next greater element"
def next_greater(nums: list[int]) -> list[int]:
    result = [-1] * len(nums)
    stack: list[int] = []  # stores indices
    for i, v in enumerate(nums):
        while stack and nums[stack[-1]] < v:
            result[stack.pop()] = v
        stack.append(i)
    return result

# Valid parentheses
def is_valid_parens(s: str) -> bool:
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        elif not stack or stack[-1] != pairs[ch]:
            return False
        else:
            stack.pop()
    return not stack
```

## Linked Lists

```python
class ListNode:
    def __init__(self, val: int = 0, next: "ListNode | None" = None):
        self.val = val
        self.next = next

# Build from list
def build(vals: list[int]) -> ListNode | None:
    dummy = ListNode()
    cur = dummy
    for v in vals:
        cur.next = ListNode(v)
        cur = cur.next
    return dummy.next

# Reverse a linked list — O(n) iterative
def reverse(head: ListNode | None) -> ListNode | None:
    prev, cur = None, head
    while cur:
        nxt = cur.next
        cur.next = prev
        prev, cur = cur, nxt
    return prev

# Find middle — slow/fast pointer
def find_middle(head: ListNode) -> ListNode:
    slow = fast = head
    while fast.next and fast.next.next:
        slow = slow.next
        fast = fast.next.next
    return slow

# Detect cycle — Floyd's algorithm
def has_cycle(head: ListNode | None) -> bool:
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            return True
    return False

# Merge two sorted lists
def merge_sorted(l1: ListNode | None, l2: ListNode | None) -> ListNode | None:
    dummy = ListNode()
    cur = dummy
    while l1 and l2:
        if l1.val <= l2.val:
            cur.next, l1 = l1, l1.next
        else:
            cur.next, l2 = l2, l2.next
        cur = cur.next
    cur.next = l1 or l2
    return dummy.next
```

## Trees

### Binary Search Tree
```python
class TreeNode:
    def __init__(self, val: int):
        self.val = val
        self.left: "TreeNode | None" = None
        self.right: "TreeNode | None" = None

# Traversals
def inorder(root: TreeNode | None) -> list[int]:
    """Left → Root → Right. Gives sorted order for BST."""
    return inorder(root.left) + [root.val] + inorder(root.right) if root else []

def preorder(root: TreeNode | None) -> list[int]:
    """Root → Left → Right. Useful for serialization."""
    return [root.val] + preorder(root.left) + preorder(root.right) if root else []

def postorder(root: TreeNode | None) -> list[int]:
    """Left → Right → Root. Useful for deletion."""
    return postorder(root.left) + postorder(root.right) + [root.val] if root else []

# Level-order (BFS)
def level_order(root: TreeNode | None) -> list[list[int]]:
    if not root:
        return []
    result, queue = [], deque([root])
    while queue:
        level = []
        for _ in range(len(queue)):
            node = queue.popleft()
            level.append(node.val)
            if node.left: queue.append(node.left)
            if node.right: queue.append(node.right)
        result.append(level)
    return result

# BST operations
def bst_insert(root: TreeNode | None, val: int) -> TreeNode:
    if not root:
        return TreeNode(val)
    if val < root.val:
        root.left = bst_insert(root.left, val)
    elif val > root.val:
        root.right = bst_insert(root.right, val)
    return root

def bst_search(root: TreeNode | None, val: int) -> bool:
    if not root:
        return False
    if val == root.val:
        return True
    return bst_search(root.left if val < root.val else root.right, val)

# Height / depth
def height(root: TreeNode | None) -> int:
    return 0 if not root else 1 + max(height(root.left), height(root.right))

# Validate BST
def is_valid_bst(root: TreeNode | None, lo=-float("inf"), hi=float("inf")) -> bool:
    if not root:
        return True
    if not (lo < root.val < hi):
        return False
    return is_valid_bst(root.left, lo, root.val) and is_valid_bst(root.right, root.val, hi)
```

### Heap (Priority Queue)
```python
import heapq

# Python heapq is a min-heap
heap: list[int] = []
heapq.heappush(heap, 5)
heapq.heappush(heap, 1)
heapq.heappush(heap, 3)
heapq.heappop(heap)   # returns 1 (minimum)
heap[0]               # peek min without removing

# Max-heap: negate values
max_heap: list[int] = []
heapq.heappush(max_heap, -5)
-heapq.heappop(max_heap)  # 5

# K largest elements — O(n log k)
def k_largest(nums: list[int], k: int) -> list[int]:
    return heapq.nlargest(k, nums)

# Merge k sorted lists — O(n log k)
def merge_k_sorted(lists: list[list[int]]) -> list[int]:
    heap = [(lst[0], i, 0) for i, lst in enumerate(lists) if lst]
    heapq.heapify(heap)
    result = []
    while heap:
        val, list_idx, elem_idx = heapq.heappop(heap)
        result.append(val)
        if elem_idx + 1 < len(lists[list_idx]):
            heapq.heappush(heap, (lists[list_idx][elem_idx + 1], list_idx, elem_idx + 1))
    return result
```

## Graphs

```python
from collections import deque

# Adjacency list representation
graph = {
    "A": ["B", "C"],
    "B": ["A", "D", "E"],
    "C": ["A", "F"],
    "D": ["B"],
    "E": ["B"],
    "F": ["C"],
}

# BFS — shortest path in unweighted graph
def bfs(graph: dict, start: str) -> dict[str, int]:
    """Returns distances from start to all reachable nodes."""
    dist = {start: 0}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for neighbor in graph.get(node, []):
            if neighbor not in dist:
                dist[neighbor] = dist[node] + 1
                queue.append(neighbor)
    return dist

# DFS — iterative and recursive
def dfs_iterative(graph: dict, start: str) -> list[str]:
    visited = set()
    stack = [start]
    result = []
    while stack:
        node = stack.pop()
        if node not in visited:
            visited.add(node)
            result.append(node)
            stack.extend(reversed(graph.get(node, [])))
    return result

def dfs_recursive(graph: dict, node: str, visited: set | None = None) -> list[str]:
    if visited is None:
        visited = set()
    visited.add(node)
    result = [node]
    for neighbor in graph.get(node, []):
        if neighbor not in visited:
            result.extend(dfs_recursive(graph, neighbor, visited))
    return result

# Topological sort (Kahn's algorithm) — for DAGs
def topo_sort(n: int, edges: list[tuple[int, int]]) -> list[int] | None:
    """Returns topological order or None if cycle detected."""
    graph = [[] for _ in range(n)]
    in_degree = [0] * n
    for u, v in edges:
        graph[u].append(v)
        in_degree[v] += 1
    
    queue = deque(i for i in range(n) if in_degree[i] == 0)
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    return order if len(order) == n else None  # cycle if not all nodes

# Dijkstra's shortest path — O((V + E) log V)
def dijkstra(graph: dict[str, list[tuple[str, int]]], start: str) -> dict[str, float]:
    dist = {start: 0}
    heap = [(0, start)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, float("inf")):
            continue
        for v, weight in graph.get(u, []):
            new_dist = d + weight
            if new_dist < dist.get(v, float("inf")):
                dist[v] = new_dist
                heapq.heappush(heap, (new_dist, v))
    return dist
```

## Sorting Algorithms

```python
# Quicksort — O(n log n) average, O(n²) worst, O(log n) space
def quicksort(arr: list[int]) -> list[int]:
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    mid = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + mid + quicksort(right)

# In-place Lomuto partition quicksort
def quicksort_inplace(arr: list[int], lo: int = 0, hi: int | None = None) -> None:
    if hi is None:
        hi = len(arr) - 1
    if lo >= hi:
        return
    pivot = arr[hi]
    i = lo - 1
    for j in range(lo, hi):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    arr[i + 1], arr[hi] = arr[hi], arr[i + 1]
    p = i + 1
    quicksort_inplace(arr, lo, p - 1)
    quicksort_inplace(arr, p + 1, hi)

# Mergesort — O(n log n) guaranteed, O(n) space, stable
def mergesort(arr: list[int]) -> list[int]:
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = mergesort(arr[:mid])
    right = mergesort(arr[mid:])
    return merge(left, right)

def merge(left: list[int], right: list[int]) -> list[int]:
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    return result + left[i:] + right[j:]

# Heapsort — O(n log n), O(1) space, not stable
def heapsort(arr: list[int]) -> list[int]:
    import heapq
    h = arr[:]
    heapq.heapify(h)
    return [heapq.heappop(h) for _ in range(len(h))]
```

## Binary Search

```python
# Standard binary search — O(log n)
def binary_search(arr: list[int], target: int) -> int:
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = lo + (hi - lo) // 2  # avoids overflow (important in other languages)
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1

# Left-most position where arr[i] >= target (lower bound)
def lower_bound(arr: list[int], target: int) -> int:
    lo, hi = 0, len(arr)
    while lo < hi:
        mid = (lo + hi) // 2
        if arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo

# Binary search on answer — search over the solution space, not the array
def min_days_to_make_bouquets(bloom: list[int], m: int, k: int) -> int:
    """Minimum days to make m bouquets of k adjacent flowers."""
    def can_make(days: int) -> bool:
        bouquets = consecutive = 0
        for b in bloom:
            if b <= days:
                consecutive += 1
                if consecutive == k:
                    bouquets += 1
                    consecutive = 0
            else:
                consecutive = 0
        return bouquets >= m
    
    lo, hi = min(bloom), max(bloom)
    while lo < hi:
        mid = (lo + hi) // 2
        if can_make(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo if can_make(lo) else -1

# Use Python bisect module for sorted arrays
import bisect
arr = [1, 3, 4, 4, 7, 9]
bisect.bisect_left(arr, 4)   # 2 — leftmost position of 4
bisect.bisect_right(arr, 4)  # 4 — rightmost position of 4
bisect.insort(arr, 5)        # insert 5 maintaining sort order
```

## Dynamic Programming

DP solves problems by breaking them into overlapping subproblems and storing results. Two approaches: top-down (memoization) and bottom-up (tabulation).

```python
from functools import lru_cache

# 1. Fibonacci — canonical DP
@lru_cache(maxsize=None)
def fib(n: int) -> int:
    if n < 2: return n
    return fib(n-1) + fib(n-2)

# Bottom-up O(n) time, O(1) space
def fib_dp(n: int) -> int:
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

# 2. Longest Common Subsequence — O(m*n) time and space
def lcs(s1: str, s2: str) -> int:
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    return dp[m][n]

# 3. 0/1 Knapsack
def knapsack(weights: list[int], values: list[int], capacity: int) -> int:
    n = len(weights)
    dp = [0] * (capacity + 1)  # space optimized
    for i in range(n):
        for w in range(capacity, weights[i] - 1, -1):  # reverse to avoid reuse
            dp[w] = max(dp[w], dp[w - weights[i]] + values[i])
    return dp[capacity]

# 4. Coin Change — minimum coins
def coin_change(coins: list[int], amount: int) -> int:
    dp = [float("inf")] * (amount + 1)
    dp[0] = 0
    for c in coins:
        for a in range(c, amount + 1):
            dp[a] = min(dp[a], dp[a - c] + 1)
    return dp[amount] if dp[amount] != float("inf") else -1

# 5. Longest Increasing Subsequence — O(n log n) with patience sorting
def lis_length(nums: list[int]) -> int:
    tails = []
    for n in nums:
        pos = bisect.bisect_left(tails, n)
        if pos == len(tails):
            tails.append(n)
        else:
            tails[pos] = n
    return len(tails)
```

## Greedy Algorithms

Greedy makes the locally optimal choice at each step. Works when the problem has the "greedy choice property" — local optimum leads to global optimum.

```python
# Interval scheduling — maximize non-overlapping intervals
def max_non_overlapping(intervals: list[tuple[int, int]]) -> int:
    sorted_intervals = sorted(intervals, key=lambda x: x[1])  # sort by end time
    count, last_end = 0, float("-inf")
    for start, end in sorted_intervals:
        if start >= last_end:
            count += 1
            last_end = end
    return count

# Minimum number of platforms (trains)
def min_platforms(arrivals: list[int], departures: list[int]) -> int:
    arrivals.sort()
    departures.sort()
    platforms = result = 0
    i = j = 0
    while i < len(arrivals):
        if arrivals[i] <= departures[j]:
            platforms += 1
            i += 1
        else:
            platforms -= 1
            j += 1
        result = max(result, platforms)
    return result

# Jump Game — can you reach the end?
def can_jump(nums: list[int]) -> bool:
    max_reach = 0
    for i, n in enumerate(nums):
        if i > max_reach:
            return False
        max_reach = max(max_reach, i + n)
    return True
```

## Time Complexity Quick Reference

| Operation | Best | Average | Worst | Space |
|-----------|------|---------|-------|-------|
| Array access | O(1) | O(1) | O(1) | O(n) |
| Hash table get/set | O(1) | O(1) | O(n) | O(n) |
| BST search | O(log n) | O(log n) | O(n) | O(n) |
| Heap push/pop | O(log n) | O(log n) | O(log n) | O(n) |
| BFS/DFS | O(V+E) | O(V+E) | O(V+E) | O(V) |
| Quicksort | O(n log n) | O(n log n) | O(n²) | O(log n) |
| Mergesort | O(n log n) | O(n log n) | O(n log n) | O(n) |
| Binary search | O(1) | O(log n) | O(log n) | O(1) |

## Referensi & Sumber Lanjut
- https://neetcode.io/ — curated problem sets by pattern
- https://leetcode.com/explore/
- CLRS: Introduction to Algorithms (Cormen et al.)
- https://docs.python.org/3/library/heapq.html
- https://docs.python.org/3/library/bisect.html
- roadmap.sh/computer-science
