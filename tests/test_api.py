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
        # Campos faltando
        response = client.post("/cadastro", json={"username": "test"})
        assert response.status_code == 422
        
        response = client.post("/cadastro", json={"password": "test"})
        assert response.status_code == 422
        
        # JSON vazio
        response = client.post("/cadastro", json={})
        assert response.status_code == 422

    def test_cadastro_strings_vazias(self):
        """Testa cadastro com strings vazias (comportamento atual da API)."""
        # Username vazio (API atualmente permite)
        response = client.post("/cadastro", json={"username": "", "password": "123"})
        assert response.status_code == 201
        
        # Password vazio (API atualmente permite)
        response = client.post("/cadastro", json={"username": "test", "password": ""})
        assert response.status_code == 201

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
        ("test", "123", 401),  # Usuário não cadastrado
    ])
    def test_login_parametrizado(self, username, password, expected_status):
        """Testa diferentes combinações de dados de login."""
        response = client.post("/login", json={"username": username, "password": password})
        assert response.status_code == expected_status

# --- Testes para o endpoint /usuario/{id} ---

class TestUsuario:
    """Agrupa todos os testes relacionados à busca de usuários."""

    def test_get_usuario_sucesso(self):
        """Testa a busca de um usuário existente pelo ID."""
        # Cadastra e obtém o ID
        cadastro_response = client.post("/cadastro", json=TEST_USER_DATA["search"])
        user_id = cadastro_response.json()["id"]
        
        # Busca o usuário
        get_response = client.get(f"/usuario/{user_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == user_id
        assert data["username"] == TEST_USER_DATA["search"]["username"]

    def test_get_usuario_nao_encontrado(self):
        """Testa o retorno de erro ao buscar um ID de usuário que não existe."""
        response = client.get("/usuario/999") # Um ID que certamente não existe
        assert response.status_code == 404
        assert response.json()["detail"] == ERROR_MESSAGES["user_not_found"]

    @pytest.mark.parametrize("user_id,expected_status", [
        ("abc", 422),  # ID não numérico
        ("-1", 404),   # ID negativo
        ("0", 404),    # ID zero
        ("999999", 404)  # ID muito grande
    ])
    def test_get_usuario_ids_invalidos(self, user_id, expected_status):
        """Testa busca com diferentes IDs inválidos."""
        response = client.get(f"/usuario/{user_id}")
        assert response.status_code == expected_status

    def test_get_usuario_usando_fixture(self, usuario_cadastrado):
        """Testa busca usando fixture de usuário já cadastrado."""
        user_id = usuario_cadastrado["id"]
        response = client.get(f"/usuario/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["username"] == usuario_cadastrado["username"]


# --- Testes de integração ---

class TestIntegracao:
    """Testes que verificam o fluxo completo da aplicação."""

    @pytest.mark.integration
    def test_fluxo_completo_cadastro_login_busca(self):
        """Testa o fluxo completo: cadastro -> login -> busca."""
        # 1. Cadastro
        user_data = {"username": "fluxocompleto", "password": "senha123"}
        cadastro_response = client.post("/cadastro", json=user_data)
        assert cadastro_response.status_code == 201
        user_id = cadastro_response.json()["id"]
        
        # 2. Login
        login_response = client.post("/login", json=user_data)
        assert login_response.status_code == 200
        assert "Login bem-sucedido!" in login_response.json()["message"]
        
        # 3. Busca
        get_response = client.get(f"/usuario/{user_id}")
        assert get_response.status_code == 200
        assert get_response.json()["username"] == user_data["username"]

    @pytest.mark.integration
    def test_multiplos_usuarios_operacoes(self):
        """Testa operações com múltiplos usuários."""
        users = [
            {"username": "multi1", "password": "pass1"},
            {"username": "multi2", "password": "pass2"},
            {"username": "multi3", "password": "pass3"}
        ]
        
        user_ids = []
        # Cadastra todos os usuários
        for user in users:
            response = client.post("/cadastro", json=user)
            assert response.status_code == 201
            user_ids.append(response.json()["id"])
        
        # Testa login de todos
        for i, user in enumerate(users):
            response = client.post("/login", json=user)
            assert response.status_code == 200
            
        # Testa busca de todos
        for i, user_id in enumerate(user_ids):
            response = client.get(f"/usuario/{user_id}")
            assert response.status_code == 200
            assert response.json()["username"] == users[i]["username"]


# --- Testes de performance básica ---

class TestPerformance:
    """Testes básicos de performance."""

    @pytest.mark.performance
    def test_multiplos_cadastros_sequenciais(self):
        """Testa cadastro de muitos usuários em sequência."""
        for i in range(10):
            response = client.post("/cadastro", json={
                "username": f"user{i:03d}",
                "password": f"pass{i:03d}"
            })
            assert response.status_code == 201
            assert response.json()["id"] == i + 1

    @pytest.mark.performance
    def test_buscas_multiplas(self):
        """Testa múltiplas buscas em sequência."""
        # Cadastra usuários primeiro
        user_ids = []
        for i in range(5):
            response = client.post("/cadastro", json={
                "username": f"search{i}",
                "password": f"pass{i}"
            })
            user_ids.append(response.json()["id"])
        
        # Busca todos múltiplas vezes
        for _ in range(3):
            for user_id in user_ids:
                response = client.get(f"/usuario/{user_id}")
                assert response.status_code == 200


# --- Testes de edge cases ---

class TestEdgeCases:
    """Testes para casos extremos e situações especiais."""

    def test_username_caracteres_especiais(self):
        """Testa cadastro com caracteres especiais no username."""
        special_users = [
            {"username": "user@domain.com", "password": "123"},
            {"username": "user-name", "password": "123"},
            {"username": "user_name", "password": "123"},
            {"username": "user.name", "password": "123"},
            {"username": "user123", "password": "123"}
        ]
        
        for user in special_users:
            response = client.post("/cadastro", json=user)
            assert response.status_code == 201

    def test_senhas_complexas(self):
        """Testa cadastro com diferentes tipos de senhas."""
        complex_passwords = [
            "senha123",
            "Senha@123!",
            "senha_super_longa_com_muitos_caracteres_123456789",
            "123",
            "abc"
        ]
        
        for i, password in enumerate(complex_passwords):
            response = client.post("/cadastro", json={
                "username": f"userpass{i}",
                "password": password
            })
            assert response.status_code == 201

    def test_username_case_preservation(self):
        """Testa se o username preserva maiúsculas/minúsculas."""
        test_cases = [
            "User",
            "USER", 
            "user",
            "UsEr"
        ]
        
        for i, username in enumerate(test_cases):
            response = client.post("/cadastro", json={
                "username": username,
                "password": "123"
            })
            assert response.status_code == 201
            assert response.json()["username"] == username