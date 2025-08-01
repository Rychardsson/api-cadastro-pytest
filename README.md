# API de Cadastro e Login com FastAPI e Pytest

![CI de Testes Python](https://github.com/Rychardsson/api-cadastro-pytest/actions/workflows/ci.yml/badge.svg)

Este projeto é uma API REST simples, desenvolvida como um exercício prático para estudar os fundamentos do desenvolvimento backend com Python, focando em boas práticas como testes automatizados e integração contínua.

---

## 🚀 Funcionalidades

- ✅ **Cadastro de Usuários:** Endpoint para registrar novos usuários com `username` e `password`.
- 🔐 **Autenticação de Usuários:** Endpoint de login que valida as credenciais.
- 👤 **Busca de Usuário:** Endpoint para consultar os dados de um usuário pelo seu ID.
- 🛡️ **Segurança de Senhas:** As senhas são armazenadas de forma segura usando hashing com Bcrypt.
- 🧪 **Testes Automatizados:** Cobertura completa de testes com diferentes categorias e fixtures reutilizáveis.
- 🤖 **Integração Contínua (CI):** Um workflow com GitHub Actions roda os testes automaticamente a cada `push`, garantindo que novas alterações não quebrem o projeto.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3.11+
- **Framework Backend:** [FastAPI](https://fastapi.tiangolo.com/)
- **Servidor ASGI:** [Uvicorn](https://www.uvicorn.org/)
- **Testes:** [Pytest](https://docs.pytest.org/)
- **Segurança (Hashing):** [Passlib](https://passlib.readthedocs.io/en/stable/) com Bcrypt
- **Cliente HTTP para Testes:** [HTTPX](https://www.python-httpx.org/)
- **Validação de Dados:** [Pydantic](https://docs.pydantic.dev/)
- **CI/CD:** [GitHub Actions](https://github.com/features/actions)

---

## 🧪 Melhorias nos Testes

### Organização dos Testes

- **Classes de Teste:** Testes organizados em classes (`TestCadastro`, `TestLogin`, `TestUsuario`, etc.)
- **Constantes Centralizadas:** Dados de teste e mensagens de erro em constantes reutilizáveis
- **Fixtures Reutilizáveis:** Fixtures para usuários cadastrados e logados

### Categorias de Testes

- **🔧 Testes Unitários:** Testam funcionalidades individuais
- **🔗 Testes de Integração:** Testam fluxos completos da aplicação
- **⚡ Testes de Performance:** Testam múltiplas operações sequenciais
- **🎯 Edge Cases:** Testam casos extremos e situações especiais

### Marcadores Pytest

Use marcadores para executar categorias específicas de testes:

```bash
# Apenas testes de integração
pytest -m integration

# Apenas testes de performance
pytest -m performance

# Excluir testes lentos
pytest -m "not slow"
```

---

## ⚙️ Como Começar

Siga os passos abaixo para executar o projeto em seu ambiente local.

### Pré-requisitos

- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

### Instalação

1.  **Clone o repositório:**

    ```bash
    git clone https://github.com/Rychardsson/api-cadastro-pytest.git
    cd api-cadastro-pytest
    ```

2.  **Crie e ative um ambiente virtual:**

    - No Windows (PowerShell):

      ```powershell
      python -m venv venv
      .\venv\Scripts\Activate.ps1
      ```

    - No macOS/Linux:
      ```bash
      python3 -m venv venv
      source venv/bin/activate
      ```

3.  **Instale as dependências do projeto:**
    ```bash
    pip install -r requirements.txt
    ```

---

## 🏃‍♀️ Como Executar

### Rodando a Aplicação

Com as dependências instaladas, inicie o servidor de desenvolvimento com Uvicorn:

```bash
uvicorn main:app --reload
```

O servidor estará disponível em `http://127.0.0.1:8000`.

- Acesse `http://127.0.0.1:8000/docs` para ver a documentação interativa da API (Swagger UI).
- Acesse `http://127.0.0.1:8000/redoc` para ver a documentação alternativa (ReDoc).

### Rodando os Testes

Para executar a suíte de testes automatizados, utilize o Pytest:

```bash
pytest
```

---

## Endpoints da API

| Método | Rota                 | Descrição                                    |
| :----- | :------------------- | :------------------------------------------- |
| `POST` | `/cadastro`          | Registra um novo usuário no sistema.         |
| `POST` | `/login`             | Autentica um usuário e retorna uma mensagem. |
| `GET`  | `/usuario/{user_id}` | Busca um usuário pelo seu ID.                |
