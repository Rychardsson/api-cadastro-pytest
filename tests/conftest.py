"""
Configurações compartilhadas para todos os testes.
"""
import pytest
from fastapi.testclient import TestClient
from main import app, db_usuarios


@pytest.fixture(scope="session")
def test_client():
    """Cliente de teste reutilizável para toda a sessão de testes."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_database():
    """Reset automático do banco de dados antes de cada teste."""
    db_usuarios.clear()
    import main
    main.user_id_counter = 1
    yield
    db_usuarios.clear()


# Constantes para dados de teste (centralizadas)
TEST_USERS = {
    "valid_user": {"username": "testuser", "password": "testpass123"},
    "admin_user": {"username": "admin", "password": "admin123"},
    "special_chars": {"username": "user@test.com", "password": "pass@123!"},
    "long_username": {"username": "a" * 50, "password": "password"},
    "long_password": {"username": "user", "password": "p" * 100}
}

# Mensagens de erro esperadas
EXPECTED_ERRORS = {
    "user_exists": "Username já cadastrado.",
    "invalid_credentials": "Usuário ou senha inválidos.",
    "user_not_found": "Usuário não encontrado."
}


@pytest.fixture
def sample_users():
    """Fixture que retorna dados de usuários para testes."""
    return TEST_USERS


@pytest.fixture
def error_messages():
    """Fixture que retorna mensagens de erro esperadas."""
    return EXPECTED_ERRORS
