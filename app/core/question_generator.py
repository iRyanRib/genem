from typing import List, Dict, Any, Optional, TypedDict, Annotated
from enum import Enum
import json
import threading
import asyncio
from datetime import datetime

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging_config import get_logger
from app.core.groq_token_manager import get_current_groq_token
from app.core.groq_client import get_groq_client
from app.schemas.question import Question
from app.schemas.generated_question import GeneratedQuestionCreate
from app.schemas.alternative import AlternativeCreate

logger = get_logger(__name__)


class QuestionGenerationStage(str, Enum):
    """Estágios do processo de geração de questão"""
    CONTEXT_RESEARCH = "context_research"
    GENERATION = "generation"
    VALIDATION = "validation"
    REFINEMENT = "refinement"
    COMPLETED = "completed"
    FAILED = "failed"


class GeneratedQuestionData(BaseModel):
    """Estrutura da questão gerada"""
    title: str
    context: str
    alternatives_introduction: Optional[str] = None
    alternatives: List[AlternativeCreate]
    correct_alternative: str
    rationale: str
    summary: Optional[str] = None
    keywords: Optional[List[str]] = None


class QuestionGenerationState(TypedDict):
    """Estado do grafo de geração de questão"""
    messages: Annotated[List[BaseMessage], add_messages]
    stage: QuestionGenerationStage
    source_question: Question
    similar_questions: List[Question]
    user_id: str
    context_research: str
    generated_question: Optional[GeneratedQuestionData]
    validation_feedback: str
    refinement_count: int
    max_refinements: int
    error_message: Optional[str]


class QuestionGeneratorAgent:
    """Agente responsável pela geração de questões usando LangGraph"""
    
    def __init__(self):
        # Usar cliente Groq customizado
        self.groq_client = get_groq_client()
        
        # Inicializar DuckDuckGo Search
        try:
            self.search_tool = DuckDuckGoSearchRun()
            logger.info("DuckDuckGo Search Tool inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar DuckDuckGo: {e}")
            self.search_tool = None
        
        self.graph = self._build_graph()
        
        logger.info(f"QuestionGeneratorAgent inicializado com modelo: {settings.GROQ_MODEL_NAME}")
    
    def _refresh_token(self):
        """Atualiza o token GROQ para o próximo na rotação"""
        try:
            # Com o cliente customizado, o token é obtido automaticamente
            logger.info("Token GROQ será atualizado na próxima requisição")
        except Exception as e:
            logger.error(f"Erro ao atualizar token GROQ: {e}")
            raise
    
    async def _call_llm_with_retry(self, messages: List[BaseMessage], max_retries: int = 3, temperature: float = 0.7):
        """Chama o LLM com retry e troca de token em caso de erro"""
        for attempt in range(max_retries):
            try:
                # Converter BaseMessage para formato dict esperado pelo Groq
                groq_messages = []
                for msg in messages:
                    if isinstance(msg, HumanMessage):
                        groq_messages.append({"role": "user", "content": msg.content})
                    elif isinstance(msg, AIMessage):
                        groq_messages.append({"role": "assistant", "content": msg.content})
                    else:
                        groq_messages.append({"role": "user", "content": str(msg.content)})
                
                # Fazer requisição para Groq com temperatura personalizada
                result = await self.groq_client.chat_completion(
                    messages=groq_messages,
                    temperature=temperature
                )
                
                # Extrair conteúdo da resposta
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    # Criar AIMessage para compatibilidade
                    return AIMessage(content=content)
                else:
                    raise Exception("Resposta inválida do Groq")
                    
            except Exception as e:
                logger.warning(f"Erro na tentativa {attempt + 1} de chamada LLM: {e}")
                
                if attempt < max_retries - 1:  # Se não é a última tentativa
                    logger.info("Tentando com próximo token...")
                    self._refresh_token()
                    await asyncio.sleep(1)  # Pequena pausa entre tentativas
                else:
                    logger.error("Todas as tentativas falharam")
                    raise
    
    def _build_graph(self) -> StateGraph:
        """Constrói o grafo de estados para geração de questão"""
        workflow = StateGraph(QuestionGenerationState)
        
        # Adicionar nós com nomes únicos
        workflow.add_node("research_node", self._research_context)
        workflow.add_node("generation_node", self._generate_question)
        workflow.add_node("validation_node", self._validate_question)
        workflow.add_node("refinement_node", self._refine_question)
        
        # Definir fluxo
        workflow.set_entry_point("research_node")
        
        workflow.add_edge("research_node", "generation_node")
        workflow.add_edge("generation_node", "validation_node")
        
        # Condicionais após validação
        workflow.add_conditional_edges(
            "validation_node",
            self._decide_after_validation,
            {
                "refine": "refinement_node",
                "complete": END,
                "fail": END
            }
        )
        
        # Condicionais após refinamento
        workflow.add_conditional_edges(
            "refinement_node",
            self._decide_after_refinement,
            {
                "validate": "validation_node",
                "fail": END
            }
        )
        
        return workflow.compile()
    
    async def _search_internet(self, query: str) -> str:
        """Realizar busca na internet usando DuckDuckGo"""
        try:
            if not self.search_tool:
                logger.error("DuckDuckGo Search não está disponível - tool é None")
                raise Exception("DuckDuckGo Search não inicializado")
            
            # Preparar query para busca
            clean_query = " ".join(query.split()[:6])  # Máximo 6 palavras para eficiência
            
            logger.info(f"Realizando busca DuckDuckGo para: '{clean_query}'")
            
            # Realizar busca com DuckDuckGo
            search_results = self.search_tool.invoke(clean_query)
            
            logger.info(f"DuckDuckGo retornou {len(search_results)} caracteres")
            
            if search_results and len(search_results.strip()) > 10:
                logger.info("Busca DuckDuckGo realizada com sucesso")
                return f"Resultados da busca DuckDuckGo sobre '{query}':\n{search_results}"
            else:
                logger.warning("Busca DuckDuckGo retornou resultados vazios ou muito curtos")
                raise Exception("Resultados DuckDuckGo vazios")
                
        except Exception as e:
            logger.error(f"Erro na busca DuckDuckGo: {e}")
            raise Exception(f"Falha na busca DuckDuckGo: {str(e)}")
    
    async def _research_context(self, state: QuestionGenerationState) -> Dict[str, Any]:
        """Pesquisa contexto atual sobre os tópicos da questão"""
        try:
            source_question = state["source_question"]
            
            # Construir query de pesquisa baseada na questão original
            search_query = self._build_search_query(source_question)
            
            # Realizar busca na internet usando DuckDuckGo
            search_results = "Erro na busca online"
            
            try:
                search_results = await self._search_internet(search_query)
                logger.info("Busca DuckDuckGo realizada com sucesso")
            except Exception as e:
                logger.error(f"Erro na busca DuckDuckGo: {e}")
                raise Exception(f"Falha na busca online: {str(e)}")
            
            # Processar resultados da pesquisa
            context_research = f"""
            Pesquisa sobre: {search_query}
            
            Resultados encontrados:
            {search_results}
            
            Questão original como referência:
            Título: {source_question.title}
            Contexto: {source_question.context or 'Sem contexto específico'}
            Disciplina: {source_question.discipline}
            Ano: {source_question.year}
            """
            
            return {
                "stage": QuestionGenerationStage.CONTEXT_RESEARCH,
                "context_research": context_research,
                "messages": [
                    HumanMessage(content="Pesquisa de contexto concluída com sucesso.")
                ]
            }
            
        except Exception as e:
            logger.error(f"Erro na pesquisa de contexto: {e}")
            return {
                "stage": QuestionGenerationStage.FAILED,
                "error_message": f"Erro na pesquisa de contexto: {str(e)}"
            }
    
    async def _generate_question(self, state: QuestionGenerationState) -> Dict[str, Any]:
        """Gera uma nova questão baseada no contexto pesquisado"""
        try:
            source_question = state["source_question"]
            similar_questions = state["similar_questions"]
            context_research = state["context_research"]
            
            prompt = self._build_generation_prompt(
                source_question, similar_questions, context_research
            )
            
            # Tentar gerar com retry de token em caso de erro - temperatura alta para criatividade
            response = await self._call_llm_with_retry(
                [HumanMessage(content=prompt)], 
                temperature=0.7  # Alta criatividade para geração
            )
            
            # Parse da resposta para extrair a questão gerada
            generated_question = self._parse_generated_question(response.content)
            
            return {
                "stage": QuestionGenerationStage.GENERATION,
                "generated_question": generated_question,
                "messages": [
                    AIMessage(content="Questão gerada com sucesso.")
                ]
            }
            
        except Exception as e:
            logger.error(f"Erro na geração da questão: {e}")
            return {
                "stage": QuestionGenerationStage.FAILED,
                "error_message": f"Erro na geração da questão: {str(e)}"
            }
    
    async def _validate_question(self, state: QuestionGenerationState) -> Dict[str, Any]:
        """Valida a questão gerada"""
        try:
            generated_question = state["generated_question"]
            if not generated_question:
                return {
                    "stage": QuestionGenerationStage.FAILED,
                    "error_message": "Nenhuma questão foi gerada para validar"
                }
            
            validation_prompt = self._build_validation_prompt(generated_question)
            
            # Usar temperatura baixa para validação - mais determinística
            response = await self._call_llm_with_retry(
                [HumanMessage(content=validation_prompt)],
                temperature=0.2  # Baixa variabilidade para validação consistente
            )
            
            validation_feedback = response.content
            
            return {
                "stage": QuestionGenerationStage.VALIDATION,
                "validation_feedback": validation_feedback,
                "messages": [
                    AIMessage(content="Validação da questão concluída.")
                ]
            }
            
        except Exception as e:
            logger.error(f"Erro na validação da questão: {e}")
            return {
                "stage": QuestionGenerationStage.FAILED,
                "error_message": f"Erro na validação da questão: {str(e)}"
            }
    
    async def _refine_question(self, state: QuestionGenerationState) -> Dict[str, Any]:
        """Refina a questão baseada no feedback de validação"""
        try:
            generated_question = state["generated_question"]
            validation_feedback = state["validation_feedback"]
            refinement_count = state.get("refinement_count", 0)
            
            refinement_prompt = self._build_refinement_prompt(
                generated_question, validation_feedback
            )
            
            # Usar temperatura baixa para refinamento - mais preciso e determinístico
            response = await self._call_llm_with_retry(
                [HumanMessage(content=refinement_prompt)],
                temperature=0.2  # Baixa variabilidade para refinamento consistente
            )
            
            # Parse da questão refinada
            refined_question = self._parse_generated_question(response.content)
            
            return {
                "stage": QuestionGenerationStage.REFINEMENT,
                "generated_question": refined_question,
                "refinement_count": refinement_count + 1,
                "messages": [
                    AIMessage(content=f"Questão refinada (tentativa {refinement_count + 1}).")
                ]
            }
            
        except Exception as e:
            logger.error(f"Erro no refinamento da questão: {e}")
            return {
                "stage": QuestionGenerationStage.FAILED,
                "error_message": f"Erro no refinamento da questão: {str(e)}"
            }
    
    def _decide_after_validation(self, state: QuestionGenerationState) -> str:
        """Decide próximo passo após validação"""
        # Simplificar: sempre completar após primeira validação se a questão foi gerada
        generated_question = state.get("generated_question")
        
        if generated_question is not None:
            return "complete"
        else:
            return "fail"
    
    def _decide_after_refinement(self, state: QuestionGenerationState) -> str:
        """Decide próximo passo após refinamento"""
        refinement_count = state.get("refinement_count", 0)
        max_refinements = state.get("max_refinements", 3)
        
        if refinement_count >= max_refinements:
            return "fail"
        else:
            return "validate"

    def _build_search_query(self, question: Question) -> str:
        """Constrói query de pesquisa otimizada baseada na questão"""
        # Extrair palavras-chave mais importantes (máximo 3)
        keywords = []
        if question.keywords:
            keywords.extend(question.keywords[:3])
        
        # Adicionar disciplina de forma mais específica
        discipline_terms = {
            "MATEMATICA": "matemática aplicada",
            "FISICA": "física moderna",
            "QUIMICA": "química atual",
            "BIOLOGIA": "biologia contemporânea", 
            "GEOGRAFIA": "geografia atual",
            "HISTORIA": "história",
            "PORTUGUES": "língua portuguesa atual"
        }
        
        discipline_term = discipline_terms.get(question.discipline.value, question.discipline.value)
        
        # Construir query focada e concisa
        current_year = datetime.now().year
        
        if keywords:
            # Query com keywords específicas
            query = f"{' '.join(keywords)} {discipline_term} {current_year}"
        else:
            # Query genérica por disciplina
            query = f"{discipline_term} novidades {current_year}"
        
        # Limitar tamanho da query
        return query[:80]  # Máximo 80 caracteres
    
    def _build_generation_prompt(
        self, source_question: Question, similar_questions: List[Question], context_research: str
    ) -> str:
        """Constrói prompt para geração da questão"""
        similar_questions_text = "\n\n".join([
            f"Questão {i+1}:\nTítulo: {q.title}\nContexto: {q.context or 'Sem contexto'}"
            for i, q in enumerate(similar_questions[:3])
        ])
        
        # Extrair informações detalhadas da questão fonte
        source_correct_alt = getattr(source_question, 'correctAlternative', 'N/A')
        source_summary = getattr(source_question, 'summary', 'N/A')
        source_alt_intro = getattr(source_question, 'alternativesIntroduction', 'N/A')
        source_keywords = getattr(source_question, 'keywords', [])
        source_alternatives = getattr(source_question, 'alternatives', [])
        
        # Formatar alternativas da questão fonte
        source_alternatives_text = ""
        if source_alternatives:
            source_alternatives_text = "\n".join([
                f"{alt.letter}) {alt.text}" for alt in source_alternatives
            ])
        
        return f"""
        Você é um especialista em criação de questões de vestibular do tipo ENEM.
        
        CONTEXTO DA PESQUISA ATUAL:
        {context_research}
        
        QUESTÃO ORIGINAL COMO REFERÊNCIA DETALHADA:
        Título: {source_question.title}
        Contexto: {source_question.context or 'Sem contexto específico'}
        Disciplina: {source_question.discipline}
        Ano: {source_question.year}
        
        Alternativas da questão fonte:
        {source_alternatives_text}
        
        Resposta correta da fonte: {source_correct_alt}
        Introdução das alternativas da fonte: {source_alt_intro}
        Summary da questão fonte: {source_summary}
        Keywords da questão fonte: {', '.join(source_keywords) if source_keywords else 'N/A'}
        
        QUESTÕES SIMILARES PARA REFERÊNCIA (EVITE COPIAR):
        {similar_questions_text}
        
        INSTRUÇÕES:
        1. Crie uma nova questão INÉDITA baseada no contexto atual pesquisado
        2. A questão deve abordar os mesmos tópicos da questão original, mas com informações ATUAIS
        3. Use as keywords da questão fonte como guia temático
        4. Mantenha o mesmo estilo de alternativesIntroduction se relevante
        5. Crie um summary no mesmo formato da questão fonte
        6. NÃO faça apenas uma paráfrase da questão original
        7. Use o contexto da pesquisa para trazer informações recentes e relevantes
        8. Mantenha a mesma disciplina: {source_question.discipline}
        9. Crie exatamente 5 alternativas (A, B, C, D, E)
        10. Indique claramente qual é a alternativa correta
        11. Forneça um rationale detalhado para a resposta correta (campo: rationale)
        12. Use as keywords da fonte como base, mas atualize conforme necessário
        
        FORMATO DE RESPOSTA (JSON):
        {{
            "title": "Título da questão",
            "context": "Contexto/enunciado completo da questão",
            "alternatives_introduction": "Texto introdutório das alternativas (baseado na fonte: '{source_alt_intro}')",
            "alternatives": [
                {{"letter": "A", "text": "Texto da alternativa A"}},
                {{"letter": "B", "text": "Texto da alternativa B"}},
                {{"letter": "C", "text": "Texto da alternativa C"}},
                {{"letter": "D", "text": "Texto da alternativa D"}},
                {{"letter": "E", "text": "Texto da alternativa E"}}
            ],
            "correct_alternative": "A",
            "rationale": "Explicação detalhada do por que a alternativa correta está certa e as outras estão erradas",
            "summary": "Resumo da questão (similar ao formato da fonte: '{source_summary}')",
            "keywords": ["palavra1", "palavra2", "palavra3"]
        }}
        
        RESPONDA APENAS COM O JSON, SEM TEXTO ADICIONAL:
        """
    
    def _build_validation_prompt(self, generated_question: GeneratedQuestionData) -> str:
        """Constrói prompt para validação da questão"""
        return f"""
        Você é um validador especialista em questões de vestibular ENEM.
        
        QUESTÃO PARA VALIDAÇÃO:
        Título: {generated_question.title}
        Contexto: {generated_question.context}
        
        Alternativas:
        {chr(10).join([f"{alt.letter}) {alt.text}" for alt in generated_question.alternatives])}
        
        Resposta correta: {generated_question.correct_alternative}
        Rationale: {generated_question.rationale}
        
        CRITÉRIOS DE VALIDAÇÃO:
        1. A questão está bem formulada e clara?
        2. As alternativas são consistentes e do mesmo nível de dificuldade?
        3. A resposta correta é realmente a única correta?
        4. As alternativas incorretas são plausíveis mas claramente incorretas?
        5. O rationale está correto e completo?
        6. A questão testa conhecimento relevante para o ENEM?
        
        RESPONDA:
        - "APROVADO" se a questão está perfeita
        - "REFINAMENTO_NECESSÁRIO: [explicação detalhada dos problemas encontrados]" se precisa melhorar
        
        SUA AVALIAÇÃO:
        """
    
    def _build_refinement_prompt(
        self, generated_question: GeneratedQuestionData, validation_feedback: str
    ) -> str:
        """Constrói prompt para refinamento da questão"""
        return f"""
        Você precisa refinar a questão baseada no feedback de validação.
        
        QUESTÃO ATUAL:
        Título: {generated_question.title}
        Contexto: {generated_question.context}
        
        Alternativas:
        {chr(10).join([f"{alt.letter}) {alt.text}" for alt in generated_question.alternatives])}
        
        Resposta correta: {generated_question.correct_alternative}
        Rationale: {generated_question.rationale}
        
        FEEDBACK DE VALIDAÇÃO:
        {validation_feedback}
        
        INSTRUÇÕES:
        1. Corrija TODOS os problemas apontados no feedback
        2. Mantenha a essência da questão, apenas aperfeiçoe
        3. Garanta que a questão esteja no nível ENEM
        4. Verifique se todas as alternativas fazem sentido
        5. Confirme que apenas uma alternativa está correta
        
        FORMATO DE RESPOSTA (JSON):
        {{
            "title": "Título refinado da questão",
            "context": "Contexto/enunciado refinado",
            "alternatives_introduction": "Texto introdutório das alternativas (opcional)",
            "alternatives": [
                {{"letter": "A", "text": "Texto refinado da alternativa A"}},
                {{"letter": "B", "text": "Texto refinado da alternativa B"}},
                {{"letter": "C", "text": "Texto refinado da alternativa C"}},
                {{"letter": "D", "text": "Texto refinado da alternativa D"}},
                {{"letter": "E", "text": "Texto refinado da alternativa E"}}
            ],
            "correct_alternative": "A",
            "rationale": "Rationale refinado e detalhado",
            "summary": "Resumo atualizado da questão",
            "keywords": ["palavra1", "palavra2", "palavra3"]
        }}
        
        RESPONDA APENAS COM O JSON REFINADO:
        """
    
    def _parse_generated_question(self, response_content: str) -> GeneratedQuestionData:
        """Parse da resposta do LLM para extrair dados da questão"""
        try:
            # Limpar resposta para extrair apenas o JSON
            cleaned_content = response_content.strip()
            
            # Remover diferentes tipos de marcação markdown
            if cleaned_content.startswith("```json"):
                cleaned_content = cleaned_content[7:]
            elif cleaned_content.startswith("```"):
                cleaned_content = cleaned_content[3:]
                
            if cleaned_content.endswith("```"):
                cleaned_content = cleaned_content[:-3]
            
            # Limpar espaços extras
            cleaned_content = cleaned_content.strip()
            
            # Tentar encontrar o JSON válido - procurar por chaves balanceadas
            start_idx = cleaned_content.find('{')
            if start_idx == -1:
                raise ValueError("Nenhum JSON encontrado na resposta")
            
            # Contar chaves para encontrar onde o JSON termina
            brace_count = 0
            end_idx = start_idx
            for i, char in enumerate(cleaned_content[start_idx:], start_idx):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            
            # Extrair apenas o JSON válido
            json_content = cleaned_content[start_idx:end_idx]
            
            # Debug: log do conteúdo JSON extraído
            logger.debug(f"JSON extraído: {json_content[:200]}...")
            
            data = json.loads(json_content)
            
            # Converter alternativas para o formato correto
            correct_letter = data["correct_alternative"].upper()
            alternatives = [
                AlternativeCreate(
                    letter=alt["letter"],
                    text=alt["text"],
                    isCorrect=(alt["letter"].upper() == correct_letter)
                )
                for alt in data["alternatives"]
            ]
            
            return GeneratedQuestionData(
                title=data["title"],
                context=data["context"],
                alternatives_introduction=data.get("alternatives_introduction"),
                alternatives=alternatives,
                correct_alternative=data["correct_alternative"],
                rationale=data["rationale"],
                summary=data.get("summary"),
                keywords=data.get("keywords", [])
            )
            
        except Exception as e:
            logger.error(f"Erro ao fazer parse da questão gerada: {e}")
            logger.error(f"Conteúdo da resposta: {response_content}")
            raise
    
    async def generate_question(
        self,
        source_question: Question,
        similar_questions: List[Question],
        user_id: str,
        max_refinements: int = 3
    ) -> Dict[str, Any]:
        """Gera uma nova questão baseada na questão original"""
        try:
            initial_state = QuestionGenerationState(
                messages=[],
                stage=QuestionGenerationStage.CONTEXT_RESEARCH,
                source_question=source_question,
                similar_questions=similar_questions,
                user_id=user_id,
                context_research="",
                generated_question=None,
                validation_feedback="",
                refinement_count=0,
                max_refinements=max_refinements,
                error_message=None
            )
            
            # Executar o grafo
            final_state = await self.graph.ainvoke(initial_state)
            
            if final_state["stage"] == QuestionGenerationStage.FAILED:
                return {
                    "success": False,
                    "error": final_state.get("error_message", "Erro desconhecido na geração")
                }
            
            # Converter para formato de criação
            generated_data = final_state["generated_question"]
            if not generated_data:
                return {
                    "success": False,
                    "error": "Nenhuma questão foi gerada"
                }
            
            generated_question = GeneratedQuestionCreate(
                title=generated_data.title,
                index=1,  # Será ajustado no serviço
                discipline=source_question.discipline,
                language=source_question.language,
                year=datetime.now().year,
                context=generated_data.context,
                correctAlternative=generated_data.correct_alternative,
                alternativesIntroduction=generated_data.alternatives_introduction,
                alternatives=generated_data.alternatives,
                summary=generated_data.summary,
                keywords=generated_data.keywords,
                questionTopics=source_question.questionTopics,
                user=user_id,
                rationale=generated_data.rationale,
                source_question_id=source_question.id
            )
            
            return {
                "success": True,
                "generated_question": generated_question,
                "refinement_count": final_state.get("refinement_count", 0)
            }
            
        except Exception as e:
            logger.error(f"Erro geral na geração de questão: {e}")
            return {
                "success": False,
                "error": f"Erro na geração da questão: {str(e)}"
            }


# Singleton instance - lazy initialization
_question_generator = None
_generator_lock = threading.Lock()


def get_question_generator() -> QuestionGeneratorAgent:
    """Obtém a instância singleton do gerador de questões (lazy initialization)"""
    global _question_generator
    
    if _question_generator is None:
        with _generator_lock:
            if _question_generator is None:
                _question_generator = QuestionGeneratorAgent()
    
    return _question_generator


# Para compatibilidade com código existente
question_generator = get_question_generator