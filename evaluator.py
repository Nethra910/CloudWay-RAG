"""
Gradio dashboard for evaluating the CloudWay-RAG system.

Save this file in the repository root (NOT as app.py, which is your chat app)
and run it from the repository root:

    python evaluator.py
"""

import html
from collections import defaultdict

import gradio as gr
import pandas as pd
from dotenv import load_dotenv

from evaluation.eval import evaluate_all_answers, evaluate_all_retrieval

load_dotenv(override=True)

# Categories skipped for retrieval scoring (they have no matching content by design)
EXCLUDE_FROM_RETRIEVAL = {"out_of_scope"}

# Color coding thresholds - Retrieval
MRR_GREEN = 0.9
MRR_AMBER = 0.75
NDCG_GREEN = 0.9
NDCG_AMBER = 0.75
COVERAGE_GREEN = 90.0
COVERAGE_AMBER = 75.0

# Color coding thresholds - Answer (1-5 scale)
ANSWER_GREEN = 4.5
ANSWER_AMBER = 4.0

EMPTY_HTML = (
    "<div style='padding: 20px; text-align: center; color: #999;'>"
    "Click 'Run Evaluation' to start</div>"
)


# ============================================================
# Formatting helpers
# ============================================================

def get_color(value: float, metric_type: str) -> str:
    """Get color based on metric value and type."""
    thresholds = {
        "mrr": (MRR_GREEN, MRR_AMBER),
        "ndcg": (NDCG_GREEN, NDCG_AMBER),
        "coverage": (COVERAGE_GREEN, COVERAGE_AMBER),
        "accuracy": (ANSWER_GREEN, ANSWER_AMBER),
        "completeness": (ANSWER_GREEN, ANSWER_AMBER),
        "relevance": (ANSWER_GREEN, ANSWER_AMBER),
    }

    if metric_type not in thresholds:
        return "black"

    green, amber = thresholds[metric_type]

    if value >= green:
        return "green"
    if value >= amber:
        return "orange"
    return "red"


def format_metric_html(
    label: str,
    value: float,
    metric_type: str,
    is_percentage: bool = False,
    score_format: bool = False,
) -> str:
    """Format a metric with color coding."""
    color = get_color(value, metric_type)

    if is_percentage:
        value_str = f"{value:.1f}%"
    elif score_format:
        value_str = f"{value:.2f}/5"
    else:
        value_str = f"{value:.4f}"

    return f"""
    <div style="margin: 10px 0; padding: 15px; background-color: #f5f5f5; border-radius: 8px; border-left: 5px solid {color};">
        <div style="font-size: 14px; color: #666; margin-bottom: 5px;">{label}</div>
        <div style="font-size: 28px; font-weight: bold; color: {color};">{value_str}</div>
    </div>
    """


def complete_banner(count: int) -> str:
    return f"""
        <div style="margin-top: 20px; padding: 10px; background-color: #d4edda; border-radius: 5px; text-align: center; border: 1px solid #c3e6cb;">
            <span style="font-size: 14px; color: #155724; font-weight: bold;">✓ Evaluation Complete: {count} tests</span>
        </div>
    """


def error_html(message: str) -> str:
    """Show an error inside the metrics panel instead of a generic Gradio error."""
    return f"""
    <div style="padding: 15px; background-color: #f8d7da; border-radius: 8px; border: 1px solid #f5c6cb; color: #721c24;">
        <strong>Evaluation failed</strong><br>{html.escape(message)}
    </div>
    """


def empty_chart(x_col: str, y_col: str) -> pd.DataFrame:
    return pd.DataFrame({x_col: [], y_col: []})


# ============================================================
# Evaluation runners
# ============================================================

def run_retrieval_evaluation(progress=gr.Progress()):
    """Run retrieval evaluation over all tests and return (summary HTML, chart data)."""
    total_mrr = 0.0
    total_ndcg = 0.0
    total_coverage = 0.0
    category_mrr = defaultdict(list)
    count = 0

    try:
        for test, result, prog_value in evaluate_all_retrieval():
            progress(prog_value, desc=f"Evaluating test {count + 1}...")

            if test.category in EXCLUDE_FROM_RETRIEVAL:
                continue

            count += 1
            total_mrr += result.mrr
            total_ndcg += result.ndcg
            total_coverage += result.keyword_coverage
            category_mrr[test.category].append(result.mrr)

    except Exception as error:
        return error_html(str(error)), empty_chart("Category", "Average MRR")

    if count == 0:
        return (
            error_html("No tests were evaluated. Check evaluation/tests.jsonl."),
            empty_chart("Category", "Average MRR"),
        )

    avg_mrr = total_mrr / count
    avg_ndcg = total_ndcg / count
    avg_coverage = total_coverage / count

    final_html = f"""
    <div style="padding: 0;">
        {format_metric_html("Mean Reciprocal Rank (MRR)", avg_mrr, "mrr")}
        {format_metric_html("Normalized DCG (nDCG)", avg_ndcg, "ndcg")}
        {format_metric_html("Keyword Coverage", avg_coverage, "coverage", is_percentage=True)}
        {complete_banner(count)}
    </div>
    """

    df = pd.DataFrame(
        [
            {"Category": category, "Average MRR": sum(scores) / len(scores)}
            for category, scores in category_mrr.items()
        ]
    )

    return final_html, df


def run_answer_evaluation(progress=gr.Progress()):
    """Run answer evaluation over all tests and return (summary HTML, chart data)."""
    total_accuracy = 0.0
    total_completeness = 0.0
    total_relevance = 0.0
    category_accuracy = defaultdict(list)
    count = 0

    try:
        for test, result, prog_value in evaluate_all_answers():
            count += 1
            total_accuracy += result.accuracy
            total_completeness += result.completeness
            total_relevance += result.relevance
            category_accuracy[test.category].append(result.accuracy)

            progress(prog_value, desc=f"Evaluating test {count}...")

    except Exception as error:
        return error_html(str(error)), empty_chart("Category", "Average Accuracy")

    if count == 0:
        return (
            error_html("No tests were evaluated. Check evaluation/tests.jsonl."),
            empty_chart("Category", "Average Accuracy"),
        )

    avg_accuracy = total_accuracy / count
    avg_completeness = total_completeness / count
    avg_relevance = total_relevance / count

    final_html = f"""
    <div style="padding: 0;">
        {format_metric_html("Accuracy", avg_accuracy, "accuracy", score_format=True)}
        {format_metric_html("Completeness", avg_completeness, "completeness", score_format=True)}
        {format_metric_html("Relevance", avg_relevance, "relevance", score_format=True)}
        {complete_banner(count)}
    </div>
    """

    df = pd.DataFrame(
        [
            {"Category": category, "Average Accuracy": sum(scores) / len(scores)}
            for category, scores in category_accuracy.items()
        ]
    )

    return final_html, df


# ============================================================
# App
# ============================================================

def main():
    """Launch the Gradio evaluation app."""
    theme = gr.themes.Soft(font=["Inter", "system-ui", "sans-serif"])

    with gr.Blocks(title="RAG Evaluation Dashboard", theme=theme) as app:
        gr.Markdown("# 📊 RAG Evaluation Dashboard")
        gr.Markdown("Evaluate retrieval and answer quality for the CloudWay 24 RAG system")

        # Retrieval section
        gr.Markdown("## 🔍 Retrieval Evaluation")

        retrieval_button = gr.Button("Run Evaluation", variant="primary", size="lg")

        with gr.Row():
            with gr.Column(scale=1):
                retrieval_metrics = gr.HTML(EMPTY_HTML)

            with gr.Column(scale=1):
                retrieval_chart = gr.BarPlot(
                    x="Category",
                    y="Average MRR",
                    title="Average MRR by Category",
                    y_lim=[0, 1],
                    height=400,
                )

        # Answer section
        gr.Markdown("## 💬 Answer Evaluation")

        answer_button = gr.Button("Run Evaluation", variant="primary", size="lg")

        with gr.Row():
            with gr.Column(scale=1):
                answer_metrics = gr.HTML(EMPTY_HTML)

            with gr.Column(scale=1):
                answer_chart = gr.BarPlot(
                    x="Category",
                    y="Average Accuracy",
                    title="Average Accuracy by Category",
                    y_lim=[1, 5],
                    height=400,
                )

        retrieval_button.click(
            fn=run_retrieval_evaluation,
            outputs=[retrieval_metrics, retrieval_chart],
        )

        answer_button.click(
            fn=run_answer_evaluation,
            outputs=[answer_metrics, answer_chart],
        )

    app.launch(inbrowser=True)


if __name__ == "__main__":
    main()