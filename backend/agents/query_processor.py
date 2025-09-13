import os
import json
from typing import List, Dict, Any
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

from ..data_storage.database import supabase
from ..data_storage.pinecone_store import get_pinecone_store
from .state import ContractAnalysisState

load_dotenv()

class QueryProcessorAgent:
    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.1
        )

    def process_query(self, state: ContractAnalysisState) -> ContractAnalysisState:
        """
        Processes the user query to understand intent and extract legal terms.
        """
        try:
            print(f"🔍 QUERY PROCESSOR: Analyzing query: {state['original_query'][:100]}...")

            # Intent classification and query enhancement
            system_prompt = """You are a legal query analysis AI. Your job is to:

1. Classify the query intent (risk_analysis, clause_extraction, compliance_check, general_analysis)
2. Extract key legal terms and concepts
3. Generate expanded queries to improve retrieval
4. Identify specific contract sections likely to contain relevant information

Respond with JSON in this format:
{
    "intent": "risk_analysis",
    "legal_terms": ["change of control", "termination", "non-solicitation"],
    "expanded_queries": [
        "change of control provisions acquisition merger",
        "termination for convenience clauses",
        "non-solicitation agreements employment"
    ],
    "target_sections": ["governance", "employment", "termination", "definitions"]
}"""

            user_prompt = f"""Analyze this contract analysis query:

Query: "{state['original_query']}"

Provide intent classification, legal terms, and expanded queries for better retrieval."""

            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            # Parse response
            response_text = response.content.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]

            analysis = json.loads(response_text)

            print(f"📊 Intent: {analysis.get('intent', 'unknown')}")
            print(f"🔑 Legal terms: {analysis.get('legal_terms', [])}")
            print(f"📝 Expanded queries: {len(analysis.get('expanded_queries', []))}")

            return {
                **state,
                "query_intent": analysis.get("intent", "general_analysis"),
                "legal_terms": analysis.get("legal_terms", []),
                "expanded_queries": analysis.get("expanded_queries", [state["original_query"]]),
                "processing_step": "query_processed"
            }

        except Exception as e:
            print(f"❌ Query processing error: {e}")
            return {
                **state,
                "query_intent": "general_analysis",
                "legal_terms": [],
                "expanded_queries": [state["original_query"]],
                "error_message": f"Query processing failed: {str(e)}",
                "processing_step": "query_error"
            }