from sqlalchemy import Column, Integer, String, ForeignKey
from database import Base

# 1. Tabela dos Eleitores
class Eleitor(Base):
    __tablename__ = "eleitores" # Nome da tabela na base de dados

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100))
    numero_estudante = Column(String(20), unique=True, index=True) # unique=True impede que o mesmo aluno se registe duas vezes

# 2. Tabela dos Filmes (Nomeados)
class Filme(Base):
    __tablename__ = "filmes"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(100), index=True)
    realizador = Column(String(100))
    categoria = Column(String(50)) # Ex: "Melhor Filme", "Melhor Animação"

# 3. NOVA: Tabela dos Atores
class Ator(Base):
    __tablename__ = "atores"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), index=True)
    filme_participante = Column(String(100)) 
    categoria = Column(String(50)) 

# 4. Tabela dos Votos 
class Voto(Base):
    __tablename__ = "votos"

    id = Column(Integer, primary_key=True, index=True)
    
    # As ForeignKeys (Chaves Estrangeiras) ligam o voto ao eleitor e ao filme específicos
    eleitor_id = Column(Integer, ForeignKey("eleitores.id"))
    filme_id = Column(Integer, ForeignKey("filmes.id"))