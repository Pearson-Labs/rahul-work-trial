"""
Enhanced tools for contract analysis with citation tracking and smart retrieval.
"""

import os
import re
import json
import urllib.parse
from typing import List, Dict, Any
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

from data_storage.pinecone_store import get_pinecone_store

load_dotenv()

class ContractAnalysisTools:
    """Collection of specialized tools for contract analysis"""

    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.1
        )
        self.pinecone_store = get_pinecone_store()

    def document_search_tool(self, query: str, legal_terms: List[str], top_k: int = 20) -> Dict[str, Any]:
        """
        Advanced document search tool that finds relevant sections with page tracking.
        """
        try:
            print(f"🔍 DOCUMENT SEARCH TOOL: Searching for '{query[:100]}...'")

            # Multi-strategy search
            searches = []

            # 1. Semantic search with original query
            semantic_results = self.pinecone_store.search_similar_chunks(
                query=query,
                top_k=top_k // 2,
                score_threshold=0.3
            )
            searches.extend([(r, 'semantic', r.get('score', 0)) for r in semantic_results])

            # 2. Legal term focused search
            if legal_terms:
                legal_query = " AND ".join([f'"{term}"' for term in legal_terms[:3]])
                legal_results = self.pinecone_store.search_similar_chunks(
                    query=legal_query,
                    top_k=top_k // 2,
                    score_threshold=0.25
                )
                searches.extend([(r, 'legal', r.get('score', 0) + 0.1) for r in legal_results])

            # 3. Keyword expansion search
            expanded_query = self._expand_query_keywords(query)
            if expanded_query != query:
                expanded_results = self.pinecone_store.search_similar_chunks(
                    query=expanded_query,
                    top_k=top_k // 3,
                    score_threshold=0.25
                )
                searches.extend([(r, 'expanded', r.get('score', 0)) for r in expanded_results])

            # Deduplicate and rank
            seen_ids = set()
            ranked_results = []

            # Sort by adjusted score (legal terms get boost)
            searches.sort(key=lambda x: x[2], reverse=True)

            for result, search_type, score in searches:
                if result['id'] not in seen_ids:
                    seen_ids.add(result['id'])
                    result['search_type'] = search_type
                    result['adjusted_score'] = score
                    ranked_results.append(result)

            # Extract page information and enhance results
            enhanced_results = self._enhance_with_page_info(ranked_results[:top_k])

            print(f"✅ Found {len(enhanced_results)} relevant chunks from {len(set(r.get('metadata', {}).get('original_file_name', 'unknown') for r in enhanced_results))} documents")

            return {
                "results": enhanced_results,
                "total_found": len(enhanced_results),
                "search_strategies_used": list(set(r.get('search_type', 'unknown') for r in enhanced_results)),
                "confidence": self._calculate_search_confidence(enhanced_results, legal_terms)
            }

        except Exception as e:
            print(f"❌ Document search failed: {e}")
            return {
                "results": [],
                "total_found": 0,
                "search_strategies_used": [],
                "confidence": 0.0,
                "error": str(e)
            }

    def citation_extraction_tool(self, chunk_text: str, query: str, doc_metadata: Dict) -> Dict[str, Any]:
        """
        Tool to extract precise citations with page numbers and exact quotes.
        """
        try:
            print(f"📄 CITATION EXTRACTION TOOL: Processing {doc_metadata.get('original_file_name', 'unknown')[:50]}...")

            # Extract page references from text
            page_numbers = self._extract_page_numbers(chunk_text)

            # Find the most relevant excerpt for the query
            relevant_excerpt = self._find_relevant_excerpt(chunk_text, query)

            # Create citation with location tracking
            citation = {
                "exact_quote": relevant_excerpt,
                "page_numbers": page_numbers,
                "document_name": doc_metadata.get("original_file_name", "Unknown"),
                "google_drive_id": doc_metadata.get("google_drive_file_id"),
                "chunk_index": doc_metadata.get("chunk_index", 0),
                "confidence": self._calculate_citation_confidence(relevant_excerpt, query),
                "context_length": len(chunk_text),
                "location_markers": self._find_location_markers(chunk_text)
            }

            # Create clickable URL with text fragment to jump to specific location
            if citation["google_drive_id"] and relevant_excerpt:
                # Use a more reliable text fragment - shorter and cleaner
                clean_excerpt = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in relevant_excerpt)
                clean_excerpt = ' '.join(clean_excerpt.split())[:60]  # Shorter, more reliable

                if clean_excerpt:
                    encoded_text = self._encode_text_fragment(clean_excerpt)
                    citation["clickable_url"] = f"https://docs.google.com/document/d/{citation['google_drive_id']}/edit#:~:text={encoded_text}"
                else:
                    citation["clickable_url"] = f"https://docs.google.com/document/d/{citation['google_drive_id']}/edit"
            elif citation["google_drive_id"]:
                # Fallback to direct document link
                citation["clickable_url"] = f"https://docs.google.com/document/d/{citation['google_drive_id']}/edit"

            return citation

        except Exception as e:
            print(f"❌ Citation extraction failed: {e}")
            return {
                "exact_quote": chunk_text[:200] + "...",
                "page_numbers": [],
                "document_name": doc_metadata.get("original_file_name", "Unknown"),
                "confidence": 0.5,
                "error": str(e)
            }

    def legal_term_matcher_tool(self, text: str, legal_terms: List[str]) -> Dict[str, Any]:
        """
        Tool to find and rank legal term matches with context.
        """
        try:
            matches = {}
            text_lower = text.lower()

            for term in legal_terms:
                term_lower = term.lower()
                if term_lower in text_lower:
                    # Find all occurrences with context
                    contexts = []
                    start = 0
                    while True:
                        pos = text_lower.find(term_lower, start)
                        if pos == -1:
                            break

                        # Extract context around the term
                        context_start = max(0, pos - 100)
                        context_end = min(len(text), pos + len(term) + 100)
                        context = text[context_start:context_end].strip()

                        contexts.append({
                            "context": context,
                            "position": pos,
                            "highlighted_term": text[pos:pos + len(term)]
                        })
                        start = pos + 1

                    matches[term] = {
                        "count": len(contexts),
                        "contexts": contexts,
                        "relevance_score": len(contexts) * (1 + len(term) / 100)  # Longer terms get bonus
                    }

            return {
                "matches": matches,
                "total_terms_found": len(matches),
                "overall_relevance": sum(m["relevance_score"] for m in matches.values())
            }

        except Exception as e:
            print(f"❌ Legal term matching failed: {e}")
            return {"matches": {}, "total_terms_found": 0, "overall_relevance": 0, "error": str(e)}

    def document_analysis_tool(self, doc_chunks: List[Dict], query: str, columns: List[str]) -> Dict[str, Any]:
        """
        Enhanced document analysis tool with structured extraction and validation.
        """
        try:
            print(f"📊 DOCUMENT ANALYSIS TOOL: Analyzing document with {len(doc_chunks)} chunks...")

            # Combine chunks into full document
            full_text = ""
            metadata = {}
            page_info = []

            for chunk in doc_chunks:
                full_text += f"\n\n{chunk['chunk_text']}"
                if not metadata:
                    metadata = chunk.get('metadata', {})

                # Extract page information
                pages = self._extract_page_numbers(chunk['chunk_text'])
                page_info.extend(pages)

            # Use structured extraction with validation
            extraction_result = self._structured_extraction(full_text, query, columns, metadata)

            # Add page information to each extraction
            for col, data in extraction_result.items():
                if isinstance(data, dict):
                    data["page_locations"] = list(set(page_info))
                    # Create precise citation
                    citation = self.citation_extraction_tool(
                        data.get("source_text", ""),
                        query,
                        metadata
                    )
                    data["citation"] = citation

            return {
                "analysis": extraction_result,
                "document_name": metadata.get("original_file_name", "Unknown"),
                "total_pages": len(set(page_info)) if page_info else 0,
                "confidence": self._calculate_extraction_confidence(extraction_result),
                "metadata": metadata
            }

        except Exception as e:
            print(f"❌ Document analysis failed: {e}")
            return {
                "analysis": {col: {"value": "Analysis failed", "source": f"Error: {str(e)}"} for col in columns},
                "document_name": "Unknown",
                "confidence": 0.0,
                "error": str(e)
            }

    def _expand_query_keywords(self, query: str) -> str:
        """Expand query with legal synonyms and related terms"""
        expansions = {
            "termination": "termination end terminate conclusion",
            "payment": "payment pay compensation remuneration",
            "liability": "liability responsible liable obligation",
            "breach": "breach violation default non-compliance",
            "notice": "notice notification inform advise",
            "confidential": "confidential proprietary secret non-disclosure",
        }

        expanded = query
        for key, expansion in expansions.items():
            if key.lower() in query.lower():
                expanded += f" {expansion}"

        return expanded

    def _enhance_with_page_info(self, results: List[Dict]) -> List[Dict]:
        """Enhance search results with page information"""
        for result in results:
            text = result.get('chunk_text', '')
            result['page_numbers'] = self._extract_page_numbers(text)
            result['has_page_info'] = len(result['page_numbers']) > 0
        return results

    def _extract_page_numbers(self, text: str) -> List[str]:
        """Extract page numbers from text"""
        patterns = [
            r'Page\s+(\d+)',
            r'p\.\s*(\d+)',
            r'pg\.\s*(\d+)',
            r'\[Page\s+(\d+)\]',
            r'— (\d+) —'
        ]

        pages = set()
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                pages.add(match.group(1))

        return sorted(list(pages), key=int) if pages else []

    def _find_relevant_excerpt(self, text: str, query: str, max_length: int = 200) -> str:
        """Find the most relevant excerpt from text for the query"""
        query_terms = query.lower().split()
        sentences = text.split('.')

        best_sentence = ""
        best_score = 0

        for sentence in sentences:
            sentence_lower = sentence.lower()
            score = sum(1 for term in query_terms if term in sentence_lower)

            if score > best_score and len(sentence.strip()) > 20:
                best_score = score
                best_sentence = sentence.strip()

        if best_sentence and len(best_sentence) > max_length:
            return best_sentence[:max_length - 3] + "..."

        return best_sentence or text[:max_length]

    def _find_location_markers(self, text: str) -> List[str]:
        """Find section headers and other location markers"""
        markers = []

        # Common legal section patterns
        patterns = [
            r'^([A-Z][^.]*:).*$',  # Section headers ending with :
            r'^\d+\.\s+([A-Z][^.]*?)\..*$',  # Numbered sections
            r'^Article\s+\d+',  # Articles
            r'^Section\s+\d+',  # Sections
        ]

        for line in text.split('\n'):
            line = line.strip()
            for pattern in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    markers.append(match.group(0)[:100])
                    break

        return markers[:5]  # Limit to first 5 markers

    def _encode_text_fragment(self, text: str) -> str:
        """Encode text for URL fragment"""
        # Clean text for URL fragment
        clean_text = re.sub(r'[^\w\s]', ' ', text).strip()
        clean_text = ' '.join(clean_text.split())  # Normalize spaces
        return urllib.parse.quote(clean_text[:50])  # Limit length

    def _structured_extraction(self, full_text: str, query: str, columns: List[str], metadata: Dict) -> Dict[str, Any]:
        """Perform structured extraction with enhanced prompting"""
        try:
            doc_name = metadata.get("original_file_name", "Unknown Document")

            system_prompt = """You are an expert legal document analyst. Your task is to extract specific, concise information from legal documents.

CRITICAL INSTRUCTIONS:
1. **Be Concise**: Extract only the most relevant, specific information for each column
2. **Direct Answers**: Provide short, direct answers - NOT long text blocks
3. **No Wholesale Copying**: Summarize or paraphrase instead of copying large chunks
4. **Focus on the Question**: Only extract information that directly answers the column heading
5. **Precise Language**: Use clear, professional language
6. **Handle Missing Data**: If information doesn't exist, return "Not found"

EXAMPLES:
- Instead of: "liers, potential suppliers, employees, independent contractors, and other personnel, and others, and I will not use or disclose such Confidential..."
- Extract: "Non-solicitation of employees and contractors"

OUTPUT FORMAT:
Return a JSON object where each column maps to:
{
    "value": "concise, specific answer",
    "source": "relevant page or section reference"
}"""

            # Truncate text smartly - try to keep complete sections
            max_length = 12000
            if len(full_text) > max_length:
                truncated = full_text[:max_length]
                # Try to end at a sentence boundary
                last_period = truncated.rfind('.')
                if last_period > max_length * 0.8:
                    truncated = truncated[:last_period + 1]
                full_text = truncated + "\n\n[DOCUMENT TRUNCATED]"

            user_prompt = f"""EXTRACTION TASK:

Document: {doc_name}
Query: "{query}"
Columns to extract: {columns}

Document Text:
{full_text}

INSTRUCTIONS:
1. For each column in {columns}, find specific information from this document
2. Look for information that directly answers: "{query}"
3. Extract exact quotes as sources
4. Rate your confidence (0.0 to 1.0) based on how certain you are about the extraction
5. If you cannot find relevant information for a column, use "Not Found" as the value

Analyze the document step by step and extract information for each column."""

            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            response_text = response.content.strip()

            # Try to extract JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group(0))

                    # Validate and ensure all columns are present
                    for col in columns:
                        if col not in result:
                            result[col] = {
                                "value": "Not found",
                                "source": "Information not available in document"
                            }
                        elif not isinstance(result[col], dict):
                            # Handle simple string responses
                            result[col] = {
                                "value": str(result[col]),
                                "source": "Extracted from document"
                            }

                        # Ensure each result has required fields
                        if isinstance(result[col], dict):
                            if "value" not in result[col]:
                                result[col]["value"] = "Not found"
                            if "source" not in result[col]:
                                result[col]["source"] = "Document analysis"

                    return result

                except json.JSONDecodeError as e:
                    print(f"JSON parsing error: {e}")
                    print(f"Response text: {response_text[:500]}...")

            # Fallback extraction
            print("JSON extraction failed, using fallback method")
            return self._fallback_extraction(full_text, query, columns)

        except Exception as e:
            print(f"Structured extraction error: {e}")
            return {col: {"value": "Analysis error", "source": f"Error: {str(e)}"} for col in columns}

    def _fallback_extraction(self, text: str, query: str, columns: List[str]) -> Dict[str, Any]:
        """Simple fallback extraction when structured method fails"""
        result = {}
        text_lower = text.lower()
        query_terms = query.lower().split()

        # Find sentences that contain query terms
        sentences = text.split('.')
        relevant_sentences = []

        for sentence in sentences:
            if any(term in sentence.lower() for term in query_terms):
                relevant_sentences.append(sentence.strip())

        # Distribute relevant sentences across columns
        for i, col in enumerate(columns):
            if i < len(relevant_sentences):
                sentence = relevant_sentences[i]
                result[col] = {
                    "value": sentence[:200] + ("..." if len(sentence) > 200 else ""),
                    "source": sentence,
                    "source_text": sentence,
                    "confidence": 0.4
                }
            else:
                result[col] = {
                    "value": "Not Found",
                    "source": "Information not available",
                    "source_text": "",
                    "confidence": 0.1
                }

        return result

    def _calculate_search_confidence(self, results: List[Dict], legal_terms: List[str]) -> float:
        """Calculate confidence in search results"""
        if not results:
            return 0.0

        # Base confidence from scores
        avg_score = sum(r.get('adjusted_score', 0.5) for r in results) / len(results)

        # Bonus for legal term coverage
        legal_bonus = 0.0
        if legal_terms:
            found_terms = set()
            for result in results:
                text = result.get('chunk_text', '').lower()
                for term in legal_terms:
                    if term.lower() in text:
                        found_terms.add(term)
            legal_bonus = len(found_terms) / len(legal_terms) * 0.2

        # Bonus for page information
        page_bonus = sum(1 for r in results if r.get('page_numbers')) / len(results) * 0.1

        return min(1.0, avg_score + legal_bonus + page_bonus)

    def _calculate_citation_confidence(self, excerpt: str, query: str) -> float:
        """Calculate confidence in citation quality"""
        if not excerpt:
            return 0.1

        query_terms = query.lower().split()
        excerpt_lower = excerpt.lower()

        term_matches = sum(1 for term in query_terms if term in excerpt_lower)
        coverage = term_matches / len(query_terms) if query_terms else 0

        # Length penalty/bonus
        length_factor = min(1.0, len(excerpt) / 100)

        return min(1.0, coverage * 0.7 + length_factor * 0.3)

    def _calculate_extraction_confidence(self, extraction: Dict) -> float:
        """Calculate overall confidence in extraction results"""
        if not extraction:
            return 0.0

        confidences = []
        for col_data in extraction.values():
            if isinstance(col_data, dict):
                conf = col_data.get('confidence', 0.5)
                value = col_data.get('value', '')

                # Penalty for "Not Found" values
                if value in ['Not Found', 'N/A', 'Not specified']:
                    conf *= 0.2

                confidences.append(conf)

        return sum(confidences) / len(confidences) if confidences else 0.0

