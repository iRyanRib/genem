"""
Utility functions for serializing MongoDB data to JSON.
"""

from typing import Any, Dict, List, Union
from bson import ObjectId
from datetime import datetime
import json


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



