import json
import asyncio 
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging_config import get_logger
from app.utils.serializers import serialize_mongodb_doc

# Load environment variables
load_dotenv()

# Setup logging
logger = get_logger(__name__)

# Check Google API Key
if not settings.GOOGLE_API_KEY:
    logger.warning("⚠️ GOOGLE_API_KEY não configurada - o agente ADK pode não funcionar!")
else:
    logger.info(f"✅ Google API Key configurada: {settings.GOOGLE_API_KEY[:10]}...")

# --- 1. Define Constants ---
APP_NAME = settings.APP_NAME
MODEL_NAME = settings.GOOGLE_MODEL_NAME

# MongoDB Configuration
CONNECTION_STRING = settings.MONGODB_CONNECTION_STRING
DATABASE_NAME = settings.DATABASE_NAME
QUESTIONS_COLLECTION = 'questions'
ANSWERS_DATA_COLLECTION = 'answers_data'
CONVERSATIONS_COLLECTION = 'conversations'

# MongoDB Client
logger.info(f"Conectando ao MongoDB: {DATABASE_NAME}")
logger.info(f"Connection String: {CONNECTION_STRING[:50]}..." if len(CONNECTION_STRING) > 50 else CONNECTION_STRING)
mongo_client = MongoClient(CONNECTION_STRING)
db = mongo_client[DATABASE_NAME]

# Test connection
try:
    mongo_client.admin.command('ping')
    logger.info("✅ Conexão com MongoDB estabelecida com sucesso")
except Exception as e:
    logger.error(f"❌ Erro ao conectar com MongoDB: {e}")
    raise

# Input schema for ENEM question
class QuestionInput(BaseModel):
    question_id: str = Field(description="The ID of the ENEM question to analyze.")
    context: str = Field(description="The context/text of the question.")
    alternatives: List[Dict[str, Any]] = Field(description="The question alternatives.")
    sources: List[str] = Field(description="Relevant sources from answers_data collection.")

# Output schema for ENEM answer
class EnemAnswerOutput(BaseModel):
    reasoning: str = Field(description="Detailed reasoning explaining how to solve the question.")
    correct_alternative: str = Field(description="The letter of the correct alternative (A, B, C, D, or E).")
    explanation: str = Field(description="Explanation of why this alternative is correct.")
    sources_used: List[str] = Field(description="List of sources that were most relevant for answering.")

# --- 3. Define Tools for ENEM Agent ---
def get_question_sources(question_id: str) -> List[str]:
    """Retrieves relevant sources from answers_data collection for a specific question."""
    logger.info(f"Buscando fontes para question_id: {question_id}")
    
    try:
        # Try both string and ObjectId formats for question_id field
        # answers_data collection might store question_id as string or ObjectId
        search_queries = [
            {"question_id": question_id},  # Try as string first
        ]
        
        # If it's a valid ObjectId, also try as ObjectId
        if ObjectId.is_valid(question_id):
            search_queries.append({"question_id": ObjectId(question_id)})
        
        sources = []
        for query in search_queries:
            logger.debug(f"Tentando query: {query}")
            # Buscar o documento completo que contém os search_results
            sources_cursor = db[ANSWERS_DATA_COLLECTION].find(
                query,
                {"search_results": 1, "_id": 0}
            ).limit(10)
            
            for document in sources_cursor:
                # Debug: mostrar a estrutura completa do documento
                logger.debug(f"Documento encontrado: {list(document.keys())}")
                
                # Acessar o array search_results
                search_results = document.get('search_results', [])
                logger.debug(f"Número de search_results encontrados: {len(search_results)}, usando as 3 primeiras")
                
                # Processar apenas as 3 primeiras fontes
                for result in search_results[:3]:  # Limitar a 3 fontes
                    source_text = f"Título: {result.get('title', 'N/A')}\n"
                    source_text += f"URL: {result.get('url', 'N/A')}\n"
                    source_text += f"Conteúdo: {result.get('content', 'N/A')}\n"
                    sources.append(source_text)
            
            # If we found sources, no need to try other queries
            if sources:
                break
        
        logger.info(f"Encontradas {len(sources)} fontes para question_id: {question_id}")
        
        # Log das fontes encontradas para debug
        if sources:
            logger.info(f"Fontes encontradas: {sources[:2]}")  # Mostrar apenas as 2 primeiras para não poluir o log
        
        # If no sources found, let's debug a bit
        if not sources:
            logger.warning(f"Nenhuma fonte encontrada para question_id: {question_id}")
            
            # Check some sample documents to understand the structure
            sample_docs = list(db[ANSWERS_DATA_COLLECTION].find({}, {"question_id": 1, "_id": 1}).limit(3))
            if sample_docs:
                logger.info("Exemplos de question_id encontrados na answers_data:")
                for doc in sample_docs:
                    logger.info(f"  _id: {doc.get('_id')}, question_id: {doc.get('question_id')} (type: {type(doc.get('question_id'))})")
            else:
                logger.warning("Nenhum documento encontrado na collection answers_data!")
        
        return sources
        
    except Exception as e:
        logger.error(f"Erro ao buscar fontes para question_id {question_id}: {str(e)}")
        return [f"Erro ao buscar fontes: {str(e)}"]

def get_question_details(question_id: str) -> Dict[str, Any]:
    """Retrieves question details from the questions collection."""
    logger.info(f"Buscando detalhes da questão: {question_id}")
    
    try:
        # Convert string to ObjectId if needed
        if ObjectId.is_valid(question_id):
            search_id = ObjectId(question_id)
            logger.debug(f"Convertendo para ObjectId: {question_id} -> {search_id}")
        else:
            search_id = question_id
            logger.debug(f"Usando string diretamente: {question_id}")
        
        question = db[QUESTIONS_COLLECTION].find_one({"_id": search_id})
        
        if question:
            # Use the serializer to handle ObjectIds properly
            result = serialize_mongodb_doc(question)
            logger.info(f"Questão encontrada: {result.get('title', 'N/A')}")
            return result
        else:
            # Try to find some sample questions to help debug
            logger.warning(f"Questão não encontrada: {question_id}")
            logger.info("Tentando listar algumas questões disponíveis...")
            
            sample_questions = list(db[QUESTIONS_COLLECTION].find({}, {"_id": 1, "title": 1}).limit(3))
            if sample_questions:
                logger.info("Exemplos de questões encontradas:")
                for q in sample_questions:
                    logger.info(f"  ID: {q['_id']} - {q.get('title', 'N/A')}")
            else:
                logger.warning("Nenhuma questão encontrada na coleção!")
            
            return {}
            
    except Exception as e:
        logger.error(f"Erro ao buscar questão {question_id}: {str(e)}")
        return {"error": str(e)}

# --- 4. Configure ENEM Agent ---

# ENEM Question Agent: Uses tools to get sources and question details
enem_agent = LlmAgent(
    model=MODEL_NAME,
    name="enem_question_agent",
    description="Agente especializado em responder questões do ENEM usando fontes relevantes.",
    instruction="""Você é um agente especializado em resolver questões do ENEM (Exame Nacional do Ensino Médio) do Brasil.

IMPORTANTE: As fontes relevantes já estão incluídas no input fornecido no campo 'sources'.
Você DEVE basear sua resposta principalmente nessas fontes fornecidas.

Suas responsabilidades:
1. Analisar o contexto da questão fornecida
2. Examinar cuidadosamente as fontes relevantes que foram fornecidas no campo 'sources'
3. Examinar todas as alternativas fornecidas
4. Fornecer um raciocínio detalhado baseado nas fontes fornecidas
5. Indicar a alternativa correta com justificativa clara
6. Citar especificamente quais fontes (por número ou título) foram usadas na resposta

Formato de resposta esperado:
- Raciocínio detalhado explicando o conceito/tópico da questão, citando as fontes
- Análise de por que cada alternativa está correta ou incorreta
- Identificação da alternativa correta
- Explicação clara do motivo da resposta
- Lista das fontes específicas que foram utilizadas (cite pelo número ou título)

Sempre baseie suas respostas nas fontes fornecidas e no conhecimento acadêmico apropriado para o nível do ensino médio brasileiro.
Se as fontes fornecidas não contiverem informação suficiente, indique isso claramente.
""",
    tools=[get_question_details],
    input_schema=QuestionInput,
    output_key="enem_response", # Store final response
)

# ENEM Agent with structured output (for API responses)
enem_structured_agent = LlmAgent(
    model=MODEL_NAME,
    name="enem_structured_agent",
    description="Agente ENEM que retorna respostas em formato JSON estruturado.",
    instruction=f"""Você é um agente especializado em resolver questões do ENEM.

IMPORTANTE: As fontes relevantes já estão incluídas no input fornecido no campo 'sources'.
Você DEVE basear sua resposta principalmente nessas fontes fornecidas.

Analise a questão fornecida e responda APENAS com um JSON estruturado conforme o schema:
{json.dumps(EnemAnswerOutput.model_json_schema(), indent=2)}

Baseie suas respostas nas fontes fornecidas no campo 'sources' e forneça:
1. reasoning: Raciocínio detalhado explicando como resolver a questão, citando as fontes específicas
2. correct_alternative: A letra da alternativa correta (A, B, C, D ou E)
3. explanation: Explicação clara do porquê essa alternativa é correta
4. sources_used: Lista das fontes específicas que foram utilizadas (cite pelo número ou título da fonte)

Use sempre linguagem clara e apropriada para estudantes do ensino médio brasileiro.
Se as fontes fornecidas não contiverem informação suficiente, indique isso claramente no reasoning.
""",
    input_schema=QuestionInput,
    output_schema=EnemAnswerOutput, # Enforce JSON output structure
    output_key="enem_structured_response", # Store final JSON response
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)

# --- 5. Set up Session Management and Runners ---
session_service = InMemorySessionService()

# Create runners for ENEM agents
enem_runner = Runner(
    agent=enem_agent,
    app_name=APP_NAME,
    session_service=session_service
)

enem_structured_runner = Runner(
    agent=enem_structured_agent,
    app_name=APP_NAME,
    session_service=session_service
)

# --- 6. Define Agent Interaction Functions ---
async def process_enem_question(
    question_id: str,
    user_id: str,
    session_id: str,
    use_structured_output: bool = False
) -> Dict[str, Any]:
    """
    Process an ENEM question using the appropriate agent.
    
    Args:
        question_id: ID of the question in MongoDB
        user_id: User identifier
        session_id: Session identifier  
        use_structured_output: Whether to use structured JSON output
    
    Returns:
        Dict containing the agent's response and metadata
    """
    
    logger.info(f"🤖 Processando questão ENEM - Question: {question_id}, User: {user_id}, Session: {session_id}")
    
    # Ensure ADK session exists before proceeding
    try:
        session_created = get_or_create_session(user_id, session_id)
        if session_created:
            logger.info(f"🆕 Nova sessão ADK criada: {session_id}")
        else:
            logger.info(f"🔄 Usando sessão ADK existente: {session_id}")
    except Exception as e:
        logger.error(f"❌ Falha ao criar/obter sessão ADK: {e}")
        return {"error": f"Failed to create/get ADK session: {str(e)}"}
    
    # Get question details from database
    question_details = get_question_details(question_id)
    if not question_details or "error" in question_details:
        return {"error": f"Question {question_id} not found or error retrieving it"}
    
    # Get relevant sources
    logger.info(f"📚 Buscando fontes para question_id: {question_id}")
    sources = get_question_sources(question_id)
    logger.info(f"📚 Fontes retornadas: {len(sources)} fontes (tipo: {type(sources)})")
    
    if sources:
        logger.info(f"📚 Primeiras 100 chars da primeira fonte: {str(sources[0])[:100] if sources else 'N/A'}")
    else:
        logger.warning(f"⚠️ NENHUMA FONTE ENCONTRADA para question_id: {question_id}")
    
    # Format sources with clear numbering and structure for better LLM comprehension
    formatted_sources = []
    if sources and len(sources) > 0:
        formatted_sources.append(f"=== FONTES RELEVANTES ({len(sources)} fontes encontradas) ===\n")
        for idx, source in enumerate(sources, 1):
            formatted_sources.append(f"--- FONTE #{idx} ---")
            formatted_sources.append(source)
            formatted_sources.append("")  # Empty line for separation
        logger.info(f"✅ Fontes formatadas com sucesso: {len(sources)} fontes")
    else:
        logger.warning("⚠️ Formatando resposta sem fontes")
        formatted_sources.append("=== NENHUMA FONTE ENCONTRADA ===")
        formatted_sources.append("Responda baseado no seu conhecimento acadêmico.")
    
    # Prepare input for agent
    question_input = {
        "question_id": question_id,
        "context": question_details["context"],
        "alternatives": question_details["alternatives"],
        "sources": formatted_sources
    }
    
    # Choose the appropriate runner and agent
    if use_structured_output:
        runner_instance = enem_structured_runner
        agent_instance = enem_structured_agent
    else:
        runner_instance = enem_runner
        agent_instance = enem_agent
    
    # Send query to agent
    logger.info(f"📤 Enviando questão para agente ADK...")
    user_content = types.Content(
        role='user', 
        parts=[types.Part(text=json.dumps(question_input))]
    )
    
    final_response_content = "No response received."
    

    try:
        logger.debug(f"🔧 Running with app_name={APP_NAME}, user_id={user_id}, session_id={session_id}")
        async for event in runner_instance.run_async(
            user_id=user_id, 
            session_id=session_id, 
            new_message=user_content
        ):
            logger.debug(f"📥 Event received from ADK")
            if event.is_final_response() and event.content and event.content.parts:
                final_response_content = event.content.parts[0].text
                logger.info(f"✅ Resposta recebida do agente ADK (tamanho: {len(final_response_content)} chars)")
    except Exception as e:
        logger.error(f"❌ Erro durante execução do agente ADK: {e}")
        logger.warning("🔄 Usando resposta de fallback devido ao erro do ADK")
    
    # Get session state
    try:
        current_session = session_service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )
        stored_output = current_session.state.get(agent_instance.output_key) if current_session.state else None
    except Exception as e:
        logger.warning(f"⚠️ Erro ao obter estado da sessão: {e}")
        stored_output = None
    
    return {
        "question_id": question_id,
        "question_details": question_details,
        "response": final_response_content,
        "stored_output": stored_output,
        "session_id": session_id,
        "sources_count": len(sources),
        "sources": sources  # Include original sources for storage in conversation metadata
    }

async def add_message_to_conversation(
    user_id: str,
    session_id: str,
    message: str,
    use_structured_output: bool = False
) -> Dict[str, Any]:
    """
    Add a message to an existing conversation session.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        message: User's message/question
        use_structured_output: Whether to use structured JSON output
    
    Returns:
        Dict containing the agent's response
    """
    
    logger.info(f"💬 Adicionando mensagem à conversa - Session: {session_id}")
    
    # Get conversation and its full history from MongoDB
    conversation = db[CONVERSATIONS_COLLECTION].find_one({"session_id": session_id})
    logger.info(f"🔍 Conversa encontrada: {conversation is not None}")
    
    if not conversation:
        logger.error(f"❌ Conversa não encontrada para session_id: {session_id}")
        return {"error": f"Conversation not found for session_id: {session_id}"}
    
    # Get conversation history
    conversation_history = conversation.get("messages", [])
    logger.info(f"📜 Histórico recuperado: {len(conversation_history)} mensagens")
    
    # Get sources for this question
    sources_context = ""
    question_id = conversation.get("question_id")
    if question_id:
        logger.info(f"📚 Recuperando fontes para question_id: {question_id}")
        sources = get_question_sources(question_id)
        logger.info(f"📚 Fontes recuperadas: {len(sources)} fontes (tipo: {type(sources)})")
        
        # Format sources with clear numbering and structure
        formatted_sources = []
        if sources and len(sources) > 0:
            formatted_sources.append(f"=== FONTES RELEVANTES ({len(sources)} fontes encontradas) ===")
            for idx, source in enumerate(sources, 1):
                formatted_sources.append(f"--- FONTE #{idx} ---")
                formatted_sources.append(source)
                formatted_sources.append("")  # Empty line for separation
            sources_context = "\n".join(formatted_sources)
            logger.info(f"✅ Contexto de fontes adicionado ({len(sources)} fontes)")
        else:
            logger.warning(f"⚠️ Nenhuma fonte encontrada para question_id: {question_id}")
    else:
        logger.warning(f"⚠️ Conversa encontrada mas sem question_id associado")
    
    # Build conversation history context
    history_context = ""
    if conversation_history:
        history_lines = ["=== HISTÓRICO DA CONVERSA ==="]
        for msg in conversation_history:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if role == "system":
                history_lines.append(f"[SISTEMA]: {content}")
            elif role == "user":
                history_lines.append(f"[USUÁRIO]: {content}")
            elif role == "agent":
                history_lines.append(f"[AGENTE]: {content}")
            else:
                history_lines.append(f"[{role.upper()}]: {content}")
        
        history_context = "\n".join(history_lines)
        logger.info(f"📜 Contexto do histórico criado ({len(history_lines)} linhas)")
    
    # Choose the appropriate runner and agent
    if use_structured_output:
        runner_instance = enem_structured_runner
        agent_instance = enem_structured_agent
    else:
        runner_instance = enem_runner
        agent_instance = enem_agent
    
    # Build complete context: History + Sources + New Message
    context_parts = []
    
    if history_context:
        context_parts.append(history_context)
    
    if sources_context:
        context_parts.append(sources_context)
    
    context_parts.append("=== NOVA MENSAGEM DO USUÁRIO ===")
    context_parts.append(message)
    
    complete_context = "\n\n".join(context_parts)
    
    # Create a new ADK session for this stateless interaction
    temp_session_id = f"temp_{session_id}_{len(conversation_history)}"
    logger.info(f"🔄 Criando sessão temporária para interação: {temp_session_id}")
    
    try:
        session_created = get_or_create_session(user_id, temp_session_id)
        logger.info(f"✅ Sessão temporária criada: {session_created}")
    except Exception as e:
        logger.error(f"❌ Falha ao criar sessão temporária: {e}")
        return {"error": f"Failed to create temporary session: {str(e)}"}
    
    # Send complete context to agent
    try:
        logger.info(f"📤 Enviando contexto completo para agente (tamanho: {len(complete_context)} chars)")
        user_content = types.Content(
            role='user',
            parts=[types.Part(text=complete_context)]
        )
        
        final_response_content = "No response received."
        logger.info(f"🔄 Iniciando comunicação com agente ADK...")
        
        async for event in runner_instance.run_async(
            user_id=user_id,
            session_id=temp_session_id,
            new_message=user_content
        ):
            logger.debug(f"📥 Event recebido do ADK: {type(event)}")
            if event.is_final_response() and event.content and event.content.parts:
                final_response_content = event.content.parts[0].text
                logger.info(f"✅ Resposta recebida do agente ADK (tamanho: {len(final_response_content)} chars)")
        
        # Clean up temporary session
        try:
            session_service.delete_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=temp_session_id
            )
            logger.debug(f"🗑️ Sessão temporária removida: {temp_session_id}")
        except:
            pass  # Ignore cleanup errors
        
        logger.info(f"🎯 Retornando resposta final")
        return {
            "response": final_response_content,
            "session_id": session_id,
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"❌ Erro durante comunicação com agente ADK: {e}")
        logger.error(f"❌ Tipo do erro: {type(e).__name__}")
        logger.error(f"❌ Detalhes do erro: {str(e)}")
        raise e

# Function to get or create session
def get_or_create_session(user_id: str, session_id: str) -> bool:
    """
    Get existing session or create a new one.
    
    Returns:
        bool: True if session was created, False if it already existed
    """
    logger.info(f"🔗 Verificando sessão ADK - User: {user_id}, Session: {session_id}")
    
    try:
        # Try to get existing session
        existing_session = session_service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )
        logger.info(f"✅ Sessão ADK já existe: {session_id}")
        logger.debug(f"   Session details: {type(existing_session)}, state: {len(str(existing_session.state)) if existing_session.state else 0} chars")
        
        # Even if session exists, let's verify it's properly initialized
        # by trying to access its state
        try:
            _ = existing_session.state
            logger.debug(f"   Session state accessible")
        except Exception as state_error:
            logger.warning(f"⚠️ Session exists but state not accessible: {state_error}")
            # Session might be corrupted, recreate it
            return _force_create_session(user_id, session_id)
        
        return False  # Session already exists and is valid
        
    except Exception as e:
        # Session doesn't exist, create it
        logger.info(f"🆕 Criando nova sessão ADK: {session_id}")
        logger.debug(f"   Reason for creation: {str(e)}")
        return _force_create_session(user_id, session_id)


def _force_create_session(user_id: str, session_id: str) -> bool:
    """Force create a new session, removing any existing one first."""
    try:
        # Check Google API Key first
        if not settings.GOOGLE_API_KEY:
            error_msg = "Google API Key not configured. Set GOOGLE_API_KEY in environment variables."
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        # Try to remove existing session if any
        try:
            session_service.delete_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id
            )
            logger.debug(f"   Removed existing session: {session_id}")
        except:
            pass  # Session didn't exist
        
        # Create new session
        logger.debug(f"   Creating session with app_name={APP_NAME}, user_id={user_id}, session_id={session_id}")
        session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )
        logger.info(f"✅ Sessão ADK criada com sucesso: {session_id}")
        
        # Verify the session was created properly
        verify_session = session_service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )
        logger.debug(f"   Verification: session type {type(verify_session)}")
        
        return True  # Session was created
        
    except Exception as create_error:
        logger.error(f"❌ Erro ao criar sessão ADK {session_id}: {create_error}")
        logger.error(f"   Error details: {type(create_error).__name__}: {str(create_error)}")
        raise create_error

# --- 7. Export the main functions for use in API ---
__all__ = [
    'process_enem_question',
    'add_message_to_conversation', 
    'get_or_create_session',
    'enem_agent',
    'enem_structured_agent',
    'session_service'
]   