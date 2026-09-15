# 📋 Sistema de Cadastro de Clientes

Um sistema desktop completo para gestão de clientes, desenvolvido em **Python** com **PySide6** (Qt for Python) e banco de dados **SQLite**. Possui interface moderna com suporte a temas (claro/escuro), validações robustas e exportação de relatórios em PDF.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-6.x-green?logo=qt&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3.x-lightgrey?logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Funcionalidades

### 🗂️ CRUD Completo
- **Create** — Cadastro de novos clientes com validação
- **Read** — Listagem em tabela com filtro dinâmico
- **Update** — Edição via botão ou duplo clique na linha
- **Delete** — Exclusão com confirmação

### 🔍 Validações Inteligentes
- ✅ **CPF** validado matematicamente (algoritmo oficial dos dígitos verificadores)
- ✅ **E-mail** verificado com expressão regular
- ✅ **CPF e E-mail duplicados** bloqueados automaticamente
- ✅ Campos obrigatórios destacados em vermelho

### 📍 Busca Automática de CEP
- Integração com a API pública **ViaCEP**
- Preenchimento automático de **Logradouro**, **Bairro**, **Cidade** e **Estado**
- Mensagem detalhada informando quais campos foram preenchidos

### 🎨 Interface Moderna
- **Tema Escuro** e **Tema Claro** com alternância instantânea
- **Memória de preferências:** salva o tema e o tamanho da janela entre sessões
- Layout responsivo com QGridLayout
- Barra de status com contador de registros visíveis

### 📄 Exportação para PDF
- Gera relatório em **A4 paisagem** com os dados da tabela
- **Respeita o filtro ativo** (exporta apenas o que está visível)
- Cabeçalho colorido e linhas zebradas para facilitar a leitura
- Nome do arquivo inclui a data de geração

### ⌨️ Atalhos de Teclado
| Atalho | Ação |
|--------|------|
| `Ctrl + S` | Salvar cliente |
| `Ctrl + L` | Limpar formulário |
| `Ctrl + P` | Exportar PDF |
| `Delete` | Excluir cliente selecionado |
| `F5` | Atualizar lista |

---

## 🛠️ Tecnologias Utilizadas

| Biblioteca | Uso |
|------------|-----|
| [**PySide6**](https://pypi.org/project/PySide6/) | Interface gráfica (Qt for Python) |
| [**SQLite3**](https://docs.python.org/3/library/sqlite3.html) | Banco de dados local |
| [**Requests**](https://pypi.org/project/requests/) | Consulta de CEP na API ViaCEP |
| [**ReportLab**](https://pypi.org/project/reportlab/) | Geração de relatórios em PDF |

---

## 🚀 Como Executar

### Pré-requisitos
- Python **3.10** ou superior
- Pip atualizado

### Instalação

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/seu-usuario/sistema-cadastro.git
   cd sistema-cadastro
