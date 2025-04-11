import logging
from typing import Optional
from langfuse.callback import CallbackHandler
from django.conf import settings

logger = logging.getLogger(__name__)

def get_langfuse_handler(plan, user) -> Optional[CallbackHandler]:
    """
    Initialize and return a Langfuse CallbackHandler.
    
    Args:
        plan: Plan instance with id attribute
        user: User instance with id attribute
        
    Returns:
        CallbackHandler if credentials are valid, None otherwise
    """
    try:
        if not all([
            settings.LANGFUSE_SECRET_KEY,
            settings.LANGFUSE_PUBLIC_KEY
        ]):
            logger.warning("Langfuse credentials not configured")
            return None
            
        if not plan or not plan.id:
            raise ValueError("Plan with id is required")
            
        if not user or not user.id:
            raise ValueError("User with id is required")
            
        return CallbackHandler(
            host=settings.LANGFUSE_HOST,
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            session_id=str(plan.id),
            user_id=str(user.id)
        )
        
    except Exception as e:
        logger.error(f"Failed to initialize Langfuse handler: {str(e)}")
        return None
