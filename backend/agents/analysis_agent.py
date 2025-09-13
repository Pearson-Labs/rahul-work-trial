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

class AnalysisAgent:
    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.1
        )

    def _generate_analysis_columns(self, state: ContractAnalysisState) -> List[str]:
        """Generate appropriate column headers for analysis"""
        try:
            # Get sample content from top results
            sample_content = []
            for result in state["hybrid_results"][:3]:
                sample_content.append(result["chunk_text"][:500])  # First 500 chars

            combined_content = "\n---\n".join(sample_content)

            system_prompt = """You are a legal analysis AI. Generate 4-6 column headers for extracting information based on the query and document content.

Focus on:
- Specific, actionable column names
- Information that can be extracted from legal documents
- Relevant to the user's query intent

Return only a JSON array of strings."""

            user_prompt = f"""Query: "{state['original_query']}"
Intent: {state['query_intent']}
Legal Terms: {state['legal_terms']}

Sample Content:
{combined_content}

Generate appropriate column headers as JSON array:"""

            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            response_text = response.content.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]

            columns = json.loads(response_text)

            if not isinstance(columns, list) or not columns:
                columns = ["Document Analysis", "Key Findings", "Relevant Clauses", "Risk Level"]

            return columns[:6]  # Limit to 6 columns

        except Exception as e:
            print(f"Warning: Column generation failed: {e}")
            return ["Document Analysis", "Key Findings", "Relevant Clauses"]

    def _analyze_chunk(self, state: ContractAnalysisState, chunk_text: str, columns: List[str], chunk_id: str) -> Optional[Dict]:
        """
        Analyze a single document chunk
        """
        try:
            system_prompt = f"""You are a contract analysis expert. Extract information from this document chunk based on the query and organize it by the provided columns.

Query: "{state['original_query']}"
Columns: {columns}

Rules:
1. For each column, extract the most relevant information
2. If no relevant information exists, use "N/A"
3. Include direct quotes as sources when possible
4. Be specific and factual

Return JSON format:
{{
    "Column 1": {{'value': 'extracted info', 'source': 'direct quote'}},
    "Column 2": {{'value': 'extracted info', 'source': 'direct quote'}}
}}"""

            user_prompt = f"""Document Content:
{chunk_text}

Extract information for the columns:"""

            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            response_text = response.content.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]

            return json.loads(response_text)

        except Exception as e:
            print(f"Warning: Chunk analysis failed for {chunk_id}: {e}")
            return None

    def _extract_evidence(self, state: ContractAnalysisState, chunk_text: str, analysis: Dict) -> Optional[Dict]:
        """
        Extract evidence chains for findings
        """
        try:
            # Simple evidence extraction - collect non-N/A findings with sources
            evidence = {
                "chunk_preview": chunk_text[:200],
                "findings": []
            }

            for column, data in analysis.items():
                if isinstance(data, dict) and data.get("value", "N/A") != "N/A":
                    evidence["findings"].append({
                        "column": column,
                        "value": data.get("value"),
                        "source": data.get("source", "")
                    })

            return evidence if evidence["findings"] else None

        except Exception as e:
            print(f"Warning: Evidence extraction failed: {e}")
            return None

    def multi_turn_analysis(self, state: ContractAnalysisState) -> ContractAnalysisState:
        """
        Performs multi-turn analysis with column generation and evidence gathering.
        """
        try:
            print(f"🧠 ANALYSIS AGENT: Processing {len(state['hybrid_results'])} documents...")

            # Step 1: Generate columns based on query and retrieved content
            columns = self._generate_analysis_columns(state)

            # Step 2: Analyze each document chunk
            analyzed_docs = {}
            evidence_chains = []
            doc_name_to_chunk_id = {}  # Track document name to chunk ID mapping

            for i, result in enumerate(state["hybrid_results"][:15]):  # Limit processing
                chunk_id = result["id"]
                chunk_text = result["chunk_text"]

                # Get the actual document name from metadata
                try:
                    chunk_response = supabase.table("document_chunks").select("metadata").eq("id", chunk_id).single().execute()
                    if chunk_response.data and chunk_response.data["metadata"]:
                        original_file_name = chunk_response.data["metadata"].get("original_file_name", "Unknown Document")
                        # Clean up the file name (remove extension and long suffixes)
                        doc_name = original_file_name.replace(".docx", "").replace("Copy of ", "")
                        # Truncate very long names
                        if len(doc_name) > 80:
                            doc_name = doc_name[:77] + "..."
                    else:
                        doc_name = f"Document {i+1}"
                except Exception as e:
                    print(f"Warning: Could not get document name for chunk {chunk_id}: {e}")
                    doc_name = f"Document {i+1}"

                # Handle duplicate document names by adding chunk info
                if doc_name in analyzed_docs:
                    doc_name = f"{doc_name} (Chunk {i+1})"

                print(f"  📄 Analyzing {doc_name[:50]}{'...' if len(doc_name) > 50 else ''}")

                analysis = self._analyze_chunk(state, chunk_text, columns, chunk_id)
                if analysis:
                    analyzed_docs[doc_name] = analysis
                    doc_name_to_chunk_id[doc_name] = chunk_id  # Store mapping

                    # Extract evidence chains
                    evidence = self._extract_evidence(state, chunk_text, analysis)
                    if evidence:
                        evidence_chains.append(evidence)

            print(f"✅ Analysis complete: {len(analyzed_docs)} documents processed")

            return {
                **state,
                "generated_columns": columns,
                "preliminary_findings": analyzed_docs,
                "evidence_chains": evidence_chains,
                "doc_name_to_chunk_id": doc_name_to_chunk_id,  # Pass mapping to state
                "processing_step": "analysis_complete"
            }

        except Exception as e:
            print(f"❌ Analysis error: {e}")
            return {
                **state,
                "generated_columns": ["Error"],
                "preliminary_findings": {"error": {"Error": str(e)}},
                "evidence_chains": [],
                "error_message": f"Analysis failed: {str(e)}",
                "processing_step": "analysis_error"
            }
