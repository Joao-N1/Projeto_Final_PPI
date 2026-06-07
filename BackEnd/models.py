from sqlalchemy import Column, Integer, String, ForeignKey
from database import Base


class Filme(Base):
    __tablename__ = "filmes"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), index=True)
    realizador = Column(String(100))

    imagem = Column(String(200))

class Ator(Base):
    __tablename__ = "atores"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), index=True)
    filme_participante = Column(String(100))

    imagem = Column(String(200))


class Voto(Base):
    __tablename__ = "votos"
    id = Column(Integer, primary_key=True, index=True)


    #novo
    user_nome = Column(String(100), ForeignKey("users.nome"))
    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    
    voto = Column(Integer) #deve ser um número entre 1 e 4



class User(Base):
    __tablename__ = "users"
    nome = Column(String(50), primary_key=True, index=True)
    senha = Column(String(300))


class Categoria(Base):
    __tablename__ = "categorias"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100))

    tipo = Column(String(10)) #deve ser "filmes" ou "atores"

    candidato1_id = Column(Integer)
    candidato2_id = Column(Integer)
    candidato3_id = Column(Integer)
    candidato4_id = Column(Integer)
