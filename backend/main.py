"""
Enhanced AI Contract Analysis Platform - FastAPI Backend with LangGraph

Features:
- ✅ LangGraph multi-agent orchestration with proper message handling
- ✅ Clickable citations linking to exact Google Drive locations
- ✅ Confidence scoring and page number tracking
- ✅ Smart retry logic with conditional edges
- ✅ Tool-based document analysis for better precision
- ✅ Pinecone vector search with semantic + keyword hybrid retrieval
- ✅ Supabase integration for metadata and full-text storage
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import traceback
from typing import Optional
from enum import Enum
from data_storage.database import supabase
from data_storage.google_drive import ingest_documents_from_drive
from data_storage.pinecone_store import get_pinecone_store
from core.utils import handle_api_error, validate_required_env_vars, log_operation, create_success_response, APIError
from core.auth import verify_clerk_jwt
from agents.langgraph_workflow import LangGraphMultiAgentContractAnalysis as MultiAgentContractAnalysis

app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://*.ngrok-free.app",
    "https://*.ngrok.io",
    "https://*.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalysisType(str, Enum):
    GENERAL = "general"
    RISK = "risk"
    COMPLIANCE = "compliance"

class ProcessRequest(BaseModel):
    prompt: str
    analysis_type: Optional[AnalysisType] = AnalysisType.GENERAL

class IngestRequest(BaseModel):
    folder_id: str

@app.post("/api/process")
# CHANGE 1: The function must be defined with 'async def'
async def process_prompt(request: ProcessRequest, user_id: str = Depends(verify_clerk_jwt)):
    """
    Process a user prompt to extract structured information from documents.
    """
    try:
        log_operation("Document Analysis Request", {
            "user_id": user_id,
            "prompt_length": len(request.prompt),
            "analysis_type": request.analysis_type
        })
        validate_required_env_vars("PINECONE_API_KEY", "ANTHROPIC_API_KEY")

        # 1. Create matrix record
        try:
            matrix_response = supabase.table("matrices").insert({
                "user_id": user_id,
                "prompt": request.prompt,
                "columns": []
            }).execute()
            matrix_id = matrix_response.data[0]["id"]
            log_operation("Matrix Created", {"matrix_id": matrix_id})
        except Exception as e:
            raise APIError(f"Failed to create analysis matrix: {str(e)}", "MATRIX_CREATION_ERROR")

        # 2. Use Multi-Agent System for Analysis
        try:
            log_operation("Starting Multi-Agent Analysis", { "query": request.prompt, "matrix_id": matrix_id })
            multi_agent = MultiAgentContractAnalysis()

            # CHANGE 2: You must 'await' the result of an async function
            result = await multi_agent.analyze_documents(
                user_query=request.prompt,
                matrix_id=matrix_id
            )

            if result.get("error"):
                raise APIError(f"Multi-agent analysis failed: {result['error']}", "MULTI_AGENT_ERROR")

            generated_columns = result["columns"]
            extracted_data = result["data"]
            log_operation("Multi-Agent Analysis Complete", { "columns_generated": len(generated_columns), "documents_processed": len(extracted_data), "matrix_id": matrix_id })

        except APIError:
            raise
        except Exception as e:
            raise APIError(f"Multi-agent analysis failed: {str(e)}", "MULTI_AGENT_ERROR")

        return create_success_response(
            "Document analysis completed successfully",
            {
                "columns": generated_columns,
                "data": extracted_data,
                "matrix_id": matrix_id,
                "documents_analyzed": len(extracted_data)
            }
        )

    except APIError as e:
        raise handle_api_error(e, "process_prompt")
    except Exception as e:
        raise handle_api_error(e, "process_prompt")

@app.post("/api/analyze-specialized")
# CHANGE 3: This function must also be 'async def'
async def analyze_specialized(request: ProcessRequest, user_id: str = Depends(verify_clerk_jwt)):
    """
    This endpoint performs specialized analysis using different agent types.
    """
    try:
        validate_required_env_vars("PINECONE_API_KEY", "ANTHROPIC_API_KEY")

        try:
            matrix_response = supabase.table("matrices").insert({
                "user_id": user_id,
                "prompt": request.prompt,
                "columns": []
            }).execute()
            matrix_id = matrix_response.data[0]["id"]
        except Exception as e:
            raise APIError(f"Failed to create analysis matrix: {str(e)}", "MATRIX_CREATION_ERROR")

        multi_agent = MultiAgentContractAnalysis()
        enhanced_prompt = f"[{request.analysis_type.value.upper()} ANALYSIS] {request.prompt}"

        # CHANGE 4: And you must 'await' the result here as well
        result = await multi_agent.analyze_documents(
            user_query=enhanced_prompt,
            matrix_id=matrix_id
        )

        if result.get("error"):
            raise APIError(f"Specialized analysis failed: {result['error']}", "SPECIALIZED_ANALYSIS_ERROR")

        return create_success_response(
            f"{request.analysis_type.value.title()} analysis completed successfully",
            {
                "analysis_type": request.analysis_type.value,
                "columns": result["columns"],
                "data": result["data"],
                "matrix_id": matrix_id
            }
        )

    except APIError as e:
        raise handle_api_error(e, "analyze_specialized")
    except Exception as e:
        raise handle_api_error(e, "analyze_specialized")


# --- NO CHANGES NEEDED BELOW THIS LINE ---

@app.post("/api/ingest-documents")
def ingest_documents(request: IngestRequest, user_id: str = Depends(verify_clerk_jwt)):
    try:
        result = ingest_documents_from_drive(request.folder_id, user_id)
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error during document ingestion: {e}")

@app.get("/api/documents")
def get_documents():
    try:
        response = supabase.table("document_chunks").select("*").execute()
        return {"document_chunks": response.data}
    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}

@app.get("/api/pinecone-stats")
def get_pinecone_stats(user_id: str = Depends(verify_clerk_jwt)):
    try:
        pinecone_store = get_pinecone_store()
        stats = pinecone_store.get_index_stats()
        return {
            "vector_store": "pinecone",
            "index_name": os.getenv("PINECONE_INDEX_NAME", "contract-documents"),
            "stats": stats
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting Pinecone stats: {e}")

# Root endpoint for health check
@app.get("/")
def read_root():
    return {
        "message": "🚀 Enhanced AI Contract Analysis Platform - Backend API",
        "status": "operational",
        "version": "2.0.0",
        "features": [
            "LangGraph Multi-Agent Orchestration",
            "Clickable Citations with Google Drive Links",
            "Confidence Scoring and Page Number Tracking",
            "Smart Retry Logic with Conditional Edges",
            "Tool-Based Document Analysis"
        ],
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting Contract Analysis Backend...")
    print("📍 Backend URL: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print("🔧 Make sure your .env file is configured!")
    print("-" * 50)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

# Vercel handler for serverless deployment
try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except ImportError:
    # Mangum not available in local development
    pass