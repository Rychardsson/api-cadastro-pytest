import pytest
from fastapi.testclient import TestClient
from main import app, db_usuarios # Importamos o app e o "banco de dados"

# Cliente de teste para fazer requisições à nossa API
client = TestClient(app)

# --- Constantes para testes ---
TEST_USER_DATA = {
    "valid": {"username": "testuser", "password": "testpass123"},
    "existing": {"username": "existente", "password": "123"},
    "login": {"username": "logado", "password": "senhaforte"},
    "invalid_password": {"username": "userpass", "password": "senha1"},
    "search": {"username": "buscado", "password": "123"}
}

ERROR_MESSAGES = {
    "user_exists": "Username já cadastrado.",
    "invalid_credentials": "Usuário ou senha inválidos.",
    "user_not_found": "Usuário não encontrado."
}

# --- Fixture para limpar o "banco de dados" antes de cada teste ---
@pytest.fixture(autouse=True)
def clean_database():
    """Esta fixture é executada automaticamente antes de cada teste."""
    db_usuarios.clear()
    # Reset do contador de ID para testes consistentes
    import main
    main.user_id_counter = 1
    yield # O teste é executado aqui
    db_usuarios.clear() # Limpa depois do teste também


# --- Fixtures auxiliares ---
@pytest.fixture
def usuario_cadastrado():
    """Fixture que retorna um usuário já cadastrado."""
    response = client.post("/cadastro", json=TEST_USER_DATA["valid"])
    return response.json()

@pytest.fixture
def usuario_logado(usuario_cadastrado):
    """Fixture que retorna dados de um usuário logado."""
    login_response = client.post("/login", json=TEST_USER_DATA["valid"])
    return {
        "user_data": usuario_cadastrado,
        "login_response": login_response.json()
    }


# --- Testes para o endpoint /cadastro ---

class TestCadastro:
    """Agrupa todos os testes relacionados ao cadastro."""

    def test_cadastro_sucesso(self):
        """Testa o cadastro de um novo usuário com sucesso."""
        response = client.post("/cadastro", json=TEST_USER_DATA["valid"])
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == TEST_USER_DATA["valid"]["username"]
        assert "id" in data

    def test_cadastro_falha_usuario_existente(self):
        """Testa a falha ao tentar cadastrar um usuário que já existe."""
        # Primeiro, cadastra um usuário
        client.post("/cadastro", json=TEST_USER_DATA["existing"])
        
        # Agora, tenta cadastrar o mesmo usuário novamente
        response = client.post("/cadastro", json={"username": "existente", "password": "456"})
        assert response.status_code == 400
        assert response.json()["detail"] == ERROR_MESSAGES["user_exists"]

    def test_cadastro_dados_invalidos(self):
        """Testa cadastro com dados inválidos."""
        # Username vazio
        response = client.post("/cadastro", json={"username": "", "password": "123"})
        assert response.status_code == 422
        
        # Password vazio
        response = client.post("/cadastro", json={"username": "test", "password": ""})
        assert response.status_code == 422
        
        # Campos faltando
        response = client.post("/cadastro", json={"username": "test"})
        assert response.status_code == 422

    def test_multiplos_usuarios_sequenciais(self):
        """Testa cadastro de múltiplos usuários para verificar IDs sequenciais."""
        users = [
            {"username": "user1", "password": "pass1"},
            {"username": "user2", "password": "pass2"},
            {"username": "user3", "password": "pass3"}
        ]
        
        ids = []
        for user in users:
            response = client.post("/cadastro", json=user)
            assert response.status_code == 201
            ids.append(response.json()["id"])
        
        # Verifica se IDs são sequenciais
        assert ids == [1, 2, 3]

    def test_cadastro_username_case_sensitive(self):
        """Testa se usernames são case-sensitive."""
        client.post("/cadastro", json={"username": "User", "password": "123"})
        response = client.post("/cadastro", json={"username": "user", "password": "123"})
        # Assumindo que deveria permitir (case-sensitive)
        assert response.status_code == 201

    @pytest.mark.parametrize("username,password,expected_status", [
        ("test", "123", 201),  # Caso válido
        ("", "123", 422),      # Username vazio
        ("test", "", 422),     # Password vazio
        ("a" * 100, "123", 201),  # Username muito longo
        ("test", "a" * 100, 201), # Password muito longo
    ])
    def test_cadastro_parametrizado(self, username, password, expected_status):
        """Testa diferentes combinações de dados de cadastro."""
        response = client.post("/cadastro", json={"username": username, "password": password})
        assert response.status_code == expected_status

# --- Testes para o endpoint /login ---

class TestLogin:
    """Agrupa todos os testes relacionados ao login."""

    def test_login_sucesso(self):
        """Testa o login com credenciais válidas."""
        # Cadastra o usuário primeiro
        client.post("/cadastro", json=TEST_USER_DATA["login"])
        
        # Tenta fazer login
        response = client.post("/login", json=TEST_USER_DATA["login"])
        assert response.status_code == 200
        assert "Login bem-sucedido!" in response.json()["message"]

    def test_login_com_dados_invalidos_senha(self):
        """Testa o login com a senha incorreta."""
        client.post("/cadastro", json=TEST_USER_DATA["invalid_password"])
        
        response = client.post("/login", json={"username": "userpass", "password": "senha_errada"})
        assert response.status_code == 401
        assert response.json()["detail"] == ERROR_MESSAGES["invalid_credentials"]

    def test_login_com_dados_invalidos_usuario(self):
        """Testa o login com um usuário que não existe."""
        response = client.post("/login", json={"username": "naoexiste", "password": "123"})
        assert response.status_code == 401
        assert response.json()["detail"] == ERROR_MESSAGES["invalid_credentials"]

    def test_login_dados_invalidos(self):
        """Testa login com dados inválidos."""
        # Campos faltando
        response = client.post("/login", json={"username": "test"})
        assert response.status_code == 422
        
        # JSON vazio
        response = client.post("/login", json={})
        assert response.status_code == 422

    @pytest.mark.parametrize("username,password,expected_status", [
        ("", "123", 422),      # Username vazio
        ("test", "", 422),     # Password vazio
        ("test", "123", 401),  # Usuário não cadastrado
    ])
    def test_login_parametrizado(self, username, password, expected_status):
        """Testa diferentes combinações de dados de login."""
        response = client.post("/login", json={"username": username, "password": password})
        assert response.status_code == expected_status

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