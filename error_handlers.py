from typing import Any, Dict, Optional, Tuple
import logging
import traceback
from functools import wraps
from langchain_core.messages import HumanMessage, AIMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ErrorHandler:
    """Centralized error handling for the TDH Agency Assistant."""
    
    @staticmethod
    def safe_extract_info(message: str, current_info: Dict[str, Any]) -> Dict[str, Any]:
        """Safely extract applicant info with error handling."""
        try:
            from tdh_agent import extract_applicant_info
            return extract_applicant_info(message, current_info)
        except Exception as e:
            logger.error(f"Error extracting info: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return current_info
    
    @staticmethod
    def safe_llm_invoke(llm, prompt: str) -> str:
        """Safely invoke LLM with fallback."""
        try:
            response = llm.invoke(prompt)
            return str(response.content) if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.error(f"LLM invocation error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return "I apologize, but I'm having trouble processing that. Could you please rephrase?"
    
    @staticmethod
    def safe_validate_material(material_type: str, content: str) -> Tuple[bool, str]:
        """Safely validate material with error handling."""
        try:
            from tdh_agent import validate_material
            return validate_material(material_type, content)
        except Exception as e:
            logger.error(f"Material validation error for {material_type}: {e}")
            return False, f"I encountered an error validating your {material_type}. Please try submitting it again."
    
    @staticmethod
    def safe_state_update(state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Safely update state with validation."""
        try:
            # Create a copy to avoid mutating original
            updated_state = state.copy()
            
            # Validate required keys exist
            required_keys = ["messages", "applicant_info", "current_stage"]
            for key in required_keys:
                if key not in updated_state:
                    updated_state[key] = [] if key == "messages" else {} if key == "applicant_info" else "unknown"
            
            # Apply updates
            for key, value in updates.items():
                if key in updated_state or key in ["role_type", "requirements_collected", "materials_collected"]:
                    updated_state[key] = value
                else:
                    logger.warning(f"Ignoring unknown state key: {key}")
            
            return updated_state
            
        except Exception as e:
            logger.error(f"State update error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return state  # Return original state if update fails
    
    @staticmethod
    def safe_message_append(state: Dict[str, Any], message: AIMessage) -> Dict[str, Any]:
        """Safely append AI message to conversation."""
        try:
            if "messages" not in state:
                state["messages"] = []
            
            # Ensure message content is string
            if hasattr(message, 'content'):
                content = str(message.content)
            else:
                content = str(message)
                message = AIMessage(content=content)
            
            state["messages"].append(message)
            return state
            
        except Exception as e:
            logger.error(f"Message append error: {e}")
            # Create a fallback message
            fallback_message = AIMessage(content="I encountered an error processing the previous request.")
            if "messages" not in state:
                state["messages"] = []
            state["messages"].append(fallback_message)
            return state

class ConversationErrorHandler:
    """Handles conversation-specific errors."""
    
    @staticmethod
    def handle_node_execution_error(node_name: str, error: Exception, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle errors during node execution."""
        logger.error(f"Node execution error in {node_name}: {error}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Add error message to conversation
        error_message = AIMessage(
            content=f"I encountered an issue while processing your request. Let me try to help you differently. "
                   f"Could you please provide the information again?"
        )
        
        return ErrorHandler.safe_message_append(state, error_message)
    
    @staticmethod
    def handle_routing_error(current_stage: str, error: Exception, state: Dict[str, Any]) -> str:
        """Handle routing errors and provide fallback stage."""
        logger.error(f"Routing error from stage {current_stage}: {error}")
        
        # Fallback routing logic
        fallback_stages = {
            "welcome": "collect_basic_info",
            "collect_basic_info": "classify_role", 
            "classify_role": "explain_requirements_dancer",  # Default to dancer
            "materials_collection": "research_questions",
            "research_questions": "final_summary"
        }
        
        return fallback_stages.get(current_stage, "welcome")

class ValidationErrorHandler:
    """Handles validation-specific errors."""
    
    @staticmethod
    def handle_validation_error(material_type: str, error: Exception) -> Tuple[bool, str]:
        """Handle validation errors gracefully."""
        logger.error(f"Validation error for {material_type}: {error}")
        
        material_name = material_type.replace("_", " ").title()
        return False, f"I had trouble validating your {material_name}. Please provide it in the correct format and try again."
    
    @staticmethod
    def handle_input_validation_error(field_name: str, error: Exception) -> Tuple[bool, str]:
        """Handle input validation errors."""
        logger.error(f"Input validation error for {field_name}: {error}")
        
        return False, f"Please provide a valid {field_name}."

def error_handler(fallback_return=None):
    """Decorator for automatic error handling."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                
                if fallback_return is not None:
                    return fallback_return
                else:
                    # Try to return something sensible based on function name
                    if "validate" in func.__name__:
                        return False, "Validation failed due to an error."
                    elif "extract" in func.__name__:
                        return kwargs.get('current_info', {}) if 'current_info' in kwargs else {}
                    else:
                        raise e  # Re-raise if we don't know how to handle it
        return wrapper
    return decorator

class PersistenceErrorHandler:
    """Handles persistence-related errors."""
    
    @staticmethod
    def handle_save_error(thread_id: str, error: Exception) -> bool:
        """Handle state saving errors."""
        logger.error(f"Failed to save state for thread {thread_id}: {error}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False
    
    @staticmethod
    def handle_load_error(thread_id: str, error: Exception) -> Optional[Dict[str, Any]]:
        """Handle state loading errors."""
        logger.error(f"Failed to load state for thread {thread_id}: {error}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None
    
    @staticmethod
    def handle_serialization_error(data: Any, error: Exception) -> Optional[Dict[str, Any]]:
        """Handle serialization errors."""
        logger.error(f"Failed to serialize data: {error}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Try to create a minimal serializable version
        try:
            if isinstance(data, dict):
                # Keep only basic types
                safe_data = {}
                for key, value in data.items():
                    if isinstance(value, (str, int, float, bool, type(None))):
                        safe_data[key] = value
                    elif isinstance(value, dict):
                        safe_data[key] = {k: v for k, v in value.items() 
                                        if isinstance(v, (str, int, float, bool, type(None)))}
                return safe_data
        except Exception:
            logger.error("Failed to create safe serialization")
        
        return None

# Helper functions for common error scenarios
def safe_get_last_message(state: Dict[str, Any]) -> Optional[HumanMessage]:
    """Safely get the last human message from state."""
    try:
        messages = state.get("messages", [])
        if not messages:
            return None
        
        # Find last human message
        for message in reversed(messages):
            if isinstance(message, HumanMessage):
                return message
        
        return None
    except Exception as e:
        logger.error(f"Error getting last message: {e}")
        return None

def safe_stage_transition(state: Dict[str, Any], new_stage: str) -> Dict[str, Any]:
    """Safely transition to a new stage."""
    try:
        state["current_stage"] = new_stage
        logger.info(f"Stage transition to: {new_stage}")
        return state
    except Exception as e:
        logger.error(f"Stage transition error: {e}")
        # Ensure current_stage exists
        if "current_stage" not in state:
            state["current_stage"] = "welcome"
        return state