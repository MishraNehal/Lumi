from fastapi import APIRouter, Depends
from backend.database.vectorstore import get_vector_store
from backend.auth.dependencies import get_current_user
from backend.database.models import User

router = APIRouter(prefix="/sources")


@router.get("")
def list_sources(current_user: User = Depends(get_current_user)):
    """Distinct sources ingested by this user — used for the source-filter dropdown."""
    return get_vector_store(current_user.id).list_sources()
