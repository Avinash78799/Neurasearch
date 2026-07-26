# Performance Benchmarks

Performance profile of NeuraSearch RAG pipeline and deep research orchestration.

## Execution Metrics

The execution timeline of deep research spans multiple phases: query decomposition, parallel chunk retrieval, reciprocal rank fusion (RRF), document grading, and report synthesis.

### With Local CPU Inference (Llama 3.1 8B Q4_K_M)
- **Blueprint Generation**: ~16.8 seconds
- **Parallel Retrieval (3 queries)**: ~134.4 seconds (Ollama CPU sequential execution)
- **Synthesis Report**: ~153.3 seconds

### Core Orchestration Overhead (Mocked LLM)
- **Blueprint Generation**: < 1.0 ms
- **Parallel Retrieval**: ~20.6 ms
- **Report Synthesis**: < 1.0 ms
- **State Checkpoint Saver**: ~0.0 ms

### Memory Profile
- **Active Idle State**: ~119.5 MB
- **Peak Query Execution**: ~121.4 MB
- **Leaked Memory / Iteration**: ~0.0 KB (Zero memory leak detected)
