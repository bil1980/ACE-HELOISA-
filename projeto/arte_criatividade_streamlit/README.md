# Arte e Criatividade — Painel de Inteligência de Dados

Consulta de vendas, posição de estoque e planejamento de compras do ateliê.

## Como executar no Windows
1. Extraia todo o ZIP (não abra o BAT dentro do arquivo compactado).
2. Abra a pasta extraída e execute `INICIAR_WINDOWS.bat`. É necessário Python 3.10+ e acesso à internet na primeira instalação.
3. O navegador abrirá o painel, normalmente em http://localhost:8501. Mantenha o terminal aberto durante o uso.

Alternativa pelo terminal do VS Code, sem ativar a venv:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Para encerrar, use Ctrl+C no terminal. A pasta `dados` contém as planilhas históricas de vendas e estoque. Não precisa importar as bases manualmente. Para publicar no Streamlit Community Cloud, envie a pasta para um repositório GitHub (sem a `.venv`), selecione `app.py` como arquivo principal e use Python compatível.

## Áreas do painel
- Visão geral: indicadores, produtos líderes e status de estoque.
- Vendas: evolução mensal, rankings, formas de pagamento.
- Estoque: ponto de reposição, alertas históricos, consumo e previsão, evolução individual.
- Planejamento: prioridades de reposição e exportação da lista de compras.
- Fontes e critérios: cobertura, fontes e limitações.

## Atenção
Vendas (2016–2018) e estoque (2022–2024) são bases reduzidas, de períodos distintos. Os rótulos de produtos e materiais de vendas foram adaptados por IA segundo o relatório. O painel não representa a situação atual confirmada do negócio. Os indicadores de faturamento não são lucro; a previsão já existe na planilha; a sugestão de compra é um cenário sem novas entradas e deve ser validada pela artesã. O saldo é obtido do último registro de cada material dentro do filtro, não por soma de saldos históricos. Os números são recalculados a partir das planilhas incluídas, não dos totais dos relatórios.
