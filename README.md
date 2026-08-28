# TrabalhoCJOPOOSPyQt6
Sistema de Cadastro de Pessoas - PySide6

Aplicação desktop para cadastro de pessoas com validação, integração com API ViaCEP e banco de dados SQLite.

 Funcionalidades

- Formulário completo com campos para nome, CPF/CNPJ, e-mail, celular, CEP, endereço.
- Validações:
  - Campos obrigatórios.
  - CPF e CNPJ (algoritmos de verificação).
  - Formato de e-mail.
  - Formato de celular e CEP.
- Consulta automática de CEP via API ViaCEP, preenchendo logradouro, bairro, cidade e estado.
- CRUD completo:
  - Cadastrar novos registros.
  - Editar registros existentes (clique em "Editar" na tabela).
  - Excluir registros.
- Pesquisapor nome, CPF ou e-mail.
- Máscaras nos campos CPF/CNPJ, celular e CEP para melhor experiência do usuário.
- Feedback claro com mensagens específicas sobre erros.

Como executar

1. Instale as dependências:
   pip install pyside6 requests
2. Rode o programa e seja feliz 😁😊
