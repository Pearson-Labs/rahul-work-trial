"""
Synthesis agent for finalizing analysis results and storing them in the database.
"""

from typing import Dict
from data_storage.database import supabase
from agents.state import ContractAnalysisState

class SynthesisAgent:
    async def synthesize_results(self, state: ContractAnalysisState) -> ContractAnalysisState:
        """
        Synthesizes and formats the final analysis and stores it in the database.
        """
        try:
            print("🔎 SYNTHESIS AGENT: Finalizing and storing results...")
            matrix_data = state.get("matrix_data", {})
            
            final_analysis = {
                "columns": state["generated_columns"],
                "data": matrix_data,
                "metadata": {
                    "query_intent": state["query_intent"],
                    "documents_analyzed": len(matrix_data),
                    "confidence_scores": state["confidence_scores"],
                    "retrieval_confidence": state.get("retrieval_confidence", 0.0),
                }
            }

            await self._store_results_in_db(state, final_analysis)

            print(f"✅ Synthesis complete!")
            return {
                **state,
                "final_analysis": final_analysis,
                "processing_step": "synthesis_complete"
            }

        except Exception as e:
            print(f"❌ Synthesis error: {e}")
            return {**state, "error_message": f"Synthesis failed: {str(e)}", "processing_step": "synthesis_error"}

    async def _store_results_in_db(self, state: ContractAnalysisState, final_analysis: Dict):
        """Stores the final analysis results in Supabase."""
        try:
            matrix_id = state["matrix_id"]
            
            # Update matrix with final columns and status
            supabase.table("matrices").update({
                "columns": final_analysis["columns"],
                "status": "completed" # Example of updating status
            }).eq("id", matrix_id).execute()

            # Store individual document results
            for doc_name, row_data in final_analysis["data"].items():
                chunk_id = state["doc_name_to_chunk_id"].get(doc_name)
                if chunk_id:
                    supabase.table("matrix_data").insert({
                        "matrix_id": matrix_id,
                        "document_chunk_id": chunk_id, # Link to a representative chunk
                        "row_data": row_data,
                        "document_name": doc_name
                    }).execute()

            print(f"  - Results for matrix {matrix_id} stored in database.")
        except Exception as e:
            print(f"⚠️ Database storage failed: {e}")
            # Do not fail the whole process, just log the warning