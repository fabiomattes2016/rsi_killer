import pandas_ta as ta
import pandas as pd
from ta.momentum import RSIIndicator
from pandas import DataFrame


class Indicadores:
    def calcular_ema(self, candles: DataFrame, periodos: list[int]) -> DataFrame:
        """
        Calcula a Média Móvel Exponencial (EMA) para os preços de fechamento.

        Esta função adiciona colunas de EMA ao DataFrame de candles para cada período especificado.

        Parâmetros:
        - candles (DataFrame): DataFrame contendo os dados dos candles com coluna 'fechamento'.
        - periodos (list[int]): Lista de períodos para calcular a EMA (ex: [20, 50]).

        Retorna:
        - DataFrame: O DataFrame original com as novas colunas 'EMA_{periodo}' adicionadas.
        """
        for periodo in periodos:
            candles[f'EMA_{periodo}'] = ta.ema(candles['fechamento'], length=periodo)

        return candles
    
    def calcular_sma(self, candles: DataFrame, periodos: list[int]) -> DataFrame:
        """
        Calcula a Média Móvel Simples (SMA) para os preços de fechamento.

        Esta função adiciona colunas de SMA ao DataFrame de candles para cada período especificado.

        Parâmetros:
        - candles (DataFrame): DataFrame contendo os dados dos candles com coluna 'fechamento'.
        - periodos (list[int]): Lista de períodos para calcular a SMA (ex: [20, 50]).

        Retorna:
        - DataFrame: O DataFrame original com as novas colunas 'SMA_{periodo}' adicionadas.
        """
        for periodo in periodos:
            candles[f'SMA_{periodo}'] = ta.sma(candles['fechamento'], length=periodo)

        return candles
    
    def calcular_rsi(self, candles: DataFrame, window:int=14) -> DataFrame:
        """
        Calcula o Índice de Força Relativa (RSI) para os preços de fechamento.

        Esta função adiciona a coluna 'RSI' ao DataFrame de candles usando o período padrão de 14.

        Parâmetros:
        - candles (DataFrame): DataFrame contendo os dados dos candles com coluna 'fechamento'.
        - window (int): Período para o cálculo do RSI. Padrão: 14.

        Retorna:
        - DataFrame: O DataFrame original com a nova coluna 'RSI' adicionada.
        """
        rsi = RSIIndicator(close=candles['fechamento'], window=window)
        candles[f'RSI'] = rsi.rsi()
        
        return candles
    
    def calcular_bb(self, candles: DataFrame, length:int=20, std: int=2) -> DataFrame:
        """
        Calcula as Bandas de Bollinger (BB) para os preços de fechamento.

        Esta função adiciona as colunas 'BBL' (banda inferior), 'BBM' (banda média) e 'BBU' (banda superior) ao DataFrame.

        Parâmetros:
        - candles (DataFrame): DataFrame contendo os dados dos candles com coluna 'fechamento'.
        - length (int): Período para o cálculo das bandas. Padrão: 20.
        - std (int): Número de desvios padrão. Padrão: 2.

        Retorna:
        - DataFrame: O DataFrame original com as novas colunas 'BBL', 'BBM' e 'BBU' adicionadas.
        """
        bb = candles.ta.bbands(close='fechamento', length=length, std=std, append=True)
        bb = bb.iloc[:, [0, 1, 2]]
        bb.columns = ['BBL', 'BBM', 'BBU']
        
        return candles
    
    def calcular_macd(self, candles: DataFrame, fast: int=12, slow: int=26, signal: int=9) -> DataFrame:
        """
        Calcula o MACD (Moving Average Convergence Divergence) para os preços de fechamento.

        Esta função adiciona as colunas 'MACD' (linha MACD), 'MACDh' (histograma) e 'MACDs' (linha de sinal) ao DataFrame.

        Parâmetros:
        - candles (DataFrame): DataFrame contendo os dados dos candles com coluna 'fechamento'.
        - fast (int): Período da média móvel rápida. Padrão: 12.
        - slow (int): Período da média móvel lenta. Padrão: 26.
        - signal (int): Período da linha de sinal. Padrão: 9.

        Retorna:
        - DataFrame: O DataFrame original com as novas colunas 'MACD', 'MACDh' e 'MACDs' adicionadas.
        """
        macd = candles.ta.macd(close='fechamento', fast=fast, slow=slow, signal=signal, append=True)
        macd = macd.iloc[:, [0, 1, 2]]
        macd.columns = ['MACD', 'MACDh', 'MACDs']
        
        return candles
    
    def calcular_vwap(self, candles: DataFrame, start_range: int=25, end_range: int=35) -> DataFrame:
        """
        Calcula o Volume Weighted Average Price (VWAP) para um intervalo específico dos candles.

        Esta função calcula o VWAP baseado nos preços de fechamento e volumes dentro do intervalo definido, adicionando a coluna 'VWAP' ao DataFrame.

        Parâmetros:
        - candles (DataFrame): DataFrame contendo os dados dos candles com colunas 'fechamento' e 'volume'.
        - start_range (int): Índice inicial do intervalo para cálculo. Padrão: 25.
        - end_range (int): Índice final do intervalo para cálculo. Padrão: 35.

        Retorna:
        - DataFrame: O DataFrame original com a nova coluna 'VWAP' adicionada.
        """
        candles[[ 'fechamento', 'volume' ]] = candles[['fechamento', 'volume']][start_range:end_range]
        candles['preco_ponderado'] = candles['fechamento'] * candles['volume']
        candles['VWAP'] = candles['preco_ponderado'].sum() / candles['volume'].sum()
        
        return candles
    
    def calcular_suporte_resitencia(self, candles: DataFrame, window: int=10) -> DataFrame:
        """
        Calcula os níveis de suporte e resistência usando uma janela móvel.

        Esta função adiciona as colunas 'suporte' e 'resistencia' ao DataFrame baseado nos mínimos e máximos da janela, e retorna os valores do penúltimo candle.

        Parâmetros:
        - candles (DataFrame): DataFrame contendo os dados dos candles com colunas 'min' e 'max'.
        - window (int): Tamanho da janela para o cálculo. Padrão: 10.

        Retorna:
        - tuple: Uma tupla contendo (suporte, resistencia) do penúltimo candle.
        """
        candles['suporte'] = candles['min'].rolling(window=window).min()
        candles['resistencia'] = candles['max'].rolling(window=window).max()
        
        return candles.iloc[-2]['suporte'], candles.iloc[-2]['resistencia']