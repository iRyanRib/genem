from typing import List, Optional, Dict, Any
from datetime import datetime
import random
import uuid

from bson import ObjectId

from app.schemas.exam import (
    Exam, ExamCreate, ExamUpdate, ExamQuestion, ExamStatus,
    ExamSummary, ExamDetails, QuestionForExam, ExamForUser
)
from app.schemas.question import Question, DisciplineType
from app.services.question import QuestionService
from app.services.base import MongoService
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ExamService(MongoService):
    """Serviço para operações CRUD de Exams"""
    
    def __init__(self):
        super().__init__("exams")
        # Usar o serviço real de questões
        self.question_service = QuestionService()
    
    def create_exam(self, exam_data: ExamCreate) -> Exam:
        """Criar um novo exame"""
        logger.info(f"🎯 Criando exame para usuário {exam_data.user_id}")
        logger.info(f"📝 Dados recebidos - Topics: {exam_data.topics}, Years: {exam_data.years}, Count: {exam_data.question_count}")
        logger.info(f"🔄 ExamReplicId: {exam_data.exam_replic_id}")
        
        try:
            # Se exam_replic_id for fornecido, replicar exatamente as questões desse exame
            selected_questions = []
            
            # Verificar se há ID de replicação
            replic_id = exam_data.exam_replic_id
            if replic_id:
                logger.info(f"🔁 Replicando questões do exame {replic_id} para novo exame")
                try:
                    existing_exam = self.get_by_id(replic_id)
                    if not existing_exam:
                        logger.error(f"❌ Exame para replicação não encontrado: {replic_id}")
                        raise ValueError(f"Exame para replicação não encontrado: {replic_id}")

                    logger.info(f"✅ Exame original encontrado com {len(existing_exam.get('questions', []))} questões")
                    
                    # Extrair question ids do exame existente e buscar cada questão
                    question_ids = [q.get('question_id') for q in existing_exam.get('questions', [])]
                    logger.info(f"📋 IDs das questões para replicar: {question_ids}")
                    
                    for i, qid in enumerate(question_ids):
                        # Usar serviço de questões para obter objeto Question
                        question_obj = self.question_service.get_question_by_id(str(qid))
                        if question_obj:
                            selected_questions.append(question_obj)
                            logger.info(f"✅ Questão {i+1}/{len(question_ids)} replicada: {qid}")
                        else:
                            logger.warning(f"⚠️ Questão não encontrada para replicar: {qid}")
                    
                    logger.info(f"🎯 Total de questões replicadas: {len(selected_questions)}")
                    
                    # Para replicação, usar o número exato de questões do exame original
                    # IGNORAR o question_count passado no request
                    if len(selected_questions) == 0:
                        raise ValueError("Nenhuma questão válida encontrada no exame para replicação")
                        
                except Exception as e:
                    logger.error(f"❌ Erro ao replicar exame {replic_id}: {e}")
                    raise e
            else:
                logger.info("🎲 Selecionando questões aleatórias (sem replicação)")
                # Selecionar questões baseado nos filtros
                selected_questions = self._select_questions(
                    topics=exam_data.topics,
                    years=exam_data.years,
                    question_count=exam_data.question_count
                )
            
            # Criar questões do exame
            exam_questions = []
            for question in selected_questions:
                exam_question = ExamQuestion(
                    question_id=question.id,
                    correct_answer=question.correctAlternative
                )
                exam_questions.append(exam_question)

            # Se não há questões selecionadas, falhar explicitamente
            if not exam_questions:
                raise ValueError("Nenhuma questão encontrada para os filtros informados")
            
            # Criar dados do exame para inserção no MongoDB
            exam_data_dict = {
                "user_id": ObjectId(exam_data.user_id),  # Converter para ObjectId
                "questions": [
                    {
                        "question_id": ObjectId(q.question_id),  # Converter para ObjectId
                        "user_answer": q.user_answer,
                        "correct_answer": q.correct_answer,
                        "is_correct": q.is_correct
                    }
                    for q in exam_questions
                ],
                "total_questions": len(exam_questions),
                "total_correct_answers": 0,
                "total_wrong_answers": 0,
                "status": ExamStatus.NOT_STARTED,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "finished_at": None
            }
            
            # Salvar no MongoDB
            created_exam_data = self.create(exam_data_dict)
            if not created_exam_data:
                raise Exception("Falha ao criar exame no banco de dados")
            
            # Converter para objeto Exam
            exam = Exam(**created_exam_data)
            
            logger.info(f"✅ Exame criado com sucesso - ID: {exam.id}, Questões: {len(exam_questions)}")
            return exam
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar exame: {e}")
            raise e
    
    def _convert_exam_data(self, exam_data: Dict[str, Any]) -> Dict[str, Any]:
        """Converter ObjectIds para strings nos dados do exame"""
        if not exam_data:
            return exam_data
            
        # Converter user_id de ObjectId para string
        if "user_id" in exam_data and isinstance(exam_data["user_id"], ObjectId):
            exam_data["user_id"] = str(exam_data["user_id"])
        
        # Converter question_id nas questões de ObjectId para string
        if "questions" in exam_data and isinstance(exam_data["questions"], list):
            for question in exam_data["questions"]:
                if "question_id" in question and isinstance(question["question_id"], ObjectId):
                    question["question_id"] = str(question["question_id"])
        
        return exam_data
    
    def get_exam(self, exam_id: str) -> Optional[Exam]:
        """Obter exame por ID"""
        exam_data = self.get_by_id(exam_id)
        if not exam_data:
            return None
        
        # Converter ObjectIds para strings
        exam_data = self._convert_exam_data(exam_data)
        return Exam(**exam_data)
    
    def get_exam_for_user(self, exam_id: str, user_id: str) -> Optional[ExamForUser]:
        """Obter exame formatado para o usuário responder (sem gabarito)"""
        exam_data = self.get_by_id(exam_id)
        if not exam_data:
            return None
            
        # Converter ObjectIds para strings
        exam_data = self._convert_exam_data(exam_data)
        
        # Verificar se o exame pertence ao usuário
        if exam_data.get("user_id") != user_id:
            return None
        
        exam = Exam(**exam_data)
        
        # Buscar questões usando agregação para otimizar performance
        question_ids = [ObjectId(q["question_id"]) for q in exam_data["questions"]]

        # Usar agregação MongoDB para buscar questões sem gabarito
        # Importante: preservar a ordem das questões conforme salvo no exame original
        pipeline = [
            {"$match": {"_id": {"$in": question_ids}}},
            # Criar um campo auxiliar com o índice da questão na lista original
            {"$addFields": {"__order": {"$indexOfArray": [question_ids, "$_id"]}}},
            {"$sort": {"__order": 1}},
            {"$project": {
                "_id": 1,
                "year": 1,
                "discipline": 1,
                "context": 1,
                "alternativesIntroduction": 1,
                "alternatives.letter": 1,
                "alternatives.text": 1,
                "alternatives.base64File": 1  # Incluir base64File das alternativas
                # isCorrect removido da projeção
            }}
        ]

        try:
            questions_collection = self.question_service._get_collection()
            questions_cursor = questions_collection.aggregate(pipeline)
            questions_data = list(questions_cursor)

            # Converter para formato esperado preservando ordem
            questions_for_user = []
            for q_data in questions_data:
                question_for_user = QuestionForExam(
                    id=str(q_data["_id"]),
                    year=q_data["year"],
                    discipline=q_data["discipline"],
                    context=q_data.get("context", ""),
                    alternatives_introduction=q_data.get("alternativesIntroduction"),
                    alternatives=q_data.get("alternatives", [])
                )
                questions_for_user.append(question_for_user)

        except Exception as e:
            logger.warning(f"Erro na agregação, usando busca individual: {e}")
            # Fallback para busca individual se agregação falhar (preserva ordem)
            questions_for_user = []
            for exam_question in exam.questions:
                question = self.question_service.get_question_by_id(exam_question.question_id)
                if question:
                    alternatives_clean = [
                        {
                            "letter": alt.letter, 
                            "text": alt.text,
                            "base64File": getattr(alt, 'base64File', None)
                        }
                        for alt in question.alternatives
                    ]

                    question_for_user = QuestionForExam(
                        id=question.id,
                        year=question.year,
                        discipline=question.discipline.value,
                        context=question.context or "",
                        alternatives_introduction=question.alternativesIntroduction,
                        alternatives=alternatives_clean
                    )
                    questions_for_user.append(question_for_user)
        
        # Contar questões respondidas
        answered_count = sum(1 for q in exam.questions if q.user_answer is not None)
        
        return ExamForUser(
            id=exam.id,
            status=exam.status,
            total_questions=exam.total_questions,
            answered_questions=answered_count,
            questions=questions_for_user,
            created_at=exam.created_at
        )
    
    def get_exam_details(self, exam_id: str, user_id: str) -> Optional[ExamDetails]:
        """Obter exame com detalhes completos (gabarito + respostas)"""
        exam_data = self.get_by_id(exam_id)
        if not exam_data or exam_data.get("user_id") != user_id:
            return None
        
        exam = Exam(**exam_data)
        return ExamDetails(**exam.model_dump())
    
    def update_answer(self, exam_id: str, user_id: str, update_data: ExamUpdate) -> Optional[Exam]:
        """Atualizar resposta do usuário no exame"""
        exam_data = self.get_by_id(exam_id)
        if not exam_data or exam_data.get("user_id") != user_id:
            return None
        
        if exam_data.get("status") == ExamStatus.FINISHED:
            raise ValueError("Não é possível alterar respostas de um exame finalizado")
        
        # Encontrar a questão e atualizar resposta usando update direto no MongoDB
        question_found = False
        update_fields = {}
        
        for i, question in enumerate(exam_data["questions"]):
            if question["question_id"] == update_data.question_id:
                question_found = True
                user_answer = update_data.user_answer.upper()
                is_correct = user_answer == question["correct_answer"]
                
                # Atualizar campos específicos usando dot notation
                update_fields[f"questions.{i}.user_answer"] = user_answer
                update_fields[f"questions.{i}.is_correct"] = is_correct
                update_fields["updated_at"] = datetime.utcnow()
                
                # Atualizar status para em progresso se for a primeira resposta
                if exam_data.get("status") == ExamStatus.NOT_STARTED:
                    update_fields["status"] = ExamStatus.IN_PROGRESS
                
                break
        
        if not question_found:
            raise ValueError(f"Questão {update_data.question_id} não encontrada no exame")
        
        # Atualizar no banco usando MongoDB update
        updated_exam_data = self.update(exam_id, update_fields)
        if not updated_exam_data:
            raise Exception("Falha ao atualizar exame no banco de dados")
        
        exam = Exam(**updated_exam_data)
        
        logger.info(f"📝 Resposta atualizada - Exame: {exam_id}, Questão: {update_data.question_id}, Resposta: {update_data.user_answer}")
        return exam
    
    def finalize_exam(self, exam_id: str, user_id: str) -> Optional[Exam]:
        """Finalizar exame e calcular métricas"""
        exam_data = self.get_by_id(exam_id)
        if not exam_data or exam_data.get("user_id") != user_id:
            return None
        
        if exam_data.get("status") == ExamStatus.FINISHED:
            raise ValueError("Exame já está finalizado")
        
        # Verificar se todas as questões foram respondidas
        unanswered = [q for q in exam_data["questions"] if q.get("user_answer") is None]
        if unanswered:
            raise ValueError(f"Ainda há {len(unanswered)} questões sem resposta")
        
        # Calcular métricas
        correct_count = sum(1 for q in exam_data["questions"] if q.get("is_correct", False))
        total_questions = exam_data["total_questions"]
        wrong_count = total_questions - correct_count
        
        # Atualizar no banco usando uma única operação
        update_fields = {
            "total_correct_answers": correct_count,
            "total_wrong_answers": wrong_count,
            "status": ExamStatus.FINISHED,
            "finished_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        updated_exam_data = self.update(exam_id, update_fields)
        if not updated_exam_data:
            raise Exception("Falha ao finalizar exame no banco de dados")
        
        exam = Exam(**updated_exam_data)
        
        logger.info(f"🏁 Exame finalizado - ID: {exam_id}, Acertos: {correct_count}/{total_questions}")
        return exam
    
    def delete_exam(self, exam_id: str, user_id: str) -> bool:
        """Deletar exame"""
        exam_data = self.get_by_id(exam_id)
        if not exam_data or exam_data.get("user_id") != user_id:
            return False
        
        success = self.delete(exam_id)
        if success:
            logger.info(f"🗑️ Exame deletado - ID: {exam_id}")
        return success
    
    def get_user_exams(self, user_id: str, skip: int = 0, limit: int = 50, 
                       created_after: Optional[datetime] = None, 
                       created_before: Optional[datetime] = None,
                       status: Optional[str] = None) -> List[ExamSummary]:
        """Listar exames do usuário com paginação e filtros de data e status"""
        
        try:
            # Converter user_id string para ObjectId para consulta no MongoDB
            user_object_id = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
            
            # Preparar filtros adicionais para datas e status
            additional_filters = {}
            if created_after or created_before:
                date_filter = {}
                if created_after:
                    date_filter["$gte"] = created_after
                if created_before:
                    date_filter["$lte"] = created_before
                additional_filters["created_at"] = date_filter
            
            # Adicionar filtro de status
            if status:
                additional_filters["status"] = status
            
            # Buscar exames com paginação direta no MongoDB
            exams_data = self.get_multi(
                skip=skip,
                limit=limit,
                sort_by="created_at",
                sort_order=-1,  # Mais recentes primeiro
                user_id=user_object_id,  # Usar ObjectId na consulta
                **additional_filters  # Filtros de data
            )
        except Exception as e:
            logger.error(f"Erro ao converter user_id para ObjectId: {e}")
            # Fallback para busca com string
            exams_data = self.get_multi(
                skip=skip,
                limit=limit,
                sort_by="created_at",
                sort_order=-1,
                user_id=user_id
            )
        
        # Converter para resumos
        exam_summaries = []
        for exam_data in exams_data:
            try:
                # Calcular quantas questões foram respondidas (user_answer não nulo)
                answered_questions = 0
                if "questions" in exam_data:
                    answered_questions = sum(
                        1 for q in exam_data["questions"] 
                        if q.get("user_answer") is not None
                    )
                
                summary = ExamSummary(
                    id=exam_data["id"],
                    user_id=exam_data["user_id"],
                    total_questions=exam_data["total_questions"],
                    answered_questions=answered_questions,
                    total_correct_answers=exam_data.get("total_correct_answers", 0),
                    total_wrong_answers=exam_data.get("total_wrong_answers", 0),
                    status=exam_data["status"],
                    created_at=exam_data["created_at"],
                    updated_at=exam_data["updated_at"],
                    finished_at=exam_data.get("finished_at")
                )
                exam_summaries.append(summary)
            except Exception as e:
                logger.warning(f"Erro ao converter exame {exam_data.get('id', 'unknown')}: {e}")
                continue
        
        return exam_summaries
    
    def count_user_exams(self, user_id: str, 
                         created_after: Optional[datetime] = None, 
                         created_before: Optional[datetime] = None,
                         status: Optional[str] = None) -> int:
        """Contar total de exames do usuário de forma eficiente com filtros de data e status"""
        try:
            # Converter user_id string para ObjectId para consulta no MongoDB
            user_object_id = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
            
            # Preparar filtros
            filters = {"user_id": user_object_id}
            
            # Adicionar filtros de data
            if created_after or created_before:
                date_filter = {}
                if created_after:
                    date_filter["$gte"] = created_after
                if created_before:
                    date_filter["$lte"] = created_before
                filters["created_at"] = date_filter
            
            # Adicionar filtro de status
            if status:
                filters["status"] = status
            
            # Usar count_documents para contar eficientemente
            collection = self._get_collection()
            count = collection.count_documents(filters)
            return count
            
        except Exception as e:
            logger.error(f"Erro ao contar exames do usuário {user_id}: {e}")
            return 0
    
    def _select_questions(
        self,
        topics: Optional[List[str]] = None,
        years: Optional[List[int]] = None,
        question_count: int = 25
    ) -> List[Question]:
        """Selecionar questões baseado nos filtros usando agregação MongoDB"""
        
        try:
            # Se não há filtros específicos, selecionar questões distribuidas por disciplina
            if not topics and not years:
                return self._select_questions_by_discipline(question_count)
            
            # Preparar pipeline de agregação MongoDB
            pipeline = []
            
            # Etapa de match com filtros
            match_stage = {}
            
            if years:
                match_stage["year"] = {"$in": years}
            
            if topics:
                # Converter strings para ObjectId para comparar com questionTopics
                try:
                    topic_object_ids = []
                    for topic in topics:
                        if isinstance(topic, str) and ObjectId.is_valid(topic):
                            topic_object_ids.append(ObjectId(topic))
                        elif isinstance(topic, ObjectId):
                            topic_object_ids.append(topic)
                        else:
                            logger.warning(f"Tópico inválido ignorado: {topic}")
                    
                    if topic_object_ids:
                        match_stage["questionTopics"] = {"$in": topic_object_ids}
                    else:
                        logger.warning("Nenhum tópico válido encontrado")
                        
                except Exception as e:
                    logger.error(f"Erro ao converter tópicos para ObjectId: {e}")
                    # Se falhar, tentar como string mesmo
                    match_stage["questionTopics"] = {"$in": topics}
            
            # Adicionar match stage se houver filtros
            if match_stage:
                pipeline.append({"$match": match_stage})
            
            # Adicionar sample para seleção aleatória
            pipeline.append({"$sample": {"size": question_count}})
            
            # Executar agregação
            questions_collection = self.question_service._get_collection()
            questions_cursor = questions_collection.aggregate(pipeline)
            questions_data = list(questions_cursor)
            
            # Converter dados para objetos Question
            questions = []
            for data in questions_data:
                try:
                    # Usar método da classe base para converter todos os ObjectIds
                    converted_data = self._object_id_to_str(data.copy())
                    question = Question(**converted_data)
                    questions.append(question)
                except Exception as e:
                    logger.warning(f"Erro ao converter questão {data.get('_id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Selecionadas {len(questions)} questões para o exame via agregação")
            return questions
            
        except Exception as e:
            logger.error(f"Erro na agregação de questões: {e}")
            # Fallback para método anterior se agregação falhar
            return self._select_questions_fallback(topics, years, question_count)
    
    def _select_questions_by_discipline(self, question_count: int) -> List[Question]:
        """Selecionar questões por disciplina usando agregação (distribuição proporcional por disciplina)"""
        try:
            all_questions = []
            
            # Lista das disciplinas principais do ENEM
            disciplines = [
                DisciplineType.CIENCIAS_HUMANAS,
                DisciplineType.CIENCIAS_NATUREZA, 
                DisciplineType.LINGUAGENS,
                DisciplineType.MATEMATICA
            ]
            
            # Calcular quantas questões por disciplina baseado no total solicitado
            questions_per_discipline = max(1, question_count // len(disciplines))
            remaining_questions = question_count % len(disciplines)
            
            # Buscar por disciplina usando agregação MongoDB para seleção aleatória
            for i, discipline in enumerate(disciplines):
                try:
                    # Adicionar uma questão extra para as primeiras disciplinas se houver resto
                    current_discipline_count = questions_per_discipline
                    if i < remaining_questions:
                        current_discipline_count += 1
                    
                    # Pipeline de agregação para seleção aleatória
                    pipeline = [
                        {"$match": {"discipline": discipline.value}},
                        {"$sample": {"size": current_discipline_count}}
                    ]
                    
                    questions_collection = self.question_service._get_collection()
                    questions_cursor = questions_collection.aggregate(pipeline)
                    discipline_questions = list(questions_cursor)
                    
                    # Converter dados para objetos Question
                    for data in discipline_questions:
                        try:
                            # Usar método da classe base para converter todos os ObjectIds
                            converted_data = self._object_id_to_str(data.copy())
                            question = Question(**converted_data)
                            all_questions.append(question)
                        except Exception as e:
                            logger.warning(f"Erro ao converter questão da disciplina {discipline.value}: {e}")
                            continue
                            
                    logger.debug(f"Selecionadas {len(discipline_questions)} questões aleatórias da disciplina {discipline.value}")
                    
                except Exception as e:
                    logger.warning(f"Erro ao buscar questões da disciplina {discipline.value}: {e}")
                    continue
            
            # Limitar ao total solicitado se necessário (garantia extra)
            if len(all_questions) > question_count:
                all_questions = random.sample(all_questions, question_count)
            
            logger.info(f"Selecionadas {len(all_questions)} questões distribuídas por disciplina (solicitadas: {question_count})")
            return all_questions
            
        except Exception as e:
            logger.error(f"Erro na seleção por disciplina: {e}")
            return []
    
    def _select_questions_fallback(
        self,
        topics: Optional[List[str]] = None,
        years: Optional[List[int]] = None,
        question_count: int = 25
    ) -> List[Question]:
        """Fallback para seleção de questões usando método anterior"""
        try:
            # Preparar filtros para busca
            filters = {}
            
            if years:
                filters["year"] = {"$in": years}
            
            if topics:
                # Converter strings para ObjectId para comparar com questionTopics
                try:
                    topic_object_ids = []
                    for topic in topics:
                        if isinstance(topic, str) and ObjectId.is_valid(topic):
                            topic_object_ids.append(ObjectId(topic))
                        elif isinstance(topic, ObjectId):
                            topic_object_ids.append(topic)
                        else:
                            logger.warning(f"Tópico inválido ignorado no fallback: {topic}")
                    
                    if topic_object_ids:
                        filters["questionTopics"] = {"$in": topic_object_ids}
                    else:
                        logger.warning("Nenhum tópico válido encontrado no fallback")
                        
                except Exception as e:
                    logger.error(f"Erro ao converter tópicos para ObjectId no fallback: {e}")
                    # Se falhar, tentar como string mesmo
                    filters["questionTopics"] = {"$in": topics}
            
            # Buscar questões filtradas
            questions_data = self.question_service.get_multi(
                skip=0,
                limit=question_count * 3,  # Buscar mais para ter opções aleatórias
                **filters
            )
            
            # Converter dados para objetos Question
            questions = []
            for data in questions_data:
                try:
                    question = Question(**data)
                    questions.append(question)
                except Exception as e:
                    logger.warning(f"Erro ao converter questão {data.get('id', 'unknown')}: {e}")
                    continue
            
            # Seleção aleatória se houver mais que o solicitado
            if len(questions) > question_count:
                questions = random.sample(questions, question_count)
            
            logger.info(f"Selecionadas {len(questions)} questões (fallback)")
            return questions
            
        except Exception as e:
            logger.error(f"Erro no fallback de seleção: {e}")
            return []
    
    def get_user_totalizers(self, user_id: str) -> Dict[str, Any]:
        """
        Obter totalizadores/estatísticas completas de todos os exames do usuário.
        
        Retorna métricas agregadas considerando TODOS os exames, não apenas os paginados.
        """
        try:
            # Converter user_id string para ObjectId
            user_object_id = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
            
            # Usar agregação MongoDB para calcular estatísticas de forma eficiente
            collection = self._get_collection()
            
            # Pipeline de agregação para calcular todas as métricas
            pipeline = [
                {"$match": {"user_id": user_object_id}},
                {
                    "$group": {
                        "_id": None,
                        "total_exams": {"$sum": 1},
                        "finished_exams": {
                            "$sum": {
                                "$cond": [{"$eq": ["$status", "finished"]}, 1, 0]
                            }
                        },
                        "in_progress_exams": {
                            "$sum": {
                                "$cond": [{"$eq": ["$status", "in_progress"]}, 1, 0]
                            }
                        },
                        "not_started_exams": {
                            "$sum": {
                                "$cond": [{"$eq": ["$status", "not_started"]}, 1, 0]
                            }
                        },
                        "total_questions_answered": {
                            "$sum": {
                                "$cond": [
                                    {"$eq": ["$status", "finished"]},
                                    "$total_questions",
                                    0
                                ]
                            }
                        },
                        "total_correct_answers": {
                            "$sum": "$total_correct_answers"
                        },
                        "total_wrong_answers": {
                            "$sum": "$total_wrong_answers"
                        }
                    }
                }
            ]
            
            result = list(collection.aggregate(pipeline))
            
            # Se não houver resultados, retornar zeros
            if not result:
                return {
                    "total_exams": 0,
                    "finished_exams": 0,
                    "in_progress_exams": 0,
                    "not_started_exams": 0,
                    "total_questions_answered": 0,
                    "total_correct_answers": 0,
                    "total_wrong_answers": 0,
                    "average_score": 0.0
                }
            
            stats = result[0]
            
            # Calcular média de acerto
            total_questions = stats.get("total_questions_answered", 0)
            total_correct = stats.get("total_correct_answers", 0)
            average_score = round(total_correct / total_questions * 100, 1) if total_questions > 0 else 0.0
            
            return {
                "total_exams": stats.get("total_exams", 0),
                "finished_exams": stats.get("finished_exams", 0),
                "in_progress_exams": stats.get("in_progress_exams", 0),
                "not_started_exams": stats.get("not_started_exams", 0),
                "total_questions_answered": stats.get("total_questions_answered", 0),
                "total_correct_answers": stats.get("total_correct_answers", 0),
                "total_wrong_answers": stats.get("total_wrong_answers", 0),
                "average_score": average_score
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter totalizadores do usuário {user_id}: {e}")
            return {
                "total_exams": 0,
                "finished_exams": 0,
                "in_progress_exams": 0,
                "not_started_exams": 0,
                "total_questions_answered": 0,
                "total_correct_answers": 0,
                "total_wrong_answers": 0,
                "average_score": 0.0
            }


# Singleton instance
exam_service = ExamService()