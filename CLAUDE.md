# TDH Agency Application Assistant - Claude Code Documentation

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based conversational AI agent built with LangGraph and Google Gemini that guides talent through the TDH Agency application process. The system uses a state-driven workflow to manage multi-step conversations for three performer types: Dancer, Dancer Who Sings, and Singer/Actor.

## Development Commands

### Running the Application
```bash
python tdh_agent.py
```

### Running Tests
```bash
python test_tdh_agent.py
```

### Testing Gemini Connection
```bash
python test_gemini.py
```

### Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up Gemini API key
echo "GOOGLE_API_KEY=your-api-key-here" > .env
# Get your API key from: https://aistudio.google.com/app/apikey
```

## Application Architecture

### Core Components

**AgentState (TypedDict)**: Central state management containing:
- `messages`: Conversation history (HumanMessage/AIMessage)
- `applicant_info`: Collected application data
- `role_type`: Performer classification ("Dancer", "Dancer Who Sings", "Singer/Actor")
- `current_stage`: Current workflow node
- `requirements_collected`: Dictionary tracking material collection status
- `materials_collected`: Dictionary storing actual material content/links
- State flags for conditional routing (has_spotlight, has_representation, work_preferences)

**Manual Node Execution System**: Replaced LangGraph's automatic execution with controlled routing:
- `determine_next_node()`: Selects appropriate node based on current state
- `execute_node()`: Runs specific node functions individually
- `continue_conversation()`: Iterative processing until stage stabilizes
- Prevents recursion errors and provides precise control over conversation flow

**LLM Integration**: Uses Google Gemini 2.5 Flash model via LangChain Google GenAI

### Application Flow

1. **Initial Setup**: `START` → `welcome` (Initialize conversation state)
2. **Basic Information Collection**: `welcome` → `collect_basic_info` (Name, email, phone, work authorization)
3. **Role Classification**: `collect_basic_info` → `classify_role` (Dancer, Dancer Who Sings, Singer/Actor)
4. **Role-Specific Requirements**: Explain materials needed based on role type
5. **Spotlight Profile Check**: Optional Spotlight profile collection
6. **Current Representation Check**: Optional current representation details
7. **Work Preferences**: Collect work type preferences (Theatre, Abroad, Cruises, TV/Film, Commercial)
8. **Materials Collection**: Role-specific CV and reel collection with validation
9. **Research Questions**: Additional applicant information
10. **Final Summary**: Application completion and submission instructions

### Key Routing Functions

- `route_after_role_classification()`: Directs to role-specific requirements
- `route_after_spotlight_check()`: Routes based on Spotlight profile status
- `route_after_representation_check()`: Routes based on current representation
- `route_after_work_preferences()`: Routes to appropriate materials collection
- `route_after_materials_collection()`: Handles completion logic

### State Management

The application uses LangGraph's MemorySaver for conversation persistence. Each conversation has a unique thread_id that maintains state across interactions.

**Global State**: `conversation_states` dict tracks active conversations
**Conversation Flow**: Managed through `initialize_conversation()` and `continue_conversation()`

### Material Validation

- **CV**: Must be PDF or Word format
- **Reels**: Must be YouTube or Vimeo links only
- **Real-time Validation**: Using regex patterns and content analysis

## Architecture Changes (v2.0)

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

## Testing Framework

Three test scenarios in `test_tdh_agent.py`:
1. **Dancer Application**: Full flow for dancer role
2. **Singer/Actor Application**: Complete singer/actor workflow  
3. **Invalid Materials**: Error handling and validation testing

## Key Dependencies

- **LangGraph**: Workflow orchestration and state management
- **LangChain**: LLM integration and prompt templates  
- **Google Gemini**: Cloud-based LLM via Google AI Studio API
- **Python 3.8+**: Core runtime requirement

## Development Notes

- The application requires a valid Google Gemini API key from Google AI Studio
- All conversation state is held in memory (no persistent storage)
- Material validation uses regex patterns for URLs and basic format checking
- Role-specific workflows are hardcoded in the state graph structure
- The agent maintains conversation context through manual state management

## Known Issues & Solutions

### GraphRecursionError (Resolved)
**Previous Issue**: `GraphRecursionError: Recursion limit of 50 reached without hitting a stop condition`

**Root Cause**: Conditional edges created infinite loops in materials collection

**Solution Implemented**: 
- Manual node execution system
- Direct edges for linear flow sections
- Conditional edges only for true branching decisions
- State-based routing that checks state, not conversation history

### Quick Fixes for Future Development

To prevent recursion issues:
1. Use direct edges for linear progressions
2. Handle completion logic within node functions
3. Avoid circular conditional routing
4. Test conversation flows end-to-end

## Testing and Validation

- All recursion errors resolved
- Complete conversation flows tested (basic info → role → requirements → materials)
- Role classification working for all three performer types
- Requirements tracking properly initialized based on detected roles
- Materials collection with validation working correctly