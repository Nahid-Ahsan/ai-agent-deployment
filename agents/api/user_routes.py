from fastapi import APIRouter, HTTPException
from schema.user_schemas import UserCreate, User
from service.user_service import create_user

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.post("/", response_model=User)
async def register_user(user: UserCreate):
    try:
        return await create_user(user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))