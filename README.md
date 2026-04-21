# Problem Statement: Intelligent DSA Revision Planner

## The Problem

Students preparing for coding interviews and competitive programming often solve DSA problems in random order.
This leads to three major issues:

1. Knowledge decay: previously solved concepts are forgotten after a few days.
2. Poor prioritization: weak topics are not reviewed at the right time.
3. Inefficient scheduling: available study time is not used optimally.

As a result, learners spend high effort but get low long-term retention and inconsistent interview readiness.

## Proposed Problem Focus

Design a study system that decides:

- which problem a student should solve next,
- when each solved problem should be reviewed,
- how to allocate limited daily time across topics.

## DSA Algorithms Used 

### 1) Priority Queue (Heap)

Use a max-heap or min-heap to rank due problems by urgency score.

Example urgency factors:

- days overdue,
- low confidence history,
- high-value interview topic weight.

Why this fits DSA: selecting the next best item repeatedly is efficient with heap operations in O(log n).

### 2) Greedy Scheduling

Given fixed daily study time, pick problems that maximize learning gain per minute.

Why this fits DSA: greedy selection provides a practical near-optimal schedule under time constraints.

<!-- ### 3) Graph Traversal on Topic Dependencies
Model topics as a directed graph (for example, Arrays -> Hashing -> Sliding Window -> Dynamic Programming).
Use topological ordering to avoid recommending advanced topics before prerequisites are covered.

Why this fits DSA: dependency management is a classic directed acyclic graph problem. -->

<!-- ### 4) Dynamic Programming (Advanced Optimization)

Optimize a multi-day plan where each topic has expected retention gain and time cost.

State idea:

- dp[day][time] = maximum mastery score achievable.

Why this fits DSA: this is a bounded optimization problem solved effectively using DP. -->
