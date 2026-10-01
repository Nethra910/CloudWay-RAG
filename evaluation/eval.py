"""
RAG evaluation for CloudWay-RAG.

"""

import math
import os
import sys
import time
from functools import lru_cache

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

from evaluation.test import TestQuestion, load_tests
from implementation.answer import answer_question, fetch_context

# Finds a .env in the project tree; no machine-specific absolute path
load_dotenv(override=True)

MODEL = "openai/gpt-oss-120b"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5


# ============================================================
# Evaluation Models
# ============================================================

class RetrievalEval(BaseModel):
    """Evaluation metrics for retrieval performance."""

    mrr: float = Field(description="Mean Reciprocal Rank - average across all keywords")
    ndcg: float = Field(description="Normalized Discounted Cumulative Gain (binary relevance)")
    keywords_found: int = Field(description="Number of keywords found in retrieved results")
    total_keywords: int = Field(description="Total number of keywords to find")
    keyword_coverage: float = Field(description="Percentage of keywords found")


class AnswerEval(BaseModel):
    """LLM-as-a-judge evaluation of answer quality."""

    feedback: str = Field(description="Concise feedback on the answer quality")
    accuracy: float = Field(
        description="How factually correct the answer is. 1 = wrong, 5 = perfectly accurate"
    )
    completeness: float = Field(
        description="How completely the answer addresses the question. "
                    "1 = very incomplete, 5 = complete"
    )
    relevance: float = Field(
        description="How relevant the answer is to the question. "
                    "1 = irrelevant, 5 = directly relevant"
    )


# ============================================================
# Helpers
# ============================================================

def _norm(text: str) -> str:
    """Lowercase and collapse all whitespace (handles PDF line breaks)."""
    return " ".join(text.lower().split())


def _clamp(score: float) -> float:
    """Keep judge scores within 1-5."""
    return max(1.0, min(5.0, float(score)))


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    """Create the Groq client once and reuse it."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY was not found in the .env file or environment.")
    return OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)


# ============================================================
# Retrieval Metrics
# ============================================================

def calculate_mrr(keyword: str, retrieved_docs: list) -> float:
    """Reciprocal rank of the first retrieved doc containing the keyword (0 if none)."""
    keyword_norm = _norm(keyword)

    for rank, doc in enumerate(retrieved_docs, start=1):
        if keyword_norm in _norm(doc.page_content):
            return 1.0 / rank

    return 0.0


def calculate_dcg(relevances: list[int], k: int) -> float:
    """Discounted Cumulative Gain over the top-k relevances."""
    return sum(
        relevances[i] / math.log2(i + 2)
        for i in range(min(k, len(relevances)))
    )


def calculate_ndcg(keyword: str, retrieved_docs: list, k: int = 10) -> float:
    """nDCG for one keyword with binary relevance (keyword present = 1)."""
    keyword_norm = _norm(keyword)

    relevances = [
        1 if keyword_norm in _norm(doc.page_content) else 0
        for doc in retrieved_docs[:k]
    ]

    dcg = calculate_dcg(relevances, k)
    idcg = calculate_dcg(sorted(relevances, reverse=True), k)

    return dcg / idcg if idcg > 0 else 0.0


def evaluate_retrieval(test: TestQuestion, k: int = 10) -> RetrievalEval:
    """Evaluate retrieval: MRR, nDCG, and keyword coverage."""
    retrieved_docs = fetch_context(test.question)

    mrr_scores = [calculate_mrr(kw, retrieved_docs) for kw in test.keywords]
    ndcg_scores = [calculate_ndcg(kw, retrieved_docs, k) for kw in test.keywords]

    avg_mrr = sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0
    avg_ndcg = sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0

    keywords_found = sum(1 for score in mrr_scores if score > 0)
    total_keywords = len(test.keywords)
    keyword_coverage = (
        keywords_found / total_keywords * 100 if total_keywords > 0 else 0.0
    )

    return RetrievalEval(
        mrr=avg_mrr,
        ndcg=avg_ndcg,
        keywords_found=keywords_found,
        total_keywords=total_keywords,
        keyword_coverage=keyword_coverage,
    )


# ============================================================
# Answer Evaluation
# ============================================================

def _call_judge(messages: list[dict]) -> AnswerEval:
    """Call the LLM judge with retries on transient failures (e.g. rate limits)."""
    client = get_client()
    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "answer_eval",
                        "schema": {
                            **AnswerEval.model_json_schema(),
                            "additionalProperties": False,
                        },
                        "strict": True,
                    },
                },
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("LLM judge returned an empty response.")

            result = AnswerEval.model_validate_json(content)
            result.accuracy = _clamp(result.accuracy)
            result.completeness = _clamp(result.completeness)
            result.relevance = _clamp(result.relevance)
            return result

        except Exception as error:
            last_error = error
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS * attempt)

    raise RuntimeError(f"Judge failed after {MAX_RETRIES} attempts: {last_error}")


def evaluate_answer(test: TestQuestion) -> tuple[AnswerEval, str, list]:
    """
    Generate a RAG answer and grade it with an LLM judge.

    Returns:
        (AnswerEval, generated answer, retrieved docs)
    """
    generated_answer, retrieved_docs = answer_question(test.question)

    judge_messages = [
        {
            "role": "system",
            "content": (
                "You are an expert evaluator assessing the quality of answers. "
                "Compare the generated answer with the reference answer. "
                "Only give 5/5 for a perfect answer."
            ),
        },
        {
            "role": "user",
            "content": f"""
Question:
{test.question}

Generated Answer:
{generated_answer}

Reference Answer:
{test.reference_answer}

Evaluate the generated answer on three dimensions:

1. Accuracy:
How factually correct is the answer compared to the reference answer?
1 = wrong
5 = perfectly accurate

2. Completeness:
Does the answer cover all important information from the reference answer?
1 = very incomplete
5 = completely covers the required information

3. Relevance:
Does the answer directly answer the question without unnecessary information?
1 = irrelevant
5 = directly relevant

Provide feedback and a score from 1 to 5 for each dimension.
If the answer is factually wrong, accuracy must be 1.
""",
        },
    ]

    answer_eval = _call_judge(judge_messages)
    return answer_eval, generated_answer, retrieved_docs


# ============================================================
# Evaluate All Tests (generators, e.g. for a Gradio progress bar)
# ============================================================

def evaluate_all_retrieval():
    """Yield (test, RetrievalEval, progress) for every test question."""
    tests = load_tests()
    total_tests = len(tests)

    for index, test in enumerate(tests):
        result = evaluate_retrieval(test)
        yield test, result, (index + 1) / total_tests


def evaluate_all_answers():
    """Yield (test, AnswerEval, progress) for every test question."""
    tests = load_tests()
    total_tests = len(tests)

    for index, test in enumerate(tests):
        result = evaluate_answer(test)[0]
        yield test, result, (index + 1) / total_tests


# ============================================================
# CLI Evaluation
# ============================================================

def run_cli_evaluation(test_number: int):
    """Run retrieval and answer evaluation for one test question."""
    tests = load_tests()

    if test_number < 0 or test_number >= len(tests):
        print(f"Error: test_row_number must be between 0 and {len(tests) - 1}")
        sys.exit(1)

    test = tests[test_number]

    print("\n" + "=" * 80)
    print(f"Test #{test_number}")
    print("=" * 80)
    print(f"Question: {test.question}")
    print(f"Keywords: {test.keywords}")
    print(f"Category: {test.category}")
    print(f"Reference Answer: {test.reference_answer}")

    # Retrieval
    print("\n" + "=" * 80)
    print("Retrieval Evaluation")
    print("=" * 80)

    retrieval_result = evaluate_retrieval(test)
    print(f"MRR: {retrieval_result.mrr:.4f}")
    print(f"nDCG: {retrieval_result.ndcg:.4f}")
    print(f"Keywords Found: {retrieval_result.keywords_found}/{retrieval_result.total_keywords}")
    print(f"Keyword Coverage: {retrieval_result.keyword_coverage:.1f}%")

    # Answer
    print("\n" + "=" * 80)
    print("Answer Evaluation")
    print("=" * 80)

    answer_result, generated_answer, _ = evaluate_answer(test)

    print(f"\nGenerated Answer:\n{generated_answer}")
    print(f"\nFeedback:\n{answer_result.feedback}")
    print("\nScores:")
    print(f"  Accuracy: {answer_result.accuracy:.2f}/5")
    print(f"  Completeness: {answer_result.completeness:.2f}/5")
    print(f"  Relevance: {answer_result.relevance:.2f}/5")
    print("\n" + "=" * 80)


# ============================================================
# Main
# ============================================================

def main():
    if len(sys.argv) != 2:
        print("Usage: uv run -m evaluation.eval <test_row_number>")
        sys.exit(1)

    try:
        test_number = int(sys.argv[1])
    except ValueError:
        print("Error: test_row_number must be an integer")
        sys.exit(1)

    run_cli_evaluation(test_number)


if __name__ == "__main__":
    main()