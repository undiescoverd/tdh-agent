# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based conversational AI agent built with LangGraph and Ollama that guides talent through the TDH Agency application process. The system uses a state-driven workflow to manage multi-step conversations for three performer types: Dancer, Dancer Who Sings, and Singer/Actor.

## Development Commands

### Running the Application
```bash
python tdh_agent.py
```

### Running Tests
```bash
python test_tdh_agent.py
```

### Testing Ollama Connection
```bash
python test_llama.py
```

### Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Ensure Ollama model is available
ollama pull llama3.1:8b-instruct-q4_0
```

## Architecture Overview

### Core Components

**AgentState (TypedDict)**: Central state management containing:
- `messages`: Conversation history (HumanMessage/AIMessage)
- `applicant_info`: Collected application data
- `role_type`: Performer classification ("Dancer", "Dancer Who Sings", "Singer/Actor")
- `current_stage`: Current workflow node
- `requirements_collected`: Tracking of collected materials
- `materials_collected`: File/link storage
- State flags for conditional routing (has_spotlight, has_representation, work_preferences)

**Manual Node Execution System**: Replaced LangGraph's automatic execution with controlled routing:
- `determine_next_node()`: Selects appropriate node based on current state
- `execute_node()`: Runs specific node functions individually
- `continue_conversation()`: Iterative processing until stage stabilizes
- Prevents recursion errors and provides precise control over conversation flow

**LLM Integration**: Uses Ollama with llama3.1:8b-instruct-q4_0 model via LangChain

### Key Functions

**Routing Functions**: Control flow between nodes based on applicant responses and state
- `route_after_role_classification()`: Directs to role-specific requirements
- `route_after_materials_collection()`: Handles completion logic
- `route_after_*()`: Various conditional routing points

**Validation Functions**: 
- `extract_applicant_info()`: Regex-based extraction of contact details
- `validate_material()`: URL/file validation for submitted materials

**Node Functions**: Each conversation stage (welcome, collect info, requirements, etc.)

### State Management

The application uses LangGraph's MemorySaver for conversation persistence. Each conversation has a unique thread_id that maintains state across interactions.

**Global State**: `conversation_states` dict tracks active conversations
**Conversation Flow**: Managed through `initialize_conversation()` and `continue_conversation()`

### Test Framework

Three test scenarios in `test_tdh_agent.py`:
1. **Dancer Application**: Full flow for dancer role
2. **Singer/Actor Application**: Complete singer/actor workflow  
3. **Invalid Materials**: Error handling and validation testing

## Key Dependencies

- **LangGraph**: Workflow orchestration and state management
- **LangChain**: LLM integration and prompt templates
- **Ollama**: Local LLM hosting (requires llama3.1:8b-instruct-q4_0 model)
- **Python 3.8+**: Core runtime requirement

## Development Notes

- The application requires Ollama to be running locally with the specific model
- All conversation state is held in memory (no persistent storage)
- Material validation uses regex patterns for URLs and basic format checking
- Role-specific workflows are hardcoded in the state graph structure
- The agent maintains conversation context through manual state management

## Recent Architecture Changes (v2.0)

### Recursion Fix Implementation
- **Problem**: Original `graph.invoke()` caused infinite loops through connected nodes
- **Solution**: Manual node execution with iterative processing
- **Key Changes**:
  - `initialize_conversation()`: Direct welcome node execution instead of full graph
  - `continue_conversation()`: Loop-based processing until stage stabilizes
  - `classify_role()`: Fixed to process most recent HumanMessage, not last message
  - Enhanced error handling and state validation

### Message Processing Improvements
- Fixed role classification by finding most recent human message
- Improved stage transition logic to prevent stuck states
- Added safeguards against circular routing
- Enhanced conversation flow reliability

### Testing and Validation
- All recursion errors resolved
- Complete conversation flows tested (basic info → role → requirements → materials)
- Role classification working for all three performer types
- Requirements tracking properly initialized based on detected roles