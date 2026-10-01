import json
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

TEST_FILE = str(Path(__file__).parent / "tests.jsonl")


class TestQuestion(BaseModel):
    """A test question with expected keywords and reference answer."""

    # Stops pytest from trying to collect this class because its name starts with "Test"
    __test__ = False

    question: str = Field(description="The question to ask the RAG system")
    keywords: list[str] = Field(description="Keywords that must appear in retrieved context")
    reference_answer: str = Field(description="The reference answer for this question")
    category: str = Field(description="Question category (e.g., direct_fact, spanning, temporal)")


def load_tests() -> list[TestQuestion]:
    """Load test questions from the JSONL file, skipping blank lines."""
    path = Path(TEST_FILE)

    if not path.exists():
        raise FileNotFoundError(
            f"Test file not found: {path}. "
            "Place your JSONL file at this path (named tests.jsonl)."
        )

    tests: list[TestQuestion] = []

    with open(path, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                data = json.loads(line)
                tests.append(TestQuestion(**data))
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON on line {line_number} of {path}: {error}") from error
            except (ValidationError, TypeError) as error:
                raise ValueError(f"Invalid test entry on line {line_number} of {path}: {error}") from error

    if not tests:
        raise ValueError(f"No test questions found in {path}.")

    return tests