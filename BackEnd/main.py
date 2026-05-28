# Adicionei o HTTPException aqui em cima para podermos enviar mensagens de erro
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from database import motor, SessaoLocal
import models
import schemas

models.Base.metadata.create_all(bind=motor)

app = FastAPI()

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
@app.post("/filmes/", response_model=schemas.FilmeResponse)
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
@app.post("/atores/", response_model=schemas.AtorResponse)
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
    # Validação: Verificar se o número de estudante já existe na base de dados
    eleitor_existente = db.query(models.Eleitor).filter(models.Eleitor.numero_estudante == eleitor.numero_estudante).first()
    
    if eleitor_existente:
        # Se já existir, bloqueia a criação e envia um erro 400
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
    # 1. Verificar se o eleitor existe na base de dados
    eleitor = db.query(models.Eleitor).filter(models.Eleitor.id == voto.eleitor_id).first()
    if not eleitor:
        raise HTTPException(status_code=404, detail="Eleitor não encontrado! Regista-te primeiro.")

    # 2. Verificar se o eleitor tentou votar num filme E num ator ao mesmo tempo, ou em nenhum
    if voto.filme_id and voto.ator_id:
        raise HTTPException(status_code=400, detail="Só podes votar num filme OU num ator de cada vez!")
    if not voto.filme_id and not voto.ator_id:
        raise HTTPException(status_code=400, detail="Tens de escolher um filme ou um ator para o teu voto!")

    # 3. Descobrir a categoria do voto e verificar se o candidato (filme ou ator) existe
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

    # 4. A Regra de Ouro: Impedir fraude eleitoral (votar 2x na mesma categoria)
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

    # 5. Se sobreviveu a todas as verificações, o voto é válido! Registamos na base de dados.
    novo_voto = models.Voto(eleitor_id=voto.eleitor_id, filme_id=voto.filme_id, ator_id=voto.ator_id)
    db.add(novo_voto)
    db.commit()
    db.refresh(novo_voto)
    
    return novo_voto

@app.get("/votos/", response_model=list[schemas.VotoResponse])
def listar_votos(db: Session = Depends(get_db)):
    return db.query(models.Voto).all()