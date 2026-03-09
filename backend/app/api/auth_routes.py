"""
ObraHunter - Rotas de Autenticação + Gestão de Usuários
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.models.models import Usuario, UserRole
from app.core.auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_admin, require_gerente,
)

router = APIRouter()


# Schemas
class LoginRequest(BaseModel):
    email: str
    senha: str

class RegisterRequest(BaseModel):
    nome: str
    email: str
    senha: str
    role: UserRole = UserRole.VENDEDOR

class UserResponse(BaseModel):
    id: int
    nome: str
    email: str
    role: UserRole
    ativo: bool
    avatar_url: Optional[str] = None
    estados_interesse: Optional[list] = None
    tipos_interesse: Optional[list] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    class Config:
        from_attributes = True

class UserUpdateRequest(BaseModel):
    nome: Optional[str] = None
    estados_interesse: Optional[list] = None
    tipos_interesse: Optional[list] = None
    score_minimo_notificacao: Optional[float] = None


# ==================== AUTH ====================

@router.post("/auth/login")
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Usuario).where(Usuario.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.senha, user.senha_hash):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    if not user.ativo:
        raise HTTPException(status_code=403, detail="Usuário desativado")
    user.last_login = datetime.utcnow()
    await db.flush()
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return {"token": token, "user": {"id": user.id, "nome": user.nome, "email": user.email, "role": user.role.value}}


@router.post("/auth/setup")
async def setup_admin(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Cria primeiro admin — só funciona se não existe nenhum usuário"""
    count = (await db.execute(select(func.count(Usuario.id)))).scalar()
    if count > 0:
        raise HTTPException(status_code=400, detail="Setup já realizado. Use /auth/register.")
    user = Usuario(nome=data.nome, email=data.email, senha_hash=hash_password(data.senha), role=UserRole.ADMIN)
    db.add(user)
    await db.flush()
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return {"message": "Admin criado", "token": token, "user_id": user.id}


@router.post("/auth/register", response_model=UserResponse)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db), admin=Depends(require_admin)):
    existing = await db.execute(select(Usuario).where(Usuario.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    user = Usuario(nome=data.nome, email=data.email, senha_hash=hash_password(data.senha), role=data.role)
    db.add(user)
    await db.flush()
    return user


# ==================== USERS ====================

@router.get("/users/me", response_model=UserResponse)
async def get_me(user: Usuario = Depends(get_current_user)):
    return user

@router.patch("/users/me", response_model=UserResponse)
async def update_me(data: UserUpdateRequest, user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.flush()
    return user

@router.get("/users", response_model=List[UserResponse])
async def list_users(db: AsyncSession = Depends(get_db), admin=Depends(require_gerente)):
    result = await db.execute(select(Usuario).order_by(Usuario.created_at.desc()))
    return result.scalars().all()

@router.patch("/users/{user_id}/toggle")
async def toggle_user(user_id: int, db: AsyncSession = Depends(get_db), admin=Depends(require_admin)):
    user = await db.get(Usuario, user_id)
    if not user:
        raise HTTPException(status_code=404)
    user.ativo = not user.ativo
    await db.flush()
    return {"ativo": user.ativo}
