from fastapi import APIRouter, UploadFile, File
import shutil
import os
import uuid

from app.ingestion.service import ingest_document

router = APIRouter()

UPLOAD_DIR = "uploads"

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    tenant_id = "11111111-1111-1111-1111-111111111111"
    document_id = str(uuid.uuid4())

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 🔥 Trigger ingestion
    ingest_document(file_path, tenant_id, document_id)

    return {"message": "File uploaded and processing started"}