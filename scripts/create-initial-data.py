import sys
import os

# Adicionar o diretório raiz ao path para importar os módulos do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.user import user_service
from app.schemas.user import UserCreate

def init() -> None:
    db = SessionLocal()
    create_initial_users(db)
    db.close()

def create_initial_users(db: Session) -> None:
    # Verificar se já existe um usuário administrador
    user = user_service.get_by_email(db, email="admin@example.com")
    if not user:
        user_in = UserCreate(
            email="admin@example.com",
            password="admin123",
            is_superuser=True,
        )
        user = user_service.create(db, obj_in=user_in)
        print(f"Usuário admin criado com ID: {user.id}")
    else:
        print("Usuário admin já existe")

if __name__ == "__main__":
    print("Criando dados iniciais...")
    init()
    print("Dados iniciais criados com sucesso!") 