"""
Enhanced LangGraph workflow for contract analysis with proper message handling.
"""

import os
from typing import Dict, Any, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
import operator

from data_storage.pinecone_store import get_pinecone_store
from agents.state import ContractAnalysisState
from agents.query_processor import QueryProcessorAgent
from agents.retrieval_agent import RetrievalAgent
from agents.enhanced_document_analysis import EnhancedDocumentAnalysisAgent
from agents.validation_agent import ValidationAgent
from agents.synthesis_agent import SynthesisAgent

load_dotenv()

class LangGraphContractAnalysisState(ContractAnalysisState):
    """Extended state that includes messages for LangGraph"""
    messages: Annotated[Sequence[BaseMessage], operator.add]

class LangGraphMultiAgentContractAnalysis:
    """
    Enhanced contract analysis using LangGraph with proper message handling.
    """

    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.1
        )
        self.pinecone_store = get_pinecone_store()

        # Initialize agents
        self.query_processor_agent = QueryProcessorAgent()
        self.retrieval_agent = RetrievalAgent()
        self.document_analysis_agent = EnhancedDocumentAnalysisAgent()
        self.validation_agent = ValidationAgent()
        self.synthesis_agent = SynthesisAgent()

        self.graph = self._build_langgraph_workflow()

    def _query_processor_node(self, state: LangGraphContractAnalysisState) -> LangGraphContractAnalysisState:
        """Query processor node that handles messages properly"""
        try:
            print("🔍 LangGraph: Query Processing...")

            # Process the query using our existing agent
            result = self.query_processor_agent.process_query(state)

            # Add message for LangGraph
            message = AIMessage(content=f"Query processed: {result['query_intent']}")

            return {
                **result,
                "messages": [message]
            }
        except Exception as e:
            error_message = f"Query processing failed: {str(e)}"
            return {
                **state,
                "error_message": error_message,
                "messages": [AIMessage(content=error_message)]
            }

    def _retrieval_node(self, state: LangGraphContractAnalysisState) -> LangGraphContractAnalysisState:
        """Retrieval node with message handling"""
        try:
            print("🔎 LangGraph: Enhanced Retrieval...")

            # Perform retrieval using our existing agent
            result = self.retrieval_agent.intelligent_retrieval(state)

            # Add message for LangGraph
            hybrid_results = result.get("hybrid_results", [])
            confidence = result.get("retrieval_confidence", 0.0)
            message = AIMessage(content=f"Retrieved {len(hybrid_results)} chunks with {confidence:.2f} confidence")

            return {
                **result,
                "messages": [message]
            }
        except Exception as e:
            error_message = f"Retrieval failed: {str(e)}"
            return {
                **state,
                "error_message": error_message,
                "messages": [AIMessage(content=error_message)]
            }

    def _document_analysis_node(self, state: LangGraphContractAnalysisState) -> LangGraphContractAnalysisState:
        """Document analysis node with message handling"""
        try:
            print("📊 LangGraph: Document Analysis...")

            # Perform analysis using our enhanced agent
            result = self.document_analysis_agent.analyze_documents_for_matrix(state)

            # Add message for LangGraph
            matrix_data = result.get("matrix_data", {})
            columns = result.get("generated_columns", [])
            success_rate = result.get("success_rate", 0)

            message = AIMessage(
                content=f"Analyzed {len(matrix_data)} documents with {len(columns)} columns. Success rate: {success_rate:.1f}%"
            )

            return {
                **result,
                "messages": [message]
            }
        except Exception as e:
            error_message = f"Document analysis failed: {str(e)}"
            return {
                **state,
                "error_message": error_message,
                "messages": [AIMessage(content=error_message)]
            }

    async def _validation_node(self, state: LangGraphContractAnalysisState) -> LangGraphContractAnalysisState:
        """Validation node with message handling"""
        try:
            print("✅ LangGraph: Validation...")

            # Validate using our existing agent
            result = await self.validation_agent.validate_findings(state)

            # Add message for LangGraph
            needs_retry = result.get("needs_retry", False)
            retry_count = result.get("retry_count", 0)
            confidence_scores = result.get("confidence_scores", {})

            if confidence_scores:
                avg_confidence = sum(confidence_scores.values()) / len(confidence_scores)
                message = AIMessage(
                    content=f"Validation complete. Avg confidence: {avg_confidence:.2f}. Retry needed: {needs_retry} (attempt {retry_count})"
                )
            else:
                message = AIMessage(content="Validation complete with no confidence data")

            return {
                **result,
                "messages": [message]
            }
        except Exception as e:
            error_message = f"Validation failed: {str(e)}"
            return {
                **state,
                "error_message": error_message,
                "messages": [AIMessage(content=error_message)]
            }

    async def _synthesis_node(self, state: LangGraphContractAnalysisState) -> LangGraphContractAnalysisState:
        """Synthesis node with message handling"""
        try:
            print("🔧 LangGraph: Synthesis...")

            # Synthesize results using our existing agent
            result = await self.synthesis_agent.synthesize_results(state)

            # Add message for LangGraph
            final_analysis = result.get("final_analysis", {})
            columns = final_analysis.get("columns", [])
            data = final_analysis.get("data", {})

            message = AIMessage(
                content=f"Synthesis complete. Final result: {len(columns)} columns, {len(data)} documents"
            )

            return {
                **result,
                "messages": [message]
            }
        except Exception as e:
            error_message = f"Synthesis failed: {str(e)}"
            return {
                **state,
                "error_message": error_message,
                "messages": [AIMessage(content=error_message)]
            }

    def _should_retry(self, state: LangGraphContractAnalysisState) -> str:
        """Determine retry strategy based on validation results"""
        return self.validation_agent.should_retry_analysis(state)

    def _build_langgraph_workflow(self) -> StateGraph:
        """Build the LangGraph workflow with proper message handling"""
        workflow = StateGraph(LangGraphContractAnalysisState)

        # Add nodes with proper message handling
        workflow.add_node("query_processor", self._query_processor_node)
        workflow.add_node("retrieval", self._retrieval_node)
        workflow.add_node("document_analysis", self._document_analysis_node)
        workflow.add_node("validation", self._validation_node)
        workflow.add_node("synthesis", self._synthesis_node)

        # Define the workflow
        workflow.set_entry_point("query_processor")
        workflow.add_edge("query_processor", "retrieval")
        workflow.add_edge("retrieval", "document_analysis")
        workflow.add_edge("document_analysis", "validation")

        # Enhanced conditional logic with retry mechanism
        workflow.add_conditional_edges(
            "validation",
            self._should_retry,
            {
                "retry": "retrieval",  # Get more context if confidence low
                "retry_analysis": "document_analysis",  # Retry with same data but different approach
                "continue": "synthesis"
            }
        )
        workflow.add_edge("synthesis", END)

        return workflow.compile()

    async def analyze_documents(self, user_query: str, matrix_id: str) -> Dict[str, Any]:
        """
        Main entry point for LangGraph multi-agent document analysis
        """
        try:
            print(f"\n🚀 LANGGRAPH MULTI-AGENT ANALYSIS STARTING")
            print(f"Query: {user_query}")
            print(f"Matrix ID: {matrix_id}")
            print("-" * 60)

            # Initialize state with messages
            initial_state = {
                "messages": [HumanMessage(content=user_query)],
                "original_query": user_query,
                "query_intent": "",
                "expanded_queries": [],
                "legal_terms": [],
                "semantic_results": [],
                "keyword_results": [],
                "hybrid_results": [],
                "retrieved_chunk_ids": [],
                "retrieval_confidence": 0.0,
                "generated_columns": [],
                "preliminary_findings": {},
                "chunk_analysis_results": {},
                "matrix_data": {},
                "evidence_chains": [],
                "cross_references": [],
                "page_locations": {},
                "exact_citations": {},
                "confidence_scores": {},
                "validated_results": {},
                "final_analysis": {},
                "needs_retry": False,
                "retry_count": 0,
                "error_message": "",
                "matrix_id": matrix_id,
                "processing_step": "initialized",
                "doc_name_to_chunk_id": {},
                "tool_results": {},
                "current_tool": None,
                "success_rate": 0.0
            }

            # Run the LangGraph workflow
            result = await self.graph.ainvoke(initial_state)

            # Extract final results
            final_analysis = result.get("final_analysis", {})
            if final_analysis and not result.get("error_message"):
                print(f"🎉 LangGraph analysis completed successfully!")
                return {
                    "columns": final_analysis.get("columns", []),
                    "data": final_analysis.get("data", {}),
                    "error": ""
                }
            else:
                error_msg = result.get("error_message", "Analysis completed but no results found")
                print(f"⚠️ LangGraph analysis completed with issues: {error_msg}")

                # Return whatever data we have
                matrix_data = result.get("matrix_data", {})
                columns = result.get("generated_columns", ["Result"])

                if matrix_data:
                    return {
                        "columns": columns,
                        "data": matrix_data,
                        "error": f"Partial results: {error_msg}"
                    }
                else:
                    return {
                        "columns": ["Error"],
                        "data": {"No Results": {"Error": {
                            "value": error_msg,
                            "source": "System error",
                            "confidence": 0.0,
                            "document_url": "",
                            "page_numbers": []
                        }}},
                        "error": error_msg
                    }

        except Exception as e:
            error_msg = str(e)
            print(f"❌ LANGGRAPH MULTI-AGENT ANALYSIS FAILED: {error_msg}")
            return {
                "columns": ["Error"],
                "data": {"Error": {"Error": {
                    "value": error_msg,
                    "source": "System error",
                    "confidence": 0.0,
                    "document_url": "",
                    "page_numbers": []
                }}},
                "error": error_msg
            }

# Factory function for backward compatibility
def get_agent(agent_type: str = "general"):
    """Get the LangGraph multi-agent system."""
    return LangGraphMultiAgentContractAnalysis()

# Main export
MultiAgentContractAnalysis = LangGraphMultiAgentContractAnalysis