import os
import json
from typing import List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

from ..data_storage.database import supabase
from ..data_storage.pinecone_store import get_pinecone_store
from .state import ContractAnalysisState
from .query_processor import QueryProcessorAgent
from .retrieval_agent import RetrievalAgent
from .analysis_agent import AnalysisAgent
from .validation_agent import ValidationAgent
from .synthesis_agent import SynthesisAgent

load_dotenv()

class MultiAgentContractAnalysis:
    """
    Enhanced contract analysis using multiple specialized agents in a LangGraph workflow.
    """

    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.1
        )
        self.pinecone_store = get_pinecone_store()
        self.query_processor_agent = QueryProcessorAgent()
        self.retrieval_agent = RetrievalAgent()
        self.analysis_agent = AnalysisAgent()
        self.validation_agent = ValidationAgent()
        self.synthesis_agent = SynthesisAgent()
        self.graph = self._build_multi_agent_graph()

    def _build_multi_agent_graph(self) -> StateGraph:
        """Build the multi-agent workflow graph"""
        workflow = StateGraph(ContractAnalysisState)

        # Add specialized agent nodes
        workflow.add_node("query_processor", self.query_processor_agent.process_query)
        workflow.add_node("retrieval_agent", self.retrieval_agent.intelligent_retrieval)
        workflow.add_node("analysis_agent", self.analysis_agent.multi_turn_analysis)
        workflow.add_node("validation_agent", self.validation_agent._validate_findings)
        workflow.add_node("synthesis_agent", self.synthesis_agent._synthesize_results)

        # Define the workflow
        workflow.set_entry_point("query_processor")
        workflow.add_edge("query_processor", "retrieval_agent")
        workflow.add_edge("retrieval_agent", "analysis_agent")
        workflow.add_edge("analysis_agent", "validation_agent")

        # Conditional logic - retry if confidence is low
        workflow.add_conditional_edges(
            "validation_agent",
            self.validation_agent.should_retry_analysis,
            {
                "retry": "retrieval_agent",  # Get more context if confidence low
                "continue": "synthesis_agent"
            }
        )
        workflow.add_edge("synthesis_agent", END)

        return workflow.compile()

    def analyze_documents(self, user_query: str, matrix_id: str) -> Dict[str, Any]:
        """
        Main entry point for multi-agent document analysis
        """
        try:
            print(f"\n🚀 MULTI-AGENT ANALYSIS STARTING")
            print(f"Query: {user_query}")
            print(f"Matrix ID: {matrix_id}")
            print("-" * 60)

            # Initialize state
            initial_state = ContractAnalysisState(
                original_query=user_query,
                query_intent="",
                expanded_queries=[],
                legal_terms=[],
                semantic_results=[],
                keyword_results=[],
                hybrid_results=[],
                retrieval_confidence=0.0,
                generated_columns=[],
                preliminary_findings={},
                evidence_chains=[],
                cross_references=[],
                confidence_scores={},
                validated_results={},
                final_analysis={},
                needs_retry=False,
                error_message="",
                matrix_id=matrix_id,
                processing_step="initialized",
                doc_name_to_chunk_id={}
            )

            # Run the multi-agent workflow
            result = self.graph.invoke(initial_state)

            # Extract final results
            if result.get("final_analysis") and not result.get("error_message"):
                return {
                    "columns": result["final_analysis"]["columns"],
                    "data": result["final_analysis"]["data"],
                    "error": ""
                }
            else:
                return {
                    "columns": ["Error"],
                    "data": {"Error": {"Error": result.get("error_message", "Unknown error")}},
                    "error": result.get("error_message", "Analysis failed")
                }

        except Exception as e:
            print(f"❌ MULTI-AGENT ANALYSIS FAILED: {e}")
            return {
                "columns": ["Error"],
                "data": {"Error": {"Error": str(e)}},
                "error": str(e)
            }

# Factory function for backward compatibility
def get_agent(agent_type: str = "general"):
    """
    Get the appropriate agent based on the type of analysis needed.

    Note: All analysis types now use the multi-agent system with
    specialized prompting based on the analysis type.

    Args:
        agent_type: Legacy parameter for compatibility (risk, compliance, general)
    """
    # All analysis types now use the same multi-agent system
    # The analysis type is handled via enhanced prompting in main.py
    return MultiAgentContractAnalysis()

# Backward compatibility alias
ContractAnalysisAgent = MultiAgentContractAnalysis
