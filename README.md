# RSI Killer (Python)

Projeto de exemplo de bots de trading com execução em Binance Futures, desenvolvido em Python.

## 🚀 Visão Geral

Este projeto inclui:
- `estrategias.py`: implementa estratégia RSI Killer.
- `gerenciamento_risco.py`: controle de posições, stop loss/take profit, cancelamento de ordens.
- `indicadores.py`: cálculos de indicadores (EMA, SMA, RSI, MACD, Bandas de Bollinger, VWAP, suporte/resistência).
- `main.py`: script de orquestração para rodar bot(s) em processos separados.
- `telegram.py`: envio de notificações para Telegram.

## 🛠️ Pré-requisitos

- Python 3.11+ (ou 3.10)
- `pip` instalado
- Conta na Binance com API key/secret configurados

## 📦 Instalação (Ambiente virtual com `uv`)

### 1) Instalar `uv` (gerenciador de ambientes Python)

No Windows (PowerShell):

```powershell
pip install uv
```

No Linux/macOS:

```bash
pip install uv
```

### 2) Criar e ativar ambiente com `uv`

```bash
cd d:/Estudos/Python/trade-bots
uv create .venv
uv activate .venv
```

### 3) Instalar dependências

```bash
uv install -r requirements.txt
```

> Se não existir `requirements.txt`, gere com:
> ```bash
> uv install ccxt pandas pandas_ta ta python-dotenv schedule colorama httpx
> uv freeze > requirements.txt
> ```

## ⚙️ Configuração de variáveis de ambiente

Crie um arquivo `.env` com:

```ini
BINANCE_API_KEY=seu_token
BINANCE_SECRET_KEY=sua_chave
TELEGRAM_TOKEN=seu_telegram_token
TELEGRAM_CHAT_ID=seu_chat_id
```

## ▶️ Como rodar (modo desenvolvimento)

Execute o bot principal:

```bash
python main.py
```

## 🧪 Testes e validações locais

- Verifique lógica em `estrategias.py`, `indicadores.py` e `gerenciamento_risco.py`.
- Use prints no console e logs do Telegram para análise.
- Opcional: crie um teste rápido com `pytest`.

## 🐳 Execução com Docker / containers

### Dockerfile (sugestão)

```dockerfile
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
```

### docker-compose.yml (sugestão)

```yaml
services:
  rsi-killer-binance-eth:
    image: rsi-killer-binance:latest
    container_name: rsi-killer-binance-eth
    restart: unless-stopped
    env_file:
      - .env
    environment:
      SYMBOL: "ETH/USDT"
      LOSS: -1
      TARGET: 2
      POSICAO_MAX: 0.02
      POSICAO: 0.01
      RSI_SOBRECOMPRA: 65
      RSI_SOBREVENDA: 30
      BB_LENGTH: 20
      BB_STD: 2
      THRESHOLD: 0.0015
      LEVERAGE: 10
```

### Construir e iniciar container

```bash
docker-compose build
docker-compose up -d
```

### Logs e controle

```bash
docker-compose logs -f
docker-compose stop
docker-compose down
```

## 📌 Estrutura principal de arquivos
- `estrategias.py`: regras de entrada/saída do bot
- `gerenciamento_risco.py`: rotina de controle da carteira
- `indicadores.py`: cálculo de indicadores
- `main.py`: ponto de entrada do bot
- `telegram.py`: notificações

## 🔮 Evoluções futuras

1. Suporte a novas corretoras:
   - Bybit
   - OKX

2. Adicionar modo paper trading (simulado) com backtest.
3. Modularizar estratégias em classes e plugins.
4. Adicionar logging estruturado e métricas (Prometheus/Grafana).
5. Refinar gerenciamento de risco (valor de alavancagem, martingale, trailing stop).

## ⚠️ Avisos
- Faça testes em conta de simulação antes de operar real.
- Uso deste código é por sua conta e risco.
- Cuide da segurança das chaves de API e não as compartilhe.
