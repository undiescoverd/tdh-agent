# TDH Agency Application Assistant

An intelligent conversational agent built with LangGraph and Google Gemini that guides talent through the TDH Agency application process.

## Features

- **Interactive Application Process**: Guides applicants through collecting basic information, role classification, and material submission
- **Role-Specific Requirements**: Handles three performer types:
  - Dancer
  - Dancer Who Sings  
  - Singer/Actor
- **Material Validation**: Validates CVs, reels, and other required materials
- **Conversation Memory**: Maintains conversation state throughout the application process
- **Robust Error Handling**: Fixed recursion issues and improved state management
- **Test Scenarios**: Includes comprehensive test cases for different application types

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
Run the test suite:
```bash
python test_tdh_agent.py
```

Choose from three test scenarios:
1. Dancer Application
2. Singer/Actor Application  
3. Invalid Materials Handling

## Project Structure

```
tdh-agent/
├── tdh_agent.py          # Main application with LangGraph workflow
├── test_tdh_agent.py     # Test scenarios and validation
├── test_gemini.py        # Gemini API connection testing
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── .gitignore           # Git ignore rules
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

## Recent Fixes

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
