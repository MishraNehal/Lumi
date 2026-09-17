from fastapi import APIRouter, Depends, HTTPException
from backend.database.vectorstore import get_vector_store
from backend.auth.dependencies import get_current_user
from backend.database.models import User

router = APIRouter(prefix="/sources")


@router.get("")
def list_sources(current_user: User = Depends(get_current_user)):
    """Distinct sources ingested by this user — used for the source-filter dropdown."""
    return get_vector_store(current_user.id).list_sources()


@router.delete("/{filename}")
def delete_source(filename: str, current_user: User = Depends(get_current_user)):
    deleted = get_vector_store(current_user.id).delete_source(filename)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Source not found.")
    return {"deleted_chunks": deleted, "filename": filename}