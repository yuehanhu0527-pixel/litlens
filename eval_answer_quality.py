import json

from app.explore_agent import explore_agent_graph
from app.llm import client


# ============================================================
# Evaluation cases
# ============================================================

QUALITY_CASES = [

    {
        "id": "mechanism_attribution",

        "question": (
            "How do these papers differ in the mechanisms "
            "they propose for sleep-related brain clearance?"
        ),

        "document_ids": [4, 5],

        "requirements": """
The answer should:

- Clearly distinguish Document 4 from Document 5.
- Document 4 should be described as discussing or presenting
  the glymphatic hypothesis while noting that it is disputed
  or unresolved.
- Do NOT claim that Document 4 itself conclusively supports
  sleep-enhanced glymphatic clearance.
- Document 5 may be described as reporting its own experimental
  findings involving increased interstitial space, convective
  CSF-ISF exchange, and increased clearance during sleep.
- Preserve the difference between a disputed hypothesis and
  an experimental finding.
"""
    },

    {
        "id": "conflicting_conclusions",

        "question": (
            "How do these papers differ in their conclusions "
            "about the effect of sleep on brain clearance?"
        ),

        "document_ids": [4, 5],

        "requirements": """
The answer should:

- Clearly preserve the conflict between the two documents.
- Document 4 reports that brain clearance is markedly reduced,
  not increased, during sleep and anesthesia.
- Document 5 reports increased metabolite or beta-amyloid
  clearance during sleep.
- Do NOT force the two papers into agreement.
- The summary should directly answer how their conclusions differ.
"""
    },

    {
        "id": "irrelevant_document",

        "question": (
            "How do these papers differ in their conclusions "
            "about sleep and brain clearance?"
        ),

        "document_ids": [3, 4],

        "requirements": """
The answer should:

- Treat Document 3 as INSUFFICIENT because the available
  evidence is unrelated to sleep and brain clearance.
- Do NOT invent a sleep-related conclusion for Document 3.
- Document 4 may still be summarized using its evidence.
- The answer should acknowledge that a full comparison cannot
  be made because one document lacks relevant evidence.
"""
    },
]


# ============================================================
# LLM evaluator
# ============================================================

def judge_answer(
    question: str,
    requirements: str,
    result: dict
) -> dict:

    prompt = f"""
You are evaluating the quality of a research-paper comparison.

You are NOT answering the research question.

You are grading whether the generated answer follows the
required attribution and grounding rules.

Original question:
{question}

Evaluation requirements:
{requirements}

Generated result:

SUMMARY:
{result.get("summary", "")}

BY DOCUMENT:
{json.dumps(
    result.get("by_document", []),
    indent=2
)}

AGREEMENTS:
{json.dumps(
    result.get("agreements", []),
    indent=2
)}

DIFFERENCES:
{json.dumps(
    result.get("differences", []),
    indent=2
)}

Evaluate these four criteria:

1. answers_question
Does the result directly answer the original question?

2. attribution_correct
Does it correctly distinguish the paper's own findings
from hypotheses, prior work, disputed claims, or another
document's findings?

3. disagreement_preserved
If the documents disagree, does the result preserve that
disagreement rather than falsely forcing consensus?
If disagreement is not relevant to this case, mark true.

4. unsupported_claims_avoided
Does the result avoid inventing findings for documents
whose evidence is insufficient or unrelated?

Be strict.

Return JSON only:

{{
  "answers_question": true,
  "attribution_correct": true,
  "disagreement_preserved": true,
  "unsupported_claims_avoided": true,
  "overall_pass": true,
  "reason": "brief explanation"
}}
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    content = (
        response
        .choices[0]
        .message
        .content
    )

    return json.loads(content)


# ============================================================
# Run evaluation
# ============================================================

passed_count = 0


print("\nANSWER QUALITY EVALUATION")
print("=" * 70)


for case in QUALITY_CASES:

    print(
        f"\nCASE: {case['id']}"
    )

    print("-" * 70)

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

    result = final_state[
        "result"
    ]

    judgment = judge_answer(
        question=case["question"],
        requirements=case["requirements"],
        result=result
    )


    if judgment["overall_pass"]:
        passed_count += 1
        print("RESULT: PASS")
    else:
        print("RESULT: FAIL")


    print(
        "\nanswers_question:",
        judgment["answers_question"]
    )

    print(
        "attribution_correct:",
        judgment["attribution_correct"]
    )

    print(
        "disagreement_preserved:",
        judgment["disagreement_preserved"]
    )

    print(
        "unsupported_claims_avoided:",
        judgment[
            "unsupported_claims_avoided"
        ]
    )

    print(
        "\nREASON:"
    )

    print(
        judgment["reason"]
    )

    print(
        "\nSUMMARY:"
    )

    print(
        result.get(
            "summary",
            ""
        )
    )


# ============================================================
# Final score
# ============================================================

print(
    "\n" + "=" * 70
)

print(
    f"ANSWER QUALITY SCORE: "
    f"{passed_count}/{len(QUALITY_CASES)}"
)

print(
    "=" * 70
)