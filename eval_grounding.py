from app.explore_agent import explore_agent_graph


passed_checks = 0
total_checks = 0


def get_document_id(evidence_id: str) -> int:
    """
    Example:

    doc_5_page_1_chunk_2
    ->
    5
    """

    return int(
        evidence_id.split("_")[1]
    )


def run_grounding_case(
    name: str,
    question: str,
    document_ids: list[int]
):

    global passed_checks
    global total_checks

    print("\n" + "=" * 70)
    print(f"CASE: {name}")
    print("=" * 70)

    initial_state = {
        "question": question,
        "document_ids": document_ids,
        "top_k_per_document": 2
    }

    final_state = (
        explore_agent_graph.invoke(
            initial_state
        )
    )

    result = final_state["result"]

    evidence_by_document = (
        final_state[
            "evidence_by_document"
        ]
    )

    sufficiency_by_document = (
        final_state[
            "sufficiency_by_document"
        ]
    )


    # --------------------------------------------------------
    # Build the set of evidence IDs that actually exist
    # --------------------------------------------------------

    valid_ids_by_document = {}

    for document_id, evidence_list \
            in evidence_by_document.items():

        valid_ids_by_document[
            document_id
        ] = {
            item["evidence_id"]
            for item in evidence_list
        }


    all_valid_ids = set()

    for evidence_ids in (
        valid_ids_by_document.values()
    ):
        all_valid_ids.update(
            evidence_ids
        )


    # ========================================================
    # CHECK 1
    # Top-level evidence IDs must actually exist
    # ========================================================

    total_checks += 1

    final_evidence_ids = set(
        result.get(
            "evidence_ids",
            []
        )
    )

    invented_ids = (
        final_evidence_ids
        - all_valid_ids
    )

    if not invented_ids:
        passed_checks += 1
        print(
            "\nCHECK 1: PASS"
        )
        print(
            "No invented evidence IDs."
        )
    else:
        print(
            "\nCHECK 1: FAIL"
        )
        print(
            "Invented evidence IDs:",
            invented_ids
        )


    # ========================================================
    # CHECK 2
    # Each document may only cite its own evidence
    # ========================================================

    total_checks += 1

    wrong_document_ids = []

    for item in result.get(
        "by_document",
        []
    ):

        document_id = item[
            "document_id"
        ]

        for evidence_id in item.get(
            "evidence_ids",
            []
        ):

            evidence_document_id = (
                get_document_id(
                    evidence_id
                )
            )

            if (
                evidence_document_id
                != document_id
            ):
                wrong_document_ids.append(
                    (
                        document_id,
                        evidence_id
                    )
                )


    if not wrong_document_ids:
        passed_checks += 1
        print(
            "\nCHECK 2: PASS"
        )
        print(
            "Each document cites only "
            "its own evidence."
        )
    else:
        print(
            "\nCHECK 2: FAIL"
        )
        print(
            "Cross-document citation errors:",
            wrong_document_ids
        )


    # ========================================================
    # CHECK 3
    # Per-document cited evidence must actually
    # exist in that document's final evidence
    # ========================================================

    total_checks += 1

    invalid_document_evidence = []

    for item in result.get(
        "by_document",
        []
    ):

        document_id = item[
            "document_id"
        ]

        valid_ids = (
            valid_ids_by_document.get(
                document_id,
                set()
            )
        )

        for evidence_id in item.get(
            "evidence_ids",
            []
        ):

            if evidence_id not in valid_ids:

                invalid_document_evidence.append(
                    (
                        document_id,
                        evidence_id
                    )
                )


    if not invalid_document_evidence:
        passed_checks += 1
        print(
            "\nCHECK 3: PASS"
        )
        print(
            "All cited evidence was "
            "actually retrieved."
        )
    else:
        print(
            "\nCHECK 3: FAIL"
        )
        print(
            "Invalid citations:",
            invalid_document_evidence
        )


    # ========================================================
    # CHECK 4
    # Insufficient documents must cite nothing
    # ========================================================

    total_checks += 1

    insufficient_citation_errors = []

    for item in result.get(
        "by_document",
        []
    ):

        document_id = item[
            "document_id"
        ]

        sufficient = (
            sufficiency_by_document[
                document_id
            ]
        )

        evidence_ids = item.get(
            "evidence_ids",
            []
        )

        if (
            not sufficient
            and evidence_ids
        ):

            insufficient_citation_errors.append(
                (
                    document_id,
                    evidence_ids
                )
            )


    if not insufficient_citation_errors:
        passed_checks += 1
        print(
            "\nCHECK 4: PASS"
        )
        print(
            "INSUFFICIENT documents "
            "cite no evidence."
        )
    else:
        print(
            "\nCHECK 4: FAIL"
        )
        print(
            "INSUFFICIENT citation errors:",
            insufficient_citation_errors
        )


    # --------------------------------------------------------
    # Debug output
    # --------------------------------------------------------

    print(
        "\nFINAL EVIDENCE IDS:"
    )

    print(
        result.get(
            "evidence_ids",
            []
        )
    )

    print(
        "\nSUFFICIENCY:"
    )

    print(
        sufficiency_by_document
    )


# ============================================================
# CASE 1
# Two relevant papers
# ============================================================

run_grounding_case(
    name="two relevant sleep papers",

    question=(
        "How do these papers differ in "
        "their conclusions about sleep "
        "and brain clearance?"
    ),

    document_ids=[
        4,
        5
    ]
)


# ============================================================
# CASE 2
# One irrelevant document
# ============================================================

run_grounding_case(
    name="one irrelevant document",

    question=(
        "How do these papers differ in "
        "their conclusions about sleep "
        "and brain clearance?"
    ),

    document_ids=[
        3,
        4
    ]
)


# ============================================================
# FINAL SCORE
# ============================================================

print(
    "\n" + "=" * 70
)

print(
    f"GROUNDING SCORE: "
    f"{passed_checks}/{total_checks}"
)

print(
    "=" * 70
)