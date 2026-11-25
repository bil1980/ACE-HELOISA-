PAINEL DE VENDAS E ESTOQUE - COMO EXECUTAR

1. Extraia todos os arquivos deste ZIP para uma pasta.
2. Instale Python 3.10 ou superior.
3. Abra a pasta no VS Code.
4. No terminal, instale as dependências:
   pip install -r requirements.txt
5. Execute:
   streamlit run app.py
6. O navegador abrirá o painel automaticamente.

PLANILHAS
- Os dois arquivos Excel incluídos já estão configurados como arquivos padrão.
- Se preferir, envie outras planilhas .xlsx pela barra lateral do aplicativo.
- Não renomeie as abas/colunas sem ajustar o código.

PAINÉIS
- Vendas: receita, pedidos, valor médio por pedido, evolução mensal, categorias,
  produtos com maior receita e formas de pagamento.
- Estoque: materiais que precisam de reposição, valor estimado em estoque,
  consumo por categoria e evolução histórica.

Observação: os períodos das planilhas são diferentes. O painel os apresenta
separadamente para evitar comparações temporais incorretas.
