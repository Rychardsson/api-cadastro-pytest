import pytest
from fastapi.testclient import TestClient
from main import app, db_usuarios, db_logs

# Cliente de teste para fazer requisições à nossa API
client = TestClient(app)

# --- Fixture para limpar o "banco de dados" antes de cada teste ---
@pytest.fixture(autouse=True)
def clean_database():
    """Esta fixture é executada automaticamente antes de cada teste."""
    db_usuarios.clear()
    db_logs.clear()
    # Reset do contador de ID para testes consistentes
    import main
    main.user_id_counter = 1
    yield # O teste é executado aqui
    db_usuarios.clear()
    db_logs.clear()

# --- Testes básicos ---

def test_cadastro_sucesso():
    """Testa o cadastro de um novo usuário com sucesso."""
    response = client.post("/cadastro", json={
        "username": "teste", 
        "password": "123456", 
        "email": "teste@email.com"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "teste"
    assert data["email"] == "teste@email.com"
    assert "id" in data

def test_login_sucesso():
    """Testa o login com credenciais válidas."""
    # Cadastra o usuário primeiro
    client.post("/cadastro", json={
        "username": "logado", 
        "password": "senhaforte", 
        "email": "logado@email.com"
    })
    
    # Tenta fazer login
    response = client.post("/login", json={"username": "logado", "password": "senhaforte"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_buscar_usuario_sem_token():
    """Testa a busca sem token (deve falhar)."""
    response = client.get("/usuario/1")
    assert response.status_code == 403  # Sem autorização

def test_fluxo_completo():
    """Testa o fluxo completo: cadastro -> login -> busca."""
    # 1. Cadastro
    user_data = {
        "username": "fluxocompleto", 
        "password": "senha123",
        "email": "fluxo@email.com"
    }
    cadastro_response = client.post("/cadastro", json=user_data)
    assert cadastro_response.status_code == 201
    user_id = cadastro_response.json()["id"]
    
    # 2. Login
    login_response = client.post("/login", json={
        "username": "fluxocompleto", 
        "password": "senha123"
    })
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # 3. Busca com token
    headers = {"Authorization": f"Bearer {token}"}
    get_response = client.get(f"/usuario/{user_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["username"] == "fluxocompleto"

def test_cadastro_usuario_duplicado():
    """Testa erro ao cadastrar usuário com username duplicado."""
    user_data = {
        "username": "duplicado", 
        "password": "123456", 
        "email": "duplicado@email.com"
    }
    
    # Primeiro cadastro
    response1 = client.post("/cadastro", json=user_data)
    assert response1.status_code == 201
    
    # Segundo cadastro (deve falhar)
    user_data["email"] = "outro@email.com"  # Email diferente
    response2 = client.post("/cadastro", json=user_data)
    assert response2.status_code == 400

def test_cadastro_email_duplicado():
    """Testa erro ao cadastrar usuário com email duplicado."""
    # Primeiro usuário
    response1 = client.post("/cadastro", json={
        "username": "user1", 
        "password": "123456", 
        "email": "mesmo@email.com"
    })
    assert response1.status_code == 201
    
    # Segundo usuário com mesmo email
    response2 = client.post("/cadastro", json={
        "username": "user2", 
        "password": "123456", 
        "email": "mesmo@email.com"
    })
    assert response2.status_code == 400

def test_login_usuario_inexistente():
    """Testa login com usuário que não existe."""
    response = client.post("/login", json={
        "username": "naoexiste", 
        "password": "123456"
    })
    assert response.status_code == 401

def test_login_senha_incorreta():
    """Testa login com senha incorreta."""
    # Cadastra usuário
    client.post("/cadastro", json={
        "username": "usersenha", 
        "password": "senha123", 
        "email": "user@email.com"
    })
    
    # Tenta login com senha errada
    response = client.post("/login", json={
        "username": "usersenha", 
        "password": "senhaerrada"
    })
    assert response.status_code == 401

def test_validacao_username_muito_pequeno():
    """Testa validação de username muito pequeno."""
    response = client.post("/cadastro", json={
        "username": "ab",  # Menos de 3 caracteres
        "password": "123456", 
        "email": "test@email.com"
    })
    assert response.status_code == 422

def test_validacao_senha_muito_pequena():
    """Testa validação de senha muito pequena."""
    response = client.post("/cadastro", json={
        "username": "usuario", 
        "password": "123",  # Menos de 6 caracteres
        "email": "test@email.com"
    })
    assert response.status_code == 422

def test_validacao_email_invalido():
    """Testa validação de email inválido."""
    response = client.post("/cadastro", json={
        "username": "usuario", 
        "password": "123456", 
        "email": "emailinvalido"  # Sem @ ou .
    })
    assert response.status_code == 422

def test_campos_obrigatorios():
    """Testa que todos os campos obrigatórios são validados."""
    # Sem username
    response = client.post("/cadastro", json={
        "password": "123456", 
        "email": "test@email.com"
    })
    assert response.status_code == 422
    
    # Sem password
    response = client.post("/cadastro", json={
        "username": "test", 
        "email": "test@email.com"
    })
    assert response.status_code == 422
    
    # Sem email
    response = client.post("/cadastro", json={
        "username": "test", 
        "password": "123456"
    })
    assert response.status_code == 422
