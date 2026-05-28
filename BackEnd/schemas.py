from pydantic import BaseModel
from typing import Optional

# --- ESQUEMAS PARA FILMES ---
class FilmeBase(BaseModel):
    titulo: str
    realizador: str
    categoria: str

class FilmeCreate(FilmeBase):
    pass

class FilmeResponse(FilmeBase):
    id: int
    class Config:
        from_attributes = True 


# --- ESQUEMAS PARA ATORES ---
class AtorBase(BaseModel):
    nome: str
    filme_participante: str
    categoria: str

class AtorCreate(AtorBase):
    pass

class AtorResponse(AtorBase):
    id: int
    class Config:
        from_attributes = True


# --- ESQUEMAS PARA ELEITORES ---
class EleitorBase(BaseModel):
    nome: str
    numero_estudante: str

class EleitorCreate(EleitorBase):
    pass

class EleitorResponse(EleitorBase):
    id: int
    class Config:
        from_attributes = True

# --- ESQUEMAS PARA VOTOS ---
class VotoBase(BaseModel):
    eleitor_id: int
    # O Optional significa que este ID pode ser nulo (None)
    filme_id: Optional[int] = None
    ator_id: Optional[int] = None

class VotoCreate(VotoBase):
    pass

class VotoResponse(VotoBase):
    id: int
    class Config:
        from_attributes = True