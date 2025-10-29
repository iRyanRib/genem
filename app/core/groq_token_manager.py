from typing import List, Optional
import itertools
import threading
from app.core.logging_config import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class GroqTokenManager:
    """Gerenciador de tokens GROQ com rotação cíclica"""
    
    def __init__(self, tokens: List[str]):
        if not tokens:
            raise ValueError("Lista de tokens não pode estar vazia")
        
        self.tokens = [token.strip() for token in tokens if token.strip()]
        if not self.tokens:
            raise ValueError("Nenhum token válido fornecido")
        
        self.token_cycle = itertools.cycle(self.tokens)
        self.current_token = None
        self.lock = threading.Lock()
        self.token_usage_count = {token: 0 for token in self.tokens}
        
        logger.info(f"GroqTokenManager inicializado com {len(self.tokens)} tokens")
    
    def get_next_token(self) -> str:
        """Obtém o próximo token na rotação"""
        with self.lock:
            self.current_token = next(self.token_cycle)
            self.token_usage_count[self.current_token] += 1
            
            # Log do uso (apenas os últimos 8 caracteres para segurança)
            masked_token = self.current_token[-8:] if len(self.current_token) > 8 else "***"
            logger.debug(f"Usando token ...{masked_token} (uso #{self.token_usage_count[self.current_token]})")
            
            return self.current_token
    
    def get_current_token(self) -> Optional[str]:
        """Obtém o token atual sem avançar na rotação"""
        return self.current_token
    
    def get_token_stats(self) -> dict:
        """Retorna estatísticas de uso dos tokens"""
        with self.lock:
            total_usage = sum(self.token_usage_count.values())
            return {
                "total_tokens": len(self.tokens),
                "total_usage": total_usage,
                "usage_per_token": dict(self.token_usage_count),
                "current_token_masked": f"...{self.current_token[-8:]}" if self.current_token else None
            }
    
    def reset_stats(self):
        """Reset das estatísticas de uso"""
        with self.lock:
            self.token_usage_count = {token: 0 for token in self.tokens}
            logger.info("Estatísticas de uso dos tokens resetadas")


# Singleton instance
_groq_token_manager = None
_manager_lock = threading.Lock()


def get_groq_token_manager() -> GroqTokenManager:
    """Obtém a instância singleton do gerenciador de tokens"""
    global _groq_token_manager
    
    if _groq_token_manager is None:
        with _manager_lock:
            if _groq_token_manager is None:
                # Obtém tokens das configurações
                groq_tokens = settings.get_groq_tokens()
                
                if not groq_tokens:
                    raise ValueError("Nenhum token GROQ configurado. Configure GROQ_API_KEY ou GROQ_API_TOKENS nas variáveis de ambiente.")
                
                _groq_token_manager = GroqTokenManager(groq_tokens)
    
    return _groq_token_manager


def get_current_groq_token() -> str:
    """Obtém o próximo token GROQ na rotação"""
    return get_groq_token_manager().get_next_token()


def get_groq_token_stats() -> dict:
    """Obtém estatísticas de uso dos tokens GROQ"""
    return get_groq_token_manager().get_token_stats()