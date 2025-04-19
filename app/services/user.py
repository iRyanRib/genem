from typing import List, Optional, Dict
import secrets
import hashlib

from app.schemas.user import User, UserCreate, UserUpdate


# Mock database
USERS_DB: Dict[int, User] = {}
next_user_id = 1

# Mock password table (não seria usado em produção, apenas para demonstração)
USER_PASSWORDS: Dict[int, str] = {}


class UserService:
    def get(self, id: int) -> Optional[User]:
        """Obter um usuário pelo ID"""
        if id in USERS_DB:
            return USERS_DB[id]
        return None

    def get_by_email(self, email: str) -> Optional[User]:
        """Obter um usuário pelo email"""
        for user in USERS_DB.values():
            if user.email == email:
                return user
        return None

    def get_multi(self, *, skip: int = 0, limit: int = 100) -> List[User]:
        """Obter múltiplos usuários"""
        users = list(USERS_DB.values())
        return users[skip : skip + limit]

    def create(self, *, obj_in: UserCreate) -> User:
        """Criar um novo usuário"""
        global next_user_id
        
        # Hash da senha (mockado para simplicidade)
        hashed_password = self._get_password_hash(obj_in.password)
        
        user = User(
            id=next_user_id,
            email=obj_in.email,
            is_active=obj_in.is_active,
            is_superuser=obj_in.is_superuser
        )
        
        USERS_DB[next_user_id] = user
        USER_PASSWORDS[next_user_id] = hashed_password
        
        next_user_id += 1
        return user

    def update(self, *, user_id: int, obj_in: UserUpdate) -> Optional[User]:
        """Atualizar um usuário existente"""
        if user_id not in USERS_DB:
            return None
            
        user = USERS_DB[user_id]
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Trata a senha separadamente
        if "password" in update_data:
            password = update_data.pop("password")
            if password:
                USER_PASSWORDS[user_id] = self._get_password_hash(password)
        
        # Atualiza os demais campos
        for field in update_data:
            setattr(user, field, update_data[field])
            
        USERS_DB[user_id] = user
        return user

    def authenticate(self, *, email: str, password: str) -> Optional[User]:
        """Autenticar um usuário"""
        user = self.get_by_email(email=email)
        if not user:
            return None
        
        if not user.is_active:
            return None
            
        if not self._verify_password(password, USER_PASSWORDS.get(user.id, "")):
            return None
            
        return user

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verificar senha (mock simplificado)"""
        return self._get_password_hash(plain_password) == hashed_password
        
    def _get_password_hash(self, password: str) -> str:
        """Criar hash de senha (mockado para simplicidade)"""
        # Em uma implementação real, use bcrypt ou outro algoritmo seguro
        # Isso é apenas um mock simples para demonstração
        salt = "mock-salt"
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()


# Singleton instance
user_service = UserService()

# Cria um usuário admin inicial para facilitar testes
if not USERS_DB:
    admin = UserCreate(
        email="admin@example.com",
        password="admin",
        is_superuser=True
    )
    user_service.create(obj_in=admin) 