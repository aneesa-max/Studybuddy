# SKILL: Data Structures — Question Generation Guide

## Goal
Build intuition for *why* a data structure works, not just how to use
it — so students can choose and adapt the right structure for any problem.

## Key Topics
Arrays, linked lists (singly, doubly, circular), stacks, queues, trees
(BST, AVL, heap), graphs (BFS, DFS, shortest path), hashing (collision
resolution), sorting algorithms and their complexity.

## Question Design by Difficulty

**Recall (Easy)**
Test definitions, Big-O bounds, or structural properties.
_Example: "What is the worst-case time complexity of inserting into an AVL tree, and why?"_

**Application (Medium)**
Trace through an algorithm with a given input, or ask which structure
best solves a described problem and justify the choice.
_Example: "Trace BST insertion for the sequence [50, 30, 70, 20, 40]. Draw the resulting tree."_

**Analysis (Hard)**
Compare trade-offs, identify failure modes, or modify an algorithm.
_Example: "A min-heap supports O(1) find-min but O(log n) delete. Design a structure supporting both in O(1)."_

## Tips
- Use small concrete inputs (5–8 elements) for trace questions.
- Require Big-O justification, not just the answer.
- Test edge cases: empty structure, single element, duplicate keys.
