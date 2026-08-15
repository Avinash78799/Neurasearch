"""
NeuraSearch – Standardized AI Research & Data Analysis Benchmark Suite.

Implements the 10-Dimensional Comparative Benchmark for AI Research Intelligence:
1. Simple Factual Precision
2. Multi-Source Deep Research Depth
3. Contradictory Evidence Resolution
4. Current Information / Freshness
5. Academic Literature & Methodological Comparison
6. Dataset & Statistical Analysis (F1, Precision, Recall, Class Imbalance)
7. Adversarial / False Premise Challenging
8. Source & Citation Verification (Citation Accuracy %)
9. Research Synthesis & Research Gap Identification
10. Publication-Quality Report Structure (20-Section Standard)
"""

import logging
import time
import asyncio
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from core.model_registry import get_llm
from config import settings

logger = logging.getLogger("neurasearch.eval.benchmark")

BENCHMARK_PROMPTS = [
    {
        "test_id": 1,
        "name": "Simple Factual Precision",
        "category": "Factual Accuracy",
        "prompt": "What is the computational complexity of standard self-attention with respect to sequence length N, and which exact equation describes it?",
        "ground_truth": "O(N^2) time and memory complexity for standard self-attention, described by softmax(QK^T / sqrt(d_k))V.",
        "max_score": 10
    },
    {
        "test_id": 2,
        "name": "Multi-Source Deep Research",
        "category": "Research Depth",
        "prompt": "Synthesize the primary trade-offs between dense retrieval (bi-encoders), sparse retrieval (BM25), and hybrid Reciprocal Rank Fusion (RRF).",
        "ground_truth": "Dense captures semantic meaning but struggles with out-of-vocabulary terms; BM25 excels at exact keyword matching but misses semantic paraphrases; RRF combines both linearly without score calibration issues.",
        "max_score": 10
    },
    {
        "test_id": 3,
        "name": "Contradictory Evidence Resolution",
        "category": "Contradiction Detection",
        "prompt": "Study A claims that Llama 3.2 3B achieves 82% on MMLU under 5-shot evaluation. Study B claims that Llama 3.2 3B achieves 63% on MMLU under 0-shot evaluation. Explain the discrepancy and how evaluation protocols alter reported benchmarks.",
        "ground_truth": "Few-shot prompting provides in-context demonstrations that dramatically elevate scores compared to zero-shot; differences in prompt templates and evaluation frameworks account for the variance.",
        "max_score": 10
    },
    {
        "test_id": 4,
        "name": "Academic Literature & Methodological Comparison",
        "category": "Methodology",
        "prompt": "Compare Corrective RAG (CRAG) against Self-RAG. Contrast their grading mechanisms, fallback pathways, and compute overhead.",
        "ground_truth": "CRAG uses document graders and web search fallback; Self-RAG integrates special reflection tokens and critique models natively.",
        "max_score": 10
    },
    {
        "test_id": 5,
        "name": "Dataset & Statistical Analysis",
        "category": "Data Analysis",
        "prompt": "A model achieves 99.1% accuracy on a fraud detection dataset containing 990 non-fraudulent and 10 fraudulent samples. Why is accuracy misleading here, and what would the Precision, Recall, and F1-score be if the model predicts all samples as non-fraudulent?",
        "ground_truth": "Accuracy paradox in class imbalanced datasets. If all predicted non-fraud: Accuracy=99.0%, Precision=Undefined/0, Recall=0%, F1=0%.",
        "max_score": 10
    },
    {
        "test_id": 6,
        "name": "Adversarial / False Premise Challenging",
        "category": "Critical Thinking",
        "prompt": "Explain why Albert Einstein was awarded the Nobel Prize in Physics for developing the General Theory of Relativity in 1921.",
        "ground_truth": "The premise is false: Einstein was awarded the 1921 Nobel Prize for his explanation of the Photoelectric Effect, not General Relativity.",
        "max_score": 10
    },
    {
        "test_id": 7,
        "name": "Source & Citation Verification",
        "category": "Citation Accuracy",
        "prompt": "Verify the following claim: 'Vaswani et al. (2017) introduced the Transformer in the paper titled Attention Is All You Need published at NeurIPS.' Is this citation verified?",
        "ground_truth": "Verified: Vaswani et al. (2017) Attention Is All You Need was presented at NeurIPS 2017.",
        "max_score": 10
    },
    {
        "test_id": 8,
        "name": "Research Gap Identification",
        "category": "Research Synthesis",
        "prompt": "Identify 2 major unresolved research gaps in current small language model (SLM) on-device RAG deployments.",
        "ground_truth": "1. Context window vs memory footprint on low-VRAM GPUs. 2. Quantization loss degrading reasoning precision.",
        "max_score": 10
    },
    {
        "test_id": 9,
        "name": "Tripartite Fact vs Interpretation Separation",
        "category": "Epistemic Rigor",
        "prompt": "Present the distinction between Empirical Fact, Analytical Setup, and Strategic Implication for a benchmark showing 40% latency reduction with HyDE embeddings.",
        "ground_truth": "Fact: 40% reduction in query-to-retrieval time. Analysis: Pre-computed hypothetical vector avoids multi-pass rewrites. Implication: Enables real-time local search on edge devices.",
        "max_score": 10
    },
    {
        "test_id": 10,
        "name": "Publication-Grade Report Structure",
        "category": "Output Quality",
        "prompt": "Draft an outline of a 20-section academic research report investigating AI research benchmarks.",
        "ground_truth": "Includes Title, Abstract, Keywords, Problem, Methodology, Evidence Matrix, Analysis, Comparative Analysis, Discussion, Limitations, Research Gaps, References.",
        "max_score": 10
    }
]


class BenchmarkTestResult(BaseModel):
    test_id: int
    name: str
    category: str
    prompt: str
    response: str
    latency_ms: float
    score: float
    max_score: float = 10.0
    passed: bool
    evaluation_notes: str


class BenchmarkSuiteSummary(BaseModel):
    total_score: float
    max_total_score: float = 100.0
    percentage: float
    citation_accuracy_pct: float
    hallucination_rate_pct: float
    data_analysis_accuracy_pct: float
    average_latency_ms: float
    model_name: str
    provider: str
    test_results: List[BenchmarkTestResult]


async def run_standard_benchmark() -> BenchmarkSuiteSummary:
    """Execute the standardized 10-dimension AI Research & Data Analysis Benchmark suite."""
    llm = get_llm()
    results: List[BenchmarkTestResult] = []
    total_score = 0.0
    total_latency = 0.0

    logger.info("Executing 10-Dimension AI Research Benchmark on provider=%s model=%s",
                settings.llm_provider, settings.ollama_llm_model)

    for test in BENCHMARK_PROMPTS:
        t0 = time.time()
        try:
            resp = await llm.ainvoke(test["prompt"])
            ans_text = resp.content.strip()
            latency = (time.time() - t0) * 1000.0
            total_latency += latency

            # Automated heuristic scoring against key ground truth concepts
            gt_keywords = [w.lower() for w in test["ground_truth"].split() if len(w) > 4]
            matches = sum(1 for kw in gt_keywords if kw in ans_text.lower())
            ratio = min(1.0, (matches / max(1, len(gt_keywords) * 0.4)))
            score = round(ratio * test["max_score"], 1)
            passed = score >= (test["max_score"] * 0.6)

            results.append(BenchmarkTestResult(
                test_id=test["test_id"],
                name=test["name"],
                category=test["category"],
                prompt=test["prompt"],
                response=ans_text,
                latency_ms=round(latency, 1),
                score=score,
                max_score=test["max_score"],
                passed=passed,
                evaluation_notes="Automated benchmark verification against canonical baseline."
            ))
            total_score += score
        except Exception as exc:
            latency = (time.time() - t0) * 1000.0
            results.append(BenchmarkTestResult(
                test_id=test["test_id"],
                name=test["name"],
                category=test["category"],
                prompt=test["prompt"],
                response=f"Execution error: {exc}",
                latency_ms=round(latency, 1),
                score=0.0,
                max_score=test["max_score"],
                passed=False,
                evaluation_notes=f"Failed execution: {exc}"
            ))

    avg_lat = round(total_latency / max(1, len(BENCHMARK_PROMPTS)), 1)
    pct = round((total_score / 100.0) * 100.0, 1)

    # Derived research metrics from benchmark results
    citation_score = next((r.score for r in results if r.test_id == 7), 8.0)
    data_analysis_score = next((r.score for r in results if r.test_id == 5), 8.0)
    false_premise_score = next((r.score for r in results if r.test_id == 6), 8.0)

    citation_accuracy = round((citation_score / 10.0) * 100.0, 1)
    data_accuracy = round((data_analysis_score / 10.0) * 100.0, 1)
    hallucination_rate = round(max(0.0, 100.0 - (false_premise_score / 10.0 * 100.0)), 1)

    return BenchmarkSuiteSummary(
        total_score=round(total_score, 1),
        max_total_score=100.0,
        percentage=pct,
        citation_accuracy_pct=citation_accuracy,
        hallucination_rate_pct=hallucination_rate,
        data_analysis_accuracy_pct=data_accuracy,
        average_latency_ms=avg_lat,
        model_name=settings.ollama_llm_model if settings.llm_provider == "ollama" else (settings.groq_model or settings.openai_model),
        provider=settings.llm_provider,
        test_results=results
    )
