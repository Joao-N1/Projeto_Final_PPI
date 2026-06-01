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

import criptografia

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
    novo_filme = models.Filme(nome=filme.nome, realizador=filme.realizador, imagem=filme.imagem)
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
    novo_ator = models.Ator(nome=ator.nome, filme_participante=ator.filme_participante, imagem=ator.imagem)
    db.add(novo_ator)
    db.commit()
    db.refresh(novo_ator)
    return novo_ator

@app.get("/atores/", response_model=list[schemas.AtorResponse])
def listar_atores(db: Session = Depends(get_db)):
    return db.query(models.Ator).all()


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
    # Como 'nome' é a chave primária, verificamos se já existe na base de dados
    utilizador_existente = db.query(models.User).filter(models.User.nome == user.nome).first()
    if utilizador_existente:
        raise HTTPException(status_code=400, detail="Usuário já existente!")
        

    senha_criptografada = criptografia.gerar_hash_senha(user.senha)

    # Cria o novo utilizador utilizando o seu modelo SQLAlchemy
    novo_utilizador = models.User(nome=user.nome, senha=senha_criptografada)

    db.add(novo_utilizador)
    db.commit()
    db.refresh(novo_utilizador)
    return novo_utilizador

@app.post("/login/")
def login_usuario(user_data: schemas.UserCreate, db: Session = Depends(get_db)):

    # 1. Busca o usuário pelo nome
    user = db.query(models.User).filter(models.User.nome == user_data.nome).first()
    
    # 2. Se o usuário não existir, barra aqui
    if not user:
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos.")
        
    # 3. Se existir, verifica se a senha bate com o hash do banco
    if not criptografia.verificar_senha(user_data.senha, user.senha):
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
    try:
        categorias_do_banco = db.query(models.Categoria).all()
    except Exception as e:
        return {"ERRO CRÍTICO": f"Falha ao ler a tabela Categoria do banco de dados. Erro: {str(e)}"}

    categorias_do_banco = db.query(models.Categoria).all()
    
    lista = []

    for cat in categorias_do_banco:
        
        tabela_alvo = models.Filme if cat.tipo == "filmes" else models.Ator
        
        # Fazemos a busca dos 4 objetos correspondentes aos IDs salvos
        cand1_obj = db.query(tabela_alvo).filter(tabela_alvo.id == cat.candidato1_id).first()
        cand2_obj = db.query(tabela_alvo).filter(tabela_alvo.id == cat.candidato2_id).first()
        cand3_obj = db.query(tabela_alvo).filter(tabela_alvo.id == cat.candidato3_id).first()
        cand4_obj = db.query(tabela_alvo).filter(tabela_alvo.id == cat.candidato4_id).first()

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
            "cand4_nome": cand4_obj.nome,

            "cand1_img": cand1_obj.imagem,
            "cand2_img": cand2_obj.imagem,
            "cand3_img": cand3_obj.imagem,
            "cand4_img": cand4_obj.imagem
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



@app.get("/votos/resultados/", response_model=list[dict])
def obter_resultados(db: Session = Depends(get_db)):
    try:
        # 1. Procuramos todas as categorias
        categorias = db.query(models.Categoria).all()
        resultados_finais = []

        for cat in categorias:
            # 2. Identifica se a categoria é de filmes ou atores para buscar os nomes corretos
            tabela_alvo = models.Filme if cat.tipo == "filmes" else models.Ator
            
            cand1_obj = db.query(tabela_alvo).filter(tabela_alvo.id == cat.candidato1_id).first()
            cand2_obj = db.query(tabela_alvo).filter(tabela_alvo.id == cat.candidato2_id).first()
            cand3_obj = db.query(tabela_alvo).filter(tabela_alvo.id == cat.candidato3_id).first()
            cand4_obj = db.query(tabela_alvo).filter(tabela_alvo.id == cat.candidato4_id).first()

            # Extrai os nomes/títulos de forma segura
            nome1 = (cand1_obj.nome) if cand1_obj else "Candidato 1"
            nome2 = (cand2_obj.nome) if cand2_obj else "Candidato 2"
            nome3 = (cand3_obj.nome) if cand3_obj else "Candidato 3"
            nome4 = (cand4_obj.nome) if cand4_obj else "Candidato 4"

            # 3. Conta os votos reais na base de dados para cada opção (1, 2, 3 ou 4) desta categoria
            # Filtramos onde categoria_id é igual a esta categoria e o voto corresponde à opção
            votos_cand1 = db.query(models.Voto).filter(models.Voto.categoria_id == cat.id, models.Voto.voto == 1).count()
            votos_cand2 = db.query(models.Voto).filter(models.Voto.categoria_id == cat.id, models.Voto.voto == 2).count()
            votos_cand3 = db.query(models.Voto).filter(models.Voto.categoria_id == cat.id, models.Voto.voto == 3).count()
            votos_cand4 = db.query(models.Voto).filter(models.Voto.categoria_id == cat.id, models.Voto.voto == 4).count()

            # 4. Monta a estrutura exata que o Chart.js (Frontend) está à espera de receber
            estrutura_categoria = {
                "categoria_nome": cat.nome,
                "candidatos": [nome1, nome2, nome3, nome4],
                "votos": [votos_cand1, votos_cand2, votos_cand3, votos_cand4]
            }
            
            resultados_finais.append(estrutura_categoria)

        return resultados_finais

    except Exception as e:
        return [{"ERRO_RESULTADOS": f"Falha ao calcular a votação: {str(e)}"}]