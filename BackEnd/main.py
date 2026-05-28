from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

# Importamos os nossos ficheiros
from database import motor, SessaoLocal
import models
import schemas

# Cria as tabelas na base de dados
models.Base.metadata.create_all(bind=motor)

app = FastAPI()

# --- FUNÇÃO AUXILIAR ---
# Esta função abre a ligação à base de dados quando um pedido chega
# e fecha-a assim que o pedido for concluído, para não sobrecarregar o sistema.
def get_db():
    db = SessaoLocal()
    try:
        yield db
    finally:
        db.close()

# --- AS NOSSAS ROTAS (ENDPOINTS) ---

@app.get("/")
def ler_raiz():
    return {"mensagem": "Bem-vindo aos Óscares! O Backend está a correr e as tabelas estão prontas!"}

# 1. Rota para CRIAR um novo filme
# Usamos @app.post porque estamos a enviar/gravar dados novos
@app.post("/filmes/", response_model=schemas.FilmeResponse)
def criar_filme(filme: schemas.FilmeCreate, db: Session = Depends(get_db)):
    # Passo A: Transformamos os dados recebidos no formato do nosso modelo SQLAlchemy
    novo_filme = models.Filme(titulo=filme.titulo, realizador=filme.realizador, categoria=filme.categoria)
    
    # Passo B: Adicionamos à sessão e guardamos (commit) na base de dados
    db.add(novo_filme)
    db.commit()
    
    # Passo C: Atualizamos a variável para obter o ID que a base de dados acabou de lhe dar
    db.refresh(novo_filme)
    
    # Passo D: Devolvemos o filme acabado de criar como confirmação
    return novo_filme

# 2. Rota para LER todos os filmes
# Usamos @app.get porque estamos apenas a pedir informação
@app.get("/filmes/", response_model=list[schemas.FilmeResponse])
def listar_filmes(db: Session = Depends(get_db)):
    # Vamos à base de dados e pedimos todos os registos da tabela Filme
    filmes = db.query(models.Filme).all()
    return filmes