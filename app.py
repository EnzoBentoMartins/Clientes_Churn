import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt
import seaborn as sns

# Função para carregar o arquivo CSV
def load_data():
    uploaded_file = st.file_uploader("Escolha um arquivo CSV", type="csv")
    if uploaded_file is not None:
        # Carregar os dados
        colunas = [
        'Conta_ID', 'Tipo_Conta', 'Razao_Social_Pessoas', 'CNPJ', 'Raiz_CNPJ', 
        'Grupo_Economico_ID', 'Grupo_Economico_Nome', 'Vendedor_Conta_ID', 'Nome_Vendedor', 
        'Data_Ultima_Venda', 'Classificacao_Conta', 'Classificacao_Pessoa', 'Porte_Empresa', 
        'Orcamento_ID', 'Data_Emissao_Ultimo_Orcamento'
        ]
        df = pd.read_csv(uploaded_file, names=colunas, sep=';')
        return df
    return None

# Função para processar os dados
def process_data(df):
    
    # Transformar as colunas de datas em datetime
    df['Data_Ultima_Venda'] = pd.to_datetime(df['Data_Ultima_Venda'], errors='coerce')
    df['Data_Emissao_Ultimo_Orcamento'] = pd.to_datetime(df['Data_Emissao_Ultimo_Orcamento'], errors='coerce')

    # Remover as linhas onde ambas as colunas de datas estão NaT
    df = df.dropna(subset=['Data_Ultima_Venda', 'Data_Emissao_Ultimo_Orcamento'], how='all')

    # Filtrando dados para as vendas até 2023
    df_filtrado = df[df['Data_Ultima_Venda'].dt.year <= 2023]

    # Contar o número de clientes por vendedor
    clientes_por_vendedor = df_filtrado.groupby('Nome_Vendedor')['Razao_Social_Pessoas'].nunique().reset_index()
    clientes_por_vendedor.rename(columns={'Razao_Social_Pessoas': 'Numero_de_Clientes'}, inplace=True)

    # Obter a última venda e o último orçamento por cliente
    ultimas_vendas_orcamentos = df_filtrado.groupby(['Nome_Vendedor', 'Razao_Social_Pessoas']).agg(
        Ultima_Venda=('Data_Ultima_Venda', 'max'),
        Ultimo_Orcamento=('Data_Emissao_Ultimo_Orcamento', 'max')
    ).reset_index()

    # Juntar os dados de clientes por vendedor com as últimas vendas e orçamentos
    resultado_final = pd.merge(clientes_por_vendedor, ultimas_vendas_orcamentos, on='Nome_Vendedor', how='left')

    # Remover as linhas onde tanto 'Ultima_Venda' quanto 'Ultimo_Orcamento' são NaT
    resultado_final = resultado_final.dropna(subset=['Ultima_Venda', 'Ultimo_Orcamento'], how='all')

    # Calcular os dias desde a última venda
    hoje = pd.to_datetime('today')
    resultado_final['Dias_Sem_Compra'] = (hoje - resultado_final['Ultima_Venda']).dt.days

    return resultado_final

# Função para salvar em Excel
def save_to_excel(df_vendedor):
    excel_buffer = io.BytesIO()  # Criando um buffer de memória para o arquivo Excel
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        df_vendedor.to_excel(writer, index=False)

    excel_buffer.seek(0)  # Voltar ao início do buffer
    return excel_buffer

# Função para salvar em CSV
def save_to_csv(df_vendedor):
    return df_vendedor.to_csv(index=False)

# Função para exibir gráficos
def plot_graphs(resultado_final):
    # Gráfico 1: Quantidade de clientes churn por vendedor
    plt.figure(figsize=(12, 20))
    order = resultado_final['Nome_Vendedor'].value_counts().index
    sns.countplot(data=resultado_final, y='Nome_Vendedor', palette='Set2', order=order)
    plt.title('Quantidade de Clientes Churn por Vendedor')
    plt.xlabel('Quantidade de Clientes')
    plt.ylabel('Nome do Vendedor')
    st.pyplot(plt)

    # Gráfico 2: Dias desde a última compra
    plt.figure(figsize=(12, 6))
    sns.histplot(resultado_final['Dias_Sem_Compra'], kde=True, color='purple')
    plt.title('Distribuição de Dias Sem Compra')
    plt.xlabel('Dias Sem Compra')
    plt.ylabel('Frequência')
    st.pyplot(plt)

# Aplicação Streamlit
st.title('Análise de Churn de Vendedores')

# Carregar os dados
df = load_data()

if df is not None:
    # Exibir as primeiras linhas do DataFrame
    st.write("Dados carregados:")
    st.dataframe(df.head())

    # Processar os dados
    resultado_final = process_data(df)

    # Exibir os dados processados
    st.write("Dados Processados:")
    st.dataframe(resultado_final)

    # Exibir gráficos
    plot_graphs(resultado_final)

    # Escolher o vendedor para filtrar os dados
    vendedor_selecionado = st.selectbox('Escolha um vendedor', resultado_final['Nome_Vendedor'].unique())

    # Filtrar os dados do vendedor selecionado
    df_vendedor = resultado_final[resultado_final['Nome_Vendedor'] == vendedor_selecionado]

    # Exibir os dados do vendedor selecionado
    st.write(f"Dados do Vendedor: {vendedor_selecionado}")
    st.dataframe(df_vendedor)

    # Download dos arquivos CSV e Excel
    excel_file = save_to_excel(df_vendedor)
    csv_file = save_to_csv(df_vendedor)

    st.download_button(
        label="Baixar Excel",
        data=excel_file,
        file_name=f'{vendedor_selecionado}_clientes_ate_2023.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    st.download_button(
        label="Baixar CSV",
        data=csv_file,
        file_name=f'{vendedor_selecionado}_clientes_ate_2023.csv',
        mime='text/csv'
    )
else:
    st.write("Por favor, faça o upload de um arquivo CSV.")
