import ccxt
import os
import time
import pandas as pd
import pandas_ta as ta
import time
from dotenv import load_dotenv
from decimal import Decimal
from telegram import send_telegram
from colorama import init as colorama_init, Fore, Style


load_dotenv()
colorama_init()

@staticmethod
def conectar_binance() -> ccxt.binance:
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
    BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")
    
    binance = ccxt.binance({
        'enableRateLimit': True,
        'apiKey': BINANCE_API_KEY,
        'secret': BINANCE_SECRET_KEY,
        'options': {
            'defaultType': 'future',
        }
    
    })
    
    return binance

class GerenciamentoRisco:
    def __init__(self): 
        self.binance: ccxt.binance = conectar_binance()

    def posicoes_abertas(self, symbol) -> tuple[str, str, str, bool, str, str, str]:
        """
        Obtém informações sobre as posições abertas para um determinado símbolo.

        Esta função consulta a API da Binance para recuperar detalhes da posição atual, incluindo 
        lado (long/short), tamanho, preço de entrada, notional, percentual e PnL não realizado.

        Parâmetros:
        - symbol (str): O símbolo do par de trading (ex: 'BTC/USDT').

        Retorna:
        - tuple: Uma tupla contendo (lado, tamanho, preco_entrada, posicao_aberta, notional, percentage, pnl).
          - lado (str): 'long' ou 'short'.
          - tamanho (str): Quantidade da posição.
          - preco_entrada (str): Preço de entrada da posição.
          - posicao_aberta (bool): True se há posição aberta, False caso contrário.
          - notional (str): Valor notional da posição.
          - percentage (str): Percentual de ganho/perda.
          - pnl (str): PnL não realizado.
        """
        lado = []
        tamanho = []
        preco_entrada = []
        notional = []
        percentage = []
        pnl = []

        posicao_aberta = False

        bal = self.binance.fetch_positions(symbols=[symbol])

        for i in bal:
            lado = i['side']
            tamanho = i['info']['positionAmt'].replace('-', '')
            preco_entrada = i['entryPrice']
            notional = i['notional']
            percentage = i['percentage']
            pnl = i['info']['unRealizedProfit']

        if lado == 'long':
            posicao_aberta = True
        elif lado == 'short':
            posicao_aberta = True

        return lado, tamanho, preco_entrada, posicao_aberta, notional, percentage, pnl

    def livro_ofertas(self, symbol) -> tuple[Decimal, Decimal]:
        """
        Obtém os melhores preços de bid e ask do livro de ofertas para um símbolo.

        Esta função consulta o livro de ofertas da Binance e retorna o melhor preço de compra (bid) 
        e venda (ask) disponíveis.

        Parâmetros:
        - symbol (str): O símbolo do par de trading (ex: 'BTC/USDT').

        Retorna:
        - tuple: Uma tupla contendo (bid, ask).
          - bid (Decimal): Melhor preço de compra.
          - ask (Decimal): Melhor preço de venda.
        """
        livro_ofertas = self.binance.fetch_order_book(symbol=symbol)
        
        bid = Decimal(livro_ofertas['bids'][0][0])
        ask = Decimal(livro_ofertas['asks'][0][0])

        return bid, ask

    def encerrar_posicao(self, symbol) -> None:
        """
        Encerra a posição aberta para um determinado símbolo.

        Esta função cancela todas as ordens pendentes e cria uma nova ordem de mercado 
        oposta para fechar a posição (sell para long, buy para short). Aguarda 20 segundos 
        entre tentativas se necessário.

        Parâmetros:
        - symbol (str): O símbolo do par de trading (ex: 'BTC/USDT').

        Retorna:
        - None
        """
        lado, tamanho, _, posicao_aberta, _, _, _ = self.posicoes_abertas(symbol)
        
        while posicao_aberta == True:
            if lado == 'long':
                self.binance.cancel_all_orders(symbol=symbol)
                
                _, ask = self.livro_ofertas(symbol)
                ask = self.binance.price_to_precision(symbol, ask)
                
                self.binance.create_order(symbol=symbol, side='sell', type='LIMIT', price=ask, amount=tamanho, params={'hedge': 'true'}) 
        
                print(f'{Fore.GREEN}📈 [{symbol}] - Vendendo posição long!{Style.RESET_ALL}')
                send_telegram(f'📈 [{symbol}] - Vendendo posição long!')
                
                time.sleep(20)
            elif lado == 'short':
                self.binance.cancel_all_orders(symbol=symbol)
                
                bid, _ = self.livro_ofertas(symbol)
                bid = self.binance.price_to_precision(symbol, bid)
        
                self.binance.create_order(symbol=symbol, side='buy', type='LIMIT', price=bid, amount=tamanho, params={'hedge': 'true'})
        
                print(f'{Fore.RED}📉 [{symbol}] - Comprando posição short!{Style.RESET_ALL}')
                send_telegram(f'📉 [{symbol}] - Comprando posição short!')
        
                time.sleep(20)
            else:
                print(f'{Fore.RED}🚫 [{symbol}] - Impossível encerrar a posição!{Style.RESET_ALL}')
                send_telegram(f'🚫 [{symbol}] - Impossível encerrar a posição!')
        
            lado, tamanho, _, posicao_aberta, _, _, _ = self.posicoes_abertas(symbol)

    def fecha_pnl(self, symbol, loss, target, timeframe) -> None:
        """
        Verifica e fecha posições baseado em stop loss e take profit.

        Esta função monitora o percentual de ganho/perda da posição e a 
        fecha automaticamente se atingir o limite de loss ou target. 
        
        Após fechar por loss, aguarda um tempo baseado no timeframe antes 
        de continuar.

        Parâmetros:
        - symbol (str): O símbolo do par de trading (ex: 'BTC/USDT').
        - loss (float): Percentual de stop loss (ex: -0.01 para -1%).
        - target (float): Percentual de take profit (ex: 0.05 para 5%).
        - timeframe (str): Timeframe usado para calcular o tempo de espera após loss (ex: '5m', '1h').

        Retorna:
        - None
        """
        _, _, _, _, _, percentage, pnl = self.posicoes_abertas(symbol)
        num_timeframe = int(timeframe[:-1])
        unidade = timeframe[-1]
        
        if percentage:
            if percentage <= loss:
                print(f"{Fore.RED}🛑 [{symbol}] - Encerrando posição por loss! PnL: {float(pnl):.2f} USDT - Percentage: {float(percentage):.2f}%{Style.RESET_ALL}")
                send_telegram(f"🛑 [{symbol}] - Encerrando posição por loss! PnL: {float(pnl):.2f} USDT - Percentage: {float(percentage):.2f}%")
                
                self.encerrar_posicao(symbol=symbol)
                
                if unidade == 'm':
                    print(f"{Fore.YELLOW}⏳ [{symbol}] - Aguardando {num_timeframe} minutos antes de continuar...{Style.RESET_ALL}")
                    t_sleep = num_timeframe * 5 * 60
                elif unidade == 'h':
                    print(f"{Fore.YELLOW}⏳ [{symbol}] - Aguardando {num_timeframe} minutos antes de continuar...{Style.RESET_ALL}")
                    t_sleep = num_timeframe * 2 * 3600
                elif unidade == 'd':
                    print(f"{Fore.YELLOW}⏳ [{symbol}] - Aguardando {num_timeframe} minutos antes de continuar...{Style.RESET_ALL}")
                    t_sleep = num_timeframe * 0.5 * 86400
                
                time.sleep(t_sleep)
            elif percentage >= target:
                print(f"{Fore.GREEN}💵 [{symbol}] - Encerrando posição por gain! PnL: {float(pnl):.2f} USDT - Percentage: {float(percentage):.2f}%{Style.RESET_ALL}")
                send_telegram(f"💵 [{symbol}] - Encerrando posição por gain! PnL: {float(pnl):.2f} USDT - Percentage: {float(percentage):.2f}%")
                
                self.encerrar_posicao(symbol=symbol)
            else:
                print(f"{Fore.BLUE}⌛ [{symbol}] - Ainda esperando momento! PnL: {float(pnl):.2f} USDT - Percentage: {float(percentage):.2f}%{Style.RESET_ALL}")

    def posicao_max(self,symbol, max_pos):
        """
        Verifica se a posição atual atingiu o tamanho máximo permitido.

        Esta função compara o tamanho da posição aberta com o limite máximo definido.

        Parâmetros:
        - symbol (str): O símbolo do par de trading (ex: 'BTC/USDT').
        - max_pos (float): Tamanho máximo permitido para a posição.

        Retorna:
        - bool: True se a posição atingiu ou ultrapassou o máximo, False caso contrário.
        """
        _, tamanho, _, _, _, _, _ = self.posicoes_abertas(symbol)
        
        if isinstance(tamanho, list):
            print(f"{Fore.RED}🚫 [{symbol}] - Sem posição aberta!{Style.RESET_ALL}")
            return False
        elif float(tamanho) >= max_pos:
            print(f"{Fore.RED}🚫 [{symbol}] - Tamanho da posição atingiu o máximo permitido! Tamanho: {tamanho} - Max: {max_pos}{Style.RESET_ALL}")
            return True
        elif float(tamanho) <= max_pos:
            return False
        else:
            print(f"{Fore.RED}🚫 [{symbol}] - Erro ao verificar tamanho da posição!{Style.RESET_ALL}")
            return False

    def ultima_ordem_aberta(self, symbol):
        """
        Verifica se a última ordem para um símbolo está aberta.

        Esta função consulta a API da Binance para obter o status da última ordem e verifica se ela ainda está aberta.

        Parâmetros:
        - symbol (str): O símbolo do par de trading (ex: 'BTC/USDT').

        Retorna:
        - bool: True se a última ordem está aberta, False caso contrário ou em caso de erro.
        """
        try:
            order = self.binance.fetch_orders(symbol=symbol)[-1]['status']
        
            if not order: order = []
        
            if isinstance(order, list):
                return False
            elif order == 'open':
                return True
            else:
                return False
        except Exception as e:
            print(f"🚨 [{symbol}] - Erro ao verificar última ordem aberta: {e}")
            send_telegram(f"🚨 [{symbol}] - Erro ao verificar última ordem aberta: {e}")
            
            return False

    def cancelar_todas_as_ordens(self, symbol):
        """
        Cancela todas as ordens pendentes para um determinado símbolo.

        Esta função tenta cancelar todas as ordens abertas na Binance para o símbolo especificado. Em caso de erro, envia uma notificação via Telegram.

        Parâmetros:
        - symbol (str): O símbolo do par de trading (ex: 'BTC/USDT').

        Retorna:
        - None
        """
        try:
            self.binance.cancel_all_orders(symbol=symbol)
        except Exception as e:
            print(f"🚨 [{symbol}] - Erro ao cancelar ordens: {e}")
            send_telegram(f"🚨 [{symbol}] - Erro ao cancelar ordens: {e}")