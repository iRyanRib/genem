from datetime import datetime, timedelta
from typing import Any, Union

# Função simplificada para criar token de acesso mock
def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """
    Criar um token de acesso mock
    Em uma implementação real, isso geraria um JWT com payload adequado
    """
    # Retorna apenas um token simplificado para demonstração
    return f"token_{subject}" 