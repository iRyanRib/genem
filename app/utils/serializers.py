"""
Utility functions for serializing MongoDB data to JSON and text processing.
"""

from typing import Any, Dict, List, Union
from bson import ObjectId
from datetime import datetime
import json
import unicodedata
import re


def serialize_objectid(obj: Any) -> Any:
    """
    Recursively convert ObjectIds to strings in nested data structures.
    
    Args:
        obj: Object that may contain ObjectIds
        
    Returns:
        Object with ObjectIds converted to strings
    """
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: serialize_objectid(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_objectid(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj


def serialize_mongodb_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize a MongoDB document for JSON output.
    
    Args:
        doc: MongoDB document
        
    Returns:
        Serialized document
    """
    if not doc:
        return doc
    
    return serialize_objectid(doc)


def serialize_mongodb_docs(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Serialize a list of MongoDB documents for JSON output.
    
    Args:
        docs: List of MongoDB documents
        
    Returns:
        List of serialized documents
    """
    return [serialize_mongodb_doc(doc) for doc in docs]


class MongoJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for MongoDB data types."""
    
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def to_json(obj: Any, **kwargs) -> str:
    """
    Convert object to JSON string, handling MongoDB types.
    
    Args:
        obj: Object to serialize
        **kwargs: Additional arguments for json.dumps
        
    Returns:
        JSON string
    """
    return json.dumps(obj, cls=MongoJSONEncoder, **kwargs)


def normalize_text(text: str) -> str:
    """
    Normalize text by removing accents and converting to lowercase.
    
    This function:
    1. Removes accents and diacritical marks
    2. Converts to lowercase
    3. Keeps only alphanumeric characters and spaces
    4. Removes multiple spaces
    
    Args:
        text: Input text to normalize
        
    Returns:
        Normalized text without accents and in lowercase
        
    Example:
        >>> normalize_text("Questões de Matemática e Física")
        "questoes de matematica e fisica"
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Remove accents and diacritical marks
    normalized = unicodedata.normalize('NFD', text)
    without_accents = ''.join(char for char in normalized if unicodedata.category(char) != 'Mn')
    
    # Convert to lowercase
    lowercased = without_accents.lower()
    
    # Keep only alphanumeric characters and spaces
    cleaned = re.sub(r'[^a-z0-9\s]', ' ', lowercased)
    
    # Remove multiple spaces and strip
    final_text = re.sub(r'\s+', ' ', cleaned).strip()
    
    return final_text




