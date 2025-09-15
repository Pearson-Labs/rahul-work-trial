"""
State management for contract analysis workflow.
"""

from typing import List, Dict, Any, TypedDict, Optional

class ContractAnalysisState(TypedDict, total=False):
    # Query Processing
    original_query: str
    query_intent: str
    expanded_queries: List[str]
    legal_terms: List[str]

    # Retrieval Results
    semantic_results: List[Dict[str, Any]]
    keyword_results: List[Dict[str, Any]]
    hybrid_results: List[Dict[str, Any]]
    retrieved_chunk_ids: List[str]
    retrieval_confidence: float

    # Analysis
    generated_columns: List[str]
    preliminary_findings: Dict[str, Any]  # Legacy support
    chunk_analysis_results: Dict[str, List[Dict[str, Any]]]
    matrix_data: Dict[str, Any]  # Final document-level data

    # Enhanced Citation Tracking
    evidence_chains: List[Dict[str, Any]]
    cross_references: List[Dict[str, Any]]
    page_locations: Dict[str, List[str]]  # doc_name -> page numbers
    exact_citations: Dict[str, str]  # extraction -> exact quote

    # Validation & Output
    confidence_scores: Dict[str, float]
    validated_results: Dict[str, Any]
    final_analysis: Dict[str, Any]
    needs_retry: bool
    retry_count: int
    error_message: str

    # Metadata
    matrix_id: str
    processing_step: str
    doc_name_to_chunk_id: Dict[str, str]

    # Tool execution tracking
    tool_results: Dict[str, Any]
    current_tool: Optional[str]