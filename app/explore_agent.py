from langgraph.graph import StateGraph, START, END

from app.agent_state import ExploreAgentState

from app.agent_nodes import (
    analyze_explore_query,
    retrieve_per_document,
    evaluate_evidence_sufficiency,
    recover_insufficient_documents_with_tools,
    has_retryable_documents,
    generate_explore_result,
)


def route_after_sufficiency(
    state: ExploreAgentState
) -> str:

    if has_retryable_documents(state):
        return "retry"

    return "finish"


builder = StateGraph(
    ExploreAgentState
)


# ------------------------------------------------------------
# Nodes
# ------------------------------------------------------------

builder.add_node(
    "analyze_query",
    analyze_explore_query
)

builder.add_node(
    "retrieve",
    retrieve_per_document
)

builder.add_node(
    "evaluate",
    evaluate_evidence_sufficiency
)

builder.add_node(
    "tool_recovery",
    recover_insufficient_documents_with_tools
)

builder.add_node(
    "generate_result",
    generate_explore_result
)


# ------------------------------------------------------------
# Normal flow
# ------------------------------------------------------------

builder.add_edge(
    START,
    "analyze_query"
)

builder.add_edge(
    "analyze_query",
    "retrieve"
)

builder.add_edge(
    "retrieve",
    "evaluate"
)


# ------------------------------------------------------------
# Conditional routing
# ------------------------------------------------------------

builder.add_conditional_edges(
    "evaluate",
    route_after_sufficiency,
    {
        "retry": "tool_recovery",
        "finish": "generate_result"
    }
)


# ------------------------------------------------------------
# Tool recovery loop
# ------------------------------------------------------------

builder.add_edge(
    "tool_recovery",
    "evaluate"
)


# ------------------------------------------------------------
# Final result
# ------------------------------------------------------------

builder.add_edge(
    "generate_result",
    END
)


# ------------------------------------------------------------
# Compile graph
# ------------------------------------------------------------

explore_agent_graph = builder.compile()