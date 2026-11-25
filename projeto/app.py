import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Painel de Vendas e Estoque",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Painel de Vendas e Estoque")
st.caption("Visão gerencial para acompanhar desempenho comercial e materiais.")

# Paleta e formatação
MOEDA = "R$"
def moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def carregar_excel(upload, nome_padrao, sheet_name=0):
    """Lê o arquivo enviado ou procura o arquivo padrão na pasta do app."""
    if upload is not None:
        return pd.read_excel(upload, sheet_name=sheet_name)
    caminho = Path(__file__).parent / nome_padrao
    if caminho.exists():
        return pd.read_excel(caminho, sheet_name=sheet_name)
    return None

def validar_colunas(df, colunas, nome):
    faltantes = [c for c in colunas if c not in df.columns]
    if faltantes:
        st.error(f"O arquivo de {nome} não possui as colunas necessárias: {', '.join(faltantes)}")
        return False
    return True

with st.sidebar:
    st.header("📁 Dados")
    st.write("Envie as planilhas Excel ou deixe os arquivos na mesma pasta deste aplicativo.")
    vendas_upload = st.file_uploader("Planilha de vendas (.xlsx)", type=["xlsx"], key="vendas")
    estoque_upload = st.file_uploader("Planilha de estoque (.xlsx)", type=["xlsx"], key="estoque")
    st.divider()
    st.caption("Os filtros de cada painel ficam dentro da respectiva aba.")

vendas = carregar_excel(vendas_upload, "vendas_organizadas_reduzida (1).xlsx", "Vendas")
estoque = carregar_excel(estoque_upload, "estoque_materiais_final_reduzido.xlsx", 0)

aba_vendas, aba_estoque, aba_orientacoes = st.tabs(["💰 Vendas", "📦 Estoque", "ℹ️ Sobre os indicadores"])

with aba_vendas:
    st.subheader("Desempenho de vendas")
    if vendas is None:
        st.info("Envie a planilha de vendas na barra lateral ou coloque o arquivo padrão na pasta do aplicativo.")
    elif validar_colunas(vendas, ["id_venda", "id_produto", "categoria_produto", "material",
                                  "valor_rs", "forma_pagamento", "data_venda", "venda_incompleta"], "vendas"):
        df = vendas.copy()
        df["data_venda"] = pd.to_datetime(df["data_venda"], errors="coerce")
        df["valor_rs"] = pd.to_numeric(df["valor_rs"], errors="coerce").fillna(0)
        df = df.dropna(subset=["data_venda"])

        if df.empty:
            st.warning("Não há registros de vendas com datas válidas.")
        else:
            c1, c2 = st.columns(2)
            data_min, data_max = df["data_venda"].dt.date.min(), df["data_venda"].dt.date.max()
            with c1:
                periodo = st.date_input("Período das vendas", value=(data_min, data_max),
                                        min_value=data_min, max_value=data_max)
            with c2:
                categorias = sorted(df["categoria_produto"].dropna().astype(str).unique())
                categorias_sel = st.multiselect("Categorias", categorias, default=categorias)

            if isinstance(periodo, (tuple, list)) and len(periodo) == 2:
                inicio, fim = periodo
            else:
                inicio, fim = data_min, data_max

            filtrado = df[
                (df["data_venda"].dt.date >= inicio) &
                (df["data_venda"].dt.date <= fim) &
                (df["categoria_produto"].astype(str).isin(categorias_sel))
            ].copy()

            if filtrado.empty:
                st.warning("Nenhum registro corresponde aos filtros selecionados.")
            else:
                receita = filtrado["valor_rs"].sum()
                pedidos = filtrado["id_venda"].nunique()
                itens = len(filtrado)
                ticket = receita / pedidos if pedidos else 0
                incompletas = filtrado["venda_incompleta"].astype(str).str.lower().isin(["sim", "yes", "true"]).sum()

                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Receita registrada", moeda(receita))
                k2.metric("Pedidos", f"{pedidos:,}".replace(",", "."))
                k3.metric("Itens/linhas", f"{itens:,}".replace(",", "."))
                k4.metric("Valor médio por pedido", moeda(ticket))
                st.caption(f"Registros marcados como venda incompleta: {incompletas}")

                mensal = (filtrado.set_index("data_venda").resample("MS")["valor_rs"]
                          .sum().reset_index())
                mensal["mês"] = mensal["data_venda"].dt.strftime("%m/%Y")
                por_categoria = (filtrado.groupby("categoria_produto", as_index=False)["valor_rs"]
                                 .sum().sort_values("valor_rs", ascending=False))
                por_produto = (filtrado.groupby(["id_produto", "categoria_produto", "material"], as_index=False)
                               .agg(receita=("valor_rs", "sum"),
                                    linhas=("id_venda", "size"),
                                    pedidos=("id_venda", "nunique"))
                               .sort_values("receita", ascending=False))
                por_pagamento = (filtrado.groupby("forma_pagamento", as_index=False)
                                 .agg(receita=("valor_rs", "sum"),
                                      pedidos=("id_venda", "nunique")))

                esquerda, direita = st.columns(2)
                with esquerda:
                    st.markdown("#### Receita ao longo do tempo")
                    fig = px.line(mensal, x="mês", y="valor_rs", markers=True,
                                  labels={"mês": "Mês", "valor_rs": "Receita (R$)"})
                    fig.update_layout(xaxis_title="", yaxis_title="Receita (R$)")
                    st.plotly_chart(fig, use_container_width=True)
                with direita:
                    st.markdown("#### Receita por categoria")
                    fig = px.bar(por_categoria, x="categoria_produto", y="valor_rs",
                                 labels={"categoria_produto": "Categoria", "valor_rs": "Receita (R$)"},
                                 text_auto=".2s")
                    fig.update_layout(xaxis_title="", yaxis_title="Receita (R$)")
                    st.plotly_chart(fig, use_container_width=True)

                esquerda, direita = st.columns(2)
                with esquerda:
                    st.markdown("#### Produtos com maior receita")
                    top = por_produto.head(10).sort_values("receita", ascending=True)
                    fig = px.bar(top, x="receita", y="id_produto", orientation="h",
                                 hover_data=["categoria_produto", "material", "pedidos"],
                                 labels={"receita": "Receita (R$)", "id_produto": "Produto"})
                    st.plotly_chart(fig, use_container_width=True)
                with direita:
                    st.markdown("#### Formas de pagamento")
                    fig = px.pie(por_pagamento, names="forma_pagamento", values="receita",
                                 hole=0.45, hover_data=["pedidos"])
                    st.plotly_chart(fig, use_container_width=True)

                st.markdown("#### Ranking de produtos")
                tabela = por_produto.copy()
                tabela["receita"] = tabela["receita"].map(moeda)
                st.dataframe(tabela.rename(columns={
                    "id_produto": "ID do produto",
                    "categoria_produto": "Categoria",
                    "material": "Material",
                    "receita": "Receita",
                    "linhas": "Itens registrados",
                    "pedidos": "Pedidos"
                }), use_container_width=True, hide_index=True)

                csv = filtrado.to_csv(index=False).encode("utf-8-sig")
                st.download_button("⬇️ Baixar vendas filtradas (CSV)", csv,
                                   "vendas_filtradas.csv", "text/csv")

with aba_estoque:
    st.subheader("Acompanhamento de materiais")
    if estoque is None:
        st.info("Envie a planilha de estoque na barra lateral ou coloque o arquivo padrão na pasta do aplicativo.")
    elif validar_colunas(estoque, ["data", "id_material", "categoria", "estoque_atual",
                                   "unidades_usadas", "unidades_compradas", "previsao_consumo",
                                   "preco_unitario_rs", "ponto_reposicao", "precisa_repor",
                                   "estoque_final_estimado"], "estoque"):
        inv = estoque.copy()
        inv["data"] = pd.to_datetime(inv["data"], errors="coerce")
        numericas = ["estoque_atual", "unidades_usadas", "unidades_compradas",
                     "previsao_consumo", "preco_unitario_rs", "ponto_reposicao",
                     "estoque_final_estimado"]
        for col in numericas:
            inv[col] = pd.to_numeric(inv[col], errors="coerce")
        inv = inv.dropna(subset=["data"])

        if inv.empty:
            st.warning("Não há registros de estoque com datas válidas.")
        else:
            datas = sorted(inv["data"].dt.date.unique())
            data_escolhida = st.select_slider("Data de referência", options=datas, value=datas[-1],
                                               format_func=lambda d: d.strftime("%d/%m/%Y"))
            categorias_inv = sorted(inv["categoria"].dropna().astype(str).unique())
            categorias_inv_sel = st.multiselect("Categorias de materiais", categorias_inv,
                                                default=categorias_inv, key="cat_inv")
            atual = inv[inv["data"].dt.date == data_escolhida].copy()
            atual = atual[atual["categoria"].astype(str).isin(categorias_inv_sel)]

            if atual.empty:
                st.warning("Nenhum material encontrado para essa data e filtros.")
            else:
                atual["valor_em_estoque"] = atual["estoque_atual"] * atual["preco_unitario_rs"]
                precisa = atual["precisa_repor"].astype(str).str.strip().str.lower().isin(["sim", "yes", "true"])
                quantidade_repor = int(precisa.sum())
                valor_total = atual["valor_em_estoque"].sum()
                consumo = atual["unidades_usadas"].sum()
                materiais = atual["id_material"].nunique()

                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Materiais monitorados", materiais)
                k2.metric("Precisam de reposição", quantidade_repor)
                k3.metric("Valor estimado em estoque", moeda(valor_total))
                k4.metric("Unidades consumidas no período", f"{consumo:,.0f}".replace(",", "."))

                esquerda, direita = st.columns(2)
                resumo_cat = (atual.groupby("categoria", as_index=False)
                              .agg(estoque=("estoque_atual", "sum"),
                                   consumo=("unidades_usadas", "sum")))
                with esquerda:
                    st.markdown("#### Estoque atual por categoria")
                    fig = px.bar(resumo_cat, x="categoria", y="estoque",
                                 labels={"categoria": "Categoria", "estoque": "Unidades em estoque"})
                    st.plotly_chart(fig, use_container_width=True)
                with direita:
                    st.markdown("#### Consumo por categoria")
                    fig = px.bar(resumo_cat, x="categoria", y="consumo",
                                 labels={"categoria": "Categoria", "consumo": "Unidades usadas"})
                    st.plotly_chart(fig, use_container_width=True)

                st.markdown("#### Materiais que precisam de reposição")
                lista_repor = atual[precisa].sort_values("estoque_atual")
                if lista_repor.empty:
                    st.success("Nenhum material está marcado para reposição nesta data.")
                else:
                    st.dataframe(lista_repor[["id_material", "categoria", "estoque_atual",
                                              "ponto_reposicao", "previsao_consumo",
                                              "estoque_final_estimado"]].rename(columns={
                        "id_material": "ID material", "categoria": "Categoria",
                        "estoque_atual": "Estoque atual", "ponto_reposicao": "Ponto de reposição",
                        "previsao_consumo": "Previsão de consumo",
                        "estoque_final_estimado": "Estoque final estimado"
                    }), use_container_width=True, hide_index=True)

                historico = inv[inv["categoria"].astype(str).isin(categorias_inv_sel)]
                evolucao = (historico.groupby("data", as_index=False)
                            .agg(estoque=("estoque_atual", "sum"),
                                 consumo=("unidades_usadas", "sum")))
                st.markdown("#### Evolução do estoque e consumo")
                metrica = st.radio("Indicador do histórico", ["Estoque atual", "Unidades usadas"],
                                   horizontal=True)
                coluna = "estoque" if metrica == "Estoque atual" else "consumo"
                fig = px.line(evolucao, x="data", y=coluna, markers=True,
                              labels={"data": "Data", coluna: metrica})
                st.plotly_chart(fig, use_container_width=True)

                tabela_inv = atual.copy()
                tabela_inv["valor_em_estoque"] = tabela_inv["valor_em_estoque"].map(moeda)
                st.markdown("#### Posição detalhada do estoque")
                st.dataframe(tabela_inv.rename(columns={
                    "id_material": "ID material", "categoria": "Categoria",
                    "estoque_atual": "Estoque atual", "unidades_usadas": "Unidades usadas",
                    "unidades_compradas": "Unidades compradas",
                    "previsao_consumo": "Previsão de consumo",
                    "preco_unitario_rs": "Preço unitário (R$)",
                    "ponto_reposicao": "Ponto de reposição",
                    "precisa_repor": "Precisa repor?",
                    "estoque_final_estimado": "Estoque final estimado",
                    "valor_em_estoque": "Valor em estoque"
                }), use_container_width=True, hide_index=True)

                csv_inv = atual.to_csv(index=False).encode("utf-8-sig")
                st.download_button("⬇️ Baixar posição do estoque (CSV)", csv_inv,
                                   "posicao_estoque.csv", "text/csv")

with aba_orientacoes:
    st.subheader("Como interpretar este painel")
    st.markdown("""
    **Vendas**
    - **Receita registrada:** soma dos valores das linhas de venda dentro do período e das categorias escolhidas.
    - **Pedidos:** quantidade de identificadores de venda únicos (`id_venda`). Um pedido pode ter mais de um item.
    - **Itens/linhas:** quantidade de registros considerados na planilha.
    - **Valor médio por pedido:** receita dividida pela quantidade de pedidos únicos.
    - **Produtos com maior receita:** ranking calculado pela soma de `valor_rs` por produto.

    **Estoque**
    - **Data de referência:** posição dos materiais na data selecionada.
    - **Precisam de reposição:** materiais marcados como “Sim” na coluna `precisa_repor`.
    - **Valor estimado em estoque:** estoque atual multiplicado pelo preço unitário informado.
    - **Evolução:** soma dos valores registrados por data para os materiais selecionados.

    **Atenção:** os arquivos abrangem períodos diferentes (vendas em 2016–2018 e estoque em 2022–2024).
    Portanto, os painéis são apresentados separadamente e não representam uma relação temporal direta.
    Os indicadores refletem os dados das planilhas, não uma previsão independente.
    """)
    st.caption("Aplicativo demonstrativo. Confira os critérios internos da empresa antes de usar os números para decisões financeiras ou compras.")
