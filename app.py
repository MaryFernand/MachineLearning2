import streamlit as st
import pandas as pd
import numpy as np
import joblib

# Carregar o modelo salvo
modelo = joblib.load('modelo_xgboost.pkl')

st.title("Previsão de Quantidade de Refeições")

# Checkbox para Férias
ferias = st.checkbox('Período de férias?')

# Radio exclusivo para condição do feriado
feriado_opcao = st.radio(
    "Selecione a condição em relação ao feriado:",
    ('Nenhuma', 'Feriado', 'Pré-feriado', 'Pós-feriado')
)

# Mapear para variáveis binárias
feriado = 1 if feriado_opcao == 'Feriado' else 0
pre_feriado = 1 if feriado_opcao == 'Pré-feriado' else 0
pos_feriado = 1 if feriado_opcao == 'Pós-feriado' else 0

# Inputs numéricos
dia_semana = st.slider('Qual o dia da semana? (1=Segunda, 5=Sexta)', 1, 5, 1)
mes = st.slider('Qual o mês do ano?', 1, 12, 1)
dia_semana_modelo = dia_semana - 1  # ajuste para 0-based

# Lista amigável para o usuário escolher
nomes_visiveis = [
    'Almôndegas de carne', 'Carne ao molho', 'Carne suína',
    'Churrasquinho misto', 'Empadão', 'Estrogonofe de camarão',
    'Estrogonofe de carne', 'Estrogonofe de frango', 'Feriado (Sem prato)',
    'Frango ao molho', 'Goulash', 'Guisado de lombo',
    'Lasanha de frango', 'Lasanha à bolonhesa', 'Peixe grelhado ao molho',
    'Picadinho', 'Não informado (Férias)'
]

# As chaves que o modelo espera (mesma ordem dos nomes_visiveis)
chaves_modelo = [
    'prato_almondegas_de_carne', 'prato_carne_ao_molho', 'prato_carne_suina',
    'prato_churrasquinho_misto', 'prato_empadao', 'prato_estrogonofe_de_camarao',
    'prato_estrogonofe_de_carne', 'prato_estrogonofe_de_frango', 'prato_feriado',
    'prato_frango_ao_molho', 'prato_goulash', 'prato_guisado_de_lombo',
    'prato_lasanha_de_frango', 'prato_lasanha_a_bolonhesa', 'prato_peixe_grelhado_ao_molho',
    'prato_picadinho', 'prato_nao_informado_ferias'
]

# Selectbox para escolher prato amigável
prato_selecionado = st.selectbox(
    "Prato servido (escolha o prato que mais se aproxima do que foi servido):",
    ['Nenhum selecionado'] + nomes_visiveis
)

# Inicializa todos pratos com zero
pratos_input = {chave: 0 for chave in chaves_modelo}

if prato_selecionado != 'Nenhum selecionado':
    idx = nomes_visiveis.index(prato_selecionado)
    pratos_input[chaves_modelo[idx]] = 1

st.markdown("### Informe as quantidades vendidas nos 5 dias úteis anteriores")
st.write(
    "Preencha as quantidades de refeições vendidas nos 5 dias úteis anteriores (sábado e domingo não entram na análise). "
)

cols = st.columns(5)

quantidades = {}
for i in range(5):
    with cols[i]:
        dia = 5 - i
        quantidades[f'POLO_QUANTIDADE_{dia}'] = st.number_input(
            f"{dia} dia{'s' if dia > 1 else ''} atrás",
            min_value=0, step=1, format="%d",
            value=0  # default 0 para já ser obrigatório
        )

if st.button("Prever quantidade"):
    # Validar seleção do prato
    if prato_selecionado == 'Nenhum selecionado':
        st.error("Por favor, selecione o prato servido antes de continuar.")
    else:
        entrada = {
            'É_FÉRIAS': int(ferias),
            'FERIADO': int(feriado),
            'PRÉ_FERIADO': int(pre_feriado),
            'PÓS_FERIADO': int(pos_feriado),
            'DIA_SEMANA': dia_semana_modelo,
            'MES': mes
        }
        entrada.update(pratos_input)
        entrada.update(quantidades)

        entrada_df = pd.DataFrame([entrada])

        pred = modelo.predict(entrada_df)

        st.success(f'Previsão da quantidade: {pred[0]:.0f}')