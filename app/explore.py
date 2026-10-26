import json

from app.llm import client


def compare_documents_with_evidence(
    question: str,
    evidence_by_document: dict[int, list[dict]]
) -> dict:

    evidence_text = ""

    for document_id, evidence_list in evidence_by_document.items():

        evidence_text += (
            f"\n\n===== Document {document_id} =====\n"
        )

        if not evidence_list:
            evidence_text += "No evidence retrieved.\n"
            continue

        filename = evidence_list[0]["filename"]

        evidence_text += f"Filename: {filename}\n"

        for chunk in evidence_list:
            evidence_text += (
                f"\nEvidence ID: {chunk['evidence_id']}\n"
                f"Page: {chunk['page_number']}\n"
                f"Text: {chunk['text']}\n"
            )

    prompt = f"""
You are an evidence-grounded research paper comparison assistant.

The user is asking a question about multiple documents.

Question:
{question}

Evidence grouped by document:
{evidence_text}

Your job is to compare and synthesize the documents using ONLY the
provided evidence.

Rules:
1. Do not use outside knowledge.
2. Treat each document separately before comparing them.
3. Do not assume that every document contains relevant evidence.
4. If the evidence for a document does not answer the question,
   explicitly say that the evidence is insufficient for that document.
5. Do not invent an agreement or disagreement.
6. Only report an agreement when the evidence from multiple documents
   actually supports the same conclusion.
7. Only report a difference when the documents actually support
   different conclusions, methods, findings, or perspectives.
8. Only use Evidence IDs exactly as provided above.
9. Every substantive comparison should be grounded in the evidence.
10. If the retrieved evidence for a document is not relevant enough,
  say "the retrieved evidence is insufficient to answer the question
  for this document."
11. Do not claim that an entire document contains no relevant information
  merely because the retrieved evidence is insufficient.
12. If a document has insufficient evidence, return an empty evidence_ids
  list for that document rather than citing irrelevant chunks.
13. Use status "ANSWERED" only when the retrieved evidence is sufficient
  to answer the question for that document.
14. Use status "INSUFFICIENT" when the retrieved evidence does not
  sufficiently answer the question.
15. If status is "INSUFFICIENT", evidence_ids MUST be an empty list.
16. When status is "INSUFFICIENT", do not claim that the entire document
  lacks information. Only say that the retrieved evidence is insufficient.
Return exactly this structure:
Return valid JSON only.


{{
  "summary": "overall evidence-grounded synthesis",
  "by_document": [
    {{
      "document_id": 1,
      "filename": "example.pdf",
      "status": "ANSWERED | INSUFFICIENT",
      "summary": "what the retrieved evidence supports",
      "evidence_ids": ["doc_1_page_1_chunk_0"]
    }}
],
  "agreements": [
    "agreement supported by multiple documents"
  ],
  "differences": [
    "difference supported by the documents"
  ],
  "evidence_ids": [
    "doc_1_page_1_chunk_0"
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

    for document in result["by_document"]:
        if document.get("status") == "INSUFFICIENT":
            document["evidence_ids"] = []

    result["evidence_ids"] = [
        evidence_id
        for document in result["by_document"]
        for evidence_id in document["evidence_ids"]
    ]

    return result