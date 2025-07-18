import streamlit as st
import pandas as pd
import numpy as np
import joblib
import xgboost as xgb
from sklearn.base import BaseEstimator, RegressorMixin
from datetime import datetime, timedelta

# Classe para previsão com valor mínimo zero
class XGBRegressorPositivo(BaseEstimator, RegressorMixin):
    def __init__(self, **kwargs):
        self.model = xgb.XGBRegressor(**kwargs)

    def fit(self, X, y):
        self.model.fit(X, y)
        return self

    def predict(self, X):
        preds = self.model.predict(X)
        return np.maximum(preds, 0)

    def get_params(self, deep=True):
        return self.model.get_params(deep)

    def set_params(self, **params):
        self.model.set_params(**params)
        return self

# Carregar o modelo salvo
modelo = joblib.load('modelo_xgboost.pkl2')

st.title("Previsão de Quantidade de Refeições")

# Dicionários para tradução
dias_semana_pt = {
    'Monday': 'Segunda-feira',
    'Tuesday': 'Terça-feira',
    'Wednesday': 'Quarta-feira',
    'Thursday': 'Quinta-feira',
    'Friday': 'Sexta-feira',
    'Saturday': 'Sábado',
    'Sunday': 'Domingo'
}

meses_pt = {
    'January': 'Janeiro',
    'February': 'Fevereiro',
    'March': 'Março',
    'April': 'Abril',
    'May': 'Maio',
    'June': 'Junho',
    'July': 'Julho',
    'August': 'Agosto',
    'September': 'Setembro',
    'October': 'Outubro',
    'November': 'Novembro',
    'December': 'Dezembro'
}

# Função para obter os últimos n dias úteis antes de uma data base
def dias_uteis_anteriores(data_base, n=5):
    dias_uteis = []
    delta = timedelta(days=1)
    atual = data_base - delta
    while len(dias_uteis) < n:
        if atual.weekday() < 5:  # 0=segunda, 4=sexta
            dias_uteis.append(atual)
        atual -= delta
    return dias_uteis

# Seletor de data base da previsão
data_base = st.date_input("Selecione a data da previsão:", datetime.today())

# Exibe a data selecionada com dia, mês e dia da semana em português
nome_mes_escolhido = meses_pt[data_base.strftime("%B")]
nome_dia_escolhido = dias_semana_pt[data_base.strftime("%A")]
st.markdown(f"**Data selecionada:** {data_base.day} de {nome_mes_escolhido} ({nome_dia_escolhido})")

# Determinar dia da semana e mês para o modelo (dia da semana 0=Segunda)
dia_semana = data_base.weekday()
mes = data_base.month

# Checkbox para Férias
ferias = st.checkbox('Período de férias?')

# Radio para condição de feriado
feriado_opcao = st.radio(
    "Selecione a condição em relação ao feriado:",
    ('Nenhuma', 'Feriado', 'Pré-feriado', 'Pós-feriado')
)

# Variáveis binárias do feriado
feriado = 1 if feriado_opcao == 'Feriado' else 0
pre_feriado = 1 if feriado_opcao == 'Pré-feriado' else 0
pos_feriado = 1 if feriado_opcao == 'Pós-feriado' else 0

# Lista de pratos e chaves conforme modelo
nomes_visiveis = [
    'Almôndegas de carne', 'Carne ao molho', 'Carne suína',
    'Churrasquinho misto', 'Empadão', 'Estrogonofe de camarão',
    'Estrogonofe de carne', 'Estrogonofe de frango', 'Sem prato (feriado/sábado/domingo)',
    'Frango ao molho', 'Goulash', 'Guisado de lombo',
    'Lasanha de frango', 'Lasanha à bolonhesa', 'Peixe grelhado ao molho',
    'Picadinho', 'Não informado (sem registro)'
]

chaves_modelo = [
    'prato_almondegas_de_carne', 'prato_carne_ao_molho', 'prato_carne_suina',
    'prato_churrasquinho_misto', 'prato_empadao', 'prato_estrogonofe_de_camarao',
    'prato_estrogonofe_de_carne', 'prato_estrogonofe_de_frango', 'prato_sem_prato',
    'prato_frango_ao_molho', 'prato_goulash', 'prato_guisado_de_lombo',
    'prato_lasanha_de_frango', 'prato_lasanha_a_bolonhesa', 'prato_peixe_grelhado_ao_molho',
    'prato_picadinho', 'prato_nao_informado'
]

# Selectbox prato
prato_selecionado = st.selectbox(
    "Prato servido (escolha o prato que mais se aproxima do que foi servido):",
    ['Nenhum selecionado'] + nomes_visiveis
)

if prato_selecionado == 'Não informado (sem registro)':
    st.info("Use esta opção se não souber qual prato foi servido no dia. Não se refere à ausência de opções na lista.")

# Inicializa pratos com zero
pratos_input = {chave: 0 for chave in chaves_modelo}

if prato_selecionado != 'Nenhum selecionado':
    idx = nomes_visiveis.index(prato_selecionado)
    pratos_input[chaves_modelo[idx]] = 1

# Entrada das quantidades vendidas nos 5 dias úteis anteriores com dias traduzidos
st.markdown("### Informe as quantidades vendidas nos 5 dias úteis anteriores")
dias_anteriores = dias_uteis_anteriores(data_base)

quantidades = {}
for i, dia in enumerate(reversed(dias_anteriores), 1):
    nome_dia = dias_semana_pt[dia.strftime("%A")]
    data_formatada = dia.strftime("%d/%m/%Y")
    label = f"{nome_dia} ({data_formatada})"
    quantidades[f'POLO_QUANTIDADE_{i}'] = st.number_input(
        label, min_value=0, step=1, format="%d", value=0
    )

# Botão para previsão
if st.button("Prever quantidade"):
    if prato_selecionado == 'Nenhum selecionado':
        st.error("Por favor, selecione o prato servido antes de continuar.")
    elif feriado == 1 or dia_semana in [5, 6]:  # Sábado ou Domingo
        st.warning("Neste dia não há venda de quentinhas.")
        st.success("Previsão da quantidade: 0")
    else:
        entrada = {
            'É_FÉRIAS': int(ferias),
            'FERIADO': int(feriado),
            'PRÉ_FERIADO': int(pre_feriado),
            'PÓS_FERIADO': int(pos_feriado),
            'DIA_SEMANA': dia_semana,
            'MES': mes
        }
        entrada.update(pratos_input)
        entrada.update(quantidades)

        entrada_df = pd.DataFrame([entrada])

        pred = modelo.predict(entrada_df)

        st.success(f'Previsão da quantidade: {pred[0]:.0f}')
