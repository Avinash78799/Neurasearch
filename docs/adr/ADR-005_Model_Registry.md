# ADR-005: Model Registry

## Context
Instantiating large models (like `ChatOllama` or `OllamaEmbeddings`) inside request handlers or graph nodes creates duplicate instances, consuming CPU resources, increasing memory overhead, and slowing down response times.

## Decision
We implemented `ModelRegistry` (`backend/core/model_registry.py`) which instantiates the LLM and Embedding objects lazily as module-level singletons.

## Alternatives Considered
1. **Ad-hoc Instantiation**: Creating new model instances inside each node function call. Rejected because the constructor runs on every call, creating unnecessary garbage collection overhead and latency spikes.

## Why Chosen
Lazy singletons guarantee that only a single instance of each model client is maintained in memory for the duration of the server process.

## Consequences
* Nodes and research functions import models via `get_llm()` and `get_embeddings()`.
* Simplifies unit testing since models can be easily mocked or swapped at one central entry point.
