# TDH Agency Application Assistant

An intelligent conversational agent built with LangGraph and Google Gemini that guides talent through the TDH Agency application process.

## Features

### Core Functionality
- **Interactive Application Process**: Guides applicants through collecting basic information, role classification, and material submission
- **Role-Specific Requirements**: Handles three performer types:
  - Dancer
  - Dancer Who Sings  
  - Singer/Actor
- **Material Validation**: Validates CVs, reels, and other required materials
- **Conversation Memory**: Maintains conversation state throughout the application process
- **Robust Error Handling**: Fixed recursion issues and improved state management
- **Test Scenarios**: Includes comprehensive test cases for different application types

### Modern Architecture (v3.0 - 2024)
- **Type-Safe Configuration**: Pydantic-based settings with validation
- **Enhanced Data Models**: Type-safe data structures with runtime validation
- **Persistent Sessions**: Optional conversation state persistence to disk
- **Advanced Validation**: Comprehensive input validation with detailed error messages  
- **Async Infrastructure**: Future-ready async conversation processing
- **Comprehensive Testing**: Extensive test suite with pytest integration
- **Production-Ready Error Handling**: Graceful degradation that never breaks conversations
- **Claude Code Integration**: Optimized for Claude Code development workflows

## Requirements

- Python 3.8+
- Google Gemini API key (free at https://aistudio.google.com/app/apikey)
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd tdh-agent
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your Gemini API key:
```bash
# Create .env file with your API key
echo "GOOGLE_API_KEY=your-api-key-here" > .env
# Replace 'your-api-key-here' with your actual Gemini API key from https://aistudio.google.com/app/apikey
```

5. Test the connection:
```bash
python test_gemini.py
```

## Usage

### Interactive Mode
Run the main application:
```bash
python tdh_agent.py
```

### Test Scenarios

#### Original Integration Tests
```bash
python test_tdh_agent.py
```

Choose from three test scenarios:
1. Dancer Application
2. Singer/Actor Application  
3. Invalid Materials Handling

#### Enhanced Validation Tests (v3.0)
```bash
# Requires pytest: pip install pytest
pytest test_validators.py -v
```

Comprehensive tests for:
- Material validation (CV, video links, Spotlight profiles)
- Input validation (emails, phone numbers, names)
- Content analysis and completion detection
- Edge cases and error scenarios

## Project Structure

### Core Files
```
tdh-agent/
├── tdh_agent.py          # Main application with LangGraph workflow
├── test_tdh_agent.py     # Integration test scenarios
├── test_gemini.py        # Gemini API connection testing
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── CLAUDE.md            # Detailed technical documentation
└── .gitignore           # Git ignore rules
```

### Modern Architecture (v3.0)
```
tdh-agent/
├── config.py             # Pydantic settings management
├── models.py             # Type-safe data models
├── persistence.py        # Conversation state persistence
├── validators.py         # Advanced input validation
├── async_handlers.py     # Async infrastructure
├── error_handlers.py     # Comprehensive error handling
├── test_validators.py    # Validation test suite
├── .cursorrules          # Claude Code integration
└── .conversation_cache/  # Persistent session storage (auto-created)
```

## Application Flow

1. **Welcome**: Initial greeting and introduction
2. **Basic Info Collection**: Name, email, phone, Spotlight link
3. **Role Classification**: Determine performer type
4. **Requirements Explanation**: Explain role-specific materials needed
5. **Material Collection**: Validate and collect CVs, reels, etc.
6. **Submission Preparation**: Summarize application and provide submission guidance
7. **Final Questions**: Handle any remaining questions

## Technical Details

- **Framework**: LangGraph for conversation flow management
- **LLM**: Google Gemini 2.5 Flash model via Google AI Studio
- **State Management**: Custom state tracking with conversation memory
- **Validation**: Regex-based validation for materials and contact information
- **Architecture**: Manual node execution with iterative stage processing to prevent recursion errors

## Version History

### v3.0 - Modern Architecture Upgrade (2024)
**Zero Breaking Changes - Systematic Enhancement**

- **🔧 Configuration Management**: Pydantic-based settings with environment validation
- **🏷️ Type Safety**: Comprehensive data models with runtime validation
- **💾 Session Persistence**: Optional conversation state saving to disk
- **✅ Enhanced Validation**: Advanced input validation with better error messages
- **⚡ Async Infrastructure**: Future-ready async conversation processing
- **🧪 Comprehensive Testing**: pytest-based validation test suite  
- **🛡️ Production-Ready Error Handling**: Graceful degradation and detailed logging
- **🤖 Claude Code Integration**: Optimized development workflow integration

### v2.0 - Recursion Error Resolution
- **Fixed LangGraph Recursion Issues**: Replaced `graph.invoke()` with targeted node execution
- **Improved State Management**: Implemented iterative processing that continues until stage stabilizes
- **Enhanced Message Processing**: Fixed role classification to properly detect human messages
- **Better Error Handling**: Added safeguards against infinite loops and improved conversation flow
- **Robust Routing**: Fixed circular routing issues and ensured all paths lead to completion

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.
