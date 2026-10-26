EVAL_CASES = [

    # --------------------------------------------------------
    # ASK
    # --------------------------------------------------------

    {
        "id": "ask_doc5_sleep_clearance",
        "mode": "ask",
        "question": (
            "What happens to brain metabolite clearance "
            "during sleep?"
        ),
        "document_ids": [5],
        "expected_document_ids": [5],
    },

    {
        "id": "ask_doc4_sleep_clearance",
        "mode": "ask",
        "question": (
            "What happens to brain clearance during sleep?"
        ),
        "document_ids": [4],
        "expected_document_ids": [4],
    },


    # --------------------------------------------------------
    # VERIFY
    # --------------------------------------------------------

    {
        "id": "verify_doc5_sleep_increases",
        "mode": "verify",
        "claim": (
            "Sleep increases brain clearance."
        ),
        "document_ids": [5],
        "expected_verdict": "SUPPORTED",
    },

    {
        "id": "verify_doc4_sleep_increases",
        "mode": "verify",
        "claim": (
            "Sleep increases brain clearance."
        ),
        "document_ids": [4],
        "expected_verdict": "CONTRADICTED",
    },


    # --------------------------------------------------------
    # EXPLORE
    # --------------------------------------------------------

    {
        "id": "explore_mechanism_compare",
        "mode": "explore",
        "question": (
            "How do these papers differ in the mechanisms "
            "they propose for sleep-related brain clearance?"
        ),
        "document_ids": [4, 5],
        "expected_intent": "compare",
    },

    {
        "id": "explore_irrelevant_document",
        "mode": "explore",
        "question": (
            "How do these papers differ in their conclusions "
            "about sleep and brain clearance?"
        ),
        "document_ids": [3, 4],
        "expected_insufficient_documents": [3],
    },
]