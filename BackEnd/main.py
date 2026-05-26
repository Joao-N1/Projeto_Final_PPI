from fastapi import FastAPI

# Inicializa a aplicação
app = FastAPI()

# Cria uma rota simples para testarmos se funciona
@app.get("/")
def ler_raiz():
    return {"mensagem": "teste de rota"}