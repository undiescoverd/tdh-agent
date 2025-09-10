import json
from pathlib import Path
from typing import Dict, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationPersistence:
    def __init__(self, storage_dir: str = ".conversation_cache"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
    
    def _serialize_messages(self, messages: list) -> list:
        """Convert messages to JSON-serializable format."""
        serialized = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                serialized.append({"type": "human", "content": msg.content})
            elif isinstance(msg, AIMessage):
                serialized.append({"type": "ai", "content": msg.content})
            else:
                # Fallback for other message types
                serialized.append({"type": "unknown", "content": str(msg)})
        return serialized
    
    def _deserialize_messages(self, messages_data: list) -> list:
        """Convert JSON data back to message objects."""
        messages = []
        for msg_data in messages_data:
            if msg_data["type"] == "human":
                messages.append(HumanMessage(content=msg_data["content"]))
            elif msg_data["type"] == "ai":
                messages.append(AIMessage(content=msg_data["content"]))
            # Skip unknown types to avoid errors
        return messages
    
    def save_state(self, thread_id: str, state: Dict[str, Any]):
        """Save conversation state to disk."""
        try:
            filepath = self.storage_dir / f"{thread_id}.json"
            
            # Convert non-serializable objects
            serializable_state = {
                "applicant_info": state.get("applicant_info", {}),
                "role_type": state.get("role_type"),
                "current_stage": state.get("current_stage"),
                "requirements_collected": state.get("requirements_collected", {}),
                "materials_collected": state.get("materials_collected", {}),
                "ready_for_submission": state.get("ready_for_submission", False),
                "has_spotlight": state.get("has_spotlight"),
                "has_representation": state.get("has_representation"),
                "work_preferences": state.get("work_preferences", {}),
                "messages": self._serialize_messages(state.get("messages", []))
            }
            
            with open(filepath, 'w') as f:
                json.dump(serializable_state, f, indent=2)
                
            logger.info(f"State saved for thread {thread_id}")
            
        except Exception as e:
            logger.error(f"Error saving state for thread {thread_id}: {e}")
    
    def load_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Load conversation state from disk."""
        try:
            filepath = self.storage_dir / f"{thread_id}.json"
            if filepath.exists():
                with open(filepath, 'r') as f:
                    state = json.load(f)
                
                # Deserialize messages
                if "messages" in state:
                    state["messages"] = self._deserialize_messages(state["messages"])
                
                logger.info(f"State loaded for thread {thread_id}")
                return state
            else:
                logger.info(f"No saved state found for thread {thread_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading state for thread {thread_id}: {e}")
            return None
    
    def delete_state(self, thread_id: str):
        """Delete saved state for a thread."""
        try:
            filepath = self.storage_dir / f"{thread_id}.json"
            if filepath.exists():
                filepath.unlink()
                logger.info(f"State deleted for thread {thread_id}")
        except Exception as e:
            logger.error(f"Error deleting state for thread {thread_id}: {e}")
    
    def list_saved_threads(self) -> list:
        """List all saved thread IDs."""
        try:
            return [f.stem for f in self.storage_dir.glob("*.json")]
        except Exception as e:
            logger.error(f"Error listing saved threads: {e}")
            return []
    
    def cleanup_old_states(self, max_age_days: int = 30):
        """Remove state files older than specified days."""
        try:
            from datetime import datetime, timedelta
            cutoff = datetime.now() - timedelta(days=max_age_days)
            
            for filepath in self.storage_dir.glob("*.json"):
                if datetime.fromtimestamp(filepath.stat().st_mtime) < cutoff:
                    filepath.unlink()
                    logger.info(f"Deleted old state file: {filepath.name}")
                    
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")