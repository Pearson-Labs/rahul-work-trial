"""
Enhanced document analysis with clickable citations and improved extraction.
"""

import os
import json
import urllib.parse
from typing import List, Dict, Any
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

from data_storage.database import supabase
from agents.state import ContractAnalysisState
from agents.tools import ContractAnalysisTools

load_dotenv()

class EnhancedDocumentAnalysisAgent:
    """
    Enhanced document-level analysis agent with better citation tracking and clickable links.
    """

    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.1
        )
        self.tools = ContractAnalysisTools()

    def _generate_dynamic_columns(self, query: str) -> List[str]:
        """Generate columns dynamically based on user query with enhanced logic"""
        try:
            system_prompt = """You are a legal document analysis expert. Generate column headers based ONLY on what the user is asking for.

RULES:
1. Generate 3-5 specific column names that directly match their query
2. DO NOT include "Document Name" - the system handles document names
3. If they want page numbers, include "Page Number"
4. Focus on the specific information they're requesting
5. Make column names specific and actionable

Return ONLY a JSON array of column names."""

            user_prompt = f"""Query: "{query}"

What columns should extract the information this user wants?

Examples:
- "find termination clauses" → ["Termination Type", "Notice Period", "Conditions", "Page Number"]
- "identify risks" → ["Risk Type", "Risk Description", "Impact Level", "Mitigation"]
- "extract payment terms" → ["Payment Amount", "Due Date", "Payment Method", "Late Fees"]
- "compliance requirements" → ["Requirement Type", "Standard Referenced", "Compliance Status", "Deadline"]

Generate specific columns for this query:"""

            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            # Parse JSON response
            response_text = response.content.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]

            columns = json.loads(response_text)

            if isinstance(columns, list) and len(columns) > 0:
                print(f"📋 Generated columns: {columns}")
                return columns[:5]  # Limit to 5 columns
            else:
                print("⚠️ Column generation failed, using defaults")
                return ["Key Finding", "Details", "Source Location"]

        except Exception as e:
            print(f"❌ Column generation error: {e}")
            return ["Key Finding", "Details", "Source Location"]

    def _get_document_chunks_by_document(self, chunk_ids: List[str]) -> Dict[str, Dict]:
        """Group chunks by document and combine them with enhanced metadata tracking"""
        try:
            # Get all chunks from database
            chunks_response = supabase.table("document_chunks").select("*").in_("id", chunk_ids).execute()

            if not chunks_response.data:
                return {}

            # Group chunks by document with enhanced tracking
            documents = {}
            for chunk in chunks_response.data:
                metadata = chunk.get("metadata", {})
                file_name = metadata.get("original_file_name", "Unknown Document")

                # Clean up file name
                doc_name = file_name.replace(".docx", "").replace("Copy of ", "")
                if len(doc_name) > 80:
                    doc_name = doc_name[:77] + "..."

                if doc_name not in documents:
                    documents[doc_name] = {
                        "chunks": [],
                        "full_text": "",
                        "metadata": metadata,
                        "chunk_count": 0,
                        "total_length": 0
                    }

                documents[doc_name]["chunks"].append(chunk)
                documents[doc_name]["full_text"] += f"\n\n{chunk['chunk_text']}"
                documents[doc_name]["chunk_count"] += 1
                documents[doc_name]["total_length"] += len(chunk['chunk_text'])

            print(f"📄 Grouped {len(chunks_response.data)} chunks into {len(documents)} documents")
            for doc_name, info in documents.items():
                print(f"  • {doc_name}: {info['chunk_count']} chunks, {info['total_length']:,} chars")

            return documents

        except Exception as e:
            print(f"❌ Error grouping chunks by document: {e}")
            return {}

    def _analyze_document_with_tools(self, query: str, doc_name: str, doc_chunks: List[Dict], columns: List[str]) -> Dict:
        """
        Enhanced document analysis using specialized tools for better extraction and citation tracking
        """
        try:
            print(f"🔧 TOOL-BASED ANALYSIS: {doc_name[:50]}...")

            # Use the document analysis tool for structured extraction
            analysis_result = self.tools.document_analysis_tool(doc_chunks, query, columns)

            if analysis_result.get('error'):
                print(f"⚠️ Tool analysis failed: {analysis_result['error']}")
                return self._fallback_analysis(doc_chunks, query, columns)

            # Extract and enhance the analysis
            tool_analysis = analysis_result.get('analysis', {})
            metadata = analysis_result.get('metadata', {})
            enhanced_result = {}

            for col in columns:
                col_data = tool_analysis.get(col, {})

                if isinstance(col_data, dict):
                    # Enhanced citation with clickable links
                    citation = col_data.get('citation', {})

                    enhanced_result[col] = {
                        "value": col_data.get('value', 'Not found'),
                        "source": col_data.get('source', 'No source available'),
                        "page_numbers": citation.get('page_numbers', []),
                        "document_url": citation.get('clickable_url', ''),
                        "exact_quote": citation.get('exact_quote', ''),
                        "location_markers": citation.get('location_markers', [])
                    }
                else:
                    # Handle simple string responses
                    enhanced_result[col] = {
                        "value": str(col_data) if col_data else 'Not found',
                        "source": "Extracted from document",
                        "page_numbers": [],
                        "document_url": "",
                        "exact_quote": ""
                    }

                # Enhance with clickable Google Drive links
                self._enhance_with_clickable_links(enhanced_result[col], metadata)

            success_count = sum(1 for v in enhanced_result.values()
                              if v.get('value', '') not in ['Not Found', 'N/A', ''])
            print(f"✅ Tool-based analysis: {success_count}/{len(columns)} successful extractions")
            return enhanced_result

        except Exception as e:
            print(f"❌ Tool-based document analysis failed for {doc_name}: {e}")
            return self._fallback_analysis(doc_chunks, query, columns)

    def _enhance_with_clickable_links(self, col_data: Dict, metadata: Dict):
        """Add clickable Google Drive links to column data with text search"""
        google_drive_id = metadata.get('google_drive_file_id')
        if google_drive_id and not col_data.get('document_url'):
            # Try to use exact quote or source for text search
            search_text = col_data.get('exact_quote', col_data.get('source', ''))

            if search_text and search_text.strip() and len(search_text.strip()) > 10:
                # Clean and prepare text for URL fragment
                clean_text = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in search_text)
                clean_text = ' '.join(clean_text.split())[:80]  # Limit length and normalize spaces

                if clean_text:
                    encoded_text = urllib.parse.quote(clean_text)
                    col_data['document_url'] = f"https://docs.google.com/document/d/{google_drive_id}/edit#:~:text={encoded_text}"
                else:
                    # Fallback to direct document link
                    col_data['document_url'] = f"https://docs.google.com/document/d/{google_drive_id}/edit"
            else:
                # Fallback to direct document link
                col_data['document_url'] = f"https://docs.google.com/document/d/{google_drive_id}/edit"

    def _fallback_analysis(self, doc_chunks: List[Dict], query: str, columns: List[str]) -> Dict:
        """
        Enhanced fallback analysis when tool-based method fails
        """
        try:
            print("🔄 Using fallback analysis method...")

            # Combine chunks for analysis
            full_text = "\n\n".join(chunk['chunk_text'] for chunk in doc_chunks)
            metadata = doc_chunks[0].get('metadata', {}) if doc_chunks else {}

            # Use structured extraction with enhanced prompting
            result = self._structured_extraction_fallback(full_text, query, columns, metadata)

            # Enhance all results with clickable links
            for col_data in result.values():
                if isinstance(col_data, dict):
                    self._enhance_with_clickable_links(col_data, metadata)

            return result

        except Exception as e:
            print(f"❌ Fallback analysis failed: {e}")
            return {col: {
                "value": "Analysis error",
                "source": f"Error: {str(e)}",
                "page_numbers": [],
                "document_url": "",
                "exact_quote": ""
            } for col in columns}

    def _structured_extraction_fallback(self, full_text: str, query: str, columns: List[str], metadata: Dict) -> Dict:
        """Enhanced structured extraction as fallback"""
        try:
            doc_name = metadata.get('original_file_name', 'Unknown Document')

            system_prompt = """You are an expert legal document analyst. Extract specific information with high precision and provide detailed citations.

CRITICAL INSTRUCTIONS:
1. **Thorough Analysis**: Read the entire document text carefully
2. **Precise Extraction**: Extract exact information, not summaries
3. **Detailed Citation**: Provide exact quotes and page references when available
4. **Confidence Rating**: Rate your confidence (0.0 to 1.0) for each extraction
5. **Handle Missing Data**: Use "Not Found" if information doesn't exist

OUTPUT FORMAT (JSON):
{
    "column_name": {
        "value": "extracted information",
        "source": "exact quote or section reference",
        "source_text": "longer context around the quote",
        "confidence": 0.8
    }
}"""

            # Smart text truncation
            max_length = 15000  # Increased limit
            if len(full_text) > max_length:
                # Try to end at paragraph boundary
                truncated = full_text[:max_length]
                last_paragraph = truncated.rfind('\n\n')
                if last_paragraph > max_length * 0.8:
                    truncated = truncated[:last_paragraph]
                full_text = truncated + "\n\n[DOCUMENT TRUNCATED - Additional content exists]"

            user_prompt = f"""EXTRACTION TASK:

Document: {doc_name}
Query: "{query}"
Extract information for these columns: {columns}

Document Text:
{full_text}

ANALYSIS INSTRUCTIONS:
1. Find information relevant to: "{query}"
2. For each column, extract specific details from the document
3. Look for page numbers (Page X, p.X, etc.) and section headers
4. Provide exact quotes as sources
5. Rate confidence based on clarity and specificity of the information found

Extract information for each column in the specified JSON format."""

            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            # Parse response
            response_text = response.content.strip()

            # Try to extract JSON
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group(0))

                    # Validate and enhance result
                    validated_result = {}
                    for col in columns:
                        if col in result and isinstance(result[col], dict):
                            validated_result[col] = result[col]
                            # Add missing fields
                            validated_result[col].setdefault("page_numbers", [])
                            validated_result[col].setdefault("document_url", "")
                            validated_result[col].setdefault("exact_quote", result[col].get('source', ''))
                        else:
                            # Handle missing or malformed columns
                            validated_result[col] = {
                                "value": "Not Found",
                                "source": "Information not available in document",
                                "source_text": "",
                                "confidence": 0.1,
                                "page_numbers": [],
                                "document_url": "",
                                "exact_quote": ""
                            }

                    return validated_result

                except json.JSONDecodeError as e:
                    print(f"JSON parsing error: {e}")

            # Simple text-based fallback
            return self._simple_text_extraction(full_text, query, columns)

        except Exception as e:
            print(f"Structured extraction fallback error: {e}")
            return {col: {
                "value": "Extraction failed",
                "source": f"Error: {str(e)}",
                "confidence": 0.1,
                "page_numbers": [],
                "document_url": "",
                "exact_quote": ""
            } for col in columns}

    def _simple_text_extraction(self, text: str, query: str, columns: List[str]) -> Dict:
        """Simple text-based extraction as last resort"""
        result = {}
        query_terms = query.lower().split()
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]

        # Find sentences containing query terms
        relevant_sentences = []
        for sentence in sentences:
            if any(term in sentence.lower() for term in query_terms):
                relevant_sentences.append(sentence)

        # Distribute sentences across columns
        for i, col in enumerate(columns):
            if i < len(relevant_sentences):
                sentence = relevant_sentences[i]
                result[col] = {
                    "value": sentence[:300] + ("..." if len(sentence) > 300 else ""),
                    "source": sentence[:200] + ("..." if len(sentence) > 200 else ""),
                    "source_text": sentence,
                    "confidence": 0.4,
                    "page_numbers": [],
                    "document_url": "",
                    "exact_quote": sentence[:100]
                }
            else:
                result[col] = {
                    "value": "Not Found",
                    "source": "Information not available",
                    "source_text": "",
                    "confidence": 0.1,
                    "page_numbers": [],
                    "document_url": "",
                    "exact_quote": ""
                }

        return result

    def analyze_documents_for_matrix(self, state: ContractAnalysisState) -> ContractAnalysisState:
        """
        Enhanced main method: Analyze documents and create matrix with clickable citations
        """
        try:
            print(f"🚀 ENHANCED DOCUMENT ANALYSIS AGENT: Creating matrix from documents...")

            # Step 1: Generate dynamic columns based on user query
            columns = self._generate_dynamic_columns(state["original_query"])

            # Step 2: Group chunks by document
            chunk_ids = [result["id"] for result in state.get("hybrid_results", [])]
            if not chunk_ids:
                # Fallback to other result types
                for result_type in ["semantic_results", "keyword_results"]:
                    if state.get(result_type):
                        chunk_ids = [r["id"] for r in state[result_type]]
                        break

            if not chunk_ids:
                raise Exception("No chunks found from retrieval stage")

            documents = self._get_document_chunks_by_document(chunk_ids)

            if not documents:
                raise Exception("No documents found to analyze")

            # Step 3: Create doc_name -> chunk_id mapping
            doc_name_to_chunk_id = {}
            for doc_name, doc_info in documents.items():
                if doc_info.get("chunks"):
                    doc_name_to_chunk_id[doc_name] = doc_info["chunks"][0]["id"]

            # Step 4: Enhanced analysis with tools
            matrix_data = {}
            for doc_name, doc_info in documents.items():
                print(f"  📄 Enhanced analysis: {doc_name}")

                analysis_result = self._analyze_document_with_tools(
                    query=state["original_query"],
                    doc_name=doc_name,
                    doc_chunks=doc_info["chunks"],
                    columns=columns
                )

                matrix_data[doc_name] = analysis_result

            # Calculate overall success rate
            total_extractions = len(documents) * len(columns)
            successful_extractions = sum(
                sum(1 for col_data in doc_data.values()
                    if col_data.get('value', '') not in ['Not Found', 'N/A', '', 'Analysis error'])
                for doc_data in matrix_data.values()
            )

            success_rate = (successful_extractions / total_extractions * 100) if total_extractions > 0 else 0

            print(f"✅ Enhanced matrix analysis complete:")
            print(f"  • Documents processed: {len(matrix_data)}")
            print(f"  • Successful extractions: {successful_extractions}/{total_extractions} ({success_rate:.1f}%)")

            return {
                **state,
                "generated_columns": columns,
                "matrix_data": matrix_data,
                "doc_name_to_chunk_id": doc_name_to_chunk_id,
                "processing_step": "enhanced_document_analysis_complete",
                "success_rate": success_rate
            }

        except Exception as e:
            print(f"❌ Enhanced document analysis error: {e}")
            return {
                **state,
                "generated_columns": ["Error"],
                "matrix_data": {"error": {"Error": {
                    "value": str(e),
                    "source": "System error",
                    "confidence": 0.0,
                    "document_url": "",
                    "page_numbers": []
                }}},
                "error_message": f"Enhanced document analysis failed: {str(e)}",
                "processing_step": "enhanced_document_analysis_error"
            }