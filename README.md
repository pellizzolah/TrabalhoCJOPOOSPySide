# Sistema de Cadastro de Clientes

## O que ele faz

- Cadastra, edita, lista e exclui clientes (CRUD completo)
- Valida CPF de verdade (com o cálculo dos dígitos verificadores, não só o tamanho)
- Valida e-mail e bloqueia CPF/e-mail duplicado
- Busca o endereço automaticamente pelo CEP (usando a API do ViaCEP)
- Tem tema claro e escuro, e lembra qual você escolheu na próxima vez
- Exporta a lista pra PDF (e respeita o filtro que você aplicou)
- Tem atalhos de teclado pra ficar mais rápido


## Tecnologias

- **Python 3.10+**
- **PySide6** — pra interface gráfica
- **SQLite** — banco de dados (não precisa instalar nada, já vem no Python)
- **Requests** — pra buscar o CEP
- **ReportLab** — pra gerar o PDF



## Como rodar

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/sistema-cadastro.git
cd sistema-cadastro
