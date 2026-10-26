from typing import TypedDict, Any


class ExploreAgentState(TypedDict, total=False):

    question: str

    document_ids: list[int]

    top_k_per_document: int

    # Explore 内部是什么任务
    # compare / synthesize / agreement / methods ...
    explore_intent: str

    # 每篇论文真正需要搜索的主题
    retrieval_focus: str

    retrieval_queries: dict[int, str]

    evidence_by_document: dict[int, list[dict]]

    sufficiency_by_document: dict[int, bool]

    sufficiency_reasons: dict[int, str]

    retryable_by_document: dict[int, bool]

    missing_aspects: dict[int, str]

    retry_counts: dict[int, int]

    result: dict[str, Any]