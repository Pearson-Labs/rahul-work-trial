import os
import json
from typing import List, Dict, Any, Optional
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

from ..data_storage.database import supabase
from ..data_storage.pinecone_store import get_pinecone_store
from .state import ContractAnalysisState

load_dotenv()

class ValidationAgent:
    def _validate_findings(self, state: ContractAnalysisState) -> ContractAnalysisState:
        """
        Validates analysis findings and calculates confidence scores.
        """
        try:
            print(f"✅ VALIDATION AGENT: Validating findings...")

            findings = state["preliminary_findings"]
            confidence_scores = {}

            # Calculate confidence for each document
            total_confidence = 0.0
            valid_docs = 0

            for doc_name, doc_analysis in findings.items():
                if isinstance(doc_analysis, dict) and "error" not in doc_name.lower():
                    confidence = self._calculate_document_confidence(doc_analysis, state)
                    confidence_scores[doc_name] = confidence
                    total_confidence += confidence
                    valid_docs += 1

            # Overall confidence
            overall_confidence = total_confidence / valid_docs if valid_docs > 0 else 0.0

            # Determine if retry is needed
            needs_retry = (
                overall_confidence < 0.4 or  # Low confidence
                len(findings) < 3 or  # Too few results
                state.get("retrieval_confidence", 0) < 0.3  # Poor retrieval
            )

            print(f"📊 Overall confidence: {overall_confidence:.2f}")
            print(f"🔄 Needs retry: {needs_retry}")

            return {
                **state,
                "confidence_scores": confidence_scores,
                "needs_retry": needs_retry,
                "processing_step": "validation_complete"
            }

        except Exception as e:
            print(f"❌ Validation error: {e}")
            return {
                **state,
                "confidence_scores": {},
                "needs_retry": False,  # Don't retry on validation errors
                "error_message": f"Validation failed: {str(e)}",
                "processing_step": "validation_error"
            }

    def _calculate_document_confidence(self, doc_analysis: Dict, state: ContractAnalysisState) -> float:
        """
        Calculate confidence for a single document analysis
        """
        try:
            if not doc_analysis:
                return 0.0

            total_columns = len(doc_analysis)
            non_na_columns = 0
            has_sources = 0

            for column_data in doc_analysis.values():
                if isinstance(column_data, dict):
                    value = column_data.get("value", "N/A")
                    source = column_data.get("source", "")

                    if value != "N/A":
                        non_na_columns += 1
                        if source and len(source) > 10:  # Has meaningful source
                            has_sources += 1

            # Calculate confidence metrics
            coverage_ratio = non_na_columns / total_columns if total_columns > 0 else 0
            source_ratio = has_sources / non_na_columns if non_na_columns > 0 else 0

            # Combined confidence
            confidence = (coverage_ratio * 0.6) + (source_ratio * 0.4)
            return min(confidence, 1.0)

        except Exception as e:
            print(f"Warning: Document confidence calculation failed: {e}")
            return 0.3  # Default low confidence

    def should_retry_analysis(self, state: ContractAnalysisState) -> str:
        """
        Determine if analysis should be retried
        """
        return "retry" if state.get("needs_retry", False) else "continue"
