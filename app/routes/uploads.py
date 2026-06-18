from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from app.database import db
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from bson import ObjectId
import io

router = APIRouter()


def get_bucket():
    return AsyncIOMotorGridFSBucket(db._db, bucket_name="uploads")


@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Solo immagini sono accettate")

    bucket = get_bucket()
    contents = await file.read()

    if len(contents) > 10 * 1024 * 1024:  # max 10MB
        raise HTTPException(status_code=400, detail="Immagine troppo grande (max 10MB)")

    file_id = await bucket.upload_from_stream(
        file.filename,
        contents,
        metadata={"content_type": file.content_type},
    )

    return {
        "id": str(file_id),
        "filename": file.filename,
        "url": f"/api/uploads/image/{file_id}",
    }


@router.get("/image/{file_id}")
async def get_image(file_id: str):
    bucket = get_bucket()
    try:
        stream = await bucket.open_download_stream(ObjectId(file_id))
        content_type = stream.metadata.get("content_type", "image/jpeg") if stream.metadata else "image/jpeg"
        data = await stream.read()
        return StreamingResponse(io.BytesIO(data), media_type=content_type)
    except Exception:
        raise HTTPException(status_code=404, detail="Immagine non trovata")


@router.delete("/image/{file_id}")
async def delete_image(file_id: str):
    bucket = get_bucket()
    try:
        await bucket.delete(ObjectId(file_id))
        return {"message": "Immagine eliminata"}
    except Exception:
        raise HTTPException(status_code=404, detail="Immagine non trovata")
