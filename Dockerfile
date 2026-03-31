FROM python:3.12-slim

# Diretório de trabalho
WORKDIR /app

# Instalar uv
RUN pip install uv

# Copiar arquivos de dependência primeiro (melhor cache)
COPY pyproject.toml uv.lock ./

# Instalar dependências
RUN uv sync --no-dev

# Copiar resto do projeto
COPY . .

# Rodar o bot
CMD ["uv", "run", "python", "main.py"]