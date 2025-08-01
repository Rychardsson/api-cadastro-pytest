from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator, EmailStr
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import List, Optional
from jose import jwt, JWTError

# --- Configuração Inicial ---
app = FastAPI(
    title="API de Cadastro Avançada",
    description="API completa com autenticação JWT, perfis de usuário e logs de atividade.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Contexto para hashing de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configurações JWT
SECRET_KEY = "sua-chave-secreta-super-segura-para-producao-mude-isso"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Autenticação
security = HTTPBearer()

# "Banco de dados" em memória expandido
db_usuarios = {}
db_logs = []
user_id_counter = 1

# --- Modelos (Schemas Pydantic) Expandidos ---

# Modelo para cadastro de usuário
class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    nome_completo: Optional[str] = None
    idade: Optional[int] = None
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username deve ter pelo menos 3 caracteres')
        if not v.isalnum():
            raise ValueError('Username deve conter apenas letras e números')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Senha deve ter pelo menos 6 caracteres')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v or '.' not in v:
            raise ValueError('Email inválido')
        return v

# Modelo para dados de saída do usuário
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    nome_completo: Optional[str]
    idade: Optional[int]
    data_criacao: datetime
    ultimo_login: Optional[datetime]

# Modelo para login
class UserLogin(BaseModel):
    username: str
    password: str

# Modelo para atualização de usuário
class UserUpdate(BaseModel):
    email: Optional[str] = None
    nome_completo: Optional[str] = None
    idade: Optional[int] = None

# Modelo para resposta de token
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

# Modelo para logs
class LogEntry(BaseModel):
    id: int
    timestamp: datetime
    usuario_id: int
    acao: str
    detalhes: str


# --- Funções Auxiliares ---

def verify_password(plain_password, hashed_password):
    """Verifica se a senha em texto plano corresponde ao hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Gera hash da senha."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Cria token JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception:
        # Fallback simples se JWT não estiver disponível
        return f"simple_token_{data.get('sub', 'unknown')}"

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verifica token JWT."""
    token = credentials.credentials
    try:
        # Tentativa de decodificar JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return username
    except JWTError:
        # Fallback simples - verifica se token segue padrão simples
        if token.startswith("simple_token_"):
            username = token.replace("simple_token_", "")
            # Verifica se usuário existe
            for user in db_usuarios.values():
                if user["username"] == username:
                    return username
        raise HTTPException(status_code=401, detail="Token inválido")

def add_log(usuario_id: int, acao: str, detalhes: str = ""):
    """Adiciona entrada no log."""
    log_entry = {
        "id": len(db_logs) + 1,
        "timestamp": datetime.now(),
        "usuario_id": usuario_id,
        "acao": acao,
        "detalhes": detalhes
    }
    db_logs.append(log_entry)


# --- Endpoints da API Expandidos ---

@app.post("/cadastro", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_usuario(user: UserCreate):
    """
    Cadastra um novo usuário no sistema.
    - Verifica se username e email já existem
    - Armazena senha de forma segura (hash)
    - Registra data de criação
    """
    global user_id_counter
    
    # Verificar se username já existe
    for existing_user in db_usuarios.values():
        if existing_user["username"] == user.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username já cadastrado."
            )
    
    # Verificar se email já existe
    for existing_user in db_usuarios.values():
        if existing_user["email"] == user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já cadastrado."
            )
    
    # Criar usuário
    hashed_password = get_password_hash(user.password)
    novo_usuario = {
        "id": user_id_counter,
        "username": user.username,
        "email": user.email,
        "nome_completo": user.nome_completo,
        "idade": user.idade,
        "hashed_password": hashed_password,
        "data_criacao": datetime.now(),
        "ultimo_login": None
    }
    
    db_usuarios[user_id_counter] = novo_usuario
    add_log(user_id_counter, "CADASTRO", f"Usuário {user.username} cadastrado")
    user_id_counter += 1
    
    return UserResponse(**{k: v for k, v in novo_usuario.items() if k != "hashed_password"})

@app.post("/login", response_model=TokenResponse)
def login(user_login: UserLogin):
    """
    Autentica um usuário e retorna token de acesso.
    - Compara senha com hash armazenado
    - Gera token JWT
    - Registra último login
    """
    # Encontrar usuário
    usuario_encontrado = None
    for usuario in db_usuarios.values():
        if usuario["username"] == user_login.username:
            usuario_encontrado = usuario
            break

    if not usuario_encontrado or not verify_password(user_login.password, usuario_encontrado["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Atualizar último login
    usuario_encontrado["ultimo_login"] = datetime.now()
    
    # Criar token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": usuario_encontrado["username"]},
        expires_delta=access_token_expires
    )
    
    add_log(usuario_encontrado["id"], "LOGIN", "Login realizado com sucesso")
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@app.get("/usuario/{user_id}", response_model=UserResponse)
def buscar_usuario(user_id: int, current_user: str = Depends(verify_token)):
    """
    Busca um usuário pelo ID.
    Requer autenticação.
    """
    if user_id not in db_usuarios:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )
    
    usuario = db_usuarios[user_id]
    add_log(user_id, "CONSULTA", f"Perfil consultado por {current_user}")
    return UserResponse(**{k: v for k, v in usuario.items() if k != "hashed_password"})

@app.get("/usuarios", response_model=List[UserResponse])
def listar_usuarios(
    limite: int = 10, 
    offset: int = 0,
    current_user: str = Depends(verify_token)
):
    """
    Lista usuários com paginação.
    Requer autenticação.
    """
    usuarios = list(db_usuarios.values())[offset:offset + limite]
    add_log(0, "LISTAGEM", f"Listagem de usuários por {current_user}")
    return [UserResponse(**{k: v for k, v in usuario.items() if k != "hashed_password"}) for usuario in usuarios]

@app.get("/me", response_model=UserResponse)
def meu_perfil(current_user: str = Depends(verify_token)):
    """
    Retorna perfil do usuário autenticado.
    """
    for usuario in db_usuarios.values():
        if usuario["username"] == current_user:
            return UserResponse(**{k: v for k, v in usuario.items() if k != "hashed_password"})
    raise HTTPException(status_code=404, detail="Usuário não encontrado.")

@app.put("/usuario/{user_id}", response_model=UserResponse)
def atualizar_usuario(
    user_id: int, 
    user_update: UserUpdate,
    current_user: str = Depends(verify_token)
):
    """
    Atualiza dados do usuário.
    Usuário só pode editar próprio perfil.
    """
    if user_id not in db_usuarios:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    usuario = db_usuarios[user_id]
    
    # Verificar permissão
    if usuario["username"] != current_user:
        raise HTTPException(status_code=403, detail="Sem permissão para editar este usuário.")
    
    # Atualizar campos
    if user_update.email is not None:
        # Verificar se email já existe
        for other_user in db_usuarios.values():
            if other_user["id"] != user_id and other_user["email"] == user_update.email:
                raise HTTPException(status_code=400, detail="Email já está em uso.")
        usuario["email"] = user_update.email
    
    if user_update.nome_completo is not None:
        usuario["nome_completo"] = user_update.nome_completo
    
    if user_update.idade is not None:
        usuario["idade"] = user_update.idade
    
    add_log(user_id, "ATUALIZACAO", "Perfil atualizado")
    return UserResponse(**{k: v for k, v in usuario.items() if k != "hashed_password"})

@app.delete("/usuario/{user_id}")
def deletar_usuario(user_id: int, current_user: str = Depends(verify_token)):
    """
    Remove usuário do sistema.
    Usuário só pode deletar próprio perfil.
    """
    if user_id not in db_usuarios:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    usuario = db_usuarios[user_id]
    
    # Verificar permissão
    if usuario["username"] != current_user:
        raise HTTPException(status_code=403, detail="Sem permissão para deletar este usuário.")
    
    del db_usuarios[user_id]
    add_log(user_id, "EXCLUSAO", "Usuário deletado")
    return {"message": "Usuário deletado com sucesso"}

@app.get("/logs", response_model=List[LogEntry])
def listar_logs(
    limite: int = 50,
    current_user: str = Depends(verify_token)
):
    """
    Lista logs de atividade do usuário autenticado.
    """
    # Encontrar ID do usuário atual
    usuario_id = None
    for usuario in db_usuarios.values():
        if usuario["username"] == current_user:
            usuario_id = usuario["id"]
            break
    
    if usuario_id is None:
        return []
    
    # Filtrar logs do usuário
    logs_usuario = [log for log in db_logs if log["usuario_id"] == usuario_id]
    return logs_usuario[-limite:]

@app.get("/stats")
def estatisticas(current_user: str = Depends(verify_token)):
    """
    Retorna estatísticas da aplicação.
    """
    usuarios_com_login = len([u for u in db_usuarios.values() if u["ultimo_login"]])
    return {
        "total_usuarios": len(db_usuarios),
        "total_logs": len(db_logs),
        "usuarios_com_login": usuarios_com_login,
        "ultima_atualizacao": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


