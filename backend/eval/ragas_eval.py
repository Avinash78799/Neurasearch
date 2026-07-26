"""
RAGAS Evaluation Runner
Evaluates RAG pipeline quality using RAGAS metrics with local Ollama models.
Uses LangchainLLMWrapper to wrap Ollama for RAGAS compatibility.
"""

import logging
from typing import Optional

from langchain_ollama import ChatOllama, OllamaEmbeddings

from config import settings

logger = logging.getLogger(__name__)


def _get_evaluator_llm():
    """Create a wrapped LLM for RAGAS evaluation using local Ollama."""
    try:
        from ragas.llms import LangchainLLMWrapper

        llm = ChatOllama(
            model=settings.ollama_llm_model,
            base_url=settings.ollama_base_url,
            temperature=0,
        )
        return LangchainLLMWrapper(llm)
    except ImportError:
        logger.error("ragas package not installed. Run: pip install ragas")
        return None


def _get_evaluator_embeddings():
    """Create wrapped embeddings for RAGAS evaluation using local Ollama."""
    try:
        from ragas.embeddings import LangchainEmbeddingsWrapper

        embeddings = OllamaEmbeddings(
            model=settings.ollama_embed_model,
            base_url=settings.ollama_base_url,
        )
        return LangchainEmbeddingsWrapper(embeddings)
    except ImportError:
        logger.error("ragas package not installed. Run: pip install ragas")
        return None


async def _eval_metric_with_llm(llm: ChatOllama, prompt: str) -> float:
    """Helper to query Ollama for a 1-5 score and map it to 0.0 - 1.0."""
    try:
        resp = await llm.ainvoke(prompt)
        content = resp.content.strip()
        import re
        match = re.search(r"[1-5]", content)
        if match:
            score = int(match.group(0))
            return (score - 1) / 4.0
        return 0.5  # Neutral default
    except Exception as e:
        logger.error("Failed fallback metric eval: %s", e)
        return 0.5


async def _run_fallback_eval(test_cases: list[dict]) -> dict:
    """Fallback LLM evaluator when ragas library is missing or fails."""
    logger.info("Running custom LLM-based fallback evaluation on %d test cases...", len(test_cases))
    llm = ChatOllama(
        model=settings.ollama_llm_model,
        base_url=settings.ollama_base_url,
        temperature=0.1,
        num_predict=10,
    )
    
    total_faithfulness = 0.0
    total_relevancy = 0.0
    total_recall = 0.0
    total_precision = 0.0
    count = len(test_cases)
    
    if count == 0:
        return {
            "faithfulness": 0.0,
            "answer_relevancy": 0.0,
            "context_recall": 0.0,
            "context_precision": 0.0,
            "error": "No test cases provided."
        }
        
    for tc in test_cases:
        query = tc.get("user_input", "")
        response = tc.get("response", "")
        contexts = "\n\n".join(tc.get("retrieved_contexts", []))
        reference = tc.get("reference", "")
        
        # 1. Faithfulness
        faith_prompt = (
            "You are a professional RAG evaluation grader. Rate the FAITHFULNESS of the answer (from 1 to 5, where 5 is completely grounded in the context and has no hallucinations, and 1 is completely hallucinated/unsupported).\n\n"
            f"Source Context:\n{contexts}\n\n"
            f"Generated Answer:\n{response}\n\n"
            "Respond with ONLY a single digit score between 1 and 5. Do not write any other explanation or text."
        )
        faith = await _eval_metric_with_llm(llm, faith_prompt)
        total_faithfulness += faith
        
        # 2. Answer Relevancy
        rel_prompt = (
            "You are a professional RAG evaluation grader. Rate the RELEVANCY of the answer to the user query (from 1 to 5, where 5 is highly relevant and directly answers the query, and 1 is completely irrelevant/off-topic).\n\n"
            f"User Query:\n{query}\n\n"
            f"Generated Answer:\n{response}\n\n"
            "Respond with ONLY a single digit score between 1 and 5. Do not write any other explanation or text."
        )
        rel = await _eval_metric_with_llm(llm, rel_prompt)
        total_relevancy += rel
        
        # 3. Context Recall
        recall_prompt = (
            "You are a professional RAG evaluation grader. Rate the CONTEXT RECALL of the retrieved documents relative to the reference ground truth (from 1 to 5, where 5 means the retrieved documents contain all the information needed to support the reference answer, and 1 means none of the info is present).\n\n"
            f"Reference Ground Truth:\n{reference}\n\n"
            f"Retrieved Contexts:\n{contexts}\n\n"
            "Respond with ONLY a single digit score between 1 and 5. Do not write any other explanation or text."
        )
        recall = await _eval_metric_with_llm(llm, recall_prompt)
        total_recall += recall
        
        # 4. Context Precision
        prec_prompt = (
            "You are a professional RAG evaluation grader. Rate the CONTEXT PRECISION of the retrieved documents (from 1 to 5, where 5 means all retrieved contexts are highly relevant to answering the query, and 1 means they are mostly noise/irrelevant).\n\n"
            f"User Query:\n{query}\n\n"
            f"Retrieved Contexts:\n{contexts}\n\n"
            "Respond with ONLY a single digit score between 1 and 5. Do not write any other explanation or text."
        )
        prec = await _eval_metric_with_llm(llm, prec_prompt)
        total_precision += prec
        
    return {
        "faithfulness": round(total_faithfulness / count, 4),
        "answer_relevancy": round(total_relevancy / count, 4),
        "context_recall": round(total_recall / count, 4),
        "context_precision": round(total_precision / count, 4),
        "error": None
    }


async def run_ragas_eval(test_cases: list[dict]) -> dict:
    """
    Run RAGAS evaluation on a list of test cases using local Ollama models.
    Falls back to a custom LLM evaluator if the RAGAS library is not installed.

    Args:
        test_cases: List of dicts with keys:
            - user_input (str): The question asked
            - response (str): The generated answer
            - retrieved_contexts (list[str]): Context chunks used
            - reference (str): Expected/ground truth answer

    Returns:
        Dict with metric scores (0.0-1.0)
    """
    try:
        from ragas import evaluate, EvaluationDataset, SingleTurnSample
        from ragas.metrics import (
            Faithfulness,
            AnswerRelevancy,
            ContextRecall,
            ContextPrecision,
        )
    except ImportError:
        # Fall back to custom LLM evaluator
        return await _run_fallback_eval(test_cases)

    evaluator_llm = _get_evaluator_llm()
    evaluator_embeddings = _get_evaluator_embeddings()

    if not evaluator_llm:
        return await _run_fallback_eval(test_cases)

    try:
        # Build SingleTurnSample objects from test cases
        samples = []
        for tc in test_cases:
            sample = SingleTurnSample(
                user_input=tc.get("user_input", ""),
                response=tc.get("response", ""),
                retrieved_contexts=tc.get("retrieved_contexts", []),
                reference=tc.get("reference", ""),
            )
            samples.append(sample)

        # Create evaluation dataset
        eval_dataset = EvaluationDataset(samples=samples)

        # Initialize metrics with local Ollama LLM
        metrics = [
            Faithfulness(llm=evaluator_llm),
            AnswerRelevancy(llm=evaluator_llm, embeddings=evaluator_embeddings),
            ContextRecall(llm=evaluator_llm),
            ContextPrecision(llm=evaluator_llm),
        ]

        # Run evaluation
        logger.info(f"Running RAGAS evaluation on {len(samples)} samples...")
        results = evaluate(dataset=eval_dataset, metrics=metrics)

        scores = {
            "faithfulness": round(float(results["faithfulness"]), 4)
            if results.get("faithfulness") is not None
            else None,
            "answer_relevancy": round(float(results["answer_relevancy"]), 4)
            if results.get("answer_relevancy") is not None
            else None,
            "context_recall": round(float(results["context_recall"]), 4)
            if results.get("context_recall") is not None
            else None,
            "context_precision": round(float(results["context_precision"]), 4)
            if results.get("context_precision") is not None
            else None,
            "error": None,
        }

        logger.info(f"RAGAS evaluation complete: {scores}")
        return scores

    except Exception as e:
        logger.error(f"RAGAS evaluation failed: {str(e)}. Attempting LLM fallback...")
        return await _run_fallback_eval(test_cases)


def run_single_eval(
    question: str,
    answer: str,
    contexts: list[str],
    ground_truth: Optional[str] = None,
) -> dict:
    """
    Run RAGAS evaluation on a single query result.

    Args:
        question: The user's question
        answer: The generated answer
        contexts: List of context chunk texts used for generation
        ground_truth: Optional expected answer for recall/precision metrics

    Returns:
        Dict with RAGAS metric scores
    """
    test_case = {
        "user_input": question,
        "response": answer,
        "retrieved_contexts": contexts,
        "reference": ground_truth or answer,
    }
    return run_ragas_eval([test_case])
