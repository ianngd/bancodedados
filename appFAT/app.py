import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text
import urllib.parse # Importar para escapar a minha senha com caracteres especiais
from datetime import date

def exibir_pdf_via_url(url): #Chamada para exibir o PDF via URL
    st.markdown(f'''
        <iframe src="{url}" width="700" height="1000" 
        style="border: none;"></iframe>
    ''', unsafe_allow_html=True)

# ===== CONFIGURAÇÕES INICIAIS =====
st.set_page_config(page_title="Dashboard Streamlit", layout="wide")
st.title("🤳 DB Cell")

# ===== MENU LATERAL =====
menu = st.sidebar.selectbox("📂 Selecione a opção", ["Clientes", "Produtos", "Vendas", "Registros", "Relatório Power BI"])

# ===== CONEXÃO COM BANCO USANDO SQLALCHEMY =====
@st.cache_resource
def conectar():
    db = st.secrets["database"]
    senha_escapada = urllib.parse.quote_plus(db["password"])
    conn_str = f"mysql+pymysql://{db['user']}:{senha_escapada}@{db['host']}:{db['port']}/{db['database']}"
    return create_engine(conn_str)

engine = conectar()

# ===== CONSULTAS =====
def consultar_clientes():
    query = "SELECT * FROM tbDCliente LIMIT 200;"
    return pd.read_sql(query, engine)

def consultar_produtos():
    query = "SELECT * FROM tbDProduto LIMIT 200;"
    return pd.read_sql(query, engine)

def consultar_vendas():
    query = """
        SELECT
            v.id_venda,
            c.nome AS cliente,
            p.descricao AS produto,
            i.quantidade,
            pg.forma_pagamento,
            pg.valor_pago,
            pg.parcelas
        FROM tbFItemvenda i
        JOIN tbDProduto p ON i.id_produto = p.id_produto
        JOIN tbFVenda v ON i.id_venda = v.id_venda
        JOIN tbDCliente c ON v.id_cliente = c.id_cliente
        JOIN tbDPagamento pg ON v.id_venda = pg.id_venda
        LIMIT 200;
    """
    return pd.read_sql(query, engine)

# ===== EXIBIÇÃO =====
if menu == "Clientes":
    st.subheader("👥 Clientes")
    try:
        df = consultar_clientes()

        # 🔍 Campo de busca
        busca = st.text_input("Buscar por nome, CPF ou e-mail:")

        if busca:
            busca = busca.lower()
            df = df[df.apply(lambda row: busca in str(row["nome"]).lower() 
                                        or busca in str(row["cpf"]).lower() 
                                        or busca in str(row["email"]).lower(), axis=1)]

        st.dataframe(df, hide_index=True)

    except Exception as e:
        st.error(f"Erro: {e}")

elif menu == "Produtos":
    st.subheader("📦 Tabela de Produtos")
    try:
        df = consultar_produtos()

        # 🎯 FILTROS DINÂMICOS
        col1, col2 = st.columns(2)

        with col1:
            nome_produto_filtro = st.selectbox("Filtrar por Nome do produto:", ["Todos"] + sorted(df["descricao"].unique()))
        with col2:
            id_produto_filtro = st.selectbox("Filtrar por ID do produto:", ["Todos"] + sorted(df["id_produto"].unique()))

        # Aplica filtros
        if nome_produto_filtro != "Todos":
            df = df[df["descricao"] == nome_produto_filtro]
        if id_produto_filtro != "Todos":
            df = df[df["id_produto"] == id_produto_filtro]
        st.dataframe(df, hide_index=True)

    except Exception as e:
        st.error(f"Erro: {e}")

elif menu == "Vendas":
    st.subheader("🛒 Vendas")
    try:
        df = consultar_vendas()

        # 🎯 FILTROS DINÂMICOS
        col1, col2, col3 = st.columns(3)

        with col1:
            cliente_filtro = st.selectbox("Filtrar por cliente:", ["Todos"] + sorted(df["cliente"].unique().tolist()))
        with col2:
            forma_pagamento_filtro = st.selectbox("Filtrar por forma de pagamento:", ["Todos"] + sorted(df["forma_pagamento"].unique().tolist()))
        with col3:
            produto_filtro = st.selectbox("Filtrar por produto:", ["Todos"] + sorted(df["produto"].unique()))

        # Aplica filtros
        if cliente_filtro != "Todos":
            df = df[df["cliente"] == cliente_filtro]
        if forma_pagamento_filtro != "Todos":
            df = df[df["forma_pagamento"] == forma_pagamento_filtro]
        if produto_filtro != "Todos":
            df = df[df["produto"] == produto_filtro]
        st.dataframe(df, hide_index=True)
    except Exception as e:
        st.error(f"Erro: {e}")

elif menu == "Registros":
    st.subheader("📝 Tela de Cadastros")

    tab1, tab2, tab3 = st.tabs(["👤 Novo Cliente", "📦 Novo Produto", "🧮Nova Venda"])

    with tab1:
        st.markdown("### Cadastro de Cliente")

        nome = st.text_input("Nome completo")
        cpf = st.text_input("CPF (somente números)")
        email = st.text_input("E-mail")
        telefone = st.text_input("Telefone (com DDD)")

        if st.button("Salvar Cliente"):
            if nome and cpf:
                try:
                    with engine.begin() as conn:
                        conn.execute(
                            text("""
                                INSERT INTO tbDCliente (nome, cpf, email, telefone)
                                VALUES (:nome, :cpf, :email, :telefone)
                            """),
                            {
                                "nome": nome,
                                "cpf": cpf,
                                "email": email,
                                "telefone": telefone
                            }
                        )
                    st.success("Cliente cadastrado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar cliente: {e}")
            else:
                st.warning("Nome e CPF são obrigatórios.")

    with tab2:
        st.markdown("### Cadastro de Produto")

        descricao = st.text_input("Descrição do produto")
        preco = st.number_input("Preço (R$)", min_value=0.0, format="%.2f")
        garantia = st.number_input("Garantia (em meses)", min_value=0)

        if st.button("Salvar Produto"):
            if descricao and preco > 0 and garantia > 0:
                try:
                    with engine.begin() as conn:
                        conn.execute(
                            text("""
                                INSERT INTO tbDProduto (descricao, preco, garantia_meses)
                                VALUES (:descricao, :preco, :garantia)
                            """),
                            {
                                "descricao": descricao,
                                "preco": preco,
                                "garantia": garantia
                            }
                        )
                    st.success("Produto cadastrado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar produto: {e}")
            else:
                st.warning("Todos os campos são obrigatórios.")

    with tab3:
        st.markdown("### Registro de Venda")

        # 🔄 Buscar clientes e produtos disponíveis
        try:
            clientes = pd.read_sql("SELECT id_cliente, nome FROM tbDCliente", engine)
            produtos = pd.read_sql("SELECT id_produto, descricao, preco FROM tbDProduto", engine)
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
            st.stop()

        # 🔘 Campos de entrada
        cliente_selecionado = st.selectbox("Cliente:", clientes["nome"].tolist())
        produto_selecionado = st.selectbox("Produto:", produtos["descricao"].tolist())
        quantidade = st.number_input("Quantidade:", min_value=1, value=1)
        forma_pagamento = st.selectbox("Forma de pagamento:", ["cartao", "pix", "cartao/parcelado", "dinheiro"])
        parcelas = st.number_input("Parcelas:", min_value=1, value=1 if forma_pagamento == "cartao/parcelado" else 1)
        data_venda = st.date_input("Data da venda:", value=date.today())

        # 🧮 Calcular subtotal
        preco_produto = produtos[produtos["descricao"] == produto_selecionado]["preco"].values[0]
        subtotal = preco_produto * quantidade
        st.warning(f"Subtotal: R$ {subtotal:.2f}")                   
        if st.button("Salvar Venda"):
            try:
                with engine.begin() as conn:
                    # 1️⃣ Inserir na tbFVenda
                    id_cliente = int(clientes[clientes["nome"] == cliente_selecionado]["id_cliente"].values[0])
                    venda_result = conn.execute(
                        text("""
                            INSERT INTO tbFVenda (data_venda, id_cliente)
                            VALUES (:data_venda, :id_cliente)
                        """),
                        {"data_venda": data_venda, "id_cliente": id_cliente}
                    )

                    # Recuperar o id_venda gerado
                    id_venda = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()

                    # 2️⃣ Inserir na tbFItemvenda
                    id_produto = int(produtos[produtos["descricao"] == produto_selecionado]["id_produto"].values[0])
                    conn.execute(
                        text("""
                            INSERT INTO tbFItemvenda (id_venda, id_produto, quantidade, subtotal)
                            VALUES (:id_venda, :id_produto, :quantidade, :subtotal)
                        """),
                        {
                            "id_venda": id_venda,
                            "id_produto": id_produto,
                            "quantidade": quantidade,
                            "subtotal": subtotal
                        }
                    )

                    # 3️⃣ Inserir na tbDPagamento
                    conn.execute(
                        text("""
                            INSERT INTO tbDPagamento (id_venda, forma_pagamento, valor_pago, parcelas)
                            VALUES (:id_venda, :forma_pagamento, :valor_pago, :parcelas)
                        """),
                        {
                            "id_venda": id_venda,
                            "forma_pagamento": forma_pagamento,
                            "valor_pago": subtotal,
                            "parcelas": parcelas
                        }
                    )

                st.success(f"Venda registrada com sucesso! Total: R$ {subtotal:.2f}")
            except Exception as e:
                st.error(f"Erro ao registrar venda: {e}")

elif menu == "Relatório Power BI":
    tab1, tab2 = st.tabs(["📊 PowerBi", "📊 PDF"])

    with tab1:
        st.subheader("📊 Relatório Integrado - Power BI")
        powerbi_url = "https://app.powerbi.com/view?r=eyJrIjoiOTM0NWQ5N2MtYjIxZS00MmNlLThiZTktNzUxNGYxOTI1ZWRlIiwidCI6IjY1OWNlMmI4LTA3MTQtNDE5OC04YzM4LWRjOWI2MGFhYmI1NyJ9"
        st.components.v1.iframe(powerbi_url, height=600, scrolling=True)
    with tab2:
        st.subheader("📄 Relatório em PDF - Power BI")
        url_pdf = "https://drive.google.com/file/d/15I8BLEJND8BJAO6HhjSOlz0J3WCeuZ0p/view?usp=sharing"
        exibir_pdf_via_url(url_pdf)


