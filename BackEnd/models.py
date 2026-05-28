from sqlalchemy import Column, Integer, String, ForeignKey
from database import Base

class Eleitor(Base):
    __tablename__ = "eleitores"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100))
    numero_estudante = Column(String(20), unique=True, index=True)

class Filme(Base):
    __tablename__ = "filmes"
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(100), index=True)
    realizador = Column(String(100))
    categoria = Column(String(50))

class Ator(Base):
    __tablename__ = "atores"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), index=True)
    filme_participante = Column(String(100))
    categoria = Column(String(50))

class Voto(Base):
    __tablename__ = "votos"
    id = Column(Integer, primary_key=True, index=True)
    
    # As três ligações cruciais
    eleitor_id = Column(Integer, ForeignKey("eleitores.id"))
    filme_id = Column(Integer, ForeignKey("filmes.id"), nullable=True)
    ator_id = Column(Integer, ForeignKey("atores.id"), nullable=True) # <-- O Python estava a queixar-se que isto não existia!