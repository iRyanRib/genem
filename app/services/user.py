from typing import List, Optional, Dict, Any
from bson import ObjectId

from app.schemas.user import User, UserCreate, UserUpdate
from app.utils.security import get_password_hash, verify_password
from app.services.base import MongoService
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class UserService(MongoService):
    """Serviço para operações CRUD de User"""
    
    def __init__(self):
        super().__init__("users")
    
    def get(self, id: str) -> Optional[User]:
        """Obter um usuário pelo ID"""
        try:
            data = self.get_by_id(id)
            return User(**data) if data else None
        except Exception as e:
            logger.error(f"Erro ao buscar usuário por ID {id}: {e}")
            return None

    def get_by_email(self, email: str) -> Optional[User]:
        """Obter um usuário pelo email"""
        try:
            collection = self._get_collection()
            doc = collection.find_one({"email": email})
            if doc:
                doc = self._object_id_to_str(doc)
                return User(**doc)
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar usuário por email {email}: {e}")
            return None

    def get_multi(self, *, skip: int = 0, limit: int = 100) -> List[User]:
        """Obter múltiplos usuários"""
        try:
            docs = super().get_multi(skip=skip, limit=limit)
            return [User(**doc) for doc in docs]
        except Exception as e:
            logger.error(f"Erro ao buscar usuários: {e}")
            return []

    def create(self, *, obj_in: UserCreate) -> User:
        """Criar um novo usuário"""
        try:
            # Hash da senha
            hashed_password = get_password_hash(obj_in.password)
            
            # Preparar dados do usuário
            user_data = obj_in.model_dump(exclude={"password"})
            user_data["hashed_password"] = hashed_password
            
            # Criar no MongoDB
            created_data = super().create(user_data)
            if created_data:
                return User(**created_data)
            
            raise Exception("Falha ao criar usuário no banco de dados")
            
        except Exception as e:
            logger.error(f"Erro ao criar usuário: {e}")
            raise

    def update(self, *, user_id: str, obj_in: UserUpdate) -> Optional[User]:
        """Atualizar um usuário existente"""
        try:
            update_data = obj_in.model_dump(exclude_unset=True)
            
            # Trata a senha separadamente
            if "password" in update_data and update_data["password"]:
                update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
            
            # Atualizar no MongoDB
            updated_data = super().update(user_id, update_data)
            if updated_data:
                return User(**updated_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao atualizar usuário {user_id}: {e}")
            return None

    def authenticate(self, *, email: str, password: str) -> Optional[User]:
        """Autenticar um usuário"""
        try:
            # Buscar usuário por email incluindo a senha hash
            collection = self._get_collection()
            doc = collection.find_one({"email": email})
            
            if not doc:
                logger.warning(f"Usuário não encontrado: {email}")
                return None
            
            doc = self._object_id_to_str(doc)
            user = User(**{k: v for k, v in doc.items() if k != "hashed_password"})
            
            if not user.is_active:
                logger.warning(f"Usuário inativo: {email}")
                return None
            
            # Verificar senha
            hashed_password = doc.get("hashed_password", "")
            if not verify_password(password, hashed_password):
                logger.warning(f"Senha incorreta para usuário: {email}")
                return None
            
            logger.info(f"Usuário autenticado com sucesso: {email}")
            return user
            
        except Exception as e:
            logger.error(f"Erro ao autenticar usuário {email}: {e}")
            return None

# Singleton instance
user_service = UserService()

# Cria um usuário admin inicial para facilitar testes
def create_admin_user():
    """Criar usuário admin se não existir"""
    try:
        # Verificar se já existe algum usuário
        users = user_service.get_multi(limit=1)
        if users:
            logger.info("✅ Já existem usuários no sistema")
            return
            
        # Criar usuário admin
        admin = UserCreate(
            email="admin@example.com",
            name="Administrador",
            password="123456",  # Senha mais simples para evitar problemas com bcrypt
            is_superuser=True
        )
        user_service.create(obj_in=admin)
        logger.info("✅ Usuário admin criado com sucesso")
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar usuário admin: {e}")

# TEMPORARIAMENTE DESABILITADO - será criado via endpoint
# try:
#     create_admin_user()
# except Exception as e:
#     logger.error(f"❌ Falha na criação do usuário admin: {e}") 