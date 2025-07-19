from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from passlib.context import CryptContext

# --- Configuração Inicial ---
app = FastAPI(
    title="API de Cadastro",
    description="Uma API simples para cadastro e login de usuários.",
    version="1.0.0"
)

# Contexto para hashing de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# "Banco de dados" em memória (para simplificar)
db_usuarios = {}
user_id_counter = 1

# --- Modelos (Schemas Pydantic) ---
# Modelo para dados de entrada no cadastro
class UserIn(BaseModel):
    username: str
    password: str

# Modelo para dados de saída (nunca expor a senha)
class UserOut(BaseModel):
    id: int
    username: str

# Modelo para login
class UserLogin(BaseModel):
    username: str
    password: str


# --- Funções Auxiliares de Segurança ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)


# --- Endpoints da API ---

@app.post("/cadastro", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def cadastrar_usuario(user: UserIn):
    """
    Cadastra um novo usuário no sistema.
    - Verifica se o username já existe.
    - Armazena a senha de forma segura (hash).
    """
    global user_id_counter
    if user.username in [u['username'] for u in db_usuarios.values()]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username já cadastrado."
        )
    
    hashed_password = get_password_hash(user.password)
    novo_usuario = {
        "id": user_id_counter,
        "username": user.username,
        "hashed_password": hashed_password
    }
    db_usuarios[user_id_counter] = novo_usuario
    user_id_counter += 1
    
    return {"id": novo_usuario["id"], "username": novo_usuario["username"]}


@app.post("/login")
def login(user_login: UserLogin):
    """
    Autentica um usuário.
    - Compara a senha fornecida com o hash armazenado.
    """
    # Encontra o usuário pelo username
    user_in_db = next((u for u in db_usuarios.values() if u['username'] == user_login.username), None)

    if not user_in_db or not verify_password(user_login.password, user_in_db["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return {"message": f"Login bem-sucedido! Bem-vindo, {user_login.username}!"}


@app.get("/usuario/{user_id}", response_model=UserOut)
def buscar_usuario(user_id: int):
    """
    Busca um usuário pelo seu ID.
    """
    if user_id not in db_usuarios:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )
    user = db_usuarios[user_id]
    return {"id": user["id"], "username": user["username"]}


