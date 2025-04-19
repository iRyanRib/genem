# Importar todos os modelos para Alembic
from app.db.base_class import Base  # noqa

# Importar todos os modelos para que Alembic os detecte
from app.models.item import Item  # noqa
from app.models.user import User  # noqa 