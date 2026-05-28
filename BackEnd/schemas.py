from pydantic import BaseModel

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