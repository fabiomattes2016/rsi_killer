import ccxt
import os
import time
import schedule
import pandas as pd
from dotenv import load_dotenv
from colorama import init as colorama_init, Fore, Style
from indicadores import Indicadores
from gerenciamento_risco import GerenciamentoRisco
from telegram import send_telegram


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

@staticmethod
def get_candles(binance: ccxt.binance, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
    timeframe_in_ms = binance.parse_timeframe(timeframe) * 1000
    now = int(time.time() * 1000)
    since = now - (limit * timeframe_in_ms)
    bars = binance.fetch_ohlcv(symbol=symbol, timeframe=timeframe, since=since, limit=limit)
    
    df_candles = pd.DataFrame(bars, columns=['time', 'abertura', 'max', 'min', 'fechamento', 'volume'])
    df_candles['time'] = pd.to_datetime(
        df_candles['time'], 
        utc=True, 
        unit='ms'
    ).map(lambda x: x.tz_convert('America/Sao_Paulo'))
    
    return df_candles

class Estrategias:
    def __init__(
        self, 
        symbol: str,  
        loss: float, 
        target: float, 
        posicao_max: float, 
        posicao: float
    ):
        self.binance = conectar_binance()
        self.symbol = symbol
        self.loss = loss
        self.target = target
        self.posicao_max = posicao_max
        self.posicao = posicao
        self.indicadores = Indicadores()
        self.gerenciamento_risco = GerenciamentoRisco()
        self.leverage = int(os.getenv("LEVERAGE"))
        
    def rsi_killer(
        self, 
        schedule_time: int=10,
        rsi_sobrecompra: int=70, 
        rsi_sobrevenda: int=30, 
        bb_length: int=20, 
        bb_std: int=2, 
        threshold=0.0015,
        timeframe: str='5m',
        limit: int=35
    ):
        """
        Estratégia RSI Killer: Utiliza o indicador RSI (Relative Strength Index) combinado com Bandas de Bollinger 
        para identificar oportunidades de entrada em posições long e short.
        
        Esta estratégia monitora o RSI para detectar condições de sobrevenda (para long) ou sobrecompra (para short), 
        considerando também a largura das Bandas de Bollinger e o preço atual em relação ao candle anterior.
        
        Parâmetros:
        - schedule_time (int): Intervalo em segundos para executar a verificação da estratégia. Padrão: 10.
        - rsi_sobrecompra (int): Nível de sobrecompra do RSI para entrada em short. Padrão: 70.
        - rsi_sobrevenda (int): Nível de sobrevenda do RSI para entrada em long. Padrão: 30.
        - bb_length (int): Período para o cálculo das Bandas de Bollinger. Padrão: 20.
        - bb_std (int): Desvio padrão para as Bandas de Bollinger. Padrão: 2.
        - threshold (float): Limite mínimo para a largura das Bandas de Bollinger. Padrão: 0.0015.
        - timeframe (str): Timeframe dos candles (ex: '5m', '1h'). Padrão: '5m'.
        - limit (int): Número de candles a serem buscados. Padrão: 35.
        
        A estratégia executa indefinidamente, verificando condições a cada 'schedule_time' segundos.
        """
        
        print(f'{Fore.GREEN}🚀 Iniciando estratégia RSI Killer no par {self.symbol}...{Style.RESET_ALL}')
        
        def job():
            self.binance.set_margin_mode('isolated', f'{self.symbol}:USDT')
            self.binance.set_leverage(self.leverage, f'{self.symbol}:USDT')
            
            self.gerenciamento_risco.fecha_pnl(self.symbol, self.loss, self.target, timeframe=timeframe)
            
            candles = get_candles(self.binance, self.symbol, timeframe, limit)
            
            price = self.binance.fetch_trades(symbol=self.symbol, limit=1)[0]['price']
            price = float(self.binance.price_to_precision(self.symbol, price))
            
            # novo dataframe = candles recebido
            df_candles = self.indicadores.calcular_rsi(candles)
        
            # calcular indicadores e adicionar ao dataframe
            df_candles = self.indicadores.calcular_bb(df_candles, length=bb_length, std=bb_std)
            df_candles['largura'] = (df_candles[f'BBU_{bb_length}_{bb_std}.0_{bb_std}.0'] - df_candles[f'BBL_{bb_length}_{bb_std}.0_{bb_std}.0']) / df_candles[f'BBM_{bb_length}_{bb_std}.0_{bb_std}.0']
            
            print(f'{Fore.CYAN}=================================================================={Style.RESET_ALL}')
            print(f'{Fore.CYAN}📊 Analisando candles para {self.symbol}...{Style.RESET_ALL}')
            print(f'{Fore.CYAN}📈 RSI:         {df_candles.iloc[-2]["RSI"]}{Style.RESET_ALL}')
            print(f'{Fore.CYAN}📈 BB UPPER:    {df_candles.iloc[-2][f"BBU_{bb_length}_{bb_std}.0_{bb_std}.0"]}{Style.RESET_ALL}')
            print(f'{Fore.CYAN}📈 BB MIDDLE:   {df_candles.iloc[-2][f"BBM_{bb_length}_{bb_std}.0_{bb_std}.0"]}{Style.RESET_ALL}')
            print(f'{Fore.CYAN}📈 BB LOWER:    {df_candles.iloc[-2][f"BBL_{bb_length}_{bb_std}.0_{bb_std}.0"]}{Style.RESET_ALL}')
            print(f'{Fore.CYAN}📈 Largura BB:  {df_candles.iloc[-2]["largura"]}{Style.RESET_ALL}')
            print(f'{Fore.CYAN}💲 Preço atual: {price}{Style.RESET_ALL}')
            print(f'{Fore.CYAN}=================================================================={Style.RESET_ALL}')
            
            if self.gerenciamento_risco.posicao_max(symbol=self.symbol, max_pos=self.posicao_max):
                print(f'{Fore.YELLOW}⚠️ [{self.symbol}] - Posição máxima atingida!{Style.RESET_ALL}')
            else:
                # lógica de entrada (long)
                if (
                    df_candles.iloc[-2]['RSI'] <= rsi_sobrevenda
                    and df_candles.iloc[-3]['fechamento'] <= df_candles.iloc[-3][f'BBL_{bb_length}_{bb_std}.0_{bb_std}.0']
                    and df_candles.iloc[-2]['fechamento'] > df_candles.iloc[-2]['abertura']  # candle de reversão
                    and df_candles.iloc[-2]['fechamento'] > df_candles.iloc[-2][f'BBL_{bb_length}_{bb_std}.0_{bb_std}.0']  # voltou pra dentro da banda
                    and df_candles.iloc[-1]['largura'] >= threshold
                ):
                    print(f'{Fore.GREEN}🚩 [{self.symbol}] - Entrando em long!{Style.RESET_ALL}')
                    # send_telegram(f'🚩 Entrando em long!')
                    
                    try:
                        bid, _ = self.gerenciamento_risco.livro_ofertas(self.symbol)
                        bid = self.binance.price_to_precision(self.symbol, bid)
                
                        self.binance.create_order(symbol=self.symbol, side='buy', type='LIMIT', price=bid, amount=self.posicao, params={'hedge': 'true'})
                        
                        print(f'{Fore.GREEN}✅️ [{self.symbol}] - Comprando posição long: {self.posicao} de {self.symbol} a {bid} USDT{Style.RESET_ALL}')
                        send_telegram(f'✅️ [{self.symbol}] - Comprando posição long: {self.posicao} de {self.symbol} a {bid} USDT')
                        
                    except Exception as e:
                        print(f'{Fore.RED}🚨 Erro ao criar ordem: {e}{Style.RESET_ALL}')
                # lógica de entrada (short)
                elif (
                    df_candles.iloc[-2]['RSI'] >= rsi_sobrecompra
                    and df_candles.iloc[-3]['fechamento'] >= df_candles.iloc[-3][f'BBU_{bb_length}_{bb_std}.0_{bb_std}.0']
                    and df_candles.iloc[-2]['fechamento'] < df_candles.iloc[-2]['abertura']  # candle de reversão
                    and df_candles.iloc[-2]['fechamento'] < df_candles.iloc[-2][f'BBU_{bb_length}_{bb_std}.0_{bb_std}.0']  # voltou pra dentro da banda
                    and df_candles.iloc[-1]['largura'] >= threshold
                ):
                    print(f'{Fore.RED}🚩 [{self.symbol}] - Entrando em short!{Style.RESET_ALL}')
                    # send_telegram(f'🚩 Entrando em short!')
                    
                    try:
                        _, ask = self.gerenciamento_risco.livro_ofertas(self.symbol)
                        ask = self.binance.price_to_precision(self.symbol, ask)
                
                        self.binance.create_order(symbol=self.symbol, side='sell', type='LIMIT', price=ask, amount=self.posicao, params={'hedge': 'true'})
                        
                        print(f'{Fore.RED}✅️ [{self.symbol}] - Vendendo posição short: {self.posicao} de {self.symbol} a {ask} USDT{Style.RESET_ALL}')
                        send_telegram(f'✅️ [{self.symbol}] - Vendendo posição short: {self.posicao} de {self.symbol} a {ask} USDT')
                    except Exception as e:
                        print(f'{Fore.RED}🚨 [{self.symbol}] - Erro ao criar ordem: {e}{Style.RESET_ALL}')
                else:
                    print(f'{Fore.YELLOW}🚫 [{self.symbol}] - Nenhuma condição de entrada satisfeita. Mercado lateralizado!{Style.RESET_ALL}')

        schedule.every(schedule_time).seconds.do(job)
        
        while True:
            try:
                schedule.run_pending()
            except Exception as e:
                print(f'{Fore.RED}🚨 Erro: {e}{Style.RESET_ALL}')
