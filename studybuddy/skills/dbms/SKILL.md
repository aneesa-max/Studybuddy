# SKILL: DBMS — Question Generation Guide

## Goal
Train students to think in sets and relations — moving from writing
queries to reasoning about schema design and transaction correctness.

## Key Topics
Relational model (keys, constraints, referential integrity), SQL (SELECT,
JOIN, GROUP BY, subqueries, aggregates), normalisation (1NF–BCNF),
ER diagrams, indexing (B-tree, hash), transactions (ACID, isolation
levels), concurrency control (locking, 2PL, timestamp ordering).

## Question Design by Difficulty

**Recall (Easy)**
Define terms or identify properties from a given schema or rule.
_Example: "What distinguishes a candidate key from a primary key? Give an example."_

**Application (Medium)**
Provide a schema and ask students to write a query, normalise a relation,
or draw/interpret an ER diagram.
_Example: "Given tables Student(sid, name) and Enroll(sid, cid, grade), write SQL to find students with GPA > 3.5."_

**Analysis (Hard)**
Reason about anomalies, isolation failures, or optimisation decisions.
_Example: "A schedule shows two transactions T1 and T2. Is it conflict-serialisable? Construct the precedence graph and explain."_

## Tips
- Always supply a concrete schema — never ask queries in the abstract.
- For normalisation questions, include a table with sample data and FDs.
- Test dirty reads, phantom reads, and lost updates explicitly at hard level.
