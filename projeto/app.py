from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from analise import carregar, vendas_resumo, ultimo_estoque, brl, inteiro

st.set_page_config(page_title='Arte e Criatividade | Painel de decisões', page_icon=':material/storefront:', layout='wide')
TERRA = '#AC4D30'
VERDE = '#246255'
OURO = '#B78731'
VERMELHO = '#A3383F'
STATUS={'Repor agora':VERMELHO,'Planejar compra':OURO,'Monitorar':VERDE}
MESES=['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez']

stylesheet = Path(__file__).with_name("estilo.css").read_text(encoding="utf-8")
st.markdown(f"<style>{stylesheet}</style>", unsafe_allow_html=True)

@st.cache_data
def bases():
    return carregar()

def graf(fig, height=360, key=None, **kw):
    fig.update_layout(template='plotly_white', height=height, margin=dict(l=12,r=20,t=20,b=12),
                      font=dict(family='Trebuchet MS, sans-serif',color='#233d38',size=13), paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)', legend_title_text='', **kw)
    fig.update_xaxes(showgrid=False, automargin=True)
    fig.update_yaxes(gridcolor='#e4dfd2', automargin=True)
    st.plotly_chart(fig, key=key, theme=None, use_container_width=True, config={'displaylogo':False,'locale':'pt-BR'})

def barras(d, x, y, labels, cor=TERRA, moeda=False, key=None):
    d=d.sort_values(x)
    fig=px.bar(d,x=x,y=y,orientation='h',labels=labels,color_discrete_sequence=[cor],text=x)
    fig.update_traces(texttemplate=('R$ %{x:,.2f}' if moeda else '%{x:,.0f}'),textposition='auto',cliponaxis=False)
    fig.update_layout(separators=',.')
    graf(fig, height=max(280, 45*len(d)+65), key=key)

def filtrar_data(df,col,periodo):
    if not isinstance(periodo,(tuple,list)) or len(periodo)!=2:
        return df.iloc[0:0]
    a,b=map(pd.Timestamp,periodo)
    return df[df[col].ge(a) & df[col].lt(b+pd.Timedelta(days=1))]

try:
    v0,e0=bases()
except Exception as exc:
    st.error(f'Não foi possível abrir as planilhas da pasta dados: {exc}')
    st.stop()

with st.sidebar:
    st.markdown('## Filtros do painel')
    st.markdown('### Vendas')
    pv=st.date_input('Período das vendas', (v0.data_venda.min().date(),v0.data_venda.max().date()), min_value=v0.data_venda.min().date(),max_value=v0.data_venda.max().date(),format='DD/MM/YYYY')
    cat=st.multiselect('Produtos', sorted(v0.categoria_produto.unique()), placeholder='Todos os produtos')
    pag=st.multiselect('Pagamento',sorted(v0.forma_pagamento.unique()),placeholder='Todas as formas')
    excluir=st.checkbox('Excluir vendas sinalizadas como incompletas',value=False)
    st.divider()
    st.markdown('### Estoque')
    pe=st.date_input('Período de estoque',(e0.data.min().date(),e0.data.max().date()),min_value=e0.data.min().date(),max_value=e0.data.max().date(),format='DD/MM/YYYY')
    ce=st.multiselect('Categorias de materiais',sorted(e0.categoria.unique()),placeholder='Todas as categorias')
    st.caption('Os períodos são independentes. Vendas e estoque não representam o mesmo intervalo histórico.')


v=filtrar_data(v0,'data_venda',pv).copy()
if cat: v=v[v.categoria_produto.isin(cat)]
if pag: v=v[v.forma_pagamento.isin(pag)]
if excluir: v=v[~v.id_venda.isin(v0.loc[v0.venda_incompleta.str.lower().eq('sim'),'id_venda'])]
e=filtrar_data(e0,'data',pe).copy()
if ce: e=e[e.categoria.isin(ce)]
r=vendas_resumo(v)
s=ultimo_estoque(e)
fat=v.valor_rs.sum(); pedidos=v.id_venda.nunique()
crit=int(s.critico.sum()); planejar=int(s.status.eq('Planejar compra').sum())

st.markdown(
    '<header class="capa"><div class="trama" aria-hidden="true"></div>'
    '<h1>Arte e Criatividade</h1>'
    '<p>Gestão de vendas e materiais</p></header>',
    unsafe_allow_html=True,
)

visao,tv,te,ta,tm=st.tabs(['Visão geral','Vendas e produtos','Estoque e consumo','Planejamento','Fontes e critérios'])

with visao:
    st.caption(f'Histórico selecionado · Vendas {pv[0]:%d/%m/%Y} – {pv[1]:%d/%m/%Y}  |  Estoque {pe[0]:%d/%m/%Y} – {pe[1]:%d/%m/%Y}'
               if len(pv) == len(pe) == 2 else 'Selecione a data inicial e a data final de cada período.')
    a,b,c,d=st.columns(4)
    a.metric('Faturamento registrado',brl(fat),help='Soma do valor dos itens filtrados; não representa lucro.')
    b.metric('Itens registrados',inteiro(len(v)))
    c.metric('Vendas identificadas',inteiro(pedidos),help='Contagem distinta dos IDs de venda no recorte.')
    d.metric('Materiais em reposição',f'{crit} de {len(s)}',help='Último registro de cada material no período selecionado.')
    l,h=st.columns(2)
    with l:
        st.markdown('#### Produtos que mais faturaram')
        if not r.empty:
            barras(r.head(5),'faturamento','categoria_produto',{'faturamento':'Faturamento (R$)','categoria_produto':'Produto'},moeda=True,key='receita_visao_geral')
            top=r.iloc[0]
            st.caption(f"{top.categoria_produto} responde por {brl(top.faturamento)} no período selecionado.")
        else: st.warning('Nenhuma venda no recorte.')
    with h:
        st.markdown('#### Situação dos materiais')
        if not s.empty:
            ct=s.status.value_counts().reindex(list(STATUS),fill_value=0).rename_axis('status').reset_index(name='materiais')
            fig=px.pie(ct,names='status',values='materiais',hole=.65,color='status',color_discrete_map=STATUS)
            fig.update_traces(textinfo='value', textposition='inside', sort=False,
                              marker_line=dict(color='#fffcf6', width=3),
                              hovertemplate='%{label} · %{value} materiais<extra></extra>')
            fig.add_annotation(text=f'<b>{len(s)}</b><br>materiais', showarrow=False,
                               x=.5, y=.5, font=dict(family='Georgia',size=19,color='#173e38'))
            graf(fig,320,legend=dict(orientation='h',x=.5,xanchor='center',y=-.04))
            st.caption(f'Última data do recorte: {s.data.max():%d/%m/%Y}.')

        else: st.warning('Nenhum registro de estoque no recorte.')

with tv:
    st.subheader('Desempenho comercial')
    if v.empty: st.warning('Nenhuma venda encontrada. Ajuste os filtros.')
    else:
        a,b,c=st.columns(3)
        a.metric('Faturamento dos itens',brl(fat)); b.metric('Valor médio por item',brl(fat/len(v))); c.metric('Valor registrado por venda',brl(fat/pedidos),help='Não é necessariamente o ticket completo, pois a base é reduzida e pode conter apenas parte dos itens.')
        m=v.assign(mes=v.data_venda.dt.to_period('M').dt.to_timestamp()).groupby('mes',as_index=False).agg(faturamento=('valor_rs','sum'),itens=('item','size'))
        st.markdown('#### Evolução mensal do faturamento registrado')
        st.caption('Somente meses com vendas registradas; lacunas não são interpretadas como vendas zero.')
        fig=px.line(m,x='mes',y='faturamento',markers=True,labels={'mes':'Mês','faturamento':'Faturamento (R$)'},color_discrete_sequence=[TERRA]); fig.update_yaxes(tickprefix='R$ '); graf(fig,340)
        a,b=st.columns(2)
        with a:
            st.markdown('#### Ranking por faturamento')
            barras(r,'faturamento','categoria_produto',{'faturamento':'Faturamento (R$)','categoria_produto':'Produto'},moeda=True)
        with b:
            st.markdown('#### Ranking por quantidade de itens')
            barras(r,'itens','categoria_produto',{'itens':'Itens registrados','categoria_produto':'Produto'},VERDE)
        a,b=st.columns(2)
        with a:
            st.markdown('#### Formas de pagamento')
            pg=v.groupby('forma_pagamento',as_index=False).valor_rs.sum()
            fig=px.pie(pg,names='forma_pagamento',values='valor_rs',hole=.55,color_discrete_sequence=[VERDE,OURO]); fig.update_traces(textinfo='label+percent'); graf(fig,300,showlegend=False)
            st.caption('Percentual do faturamento por forma de pagamento.')
        with b:
            st.markdown('#### Concentração das vendas')
            top=r.head(2).faturamento.sum()/fat
            st.metric('Participação dos dois líderes',f'{top:.1%}'.replace('.', ','))
            st.caption(' + '.join(r.head(2).categoria_produto) + ' · ' + brl(r.head(2).faturamento.sum()))
        st.download_button('Baixar resumo de vendas (CSV)',r.to_csv(index=False,sep=';',decimal=',').encode('utf-8-sig'),'resumo_vendas.csv','text/csv')

with te:
    st.subheader('Posição de estoque')
    if e.empty: st.warning('Nenhum registro encontrado. Ajuste os filtros.')
    else:
        a,b,c,d=st.columns(4)
        a.metric('Materiais acompanhados',len(s)); b.metric('Reposição imediata',crit); c.metric('Planejar compra',planejar); d.metric('Alertas no histórico',inteiro((e.estoque_atual<=e.ponto_reposicao).sum()),help='Ocorrências por data e material; o mesmo material pode aparecer diversas vezes.')
        st.markdown('#### Estoque disponível × ponto de reposição')
        st.caption('Último registro de cada material dentro do filtro. A barra de estoque abaixo ou igual ao limite indica reposição.')
        ords=s.sort_values(['prioridade','categoria','id_material'])
        fig=go.Figure(); fig.add_bar(name='Estoque registrado',x=ords.id_material,y=ords.estoque_atual,marker_color=ords.status.map(STATUS),customdata=ords[['categoria','status']],hovertemplate='%{x}<br>%{customdata[0]}<br>%{customdata[1]}<br>Estoque: %{y}<extra></extra>'); fig.add_scatter(name='Ponto de reposição',x=ords.id_material,y=ords.ponto_reposicao,mode='markers',marker=dict(color='#252D29',symbol='diamond',size=9),hovertemplate='Limite: %{y}<extra></extra>'); graf(fig,390,legend=dict(orientation='h',y=1.13))
        a,b=st.columns(2)
        with a:
            st.markdown('#### Frequência histórica de reposição por categoria')
            freq=e.assign(alerta=e.estoque_atual<=e.ponto_reposicao).groupby('categoria',as_index=False).agg(frequencia=('alerta','mean'))
            freq['frequencia']*=100
            fig=px.bar(freq.sort_values('frequencia'),x='frequencia',y='categoria',orientation='h',text='frequencia',color_discrete_sequence=[TERRA],labels={'frequencia':'Registros em alerta (%)','categoria':'Material'}); fig.update_traces(texttemplate='%{x:.1f}%',textposition='auto'); graf(fig,330)
        with b:
            st.markdown('#### Consumo registrado × previsão')
            st.caption('Soma por categoria no período; compare apenas unidades compatíveis dentro de cada categoria.')
            co=e.groupby('categoria',as_index=False).agg(Consumo=('unidades_usadas','sum'),Previsão=('previsao_consumo','sum'))
            fig=px.bar(co,x='categoria',y=['Consumo','Previsão'],barmode='group',color_discrete_sequence=[VERDE,OURO],labels={'value':'Unidades registradas','categoria':'Material'}); graf(fig,330)
        st.markdown('#### Evolução de um material')
        material=st.selectbox('Escolher material',sorted(e.id_material.unique()))
        hist=e[e.id_material.eq(material)].sort_values('data')
        fig=px.line(hist,x='data',y=['estoque_atual','ponto_reposicao','estoque_final_estimado'],labels={'data':'Data','value':'Unidades'},color_discrete_sequence=[VERDE,VERMELHO,OURO]); fig.for_each_trace(lambda t: t.update(name={'estoque_atual':'Estoque registrado','ponto_reposicao':'Ponto de reposição','estoque_final_estimado':'Saldo final estimado'}.get(t.name,t.name))); graf(fig,350,legend=dict(orientation='h',y=1.15))

with ta:
    st.subheader('Planejamento de compras')
    st.markdown('#### Necessidade de reposição')
    st.caption('Estimativa com preços históricos e sem novas entradas. Confira o saldo físico e o preço atual antes de comprar.')
    if s.empty: st.warning('Nenhum material no recorte.')
    else:
        a,b,c=st.columns(3); a.metric('Reposição imediata',crit); b.metric('Planejar compra',planejar); c.metric('Custo simulado',brl(s.custo_estimado.sum()),help='Compra sugerida multiplicada pelo preço unitário histórico do último registro.')
        st.markdown('##### Lista de prioridades')
        show_all=st.checkbox('Mostrar também materiais sem compra sugerida',value=False)
        lista=s if show_all else s[s.status.ne('Monitorar')]
        if lista.empty: st.success('Nenhum material em alerta no cenário selecionado.')
        else:
            cols={'id_material':'Material','categoria':'Categoria','data':'Data do saldo','status':'Prioridade','estoque_atual':'Estoque','ponto_reposicao':'Limite','consumo_arredondado':'Consumo previsto¹','saldo_projetado':'Saldo simulado','compra_sugerida':'Compra sugerida','custo_estimado':'Custo simulado (R$)'}
            tabela=lista[list(cols)].rename(columns=cols).copy(); tabela['Data do saldo']=tabela['Data do saldo'].dt.strftime('%d/%m/%Y')
            st.dataframe(tabela,hide_index=True,use_container_width=True,column_config={'Custo simulado (R$)':st.column_config.NumberColumn(format='R$ %.2f')})
            st.download_button('Baixar lista de compras (CSV)',tabela.to_csv(index=False,sep=';',decimal=',').encode('utf-8-sig'),'lista_compras.csv','text/csv')
        st.caption('¹ Previsão arredondada para cima. Compra sugerida = máximo de zero ou (limite + consumo previsto − estoque registrado). O cenário usa estoque_atual, sem adicionar as compras já registradas no período.')
        st.markdown('##### Materiais com maior necessidade simulada')
        if (s.compra_sugerida>0).any():
            ss=s[s.compra_sugerida>0].nlargest(10,'compra_sugerida').copy(); ss['material']=ss.id_material+' • '+ss.categoria
            barras(ss,'compra_sugerida','material',{'compra_sugerida':'Unidades sugeridas','material':'Material'},OURO)
    st.markdown('#### Produtos em destaque')
    if not r.empty:
        top=r.iloc[0]; qtd=r.sort_values('itens',ascending=False).iloc[0]
        st.write(f'**{top.categoria_produto}** lidera o faturamento ({brl(top.faturamento)}). **{qtd.categoria_produto}** lidera em quantidade ({qtd.itens} itens).')
    else: st.write('Ajuste o filtro de vendas para calcular prioridades.')

with tm:
    st.subheader('Cobertura dos dados')
    st.dataframe(pd.DataFrame([
        {'Fonte': 'Itens de vendas', 'Início': v0.data_venda.min().strftime('%d/%m/%Y'),
         'Fim': v0.data_venda.max().strftime('%d/%m/%Y'), 'Registros': inteiro(len(v0)),
         'Abrangência': f'{inteiro(v0.id_venda.nunique())} vendas'},
        {'Fonte': 'Movimentações de estoque', 'Início': e0.data.min().strftime('%d/%m/%Y'),
         'Fim': e0.data.max().strftime('%d/%m/%Y'), 'Registros': inteiro(len(e0)),
         'Abrangência': f'{e0.id_material.nunique()} materiais'},
    ]), hide_index=True, use_container_width=True)
    st.caption('As planilhas contêm amostras históricas de períodos distintos. '
               'Os nomes de produtos e materiais das vendas foram adaptados com apoio de IA.')
    st.markdown('#### Critérios dos indicadores')
    with st.expander('Faturamento e vendas', expanded=True):
        st.write('O faturamento soma os valores dos itens selecionados. Cada código de venda conta uma vez. '
                 'Uma venda pode ter apenas parte dos itens na amostra. A margem depende dos custos de produção, ausentes na base.')
    with st.expander('Estoque e reposição'):
        st.write('Cada material usa seu último saldo no período selecionado. Um saldo igual ou inferior ao limite exige reposição. '
                 'Se apenas o saldo projetado atingir esse limite, o material entra em planejamento.')
    with st.expander('Estimativa de compra'):
        st.write('A quantidade sugerida cobre o consumo previsto e recompõe o ponto de reposição. '
                 'O custo usa o preço unitário do último registro. A planilha fornece a previsão de consumo sem indicar seu horizonte.')
