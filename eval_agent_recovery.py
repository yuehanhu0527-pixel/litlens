from app.agent_nodes import (
    evaluate_evidence_sufficiency,
    recover_insufficient_documents_with_tools,
)

from app.explore_agent import explore_agent_graph

from app.retrieval_pipeline import retrieve_evidence


passed_count = 0
total_count = 3


print("\nAGENT RECOVERY EVALUATION")
print("=" * 70)


# ============================================================
# CASE A
# Recoverable incomplete evidence
# ============================================================

print("\nCASE A: recoverable incomplete evidence")
print("-" * 70)


state_a = {
    "question": (
        "How do these papers differ in the mechanisms "
        "they propose for sleep-related brain clearance?"
    ),

    "document_ids": [5],

    "top_k_per_document": 1,

    "retrieval_focus": (
        "proposed mechanisms for sleep-related brain clearance"
    ),

    "retrieval_queries": {
        5: (
            "proposed mechanisms for sleep-related "
            "brain clearance"
        )
    },

    # Deliberately incomplete evidence:
    # relevant topic, but not enough mechanism detail.
    "evidence_by_document": {
        5: [
            {
                "document_id": 5,
                "filename": "nihms540586.pdf",
                "page_number": 1,
                "chunk_index": 0,
                "evidence_id": "doc_5_page_1_chunk_0",
                "text": """
Sleep Drives Metabolite Clearance from the Adult Brain.

The conservation of sleep across all animal species
suggests that sleep serves a vital function.

We here report that sleep has a critical function
in ensuring metabolic homeostasis.
"""
            }
        ]
    },

    "sufficiency_by_document": {
        5: False
    },

    "retryable_by_document": {
        5: True
    },

    "sufficiency_reasons": {
        5: (
            "The evidence is related to sleep and brain "
            "clearance, but does not explain the mechanism."
        )
    },

    "missing_aspects": {
        5: (
            "The mechanism involving interstitial space, "
            "CSF-ISF exchange, or glymphatic clearance."
        )
    },

    "retry_counts": {
        5: 0
    }
}


# Let the LLM choose a recovery tool
recovery_result = (
    recover_insufficient_documents_with_tools(
        state_a
    )
)

state_a.update(
    recovery_result
)


# Evaluate the recovered evidence again
second_check = (
    evaluate_evidence_sufficiency(
        state_a
    )
)

state_a.update(
    second_check
)


case_a_passed = (
    state_a["retry_counts"][5] > 0
    and state_a[
        "sufficiency_by_document"
    ][5] is True
)


if case_a_passed:
    passed_count += 1
    print("RESULT: PASS")
else:
    print("RESULT: FAIL")


print(
    "Retry count:",
    state_a["retry_counts"][5]
)

print(
    "Final sufficient:",
    state_a[
        "sufficiency_by_document"
    ][5]
)

print(
    "Evidence IDs:",
    [
        item["evidence_id"]
        for item in
        state_a["evidence_by_document"][5]
    ]
)


# ============================================================
# CASE B
# Completely irrelevant document
# ============================================================

print("\nCASE B: irrelevant document should not retry")
print("-" * 70)


state_b = {
    "question": (
        "How do these papers differ in their conclusions "
        "about sleep and brain clearance?"
    ),

    "document_ids": [3, 4],

    "top_k_per_document": 2
}


final_b = explore_agent_graph.invoke(
    state_b
)


doc3_sufficient = final_b[
    "sufficiency_by_document"
][3]

doc3_retry_count = final_b[
    "retry_counts"
][3]


case_b_passed = (
    doc3_sufficient is False
    and doc3_retry_count == 0
)


if case_b_passed:
    passed_count += 1
    print("RESULT: PASS")
else:
    print("RESULT: FAIL")


print(
    "Document 3 sufficient:",
    doc3_sufficient
)

print(
    "Document 3 retry count:",
    doc3_retry_count
)

print(
    "Reason:",
    final_b[
        "sufficiency_reasons"
    ][3]
)


# ============================================================
# CASE C
# Evidence already sufficient
# ============================================================

print("\nCASE C: sufficient evidence should not retry")
print("-" * 70)


evidence_c = retrieve_evidence(
    query=(
        "proposed mechanisms for "
        "sleep-related brain clearance"
    ),
    top_k=1,
    document_ids=[4]
)


state_c = {
    "question": (
        "What mechanism is proposed for "
        "sleep-related brain clearance?"
    ),

    "document_ids": [4],

    "top_k_per_document": 1,

    "retrieval_focus": (
        "proposed mechanisms for sleep-related "
        "brain clearance"
    ),

    "retrieval_queries": {
        4: (
            "proposed mechanisms for "
            "sleep-related brain clearance"
        )
    },

    "evidence_by_document": {
        4: evidence_c
    },

    "retry_counts": {
        4: 0
    }
}


first_check_c = (
    evaluate_evidence_sufficiency(
        state_c
    )
)

state_c.update(
    first_check_c
)


# Even if we call the recovery node,
# it should leave sufficient documents alone.
recovery_c = (
    recover_insufficient_documents_with_tools(
        state_c
    )
)

state_c.update(
    recovery_c
)


case_c_passed = (
    state_c[
        "sufficiency_by_document"
    ][4] is True
    and state_c[
        "retry_counts"
    ][4] == 0
)


if case_c_passed:
    passed_count += 1
    print("RESULT: PASS")
else:
    print("RESULT: FAIL")


print(
    "Document 4 sufficient:",
    state_c[
        "sufficiency_by_document"
    ][4]
)

print(
    "Document 4 retry count:",
    state_c[
        "retry_counts"
    ][4]
)

print(
    "Evidence IDs:",
    [
        item["evidence_id"]
        for item in
        state_c["evidence_by_document"][4]
    ]
)


# ============================================================
# FINAL SCORE
# ============================================================

print("\n" + "=" * 70)

print(
    f"AGENT RECOVERY SCORE: "
    f"{passed_count}/{total_count}"
)

print("=" * 70)