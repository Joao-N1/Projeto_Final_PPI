import os # NOVA IMPORTAÇÃO
from dotenv import load_dotenv # NOVA IMPORTAÇÃO

from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from sqlalchemy import func
import time

from database import motor, SessaoLocal
import models
import schemas

# Carrega os segredos do cofre
load_dotenv()

tentativas = 5
while tentativas > 0:
    try:
        models.Base.metadata.create_all(bind=motor)
        print("✅ Sucesso! Tabelas criadas e ligadas à Base de Dados.")
        break
    except OperationalError:
        print(f"⏳ Base de dados a acordar... Tentativas restantes: {tentativas - 1}")
        time.sleep(3)
        tentativas -= 1

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 🔒 SISTEMA DE SEGURANÇA (Agora a ler do .env) ---
# Vamos buscar a chave ao cofre. Se o cofre falhar, ele usa a segunda opção por segurança
CHAVE_MESTRA = os.getenv("API_KEY_MESTRA", "chave_de_emergencia") 
chave_header = APIKeyHeader(name="X-API-Key")

def verificar_chave(chave_recebida: str = Security(chave_header)):
    if chave_recebida != CHAVE_MESTRA:
        raise HTTPException(status_code=403, detail="Acesso Negado! Chave Mestra Incorreta.")
    return chave_recebida


def get_db():
    db = SessaoLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def ler_raiz():
    return {"mensagem": "Bem-vindo aos Óscares! O Backend está a correr e as tabelas estão prontas!"}


# --- ROTAS PARA FILMES ---
# Adicionámos a dependência 'verificar_chave' para proteger a criação de filmes
@app.post("/filmes/", response_model=schemas.FilmeResponse, dependencies=[Depends(verificar_chave)])
def criar_filme(filme: schemas.FilmeCreate, db: Session = Depends(get_db)):
    novo_filme = models.Filme(titulo=filme.titulo, realizador=filme.realizador, categoria=filme.categoria)
    db.add(novo_filme)
    db.commit()
    db.refresh(novo_filme)
    return novo_filme

@app.get("/filmes/", response_model=list[schemas.FilmeResponse])
def listar_filmes(db: Session = Depends(get_db)):
    return db.query(models.Filme).all()


# --- ROTAS PARA ATORES ---
# Protegemos também a criação de atores
@app.post("/atores/", response_model=schemas.AtorResponse, dependencies=[Depends(verificar_chave)])
def criar_ator(ator: schemas.AtorCreate, db: Session = Depends(get_db)):
    novo_ator = models.Ator(nome=ator.nome, filme_participante=ator.filme_participante, categoria=ator.categoria)
    db.add(novo_ator)
    db.commit()
    db.refresh(novo_ator)
    return novo_ator

@app.get("/atores/", response_model=list[schemas.AtorResponse])
def listar_atores(db: Session = Depends(get_db)):
    return db.query(models.Ator).all()


# --- ROTAS PARA ELEITORES ---
@app.post("/eleitores/", response_model=schemas.EleitorResponse)
def registar_eleitor(eleitor: schemas.EleitorCreate, db: Session = Depends(get_db)):
    eleitor_existente = db.query(models.Eleitor).filter(models.Eleitor.numero_estudante == eleitor.numero_estudante).first()
    if eleitor_existente:
        raise HTTPException(status_code=400, detail="Este número de estudante já está registado!")
        
    novo_eleitor = models.Eleitor(nome=eleitor.nome, numero_estudante=eleitor.numero_estudante)
    db.add(novo_eleitor)
    db.commit()
    db.refresh(novo_eleitor)
    return novo_eleitor

@app.get("/eleitores/", response_model=list[schemas.EleitorResponse])
def listar_eleitores(db: Session = Depends(get_db)):
    return db.query(models.Eleitor).all()


# --- ROTAS PARA VOTOS ---
@app.post("/votos/", response_model=schemas.VotoResponse)
def registar_voto(voto: schemas.VotoCreate, db: Session = Depends(get_db)):
    eleitor = db.query(models.Eleitor).filter(models.Eleitor.id == voto.eleitor_id).first()
    if not eleitor:
        raise HTTPException(status_code=404, detail="Eleitor não encontrado! Regista-te primeiro.")

    if voto.filme_id and voto.ator_id:
        raise HTTPException(status_code=400, detail="Só podes votar num filme OU num ator de cada vez!")
    if not voto.filme_id and not voto.ator_id:
        raise HTTPException(status_code=400, detail="Tens de escolher um filme ou um ator para o teu voto!")

    categoria_voto = ""
    if voto.filme_id:
        filme = db.query(models.Filme).filter(models.Filme.id == voto.filme_id).first()
        if not filme:
            raise HTTPException(status_code=404, detail="O filme que escolheste não existe!")
        categoria_voto = filme.categoria
    else:
        ator = db.query(models.Ator).filter(models.Ator.id == voto.ator_id).first()
        if not ator:
            raise HTTPException(status_code=404, detail="O ator que escolheste não existe!")
        categoria_voto = ator.categoria

    votos_anteriores = db.query(models.Voto).filter(models.Voto.eleitor_id == voto.eleitor_id).all()
    for v in votos_anteriores:
        if v.filme_id:
            filme_votado = db.query(models.Filme).filter(models.Filme.id == v.filme_id).first()
            if filme_votado and filme_votado.categoria == categoria_voto:
                raise HTTPException(status_code=400, detail=f"Já votaste na categoria: {categoria_voto}!")
        elif v.ator_id:
            ator_votado = db.query(models.Ator).filter(models.Ator.id == v.ator_id).first()
            if ator_votado and ator_votado.categoria == categoria_voto:
                raise HTTPException(status_code=400, detail=f"Já votaste na categoria: {categoria_voto}!")

    novo_voto = models.Voto(eleitor_id=voto.eleitor_id, filme_id=voto.filme_id, ator_id=voto.ator_id)
    db.add(novo_voto)
    db.commit()
    db.refresh(novo_voto)
    return novo_voto

@app.get("/votos/", response_model=list[schemas.VotoResponse])
def listar_votos(db: Session = Depends(get_db)):
    return db.query(models.Voto).all()


# --- ROTA DE RESULTADOS ---
@app.get("/resultados/")
def obter_resultados(db: Session = Depends(get_db)):
    votos_filmes = db.query(
        models.Filme.titulo,
        models.Filme.categoria,
        func.count(models.Voto.id).label("total_votos")
    ).outerjoin(models.Voto, models.Filme.id == models.Voto.filme_id).group_by(models.Filme.id).all()

    votos_atores = db.query(
        models.Ator.nome,
        models.Ator.categoria,
        func.count(models.Voto.id).label("total_votos")
    ).outerjoin(models.Voto, models.Ator.id == models.Voto.ator_id).group_by(models.Ator.id).all()

    lista_filmes = [{"titulo": f.titulo, "categoria": f.categoria, "votos": f.total_votos} for f in votos_filmes]
    lista_atores = [{"nome": a.nome, "categoria": a.categoria, "votos": a.total_votos} for a in votos_atores]

    return {
        "filmes": sorted(lista_filmes, key=lambda x: x["votos"], reverse=True),
        "atores": sorted(lista_atores, key=lambda x: x["votos"], reverse=True)
    }