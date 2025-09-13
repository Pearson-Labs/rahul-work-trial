from typing import List, Dict, Any, TypedDict, Optional

class ContractAnalysisState(TypedDict):
    # Query Processing
    original_query: str
    query_intent: str
    expanded_queries: List[str]
    legal_terms: List[str]

    # Retrieval
    semantic_results: List[Dict[str, Any]]
    keyword_results: List[Dict[str, Any]]
    hybrid_results: List[Dict[str, Any]]
    retrieval_confidence: float

    # Analysis
    generated_columns: List[str]
    preliminary_findings: Dict[str, Any]
    evidence_chains: List[Dict[str, Any]]
    cross_references: List[Dict[str, Any]]

    # Validation & Output
    confidence_scores: Dict[str, float]
    validated_results: Dict[str, Any]
    final_analysis: Dict[str, Any]
    needs_retry: bool
    error_message: str

    # Metadata
    matrix_id: str
    processing_step: str
    doc_name_to_chunk_id: Dict[str, str]  # Mapping of document names to chunk IDs
