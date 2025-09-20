from typing import List, Optional, Dict, Any, Annotated
from datetime import datetime
from pydantic import BaseModel, Field, BeforeValidator, ConfigDict
from bson import ObjectId


def validate_object_id(v: Any) -> ObjectId:
    """Validate ObjectId from string or ObjectId."""
    if isinstance(v, ObjectId):
        return v
    if isinstance(v, str):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    raise ValueError("Invalid ObjectId format")


# Type annotation for ObjectId fields
PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]


class MessageModel(BaseModel):
    role: str = Field(..., description="Role of the message sender (user, agent, system)")
    content: str = Field(..., description="Content of the message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the message was sent")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional message metadata")

    model_config = ConfigDict(
        json_encoders={ObjectId: str},
        arbitrary_types_allowed=True
    )


class ConversationModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=lambda: ObjectId(), alias="_id")
    session_id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="User identifier")
    question_id: Optional[str] = Field(default=None, description="Original ENEM question ID if conversation started from a question")
    title: Optional[str] = Field(default=None, description="Conversation title")
    messages: List[MessageModel] = Field(default=[], description="List of messages in the conversation")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the conversation was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When the conversation was last updated")
    is_active: bool = Field(default=True, description="Whether the conversation is active")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional conversation metadata")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


# Request/Response schemas for API
class OpenConversationRequest(BaseModel):
    question_id: str = Field(..., description="ID of the ENEM question to start conversation with")
    user_id: str = Field(..., description="User identifier")
    structured_output: bool = Field(default=False, description="Whether to return structured JSON response")


class OpenConversationResponse(BaseModel):
    session_id: str = Field(..., description="Generated session ID for the conversation")
    conversation_id: str = Field(..., description="MongoDB conversation document ID")
    question_details: Dict[str, Any] = Field(..., description="Details of the ENEM question")
    agent_response: str = Field(..., description="Agent's response to the question")
    sources_count: int = Field(..., description="Number of sources used")
    created_at: datetime = Field(..., description="When the conversation was created")


class AddMessageRequest(BaseModel):
    session_id: str = Field(..., description="Session ID of the conversation")
    user_id: str = Field(..., description="User identifier")
    message: str = Field(..., description="User's message/question")
    structured_output: bool = Field(default=False, description="Whether to return structured JSON response")


class AddMessageResponse(BaseModel):
    session_id: str = Field(..., description="Session ID of the conversation")
    conversation_id: str = Field(..., description="MongoDB conversation document ID")
    user_message: str = Field(..., description="The user's original message")
    agent_response: str = Field(..., description="Agent's response")
    timestamp: datetime = Field(..., description="When the message was processed")


class ConversationHistoryResponse(BaseModel):
    conversation_id: str = Field(..., description="MongoDB conversation document ID")
    session_id: str = Field(..., description="Session ID")
    question_id: Optional[str] = Field(default=None, description="Original question ID if applicable")
    title: Optional[str] = Field(default=None, description="Conversation title")
    messages: List[MessageModel] = Field(..., description="All messages in the conversation")
    created_at: datetime = Field(..., description="When the conversation was created")
    updated_at: datetime = Field(..., description="When the conversation was last updated")
    message_count: int = Field(..., description="Total number of messages")


# Schema for ENEM question response (structured)
class EnemQuestionResponse(BaseModel):
    reasoning: str = Field(..., description="Detailed reasoning explaining how to solve the question")
    correct_alternative: str = Field(..., description="The letter of the correct alternative (A, B, C, D, or E)")
    explanation: str = Field(..., description="Explanation of why this alternative is correct")
    sources_used: List[str] = Field(..., description="List of sources that were most relevant for answering")
    confidence_level: Optional[str] = Field(default=None, description="Agent's confidence in the answer")
