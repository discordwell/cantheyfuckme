from pydantic import BaseModel
from typing import Optional


class SignupInput(BaseModel):
    email: str
    password: str


class LoginInput(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    success: bool
    message: str
    user: Optional[dict] = None
    token: Optional[str] = None


class UserInfo(BaseModel):
    email: str
    credits: int
    created_at: str


class CheckoutInput(BaseModel):
    document_hash: str
    success_url: str
    cancel_url: str


class UnlockInput(BaseModel):
    # Optional so a missing hash stays the endpoint's historical 400 rather
    # than becoming a 422 from validation.
    document_hash: Optional[str] = None
