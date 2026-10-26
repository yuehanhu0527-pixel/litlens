from fastapi.testclient import TestClient

from app.main import app
from app.explore_agent import explore_agent_graph
from eval_cases import EVAL_CASES


client = TestClient(app)


def extract_document_ids(evidence_ids):
    """
    Convert evidence IDs like:

    doc_5_page_1_chunk_2

    into:

    5
    """

    document_ids = []

    for evidence_id in evidence_ids:
        parts = evidence_id.split("_")

        if len(parts) >= 2:
            document_ids.append(
                int(parts[1])
            )

    return document_ids


def evaluate_ask(case):

    response = client.post(
        "/ask",
        json={
            "question": case["question"],
            "top_k": 3,
            "document_ids": case["document_ids"]
        }
    )

    if response.status_code != 200:
        return False, (
            f"HTTP {response.status_code}: "
            f"{response.text}"
        )

    result = response.json()

    evidence_ids = result.get(
        "evidence_ids",
        []
    )

    actual_document_ids = set(
        extract_document_ids(
            evidence_ids
        )
    )

    expected_document_ids = set(
        case["expected_document_ids"]
    )

    passed = (
        len(evidence_ids) > 0
        and actual_document_ids.issubset(
            expected_document_ids
        )
    )

    details = {
        "answer": result.get("answer"),
        "evidence_ids": evidence_ids,
        "actual_document_ids": list(
            actual_document_ids
        )
    }

    return passed, details


def evaluate_verify(case):

    response = client.post(
        "/verify",
        json={
            "claim": case["claim"],
            "top_k": 3,
            "document_ids": case["document_ids"]
        }
    )

    if response.status_code != 200:
        return False, (
            f"HTTP {response.status_code}: "
            f"{response.text}"
        )

    result = response.json()

    actual_verdict = result.get(
        "verdict"
    )

    expected_verdict = case[
        "expected_verdict"
    ]

    passed = (
        actual_verdict ==
        expected_verdict
    )

    details = {
        "expected_verdict": expected_verdict,
        "actual_verdict": actual_verdict,
        "confidence": result.get(
            "confidence"
        ),
        "evidence_ids": result.get(
            "evidence_ids",
            []
        )
    }

    return passed, details


def evaluate_explore(case):

    initial_state = {
        "question": case["question"],
        "document_ids": case["document_ids"],
        "top_k_per_document": 2
    }

    final_state = (
        explore_agent_graph.invoke(
            initial_state
        )
    )

    checks = []
    details = {}


    # --------------------------------------------------------
    # Check intent
    # --------------------------------------------------------

    if "expected_intent" in case:

        actual_intent = final_state[
            "explore_intent"
        ]

        expected_intent = case[
            "expected_intent"
        ]

        checks.append(
            actual_intent ==
            expected_intent
        )

        details[
            "expected_intent"
        ] = expected_intent

        details[
            "actual_intent"
        ] = actual_intent


    # --------------------------------------------------------
    # Check insufficient documents
    # --------------------------------------------------------

    if (
        "expected_insufficient_documents"
        in case
    ):

        actual_insufficient = [
            document_id
            for document_id, sufficient
            in final_state[
                "sufficiency_by_document"
            ].items()
            if not sufficient
        ]

        expected_insufficient = case[
            "expected_insufficient_documents"
        ]

        checks.append(
            set(actual_insufficient)
            ==
            set(expected_insufficient)
        )

        details[
            "expected_insufficient"
        ] = expected_insufficient

        details[
            "actual_insufficient"
        ] = actual_insufficient


    # --------------------------------------------------------
    # Useful debugging information
    # --------------------------------------------------------

    details[
        "retry_counts"
    ] = final_state.get(
        "retry_counts"
    )

    details[
        "summary"
    ] = final_state[
        "result"
    ].get(
        "summary"
    )


    passed = (
        all(checks)
        if checks
        else True
    )

    return passed, details


def run_case(case):

    mode = case["mode"]

    if mode == "ask":
        return evaluate_ask(case)

    if mode == "verify":
        return evaluate_verify(case)

    if mode == "explore":
        return evaluate_explore(case)

    return False, (
        f"Unknown mode: {mode}"
    )


# ------------------------------------------------------------
# Run evaluation
# ------------------------------------------------------------

passed_count = 0


print("\nLITLENS EVALUATION")
print("=" * 70)


for case in EVAL_CASES:

    print(
        f"\nCASE: {case['id']}"
    )

    print("-" * 70)

    passed, details = run_case(
        case
    )

    if passed:
        passed_count += 1
        print("RESULT: PASS")
    else:
        print("RESULT: FAIL")

    print("DETAILS:")
    print(details)


print("\n" + "=" * 70)

print(
    f"FINAL SCORE: "
    f"{passed_count}/{len(EVAL_CASES)}"
)

print("=" * 70)