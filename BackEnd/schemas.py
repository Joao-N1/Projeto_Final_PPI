from pydantic import BaseModel, Field
from typing import Optional

# --- ESQUEMAS PARA FILMES ---
class FilmeBase(BaseModel):
    nome: str
    realizador: str

    imagem: str

class FilmeCreate(FilmeBase):
    pass

class FilmeResponse(FilmeBase):
    id: int
    nome: str

    imagem: str
    class Config:
        from_attributes = True 


# --- ESQUEMAS PARA ATORES ---
class AtorBase(BaseModel):
    nome: str
    filme_participante: str

    imagem: str
    #categoria: str

class AtorCreate(AtorBase):
    pass

class AtorResponse(AtorBase):
    id: int

    imagem: str
    class Config:
        from_attributes = True


# --- ESQUEMAS PARA VOTOS ---
class VotoBase(BaseModel):
    """Antigo
    eleitor_id: int
    # O Optional significa que este ID pode ser nulo (None)
    filme_id: Optional[int] = None
    ator_id: Optional[int] = None
    """

    user_nome: str
    categoria_id: int

    voto: int = Field(..., ge=1, le=4) #garante que o voto seja apenas entre 1 e 4

class VotoCreate(VotoBase):
    pass

class VotoResponse(VotoBase):
    id: int
    class Config:
        from_attributes = True


# --- esquemas para users ---
class UserCreate(BaseModel):
    nome: str
    senha: str

class UserResponse(BaseModel):
    nome: str
    senha: str

    class Config:
        from_attributes = True # Permite ler objetos do SQLAlchemy direto


# --- esquemas para categorias ---
# Categorias
class CategoriaCreate(BaseModel):
    id: int
    nome: str

    tipo: str

    candidato1_id: int
    candidato2_id: int
    candidato3_id: int
    candidato4_id: int

class CategoriaResponse(BaseModel):
    id: int
    nome: str

    tipo: str

    candidato1_id: int
    candidato2_id: int
    candidato3_id: int
    candidato4_id: int

    
    cand1_nome: str
    cand2_nome: str
    cand3_nome: str
    cand4_nome: str

    cand1_img: str
    cand2_img: str
    cand3_img: str
    cand4_img: str
    

    class Config:
        from_attributes = True # Permite ler objetos do SQLAlchemy direto

