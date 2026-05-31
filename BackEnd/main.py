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
    novo_filme = models.Filme(nome=filme.nome, realizador=filme.realizador)
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
    novo_ator = models.Ator(nome=ator.nome, filme_participante=ator.filme_participante)
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
"""
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

"""

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


# --- log in e sign in ---
@app.post("/signin/", response_model=schemas.UserResponse)
def registrar_usuario(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Como 'nome' é a chave primária, verificamos se já existe no banco
    utilizador_existente = db.query(models.User).filter(models.User.nome == user.nome).first()
    if utilizador_existente:
        raise HTTPException(status_code=400, detail="Usuário já existente!")
        
    # Cria o novo utilizador utilizando o seu modelo SQLAlchemy
    novo_utilizador = models.User(nome=user.nome, senha=user.senha)
    db.add(novo_utilizador)
    db.commit()
    db.refresh(novo_utilizador)
    return novo_utilizador

@app.post("/login/")
def login_usuario(user_data: schemas.UserCreate, db: Session = Depends(get_db)):

    user = db.query(models.User).filter(models.User.nome == user_data.nome).first()
    
    if not user and user.senha != user_data.senha:
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos.")
        
    return {"message": "Login autorizado"}

@app.get("/users/", response_model=list[schemas.UserResponse])
def listar_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()
        


# --- sistema de votação ---  
# --- ROTA PARA CRIAR CATEGORIAS ---
@app.post("/categorias/", response_model=schemas.CategoriaResponse, dependencies=[Depends(verificar_chave)])
def criar_categoria(categoria: schemas.CategoriaCreate, db: Session = Depends(get_db)):

    if categoria.tipo not in ["filmes", "atores"]:
        raise HTTPException(
            status_code=400, 
            detail="O tipo da categoria deve ser 'filmes' ou 'atores'."
        )

    # Cria a instância do modelo SQLAlchemy
    nova_categoria = models.Categoria(
        nome=categoria.nome,
        tipo=categoria.tipo,
        candidato1_id=categoria.candidato1_id,
        candidato2_id=categoria.candidato2_id,
        candidato3_id=categoria.candidato3_id,
        candidato4_id=categoria.candidato4_id
    )
    
    db.add(nova_categoria)
    db.commit()
    db.refresh(nova_categoria)
    return nova_categoria

#list[schemas.CategoriaResponse]
@app.get("/categorias/", response_model=list[dict])
def listar_categorias(db: Session = Depends(get_db)):
    #return {"status": "O FastAPI está vivo, o problema é no banco ou dependência!"}
    try:
        categorias_do_banco = db.query(models.Categoria).all()
    except Exception as e:
        return {"ERRO CRÍTICO": f"Falha ao ler a tabela Categoria do banco de dados. Erro: {str(e)}"}

    categorias_do_banco = db.query(models.Categoria).all()
    
    lista = []

    # 2. Para cada categoria, vamos "traduzir" os IDs em objetos reais
    for cat in categorias_do_banco:
        
        tabela_alvo = models.Filme if cat.tipo == "filmes" else models.Ator
        
        # Fazemos a busca dos 4 objetos correspondentes aos IDs salvos
        cand1_obj = db.query(tabela_alvo).filter(tabela_alvo.id == cat.candidato1_id).first()
        cand2_obj = db.query(tabela_alvo).filter(tabela_alvo.id == cat.candidato2_id).first()
        cand3_obj = db.query(tabela_alvo).filter(tabela_alvo.id == cat.candidato3_id).first()
        cand4_obj = db.query(tabela_alvo).filter(tabela_alvo.id == cat.candidato4_id).first()


        # Montamos um dicionário com a estrutura idêntica à que o CategoriaCompletaResponse espera
        categoria_mapeada = {
            "id": cat.id,
            "nome": cat.nome,
            "tipo": cat.tipo,
            "candidato1": cat.candidato1_id, # Aqui vai o objeto do filme inteiro!
            "candidato2": cat.candidato2_id,
            "candidato3": cat.candidato3_id,
            "candidato4": cat.candidato4_id,

            "cand1_nome": cand1_obj.nome,
            "cand2_nome": cand2_obj.nome,
            "cand3_nome": cand3_obj.nome,
            "cand4_nome": cand4_obj.nome
        }
        
        lista.append(categoria_mapeada)

    # Retornamos a lista com os objetos totalmente montados
    return lista


@app.post("/votos/")
def registar_voto(voto_dados: schemas.VotoCreate, db: Session = Depends(get_db)):

    voto_duplicado = db.query(models.Voto).filter(
        models.Voto.user_nome == voto_dados.user_nome,
        models.Voto.categoria_id == voto_dados.categoria_id
    ).first()
    
    if voto_duplicado:
        raise HTTPException(status_code=400, detail="Você só pode votar uma vez por categoria!")

    # Cria o registo do voto
    novo_voto = models.Voto(
        user_nome=voto_dados.user_nome,
        categoria_id=voto_dados.categoria_id,
        voto=voto_dados.voto
    )
    
    db.add(novo_voto)
    db.commit()
    return {"message": "Voto registado com sucesso!"}


@app.get("/votos/", response_model=list[schemas.VotoResponse])
def listar_votos(db: Session = Depends(get_db)):
    return db.query(models.Voto).all()