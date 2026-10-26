import os
import json

from dotenv import load_dotenv
from openai import OpenAI



load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)


def answer_with_evidence(
    question: str,
    evidence_chunks: list[dict]
) -> dict:

    evidence_text = ""

    for chunk in evidence_chunks:
        evidence_id = chunk["evidence_id"]

        evidence_text += (
            f"\nEvidence ID: {evidence_id}\n"
            f"Page: {chunk['page_number']}\n"
            f"Text: {chunk['text']}\n"
        )

    prompt = f"""
You are an evidence-grounded reading assistant.

Answer the user's question using only the evidence provided below.

Rules:
1. Do not use outside knowledge.
2. If the evidence is insufficient, clearly say so.
3. Prefer specific statements, assessment targets, results, or conclusions
   over broader background statements when answering the question.
4. Only cite evidence that actually supports the answer.
5. Return valid JSON only.
6. When multiple statements appear in the same evidence chunk,
   make sure each statement refers to the same variable being asked about.

When answering yes/no questions:
- Identify the exact subject, relationship, and object in the question.
- Compare that exact relationship with the evidence.
- Do not confuse statements about different variables or outcomes.
- For example, a statement about molecular movement being independent
  of sleep is NOT the same as a statement about brain clearance.
- If the evidence says "brain clearance is reduced during sleep" or
  "clearance is reduced by sleep", and the question asks whether sleep
  reduces brain clearance, the answer is YES.
- If the evidence expresses the same relationship using active or passive
  voice, treat them as equivalent.
- The first word of the answer must be consistent with the evidence.
- Do not answer "No" and then cite evidence that supports the proposition.
- Only use Evidence IDs exactly as provided in the Evidence section.
Return exactly this structure:

{{
  "answer": "your answer here",
  "evidence_ids": ["doc_4_page_1_chunk_0"]
}}

Question:
{question}

Evidence:
{evidence_text}
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

    return json.loads(content)

def verify_claim_with_evidence(
    claim: str,
    evidence_chunks: list[dict]
) -> dict:

    evidence_text = ""

    for chunk in evidence_chunks:
        evidence_id = chunk["evidence_id"]

        evidence_text += (
            f"\nEvidence ID: {evidence_id}\n"
            f"Page: {chunk['page_number']}\n"
            f"Text: {chunk['text']}\n"
        )
    prompt = f"""
You are verifying a claim using ONLY the provided evidence.

Claim:
{claim}

Evidence:
{evidence_text}

Determine whether the claim is:

SUPPORTED:
The evidence directly states or clearly implies the SAME proposition
as the claim.

CONTRADICTED:
The evidence directly states the OPPOSITE proposition from the claim.

INSUFFICIENT:
The evidence does not provide enough information to determine whether
the claim is true or false.

Important reasoning rules:
- Read the claim literally.
- Compare the direction of the relationship carefully.
- If the claim says "X reduces Y" and the evidence says
  "Y is reduced by X", these statements mean the SAME thing
  and the verdict must be SUPPORTED.
- If the claim and evidence express the same relationship using
  different wording or active/passive voice, they are still SUPPORTED.
- Do not label a claim CONTRADICTED unless the evidence actually
  asserts the opposite.
- Missing evidence is INSUFFICIENT, not CONTRADICTED.
- Your reasoning must be logically consistent with your verdict.
- Use only the provided evidence.
- Only use Evidence IDs exactly as provided in the Evidence section.

Return valid JSON only:

{{
  "verdict": "SUPPORTED | CONTRADICTED | INSUFFICIENT",
  "confidence": 0.0,
  "reasoning": "brief explanation",
  "evidence_ids": ["doc_4_page_1_chunk_0"]
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

    return json.loads(content)