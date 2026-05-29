import os
from dotenv import load_dotenv # Importamos a ferramenta que lê o .env
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Lê o ficheiro .env e carrega os segredos para a memória
load_dotenv()

# Agora vamos buscar o URL ao nosso "cofre" virtual!
URL_DA_BASE_DE_DADOS = os.getenv("URL_DA_BASE_DE_DADOS")

motor = create_engine(URL_DA_BASE_DE_DADOS)
SessaoLocal = sessionmaker(autocommit=False, autoflush=False, bind=motor)
Base = declarative_base()