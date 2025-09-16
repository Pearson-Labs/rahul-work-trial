import os
import io
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import docx
import datetime
from .database import supabase
from .pinecone_store import get_pinecone_store

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    """Authenticates and returns a Google Drive service object."""
    # Try to get credentials from environment variable first
    google_creds_json = os.getenv("GOOGLE_CREDENTIALS")

    if google_creds_json:
        # Parse JSON credentials from environment variable
        try:
            creds_info = json.loads(google_creds_json) if isinstance(google_creds_json, str) else google_creds_json
            creds = service_account.Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Invalid GOOGLE_CREDENTIALS JSON format: {e}")
    else:
        # Fallback to local file for development
        SERVICE_ACCOUNT_FILE = "google_credentials.json"
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            raise FileNotFoundError(f"Neither GOOGLE_CREDENTIALS environment variable nor {SERVICE_ACCOUNT_FILE} file found.")
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)
    return service

def download_file(service, file_id):
    """Downloads a file from Google Drive and returns its content as bytes."""
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f"Download {int(status.progress() * 100)}%.")
    return fh.getvalue()

def read_docx_content(content_bytes):
    """Reads the text content from a .docx file given as bytes."""
    try:
        doc = docx.Document(io.BytesIO(content_bytes))
        text_content = '\n'.join([para.text for para in doc.paragraphs if para.text.strip()])
        return text_content
    except Exception as e:
        print(f"Error reading docx content: {e}")
        raise ValueError(f"Failed to parse document: {str(e)}")

def list_files_in_folder(service, folder_id):
    """Lists .docx files in a specific Google Drive folder."""
    query = f"'{folder_id}' in parents and mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    return results.get('files', [])

CHUNK_SIZE = 1500  # characters
CHUNK_OVERLAP = 200 # characters

def chunk_text(text: str) -> list[str]:
    """Splits text into overlapping chunks."""
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks

def ingest_documents_from_drive(folder_id: str, user_id: str):
    """
    Ingests all Word documents from a Google Drive folder into Pinecone and Supabase.
    Uses Pinecone for vector storage and search, Supabase for metadata and full text.
    """
    print(f"\n--- Starting Pinecone ingestion for user {user_id} from folder: {folder_id} ---")
    service = get_drive_service()
    files = list_files_in_folder(service, folder_id)
    
    if not files:
        return {"message": "No new Word documents found to ingest."}

    # Get Pinecone store instance
    pinecone_store = get_pinecone_store()
    
    ingested_chunk_count = 0
    total_files_processed = 0
    
    for file_item in files:
        file_id = file_item['id']
        file_name = file_item['name']
        
        print(f"\n--- Processing document: {file_name} ---")
        try:
            # 1. Insert parent document record in Supabase
            doc_res = supabase.table("documents").insert({
                "user_id": user_id,
                "file_name": file_name,
                "storage_path": f"google-drive/{file_id}"
            }).execute()
            document_id = doc_res.data[0]['id']

            # 2. Download and extract text content
            file_content_bytes = download_file(service, file_id)
            try:
                text_content = read_docx_content(file_content_bytes)
            except ValueError as doc_error:
                print(f"Failed to parse document {file_name}: {doc_error}")
                supabase.table("documents").update({
                    "status": "failed",
                    "error_message": f"Document parsing failed: {str(doc_error)}"
                }).eq("id", document_id).execute()
                continue
            
            if not text_content or not text_content.strip():
                print(f"Skipping empty document: {file_name}")
                # Update document status
                supabase.table("documents").update({
                    "status": "skipped",
                    "error_message": "Empty document content"
                }).eq("id", document_id).execute()
                continue

            # 3. Split into chunks
            chunks = chunk_text(text_content)
            print(f"Document split into {len(chunks)} chunks.")
            
            if not chunks:
                print(f"No chunks generated for document: {file_name}")
                # Update document status  
                supabase.table("documents").update({
                    "status": "skipped",
                    "error_message": "No chunks generated from document"
                }).eq("id", document_id).execute()
                continue

            # 4. Prepare chunks for Pinecone bulk upsert
            chunks_for_pinecone = []
            for i, current_chunk_text in enumerate(chunks):
                chunk_metadata = {
                    "original_file_name": file_name,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "document_id": document_id,
                    "user_id": user_id,
                    "file_type": "docx",
                    "created_at": datetime.datetime.now().isoformat(),
                    "google_drive_file_id": file_id
                }
                
                chunks_for_pinecone.append({
                    "chunk_text": current_chunk_text,
                    "metadata": chunk_metadata
                })

            # 5. Bulk upsert to Pinecone (also stores in Supabase)
            if chunks_for_pinecone:
                print(f"  - Bulk upserting {len(chunks_for_pinecone)} chunks to Pinecone...")
                chunk_ids = pinecone_store.bulk_upsert_chunks(chunks_for_pinecone)
                ingested_chunk_count += len(chunk_ids)
                print(f"Successfully upserted {len(chunk_ids)} chunks for {file_name}.")
                
                # 6. Update document record with chunk count
                supabase.table("documents").update({
                    "chunk_count": len(chunks),
                    "status": "processed"
                }).eq("id", document_id).execute()
            
            total_files_processed += 1

        except Exception as e:
            print(f"Error processing document {file_name}: {e}")
            # Update document status to failed (only if document was created)
            try:
                if 'document_id' in locals():
                    supabase.table("documents").update({
                        "status": "failed",
                        "error_message": str(e)
                    }).eq("id", document_id).execute()
            except Exception as update_error:
                print(f"Failed to update document status: {update_error}")
            continue
    
    # Get final Pinecone index stats
    try:
        index_stats = pinecone_store.get_index_stats()
        print(f"\n--- Pinecone Index Stats ---")
        print(f"Total vectors: {index_stats.get('total_vector_count', 'unknown')}")
        print(f"Index fullness: {index_stats.get('index_fullness', 'unknown')}")
    except Exception as e:
        print(f"Could not retrieve index stats: {e}")
            
    return {
        "message": f"Pinecone ingestion complete. {ingested_chunk_count} document chunks ingested from {total_files_processed} files.",
        "chunks_ingested": ingested_chunk_count,
        "files_processed": total_files_processed,
        "vector_store": "pinecone"
    }

