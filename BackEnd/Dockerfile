# 1. Escolhemos uma versão leve do Python
FROM python:3.10-slim

# 2. Criamos uma pasta de trabalho dentro do contentor
WORKDIR /app

# 3. Copiamos a lista de pacotes necessários e instalamos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiamos o resto do teu código do backend para o contentor
COPY . .

# 5. O comando para arrancar o FastAPI quando o contentor ligar
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]