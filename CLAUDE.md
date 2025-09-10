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
# Original integration tests
python test_tdh_agent.py

# New validation tests (requires pytest)
pytest test_validators.py -v

# Test Gemini connection
python test_gemini.py
```

### Code Quality
```bash
# Type checking (optional)
mypy tdh_agent.py

# Code formatting (optional) 
black *.py
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
- **Enhanced Validation**: New `validators.py` module with comprehensive validation classes

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

## Modern Architecture (v3.0) - 2024 Upgrade

### 8-Phase Systematic Enhancement

The application has been systematically upgraded with **zero breaking changes** through 8 carefully planned phases:

#### Phase 1: Configuration Management
- **File**: `config.py`
- **Features**: Pydantic-based settings with environment variable validation
- **Benefits**: Centralized configuration, type safety, better error messages
```python
from config import settings
# settings.google_api_key, settings.debug_mode, settings.max_retries
```

#### Phase 2: Type Safety & Data Models  
- **File**: `models.py`
- **Features**: Pydantic models for all data structures
- **Models**: `ApplicantInfo`, `MaterialsCollected`, `RequirementsCollected`, `WorkPreferences`
- **Benefits**: Runtime validation, IDE support, automatic serialization
```python
from models import ApplicantInfo
from tdh_agent import dict_to_applicant_info, applicant_info_to_dict
```

#### Phase 3: Conversation Persistence
- **File**: `persistence.py`
- **Features**: Disk-based conversation state persistence
- **Benefits**: Session recovery, debugging, conversation history
- **Storage**: `.conversation_cache/` directory with JSON serialization
```python
# Automatic state saving after each conversation update
persistence.save_state(thread_id, state)
loaded_state = persistence.load_state(thread_id)
```

#### Phase 4: Enhanced Validation
- **File**: `validators.py`
- **Features**: Comprehensive input and material validation
- **Classes**: `MaterialValidator`, `InputValidator`, `ContentValidator`
- **Benefits**: Better user feedback, robust error handling, extensible validation
```python
from validators import MaterialValidator
validator = MaterialValidator()
is_valid, message = validator.validate_cv(content)
```

#### Phase 5: Async Infrastructure
- **File**: `async_handlers.py`
- **Features**: Future-ready async conversation processing
- **Classes**: `AsyncLLMHandler`, `AsyncStateManager`, `AsyncConversationManager`
- **Benefits**: Prepared for async LangChain operations, better performance scaling

#### Phase 6: Testing Infrastructure
- **File**: `test_validators.py`
- **Features**: Comprehensive pytest test suite
- **Coverage**: All validation scenarios, edge cases, error conditions
- **Benefits**: Quality assurance, regression prevention, documentation through tests

#### Phase 7: Claude Code Integration
- **File**: `.cursorrules`
- **Features**: Comprehensive guidance for Claude Code interactions
- **Benefits**: Consistent development patterns, architectural guidance, best practices

#### Phase 8: Error Handling
- **File**: `error_handlers.py`
- **Features**: Comprehensive error handling with graceful degradation
- **Classes**: `ErrorHandler`, `ConversationErrorHandler`, `ValidationErrorHandler`
- **Benefits**: Robust error recovery, detailed logging, never-breaking conversations

### New Module Architecture

```
tdh-agent/
├── tdh_agent.py              # Main application (core unchanged)
├── config.py                 # Pydantic settings management
├── models.py                 # Type-safe data models
├── persistence.py            # Conversation state persistence  
├── validators.py             # Input & material validation
├── async_handlers.py         # Async support infrastructure
├── error_handlers.py         # Comprehensive error handling
├── test_validators.py        # Comprehensive test suite
├── .cursorrules              # Claude Code integration rules
├── requirements.txt          # Dependencies (unchanged)
└── .env                      # Environment variables
```

### Upgrade Principles

1. **Zero Breaking Changes**: All existing functionality preserved exactly
2. **Additive Enhancements**: New features are optional and fail gracefully
3. **Backward Compatibility**: Original API and state structures maintained
4. **Modular Design**: Each enhancement is self-contained
5. **Graceful Degradation**: System works even if new features fail
6. **Comprehensive Testing**: Each phase tested before proceeding

### Integration Benefits

- **Type Safety**: Pydantic models with runtime validation
- **Configuration Management**: Centralized settings with validation  
- **Persistent Sessions**: Conversation state survives restarts
- **Enhanced Validation**: Better user feedback and error handling
- **Future-Ready**: Async infrastructure for performance scaling
- **Quality Assurance**: Comprehensive test coverage
- **Developer Experience**: Claude Code integration and error handling
- **Production Ready**: Robust error handling and monitoring

## Testing Framework

Three test scenarios in `test_tdh_agent.py`:
1. **Dancer Application**: Full flow for dancer role
2. **Singer/Actor Application**: Complete singer/actor workflow  
3. **Invalid Materials**: Error handling and validation testing

## Key Dependencies

### Core Dependencies
- **LangGraph**: Workflow orchestration and state management
- **LangChain**: LLM integration and prompt templates  
- **Google Gemini**: Cloud-based LLM via Google AI Studio API
- **Python 3.8+**: Core runtime requirement

### Modern Architecture Dependencies (v3.0)
- **Pydantic v2+**: Data validation and settings management
- **Pydantic-Settings**: Environment variable handling
- **Python Standard Library**: JSON, logging, pathlib, asyncio, re, typing

### Optional Development Dependencies
- **pytest**: Testing framework for validation tests
- **mypy**: Static type checking
- **black**: Code formatting

## Development Notes

### Core Application
- The application requires a valid Google Gemini API key from Google AI Studio
- Role-specific workflows are hardcoded in the state graph structure
- The agent maintains conversation context through manual state management

### Modern Architecture (v3.0)
- **Enhanced State Management**: Optional disk persistence with fallback to memory
- **Advanced Validation**: Comprehensive input validation with better error messages
- **Type Safety**: Runtime validation with Pydantic models
- **Error Handling**: Graceful degradation ensures conversations never break
- **Configuration**: Centralized settings with validation and environment variable support
- **Testing**: Comprehensive test suite for all validation scenarios
- **Async Ready**: Infrastructure prepared for async LangChain operations
- **Modular Design**: All enhancements are optional and self-contained

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