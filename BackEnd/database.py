from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. O Endereço da Base de Dados
# Formato: mysql+pymysql://utilizador:senha@nome_do_contentor:porta/nome_da_base_de_dados
URL_DA_BASE_DE_DADOS = "mysql+pymysql://root:admin@db:3306/sve_db"

# 2. O Motor (Engine)
motor = create_engine(URL_DA_BASE_DE_DADOS)

# 3. A Sessão (SessionLocal)
SessaoLocal = sessionmaker(autocommit=False, autoflush=False, bind=motor)

# 4. A Base (Base)
Base = declarative_base()