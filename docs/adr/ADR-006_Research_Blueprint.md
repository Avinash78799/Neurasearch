# ADR-006: Research Blueprint

## Context
Running deep research queries directly is a high-cost operation. Users had no control over the planned research strategy before it was executed, leading to wasted API credits, time, and poor-quality reports.

## Decision
We implemented a two-stage transaction flow:
1. `POST /research/blueprint`: Decomposes the user question and returns a list of planned sub-queries.
2. `POST /research/execute`: Takes the approved/edited list of sub-queries and executes the parallel search and synthesis.

## Alternatives Considered
1. **Interactive Graph Interrupts**: Interrupted state executions inside LangGraph. Rejected because keeping SSE streams open while waiting for user REST requests is fragile and difficult to scale across stateless load balancers.

## Why Chosen
Stateless REST endpoints are robust, allow the client to modify the query plan arbitrarily, and fit naturally into clean HTTP schemas.

## Consequences
* Research sessions are tracked in the database under `research_sessions` table with status progression: `blueprint` -> `executing` -> `completed`.
* User has full visibility into the planner's strategy before launching execution.
