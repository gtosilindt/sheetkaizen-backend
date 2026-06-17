from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: str = "user"
    reparto: str
    linee: List[str] = []
    team: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    reparto: Optional[str] = None
    linee: Optional[List[str]] = None
    team: Optional[str] = None
    is_active: Optional[bool] = None
