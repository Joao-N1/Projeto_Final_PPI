import bcrypt

def gerar_hash_senha(senha_plana: str) -> str:
    """Transforma a senha em texto limpo em um hash seguro."""
    # Transforma a string em bytes
    senha_bytes = senha_senha = senha_plana.encode('utf-8')
    # Gera o salt e o hash
    salt = bcrypt.gensalt()
    hash_bytes = bcrypt.hashpw(senha_bytes, salt)
    # Retorna o hash como string para salvar no banco
    return hash_bytes.decode('utf-8')

def verificar_senha(senha_plana: str, hash_senha: str) -> bool:
    """Compara a senha digitada com o hash salvo no banco."""
    return bcrypt.checkpw(
        senha_plana.encode('utf-8'), 
        hash_senha.encode('utf-8')
    )

