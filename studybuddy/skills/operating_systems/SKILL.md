# SKILL: Operating Systems — Question Generation Guide

## Goal
Help BSCS students build deep understanding of how an OS manages
resources — not just memorise terms.

## Key Topics
Process lifecycle, CPU scheduling algorithms (FCFS, SJF, RR, Priority,
MLFQ), deadlock conditions and handling, memory management (paging,
segmentation, virtual memory), synchronisation primitives, file systems.

## Question Design by Difficulty

**Recall (Easy)**
Ask for definitions, state names, or algorithm properties.
_Example: "What are the four necessary conditions for deadlock?"_

**Application (Medium)**
Give a concrete scenario — process burst times, page tables, semaphore
sequences — and ask for calculation or trace output.
_Example: "Calculate average waiting time for P1–P3 using Round Robin (quantum=2)."_

**Analysis (Hard)**
Combine two concepts or introduce an edge case requiring reasoning.
_Example: "Why does MLFQ use aging, and what starvation scenario does it prevent?"_

## Tips
- Always ground medium/hard questions in specific numbers or diagrams.
- Prefer "explain why" over "what is" for harder levels.
- Common misconceptions to test: turnaround vs waiting time, SJF vs SRTF,
  internal vs external fragmentation.
