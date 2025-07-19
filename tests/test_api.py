import pytest
from fastapi.testclient import TestClient
from main import app, db_usuarios # Importamos o app e o "banco de dados"

# Cliente de teste para fazer requisições à nossa API
client = TestClient(app)

# --- Fixture para limpar o "banco de dados" antes de cada teste ---
@pytest.fixture(autouse=True)
def clean_database():
    """Esta fixture é executada automaticamente antes de cada teste."""
    db_usuarios.clear()
    # Reinicia o contador de ID importando-o ou redefinindo-o aqui se necessário.
    # Para este exemplo simples, a limpeza do dict é suficiente.
    # Em main.py, o user_id_counter não é resetado, mas para testes
    # sequenciais simples, isso não causará problemas.
    # Uma abordagem mais robusta seria resetá-lo aqui também.
    # from main import user_id_counter
    # global user_id_counter
    # user_id_counter = 1
    yield # O teste é executado aqui
    db_usuarios.clear() # Limpa depois do teste também


# --- Testes para o endpoint /cadastro ---

def test_cadastro_sucesso():
    """Testa o cadastro de um novo usuário com sucesso."""
    response = client.post("/cadastro", json={"username": "teste", "password": "123"})
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "teste"
    assert "id" in data

def test_cadastro_falha_usuario_existente():
    """Testa a falha ao tentar cadastrar um usuário que já existe."""
    # Primeiro, cadastra um usuário
    client.post("/cadastro", json={"username": "existente", "password": "123"})
    
    # Agora, tenta cadastrar o mesmo usuário novamente
    response = client.post("/cadastro", json={"username": "existente", "password": "456"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Username já cadastrado."

# --- Testes para o endpoint /login ---

def test_login_sucesso():
    """Testa o login com credenciais válidas."""
    # Cadastra o usuário primeiro
    client.post("/cadastro", json={"username": "logado", "password": "senhaforte"})
    
    # Tenta fazer login
    response = client.post("/login", json={"username": "logado", "password": "senhaforte"})
    assert response.status_code == 200
    assert "Login bem-sucedido!" in response.json()["message"]

def test_login_com_dados_invalidos_senha():
    """Testa o login com a senha incorreta."""
    client.post("/cadastro", json={"username": "userpass", "password": "senha1"})
    
    response = client.post("/login", json={"username": "userpass", "password": "senha_errada"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Usuário ou senha inválidos."

def test_login_com_dados_invalidos_usuario():
    """Testa o login com um usuário que não existe."""
    response = client.post("/login", json={"username": "naoexiste", "password": "123"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Usuário ou senha inválidos."

# --- Testes para o endpoint /usuario/{id} ---

def test_get_usuario_sucesso():
    """Testa a busca de um usuário existente pelo ID."""
    # Cadastra e obtém o ID
    cadastro_response = client.post("/cadastro", json={"username": "buscado", "password": "123"})
    user_id = cadastro_response.json()["id"]
    
    # Busca o usuário
    get_response = client.get(f"/usuario/{user_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == user_id
    assert data["username"] == "buscado"

def test_get_usuario_nao_encontrado():
    """Testa o retorno de erro ao buscar um ID de usuário que não existe."""
    response = client.get("/usuario/999") # Um ID que certamente não existe
    assert response.status_code == 404
    assert response.json()["detail"] == "Usuário não encontrado."