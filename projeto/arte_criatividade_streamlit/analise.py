from pathlib import Path
import pandas as pd
import numpy as np

BASE = Path(__file__).resolve().parent / 'dados'

def carregar():
    v = pd.read_excel(BASE / 'vendas_organizadas_reduzida.xlsx')
    e = pd.read_excel(BASE / 'estoque_materiais_final_reduzido.xlsx')
    v['data_venda'] = pd.to_datetime(v['data_venda'], errors='raise')
    e['data'] = pd.to_datetime(e['data'], errors='raise')
    return v, e

def vendas_resumo(v):
    return (v.groupby('categoria_produto', as_index=False)
              .agg(itens=('item', 'size'), faturamento=('valor_rs', 'sum'))
              .sort_values('faturamento', ascending=False))

def ultimo_estoque(e):
    # Uma fotografia por material, nunca a soma dos saldos ao longo do tempo.
    s = e.sort_values('data').drop_duplicates('id_material', keep='last').copy()
    s['critico'] = s['estoque_atual'] <= s['ponto_reposicao']
    s['consumo_arredondado'] = np.ceil(s['previsao_consumo'].clip(lower=0)).astype(int)
    s['saldo_projetado'] = s['estoque_atual'] - s['consumo_arredondado']
    s['compra_sugerida'] = (s['ponto_reposicao'] + s['consumo_arredondado'] - s['estoque_atual']).clip(lower=0).astype(int)
    s['custo_estimado'] = s['compra_sugerida'] * s['preco_unitario_rs']
    s['status'] = np.select([s['critico'], s['saldo_projetado'] <= s['ponto_reposicao']], ['Repor agora', 'Planejar compra'], default='Monitorar')
    s['prioridade'] = s['status'].map({'Repor agora':0,'Planejar compra':1,'Monitorar':2})
    return s.sort_values(['prioridade','compra_sugerida'], ascending=[True,False])

def brl(x):
    return 'R$ ' + f'{x:,.2f}'.replace(',', '|').replace('.', ',').replace('|', '.')

def inteiro(x):
    return f'{int(x):,}'.replace(',', '.')
