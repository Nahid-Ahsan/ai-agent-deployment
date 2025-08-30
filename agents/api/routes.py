from fastapi import APIRouter, Depends, HTTPException
from schema.schemas import ChatRequest, ChatResponse, ConfirmationRequest, UserLogin, Token
from utils.auth import get_current_user
from service.agent_service import process_chat, confirm_booking
from service.user_service import authenticate_user, create_access_token
from typing import Dict

router = APIRouter(prefix="/api", tags=["Travel Agent"])

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: UserLogin):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = await create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/chat/", response_model=ChatResponse)
async def chat(request: ChatRequest, user_id: str = Depends(get_current_user)):
    """
    Chat endpoint to interact with flight or hotel booking agents.
    Requires Bearer token in Authorization header: `Bearer <token>`.
    """
    try:
        return await process_chat(request, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/confirm/", response_model=ChatResponse)
async def confirm(request: ConfirmationRequest, user_id: str = Depends(get_current_user)):
    """
    Confirm booking endpoint for flight or hotel bookings.
    Requires Bearer token in Authorization header: `Bearer <token>`.
    """
    try:
        return await confirm_booking(request, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))