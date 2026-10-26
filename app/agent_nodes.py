import json

from app.agent_state import ExploreAgentState
from app.llm import client
from app.retrieval_pipeline import retrieve_evidence
from langchain_core.utils.function_calling import (
    convert_to_openai_tool
)

from app.agent_tools import (
    search_document,
    get_adjacent_context
)

MAX_RETRIES = 2

def analyze_explore_query(
    state: ExploreAgentState
) -> dict:

    question = state["question"]

    prompt = f"""
You are analyzing a user's Explore query over multiple research papers.

User question:
{question}

Your job is NOT to answer the question.

Your job is to determine:

1. explore_intent
2. retrieval_focus

explore_intent must be ONE of:

- "compare"
  The user wants differences, contrasts, disagreements, or a direct comparison.

- "agreement"
  The user specifically wants to know what the papers agree on or have in common.

- "synthesize"
  The user wants an overall summary, combined findings, or what the papers collectively say.

retrieval_focus:
A short phrase describing what should be searched for INSIDE EACH INDIVIDUAL PAPER.

Rules for retrieval_focus:
- Preserve the meaning of the user's question.
- Remove multi-document framing such as:
  "these papers",
  "compare the papers",
  "how do they differ",
  "what do they agree on".
- Do not answer the question.
- Do not introduce new scientific concepts.
- Keep it concise.
- The phrase should make sense as a search query inside one paper.

Examples:

Question:
How do these papers differ in their conclusions about sleep and brain clearance?

Output:
{{
  "explore_intent": "compare",
  "retrieval_focus": "the effect of sleep on brain clearance"
}}

Question:
What do these papers say about sleep and brain clearance?

Output:
{{
  "explore_intent": "synthesize",
  "retrieval_focus": "sleep and brain clearance"
}}

Question:
What do these papers agree on about the role of sleep in metabolite clearance?

Output:
{{
  "explore_intent": "agreement",
  "retrieval_focus": "the role of sleep in metabolite clearance"
}}

Question:
How do the experimental methods differ across these papers?

Output:
{{
  "explore_intent": "compare",
  "retrieval_focus": "experimental methods"
}}

Return JSON only.
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

    content = response.choices[0].message.content

    result = json.loads(content)

    return {
        "explore_intent": result["explore_intent"],
        "retrieval_focus": result["retrieval_focus"]
    }
def retrieve_per_document(
    state: ExploreAgentState
) -> dict:

    retrieval_focus = state["retrieval_focus"]
    document_ids = state["document_ids"]
    top_k = state["top_k_per_document"]

    evidence_by_document = {}

    retrieval_queries = {}

    retry_counts = {}

    for document_id in document_ids:

        retrieval_query = retrieval_focus

        evidence = retrieve_evidence(
            query=retrieval_query,
            top_k=top_k,
            document_ids=[document_id]
        )

        evidence_by_document[document_id] = evidence

        retrieval_queries[document_id] = retrieval_query

        retry_counts[document_id] = 0

    return {
        "retrieval_queries": retrieval_queries,
        "evidence_by_document": evidence_by_document,
        "retry_counts": retry_counts
    }

def evaluate_evidence_sufficiency(
    state: ExploreAgentState
) -> dict:

    question = state["question"]
    retrieval_focus = state["retrieval_focus"]
    evidence_by_document = state["evidence_by_document"]

    sufficiency_by_document = {}
    sufficiency_reasons = {}
    retryable_by_document = {}
    missing_aspects = {}

    for document_id, evidence_list in evidence_by_document.items():

        evidence_text = "\n\n".join(
            [
                (
                    f"Evidence ID: {item['evidence_id']}\n"
                    f"Page: {item['page_number']}\n"
                    f"Text: {item['text']}"
                )
                for item in evidence_list
            ]
        )

        prompt = f"""
You are evaluating retrieved evidence from ONE research paper
for a multi-document Explore task.

Original user question:
{question}

Retrieval focus:
{retrieval_focus}

Retrieved evidence from document {document_id}:

{evidence_text}

Your job is to decide:

1. Is the evidence sufficient?
2. If not sufficient, is another retrieval attempt likely to help?
3. If retrying could help, what specific information is missing?

Definitions:

sufficient = true
- The retrieved evidence directly addresses the retrieval focus
  well enough to determine this paper's relevant finding,
  conclusion, method, or position.

sufficient = false AND retryable = true
- The evidence is related to the correct topic,
  but it is incomplete, indirect, or missing a specific detail.
- A better retrieval query within the SAME document
  may find the missing information.

sufficient = false AND retryable = false
- The evidence is clearly unrelated to the retrieval focus,
  or the document appears to be about a completely different topic.
- Reformulating the retrieval query is unlikely to help.

Important rules:
- Judge only the provided evidence.
- Do not use outside knowledge.
- The existence of retrieved passages does NOT automatically mean
  the evidence is sufficient.
- Do not compare this document with other documents yet.
- Do not answer the user's final question.
- Do not change the document scope.

Return JSON only:

{{
  "sufficient": true,
  "retryable": false,
  "reason": "brief explanation",
  "missing_aspect": ""
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

        content = response.choices[0].message.content

        result = json.loads(content)

        sufficient = bool(
            result["sufficient"]
        )

        retryable = bool(
            result["retryable"]
        )

        # If evidence is already sufficient,
        # there is no reason to retry.
        if sufficient:
            retryable = False

        sufficiency_by_document[document_id] = sufficient

        retryable_by_document[document_id] = retryable

        sufficiency_reasons[document_id] = (
            result["reason"]
        )

        missing_aspects[document_id] = (
            result.get("missing_aspect", "")
        )

    return {
        "sufficiency_by_document": sufficiency_by_document,
        "sufficiency_reasons": sufficiency_reasons,
        "retryable_by_document": retryable_by_document,
        "missing_aspects": missing_aspects
    }

def reformulate_queries_for_insufficient_docs(
    state: ExploreAgentState
) -> dict:

    question = state["question"]
    retrieval_focus = state["retrieval_focus"]

    sufficiency_by_document = state[
        "sufficiency_by_document"
    ]

    retryable_by_document = state[
        "retryable_by_document"
    ]

    sufficiency_reasons = state[
        "sufficiency_reasons"
    ]

    missing_aspects = state[
        "missing_aspects"
    ]

    retrieval_queries = dict(
        state["retrieval_queries"]
    )

    retry_counts = state[
        "retry_counts"
    ]

    for document_id, is_sufficient in sufficiency_by_document.items():

        # 已经够了
        if is_sufficient:
            continue

        # 不值得重搜
        if not retryable_by_document[document_id]:
            continue

        # 已经达到最大 retry 次数
        if retry_counts[document_id] >= MAX_RETRIES:
            continue

        reason = sufficiency_reasons[
            document_id
        ]

        missing_aspect = missing_aspects[
            document_id
        ]

        current_query = retrieval_queries[
            document_id
        ]

        prompt = f"""
You are improving a retrieval query for ONE research paper.

Original user question:
{question}

Core retrieval focus:
{retrieval_focus}

Current retrieval query:
{current_query}

Why the current evidence was insufficient:
{reason}

Specific missing information:
{missing_aspect}

Create a better retrieval query for searching inside
this SAME research paper.

Rules:
- Preserve the meaning of the original question.
- Stay focused on the same retrieval topic.
- Target the missing information.
- Do not answer the question.
- Do not introduce unrelated scientific concepts.
- Do not change the document scope.
- Prefer terminology likely to appear in research papers.
- Keep the query concise.
- Return JSON only.

Return:

{{
  "retrieval_query": "..."
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

        content = response.choices[0].message.content

        result = json.loads(content)

        retrieval_queries[document_id] = (
            result["retrieval_query"]
        )

    return {
        "retrieval_queries": retrieval_queries
    }

def retry_insufficient_documents(
    state: ExploreAgentState
) -> dict:

    sufficiency_by_document = state[
        "sufficiency_by_document"
    ]

    retryable_by_document = state[
        "retryable_by_document"
    ]

    retrieval_queries = state[
        "retrieval_queries"
    ]

    top_k = state[
        "top_k_per_document"
    ]

    evidence_by_document = dict(
        state["evidence_by_document"]
    )

    retry_counts = dict(
        state["retry_counts"]
    )

    for document_id, is_sufficient in sufficiency_by_document.items():

        # 已经够
        if is_sufficient:
            continue

        # 不值得 retry
        if not retryable_by_document[document_id]:
            continue

        # 已达到上限
        if retry_counts[document_id] >= MAX_RETRIES:
            continue

        retrieval_query = retrieval_queries[
            document_id
        ]

        evidence = retrieve_evidence(
            query=retrieval_query,
            top_k=top_k,
            document_ids=[document_id]
        )

        evidence_by_document[document_id] = evidence

        # 真正重新搜完一次，才 +1
        retry_counts[document_id] += 1

    return {
        "evidence_by_document": evidence_by_document,
        "retry_counts": retry_counts
    }

def has_retryable_documents(
    state: ExploreAgentState
) -> bool:

    for document_id in state["document_ids"]:

        is_sufficient = state[
            "sufficiency_by_document"
        ][document_id]

        is_retryable = state[
            "retryable_by_document"
        ][document_id]

        retry_count = state[
            "retry_counts"
        ][document_id]

        if (
            not is_sufficient
            and is_retryable
            and retry_count < MAX_RETRIES
        ):
            return True

    return False

def generate_explore_result(
    state: ExploreAgentState
) -> dict:

    question = state["question"]
    explore_intent = state["explore_intent"]

    evidence_by_document = state[
        "evidence_by_document"
    ]

    sufficiency_by_document = state[
        "sufficiency_by_document"
    ]

    sufficiency_reasons = state[
        "sufficiency_reasons"
    ]

    document_sections = []

    for document_id in state["document_ids"]:

        sufficient = sufficiency_by_document[
            document_id
        ]

        reason = sufficiency_reasons[
            document_id
        ]

        evidence_list = evidence_by_document[
            document_id
        ]

        if sufficient:

            evidence_text = "\n\n".join(
                [
                    (
                        f"Evidence ID: {item['evidence_id']}\n"
                        f"Filename: {item['filename']}\n"
                        f"Page: {item['page_number']}\n"
                        f"Text: {item['text']}"
                    )
                    for item in evidence_list
                ]
            )

        else:

            evidence_text = (
                "Retrieved evidence was judged insufficient.\n"
                f"Reason: {reason}"
            )

        document_sections.append(
            f"""
DOCUMENT {document_id}

Evidence sufficient:
{sufficient}

Evidence:
{evidence_text}
"""
        )

    all_documents = "\n\n".join(
        document_sections
    )

    prompt = f"""
You are answering a multi-document research Explore query.

Original user question:
{question}

Explore intent:
{explore_intent}

Evidence from the selected documents:

{all_documents}

Answer the ORIGINAL user question using ONLY the evidence above.

Important rules:

- Do not use outside knowledge.
- Treat each document separately before combining findings.
- Do not claim that an entire paper lacks information merely because
  retrieved evidence was insufficient.
- If a document has sufficient evidence, summarize its relevant finding.
- If a document has insufficient evidence, mark it as INSUFFICIENT.
- For an insufficient document, do not invent a finding and use no
  evidence IDs for that document.
- Only cite evidence IDs that appear above.
- Preserve disagreements between papers.
- Do not force consensus if the evidence conflicts.
- Distinguish the paper's own findings or conclusions from hypotheses,
  prior work, or claims that the paper merely describes.
- Do not attribute a background hypothesis to the paper as its own
  conclusion unless the evidence clearly says the paper supports it.
- An agreement may be reported only when the provided evidence from
  EACH relevant document supports that agreement.
- If one document presents a claim as unresolved, disputed, or as prior
  work, do not describe that document as agreeing with the claim.

Intent behavior:

If explore_intent is "compare":
- emphasize similarities and differences.

If explore_intent is "agreement":
- emphasize what the papers support in common.
- still mention meaningful disagreements if necessary.

If explore_intent is "synthesize":
- provide an overall evidence-grounded synthesis.

Return JSON only in this format:

{{
  "summary": "overall answer to the user's question",

  "by_document": [
    {{
      "document_id": 1,
      "filename": "paper.pdf",
      "status": "ANSWERED",
      "finding": "document-specific finding",
      "evidence_ids": ["..."]
    }}
  ],

  "agreements": [
    "..."
  ],

  "differences": [
    "..."
  ],

  "evidence_ids": [
    "..."
  ]
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

    content = response.choices[0].message.content

    result = json.loads(content)

    # Safety cleanup:
    # insufficient documents must not expose evidence as used evidence
    insufficient_ids = {
        document_id
        for document_id, sufficient
        in sufficiency_by_document.items()
        if not sufficient
    }

    for item in result.get(
        "by_document",
        []
    ):

        document_id = item.get(
            "document_id"
        )

        if document_id in insufficient_ids:

            item["status"] = "INSUFFICIENT"
            item["evidence_ids"] = []

    return {
        "result": result
    }

def recover_insufficient_documents_with_tools(
    state: ExploreAgentState
) -> dict:

    question = state["question"]

    evidence_by_document = dict(
        state["evidence_by_document"]
    )

    retrieval_queries = dict(
        state["retrieval_queries"]
    )

    retry_counts = dict(
        state["retry_counts"]
    )

    tools = [
        convert_to_openai_tool(
            search_document
        ),
        convert_to_openai_tool(
            get_adjacent_context
        )
    ]

    tool_map = {
        "search_document": search_document,
        "get_adjacent_context": get_adjacent_context
    }

    for document_id in state["document_ids"]:

        is_sufficient = state[
            "sufficiency_by_document"
        ][document_id]

        is_retryable = state[
            "retryable_by_document"
        ][document_id]

        retry_count = retry_counts[
            document_id
        ]

        # Already enough
        if is_sufficient:
            continue

        # Another retrieval attempt is unlikely to help
        if not is_retryable:
            continue

        # Bounded retry
        if retry_count >= MAX_RETRIES:
            continue

        missing_aspect = state[
            "missing_aspects"
        ][document_id]

        reason = state[
            "sufficiency_reasons"
        ][document_id]

        current_evidence = evidence_by_document[
            document_id
        ]

        evidence_text = "\n\n".join(
            [
                (
                    f"Evidence ID: {item['evidence_id']}\n"
                    f"Page: {item['page_number']}\n"
                    f"Chunk index: {item['chunk_index']}\n"
                    f"Text: {item['text']}"
                )
                for item in current_evidence
            ]
        )

        messages = [
            {
                "role": "system",
                "content": """
You are a research evidence recovery agent.

You have two tools:

1. search_document
Use this when the current evidence does not contain
the needed information and a new search inside the
same document is appropriate.

2. get_adjacent_context
Use this when a current evidence chunk is already
relevant, but more surrounding context may provide
the missing information.

Choose the tool that is most likely to recover
the missing evidence.

Do not answer the research question.
Use exactly one tool.
Do not change the document scope.
"""
            },
            {
                "role": "user",
                "content": f"""
Original question:
{question}

Document ID:
{document_id}

Why the evidence is insufficient:
{reason}

Specific missing information:
{missing_aspect}

Current evidence:

{evidence_text}
"""
            }
        ]

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0
        )

        message = response.choices[0].message

        if not message.tool_calls:
            continue

        tool_call = message.tool_calls[0]

        tool_name = (
            tool_call.function.name
        )

        tool_args = json.loads(
            tool_call.function.arguments
        )

        selected_tool = tool_map[
            tool_name
        ]

        result = selected_tool.invoke(
            tool_args
        )

        evidence_by_document[
            document_id
        ] = result

        if tool_name == "search_document":

            retrieval_queries[
                document_id
            ] = tool_args["query"]

        retry_counts[
            document_id
        ] += 1

    return {
        "evidence_by_document": evidence_by_document,
        "retrieval_queries": retrieval_queries,
        "retry_counts": retry_counts
    }