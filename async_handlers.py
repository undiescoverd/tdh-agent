import asyncio
from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
from config import settings
import logging

logger = logging.getLogger(__name__)

class AsyncLLMHandler:
    """Async wrapper for LLM operations to enable future async support."""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.7,
            google_api_key=settings.google_api_key
        )
    
    async def agenerate_response(self, prompt: str) -> str:
        """Async version of LLM response generation."""
        try:
            # Try async invoke if available
            if hasattr(self.llm, 'ainvoke'):
                response = await self.llm.ainvoke(prompt)
                return str(response.content) if hasattr(response, 'content') else str(response)
            else:
                # Fallback to sync in thread pool
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, self.llm.invoke, prompt)
                return str(response.content) if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.error(f"Async LLM invocation error: {e}")
            # Fallback to sync
            try:
                response = self.llm.invoke(prompt)
                return str(response.content) if hasattr(response, 'content') else str(response)
            except Exception as sync_error:
                logger.error(f"Sync LLM fallback error: {sync_error}")
                return "I apologize, but I'm having trouble processing that. Could you please rephrase?"
    
    def sync_generate_response(self, prompt: str) -> str:
        """Synchronous response generation with error handling."""
        try:
            response = self.llm.invoke(prompt)
            return str(response.content) if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.error(f"LLM invocation error: {e}")
            return "I apologize, but I'm having trouble processing that. Could you please rephrase?"

class AsyncStateManager:
    """Manages async state operations for future expansion."""
    
    def __init__(self, persistence_handler):
        self.persistence = persistence_handler
    
    async def asave_state(self, thread_id: str, state: Dict[str, Any]) -> bool:
        """Async state saving."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.persistence.save_state, thread_id, state)
            return True
        except Exception as e:
            logger.error(f"Async state save error: {e}")
            return False
    
    async def aload_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Async state loading."""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.persistence.load_state, thread_id)
        except Exception as e:
            logger.error(f"Async state load error: {e}")
            return None

class AsyncConversationManager:
    """Future-ready async conversation management."""
    
    def __init__(self, llm_handler: AsyncLLMHandler, state_manager: AsyncStateManager):
        self.llm_handler = llm_handler
        self.state_manager = state_manager
    
    async def aprocess_message(self, thread_id: str, message: str) -> str:
        """Process a message asynchronously (placeholder for future implementation)."""
        # This is a placeholder for future async conversation processing
        # For now, it would need to be integrated with the existing LangGraph workflow
        
        # Load state
        state = await self.state_manager.aload_state(thread_id)
        
        # Process message (simplified example)
        response = await self.llm_handler.agenerate_response(
            f"User message: {message}. Please respond appropriately."
        )
        
        # Save updated state would go here
        # await self.state_manager.asave_state(thread_id, updated_state)
        
        return response

# Factory functions for easy integration
def create_async_llm_handler() -> AsyncLLMHandler:
    """Create an async LLM handler instance."""
    return AsyncLLMHandler()

def create_async_state_manager(persistence_handler) -> AsyncStateManager:
    """Create an async state manager instance."""
    return AsyncStateManager(persistence_handler)

def create_async_conversation_manager(persistence_handler) -> AsyncConversationManager:
    """Create a complete async conversation manager."""
    llm_handler = create_async_llm_handler()
    state_manager = create_async_state_manager(persistence_handler)
    return AsyncConversationManager(llm_handler, state_manager)