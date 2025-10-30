"""
Cliente Groq customizado usando a API REST diretamente
Evita problemas de incompatibilidade com LangChain
"""

import httpx
import json
import asyncio
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.groq_token_manager import get_current_groq_token
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class GroqClient:
    """Cliente customizado para API Groq usando HTTP direto"""
    
    def __init__(self):
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = settings.GROQ_MODEL_NAME
        
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Fazer uma requisição de chat completion para o Groq
        
        Args:
            messages: Lista de mensagens no formato [{"role": "user", "content": "..."}]
            temperature: Temperatura para geração (0-2)
            max_tokens: Máximo de tokens de resposta
            
        Returns:
            Resposta da API Groq
        """
        token = get_current_groq_token()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        # Preparar dados da requisição
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False
        }
        
        if max_tokens:
            data["max_tokens"] = max_tokens
            
        logger.debug(f"Fazendo requisição para Groq com modelo: {self.model}")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.debug("Requisição Groq concluída com sucesso")
                    return result
                else:
                    error_msg = f"Erro Groq {response.status_code}: {response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                    
            except httpx.TimeoutException:
                error_msg = "Timeout na requisição para Groq"
                logger.error(error_msg)
                raise Exception(error_msg)
            except Exception as e:
                error_msg = f"Erro na requisição Groq: {str(e)}"
                logger.error(error_msg)
                raise
    
    async def simple_completion(self, prompt: str, temperature: float = 0.7) -> str:
        """
        Fazer uma completion simples com um prompt
        
        Args:
            prompt: Texto do prompt
            temperature: Temperatura para geração
            
        Returns:
            Texto da resposta
        """
        messages = [{"role": "user", "content": prompt}]
        
        result = await self.chat_completion(messages, temperature)
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            raise Exception("Resposta inválida do Groq")
    
    async def test_connection(self) -> bool:
        """Testar conexão com Groq"""
        try:
            result = await self.simple_completion("Responda apenas: OK")
            logger.info("Teste de conexão Groq: SUCCESS")
            return True
        except Exception as e:
            logger.error(f"Teste de conexão Groq falhou: {e}")
            return False


# Singleton instance
_groq_client = None


def get_groq_client() -> GroqClient:
    """Obter instância singleton do cliente Groq"""
    global _groq_client
    if _groq_client is None:
        _groq_client = GroqClient()
    return _groq_client