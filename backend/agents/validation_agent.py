"""
Validation agent for analyzing extraction quality and determining retry strategies.
"""

from typing import Dict
from agents.state import ContractAnalysisState

class ValidationAgent:
    async def validate_findings(self, state: ContractAnalysisState) -> ContractAnalysisState:
        """
        Validates analysis findings, calculates confidence, and increments retry counter.
        """
        print("🔎 VALIDATION AGENT: Validating matrix data...")
        findings = state.get("matrix_data", {})
        
        # Increment the retry counter each time this node runs
        current_retries = state.get("retry_count", 0)
        
        confidence_scores = {}
        total_confidence = 0.0

        for doc_name, doc_analysis in findings.items():
            confidence = self._calculate_document_confidence(doc_analysis)
            confidence_scores[doc_name] = confidence
            total_confidence += confidence
        
        valid_docs = len(findings)
        overall_confidence = total_confidence / valid_docs if valid_docs > 0 else 0.0
        
        confidence_is_low = overall_confidence < 0.5 or state.get("retrieval_confidence", 0) < 0.4
        
        print(f"  - Overall confidence: {overall_confidence:.2f}")
        
        return {
            **state,
            "confidence_scores": confidence_scores,
            "needs_retry": confidence_is_low,
            "retry_count": current_retries + 1, # Increment for the next potential check
            "processing_step": "validation_complete"
        }

    def _calculate_document_confidence(self, doc_analysis: Dict) -> float:
        """Calculates confidence based on coverage and sourcing."""
        if not doc_analysis or not isinstance(doc_analysis, dict):
            return 0.0
        
        total_columns = len(doc_analysis)
        filled_columns = 0
        sourced_columns = 0

        for col_data in doc_analysis.values():
            if isinstance(col_data, dict):
                value = col_data.get("value", "Not Found")
                source = col_data.get("source", "")
                if value not in ["Not Found", "N/A", ""]:
                    filled_columns += 1
                    if source and len(source) > 10:
                        sourced_columns += 1
        
        coverage_ratio = filled_columns / total_columns if total_columns > 0 else 0
        source_ratio = sourced_columns / filled_columns if filled_columns > 0 else 0
        
        return (coverage_ratio * 0.6) + (source_ratio * 0.4)

    def should_retry_analysis(self, state: ContractAnalysisState) -> str:
        """
        Enhanced retry logic with different retry strategies
        """
        needs_retry = state.get("needs_retry", False)
        retry_count = state.get("retry_count", 0)
        retrieval_confidence = state.get("retrieval_confidence", 0.5)
        success_rate = state.get("success_rate", 0)

        # More intelligent retry logic
        if needs_retry and retry_count <= 2:  # Allow more retries
            if retry_count == 0 and retrieval_confidence < 0.3:
                print(f"🔄 Low retrieval confidence ({retrieval_confidence:.2f}). Retrying retrieval...")
                return "retry"
            elif retry_count == 1 and success_rate < 30:
                print(f"🔄 Low success rate ({success_rate:.1f}%). Retrying analysis with different approach...")
                return "retry_analysis"
            elif retry_count == 2:
                print(f"🔄 Final retry attempt with expanded search...")
                return "retry"
            else:
                print(f"🔄 Retrying analysis (Attempt {retry_count + 1})...")
                return "retry_analysis"
        else:
            if needs_retry and retry_count > 2:
                print("⚠️ Max retries reached. Continuing with best available result.")
            else:
                print("✅ Validation passed. Continuing to synthesis.")
            return "continue"