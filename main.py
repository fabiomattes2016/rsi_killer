from multiprocessing import Process
import pandas as pd
import os
from colorama import init as colorama_init, Fore, Style
from estrategias import Estrategias
from gerenciamento_risco import GerenciamentoRisco
from dotenv import load_dotenv


load_dotenv()

# Inicializa o colorama para permitir cores na saída do terminal
colorama_init()

# Definição do par de trading principal
symbol = os.getenv("SYMBOL")
# Definição do stop loss em percentual (-1%)
loss = float(os.getenv("LOSS"))
# Definição do take profit em percentual (2%)
target = float(os.getenv("TARGET"))
# Definição do tamanho máximo da posição
posicao_max = float(os.getenv("POSICAO_MAX"))
# Definição do tamanho padrão da posição
posicao = float(os.getenv("POSICAO"))

# Instancia a classe GerenciamentoRisco para gerenciar posições e ordens
gerenciamento_risco = GerenciamentoRisco()

# Instancia a classe Estrategias com os parâmetros definidos
estrategias = Estrategias(symbol, loss, target, posicao_max, posicao)

rsi_sobrecompra = int(os.getenv("RSI_SOBRECOMPRA"))
rsi_sobrevenda = int(os.getenv("RSI_SOBREVENDA"))
bb_length = int(os.getenv("BB_LENGTH"))
bb_std = int(os.getenv("BB_STD"))
threshold = float(os.getenv("THRESHOLD"))

# Função que executa a estratégia RSI Killer
def bot_rsi_killer():
    estrategias.rsi_killer(rsi_sobrecompra=rsi_sobrecompra, rsi_sobrevenda=rsi_sobrevenda, bb_length=bb_length, bb_std=bb_std, threshold=threshold, schedule_time=10, limit=35)

# Bloco principal que executa quando o script é rodado diretamente
if __name__ == "__main__":
    # Cancela todas as ordens pendentes para o símbolo principal antes de iniciar
    gerenciamento_risco.cancelar_todas_as_ordens(symbol)

    # Imprime mensagem colorida indicando o início dos bots
    print(f"{Fore.GREEN}🏁 Iniciando bots...{Style.RESET_ALL}")
        
    # Criação de processos para executar estratégias em paralelo (alguns comentados para não executar)
    bot = Process(target=bot_rsi_killer)

    # Inicia os processos ativos
    bot.start()
    
    # Aguarda os processos terminarem (join)
    bot.join()
    