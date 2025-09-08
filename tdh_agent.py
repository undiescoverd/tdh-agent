from typing import Dict, List, TypedDict, Literal, Optional, Union, Any, Tuple
import re
from langchain_core.messages import HumanMessage, AIMessage
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# Define the state structure for our agent
class AgentState(TypedDict):
    """State for the TDH Agency application assistant."""
    # Conversation history
    messages: List[Union[HumanMessage, AIMessage]]
    # Application details
    applicant_info: Dict[str, Any]
    # Current role type (used for conditional routing)
    role_type: Optional[Literal["Dancer", "Dancer Who Sings", "Singer/Actor"]]
    # Current node/stage in the conversation
    current_stage: str
    # Collected requirements tracking
    requirements_collected: Dict[str, bool]
    # Flag to indicate if the application is ready for submission
    ready_for_submission: bool

# Initialize the LLM
llm = OllamaLLM(model="llama3.1:8b-instruct-q4_0")

# Helper functions
def extract_applicant_info(message: str, current_info: Dict[str, Any]) -> Dict[str, Any]:
    """Extract applicant information from a message."""
    # Create a copy of the current info
    updated_info = current_info.copy()
    
    # Extract name
    if "name" not in updated_info or not updated_info["name"]:
        # Look for patterns like "My name is [Name]" or "I'm [Name]"
        name_patterns = [
            r"(?:my|full)?\s*name\s*(?:is|:)?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)",
            r"I(?:'m| am)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, message)
            if match:
                updated_info["name"] = match.group(1)
                break
    
    # Extract email
    if "email" not in updated_info or not updated_info["email"]:
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        match = re.search(email_pattern, message)
        if match:
            updated_info["email"] = match.group(0)
    
    # Extract phone number
    if "phone" not in updated_info or not updated_info["phone"]:
        phone_patterns = [
            r"(?:phone|number|contact)(?:\s*(?:is|:))?\s*(\+?\d[\d\s-]{8,})",
            r"(\+?\d[\d\s-]{8,})"
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, message)
            if match:
                updated_info["phone"] = match.group(1)
                break
    
    # Extract Spotlight link
    if "spotlight" not in updated_info or not updated_info["spotlight"]:
        spotlight_pattern = r"(?:spotlight|profile)(?:\s*(?:is|:))?\s*(https?://(?:www\.)?spotlight\.com\S+)"
        match = re.search(spotlight_pattern, message)
        if match:
            updated_info["spotlight"] = match.group(1)
    
    return updated_info

def validate_material(material_type: str, content: str) -> Tuple[bool, str]:
    """Validate a material based on its type and return validation result and feedback."""
    if material_type == "cv":
        # Check if the content mentions PDF or Word
        if any(ext in content.lower() for ext in ["pdf", "word", ".doc", ".docx"]):
            return True, "Great! Your CV in PDF/Word format is noted."
        else:
            return False, "Please note that your CV must be in PDF or Word format only. Do you have your CV in one of these formats?"
    
    elif any(reel in material_type for reel in ["dance_reel", "vocal_reel", "acting_reel", "movement_reel"]):
        # Check if the content contains a YouTube or Vimeo link
        youtube_pattern = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/(?:watch\?v=)?([a-zA-Z0-9_-]{11})"
        vimeo_pattern = r"(?:https?:\/\/)?(?:www\.)?vimeo\.com\/([0-9]+)"
        
        if re.search(youtube_pattern, content) or re.search(vimeo_pattern, content):
            reel_name = material_type.replace("_", " ").title()
            return True, f"Perfect! I've noted your {reel_name}."
        else:
            reel_name = material_type.replace("_", " ").title()
            return False, f"Please provide a direct YouTube or Vimeo link for your {reel_name}. Other platforms or downloadable files are not accepted."
    
    return False, "I couldn't validate this material. Please ensure it meets the requirements."

# Create LangGraph nodes for each stage in the application process
def welcome_node(state: AgentState) -> AgentState:
    """Initial greeting and explanation of the assistant's purpose."""
    # If this is the first message, send a welcome message
    if len(state["messages"]) == 0:
        prompt = ChatPromptTemplate.from_template(
            """You are Emily, the TDH Agency Application Assistant. Your job is to guide talent through the application process in a friendly, professional manner.
            
            Greet the user warmly and explain that you'll help them submit a complete application to TDH Agency.
            Briefly mention that you'll ask for some basic information and then guide them through providing
            the specific materials needed for their role type (Dancer, Dancer Who Sings, or Singer/Actor).
            
            Keep your response friendly, professional, and concise."""
        )
        
        # Format the prompt first
        formatted_prompt = prompt.format()
        response = llm.invoke(formatted_prompt)
        
        # Update the state
        state["messages"].append(AIMessage(content=str(response)))
        state["current_stage"] = "basic_info"
        state["applicant_info"] = {}
        state["requirements_collected"] = {}
        state["ready_for_submission"] = False
    
    return state

def collect_basic_info(state: AgentState) -> AgentState:
    """Collect basic applicant information."""
    # Only process if we're in the right stage
    if state["current_stage"] != "basic_info":
        return state
    
    # Get the last message from the user
    last_message = state["messages"][-1]
    
    if isinstance(last_message, HumanMessage):
        # Extract information from the message
        updated_info = extract_applicant_info(last_message.content, state["applicant_info"])
        state["applicant_info"] = updated_info
        
        # Create a prompt to generate a response based on the conversation history
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are Emily, the TDH Agency Application Assistant, currently collecting basic information.
            
            For a complete TDH Agency application, collect the following information:
            1. Full name
            2. Email address
            3. Phone number
            4. Spotlight link (if applicable)
            
            Current information collected:
            Name: {name}
            Email: {email}
            Phone: {phone}
            Spotlight: {spotlight}
            
            Based on what's missing, ask for one piece of information at a time.
            Once all information is collected, ask what type of performer they are: Dancer, Dancer Who Sings, or Singer/Actor.
            
            Be friendly, professional, and concise."""),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])
        
        # Prepare the conversation history
        messages_history = state["messages"][:-1]  # All messages except the current one
        
        # Generate a response
        response = llm.invoke(
            prompt.format(
                history=messages_history,
                input=last_message.content,
                name=updated_info.get("name", "Not provided"),
                email=updated_info.get("email", "Not provided"),
                phone=updated_info.get("phone", "Not provided"),
                spotlight=updated_info.get("spotlight", "Not provided")
            )
        )
        
        # Update the state with the assistant's response
        state["messages"].append(AIMessage(content=str(response)))
        
        # Check if we're ready to move to role classification
        has_name = "name" in updated_info and updated_info["name"]
        has_email = "email" in updated_info and updated_info["email"]
        has_phone = "phone" in updated_info and updated_info["phone"]
        
        if has_name and has_email and has_phone and "Dancer, Dancer Who Sings, or Singer/Actor" in str(response):
            state["current_stage"] = "role_classification"
    
    return state

def classify_role(state: AgentState) -> AgentState:
    """Determine the performer type and set appropriate requirements."""
    # Only process if we're in the right stage
    if state["current_stage"] != "role_classification":
        return state
    
    # Get the last message from the user
    last_message = state["messages"][-1]
    
    if isinstance(last_message, HumanMessage):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are Emily, the TDH Agency Application Assistant. You need to determine which performer type the applicant is.
            
            Based on the user's response, classify them into one of these categories:
            - Dancer
            - Dancer Who Sings
            - Singer/Actor
            
            The classification affects which materials they'll need to provide. Be clear in your determination
            and explain the specific requirements for their role type.
            
            Requirements for Dancers & Dancers Who Sing:
            1. CV (PDF or Word format only)
            2. Dance reel/self tape (YouTube/Vimeo link only)
            3. Vocal reel/self tape (YouTube/Vimeo link only)
            4. Acting reel/self tape (YouTube/Vimeo link only)
            
            Requirements for Singer/Actor/Movers:
            1. CV (PDF or Word format only)
            2. Vocal reel/self tape (YouTube/Vimeo link only)
            3. Acting reel/self tape (YouTube/Vimeo link only)
            4. Movement reel/footage (Optional) (YouTube/Vimeo link only)
            
            Be friendly, professional, and clear in your response."""),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])
        
        # Prepare the conversation history
        messages_history = state["messages"][:-1]
        
        # Extract role from user message
        user_message = last_message.content.lower()
        
        # Simple role detection - in a real implementation, you'd use a more robust approach
        if "dancer who sings" in user_message:
            role_type = "Dancer Who Sings"
        elif "dancer" in user_message:
            role_type = "Dancer"
        elif any(term in user_message for term in ["singer", "actor", "mover"]):
            role_type = "Singer/Actor"
        else:
            # If we can't determine, ask for clarification
            role_type = None
        
        # Update the state with the detected role
        if role_type:
            state["role_type"] = role_type
            
            # Initialize requirements tracking based on role type
            if role_type in ["Dancer", "Dancer Who Sings"]:
                state["requirements_collected"] = {
                    "cv": False,
                    "dance_reel": False,
                    "vocal_reel": False,
                    "acting_reel": False
                }
            else:  # Singer/Actor
                state["requirements_collected"] = {
                    "cv": False,
                    "vocal_reel": False,
                    "acting_reel": False,
                    "movement_reel": False  # Optional
                }
        
        # Generate a response that confirms the role and explains requirements
        response = llm.invoke(
            prompt.format(
                history=messages_history,
                input=last_message.content
            )
        )
        
        # Update the state with the assistant's response
        state["messages"].append(AIMessage(content=str(response)))
        
        # Move to the next stage if role is classified
        if role_type:
            state["current_stage"] = "explain_requirements"
    
    return state

def explain_requirements(state: AgentState) -> AgentState:
    """Explain the specific requirements for the applicant's role type."""
    # Only process if we're in the right stage
    if state["current_stage"] != "explain_requirements":
        return state
    
    role_type = state["role_type"]
    
    # Create role-specific requirements explanation
    if role_type in ["Dancer", "Dancer Who Sings"]:
        requirements_text = """For your application as a {role}, you'll need to provide:

1. CV (PDF or Word format only)
2. Dance reel/self tape (YouTube/Vimeo link only) - Footage must show technique and varying styles. Solo studio footage is preferred.
3. Vocal reel/self tape (YouTube/Vimeo link only) - 16 Bar minimum of any song choice that highlights your vocal tone and range.
4. Acting reel/self tape (YouTube/Vimeo link only) - Short monologue or scene that shows your acting ability.

Only direct unlisted YouTube or Vimeo links are accepted. Applications with downloadable files (Dropbox, WeTransfer, etc.) will be deleted.

Let's collect these materials one by one. First, do you have your CV ready in PDF or Word format?"""
    else:  # Singer/Actor
        requirements_text = """For your application as a Singer/Actor, you'll need to provide:

1. CV (PDF or Word format only)
2. Vocal reel/self tape (YouTube/Vimeo link only) - 16 Bar minimum of any song choice that highlights your vocal tone and range. Multiple songs are advised.
3. Acting reel/self tape (YouTube/Vimeo link only) - Short monologue or scene that shows your acting ability.
4. Movement reel/footage (Optional) (YouTube/Vimeo link only)

Only direct unlisted YouTube or Vimeo links are accepted. Applications with downloadable files (Dropbox, WeTransfer, etc.) will be deleted.

Let's collect these materials one by one. First, do you have your CV ready in PDF or Word format?"""
    
    # Format the requirements text with the role type
    formatted_requirements = requirements_text.format(role=role_type)
    
    # Update the state with the assistant's response
    state["messages"].append(AIMessage(content=formatted_requirements))
    
    # Move to the next stage
    state["current_stage"] = "collect_requirements"
    
    return state

def collect_requirements(state: AgentState) -> AgentState:
    """Collect and validate the required materials from the applicant."""
    # Only process if we're in the right stage
    if state["current_stage"] != "collect_requirements":
        return state
    
    # Get the last message from the user
    last_message = state["messages"][-1]
    
    if isinstance(last_message, HumanMessage):
        # Get current requirements status
        requirements = state["requirements_collected"]
        role_type = state["role_type"]
        user_message = last_message.content
        
        # Determine which requirement we're currently collecting
        current_requirement = None
        for req, collected in requirements.items():
            if not collected:
                current_requirement = req
                break
        
        # If we found a requirement to collect
        if current_requirement:
            # Validate the material
            is_valid, feedback = validate_material(current_requirement, user_message)
            
            if is_valid:
                # Mark the requirement as collected
                requirements[current_requirement] = True
                state["requirements_collected"] = requirements
                
                # Determine the next requirement to ask for
                next_requirement = None
                for req, collected in requirements.items():
                    if not collected:
                        next_requirement = req
                        break
                
                if next_requirement:
                    # Ask for the next requirement
                    next_req_name = next_requirement.replace("_", " ").title()
                    
                    if next_requirement == "cv":
                        response_text = f"{feedback}\n\nNow, please provide your CV. Remember, it must be in PDF or Word format only."
                    elif "reel" in next_requirement:
                        platform_text = "YouTube or Vimeo"
                        response_text = f"{feedback}\n\nNext, I need your {next_req_name}. Please provide a direct {platform_text} link."
                    else:
                        response_text = f"{feedback}\n\nNext, please provide your {next_req_name}."
                else:
                    # All requirements collected
                    response_text = f"{feedback}\n\nGreat! You've provided all the required materials for your application. Let me prepare your submission."
                    state["ready_for_submission"] = True
                    state["current_stage"] = "prepare_submission"
            else:
                # Material is invalid, provide feedback
                response_text = feedback
        else:
            # All requirements collected
            response_text = "You've already provided all the required materials. Let me prepare your submission."
            state["ready_for_submission"] = True
            state["current_stage"] = "prepare_submission"
        
        # Update the state with the assistant's response
        state["messages"].append(AIMessage(content=response_text))
    
    return state

def prepare_submission(state: AgentState) -> AgentState:
    """Prepare the collected materials for submission."""
    # Only process if we're in the right stage
    if state["current_stage"] != "prepare_submission":
        return state
    
    # Get applicant info and role type
    applicant_info = state["applicant_info"]
    role_type = state["role_type"]
    
    # Create a summary of the collected information
    summary = f"""Great! I've collected all the required materials for your application to TDH Agency as a {role_type}.

Here's a summary of your application:

Name: {applicant_info.get('name', 'Not provided')}
Email: {applicant_info.get('email', 'Not provided')}
Phone: {applicant_info.get('phone', 'Not provided')}
Spotlight Link: {applicant_info.get('spotlight', 'Not provided')}

Your application will include:
"""
    
    # Add collected materials to summary
    for req, collected in state["requirements_collected"].items():
        if collected:
            formatted_req = req.replace("_", " ").title()
            summary += f"- {formatted_req}: ✓\n"
    
    summary += """
Your application is ready to be submitted to info@tdhagency.com.

Would you like me to explain how to format your email for submission, or do you have any questions before you proceed?"""
    
    # Update the state with the summary
    state["messages"].append(AIMessage(content=summary))
    
    # Move to the final stage
    state["current_stage"] = "final"
    
    return state

def final_node(state: AgentState) -> AgentState:
    """Handle final questions and conclude the conversation."""
    # Only process if we're in the right stage
    if state["current_stage"] != "final":
        return state
    
    # Get the last message from the user
    last_message = state["messages"][-1]
    
    if isinstance(last_message, HumanMessage):
        # Create a prompt to handle final questions
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are Emily, the TDH Agency Application Assistant, concluding the application process.
            
            The applicant has provided all required materials. They might have questions about:
            1. How to format their email for submission
            2. What happens after submission
            3. Timeline for hearing back from the agency
            
            If they ask about email formatting, provide these instructions:
            - Subject Line: [THEIR NAME] - [ROLE TYPE]
            - Include: Name, Email, Phone, Spotlight Link, Cover Letter
            - Include YES/NO to: Musical Theatre, Work Abroad, Cruises, TV/Film, Commercial Dance Work
            - Mention any current representation
            - Attach CV and provide links to all required videos
            
            If they're ready to finish, thank them for using the assistant and wish them luck with their application.
            
            Be friendly, professional, and encouraging."""),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])
        
        # Prepare the conversation history
        messages_history = state["messages"][:-1]
        
        # Generate a response to the user's message
        response = llm.invoke(
            prompt.format(
                history=messages_history,
                input=last_message.content
            )
        )
        
        # Update the state with the assistant's response
        state["messages"].append(AIMessage(content=str(response)))
    
    return state


# Create the graph
builder = StateGraph(AgentState)

# Add nodes
builder.add_node("welcome", welcome_node)
builder.add_node("collect_basic_info", collect_basic_info)
builder.add_node("classify_role", classify_role)
builder.add_node("explain_requirements", explain_requirements)
builder.add_node("collect_requirements", collect_requirements)
builder.add_node("prepare_submission", prepare_submission)
builder.add_node("final_node", final_node)

# Add edges - Use direct edges to prevent infinite loops
builder.add_edge(START, "welcome")
builder.add_edge("welcome", "collect_basic_info")
builder.add_edge("collect_basic_info", "classify_role")
builder.add_edge("classify_role", "explain_requirements")
builder.add_edge("explain_requirements", "collect_requirements")
builder.add_edge("collect_requirements", "prepare_submission")
builder.add_edge("prepare_submission", "final_node")
builder.add_edge("final_node", END)

# Build the graph
graph = builder.compile()

# Global state storage for simplicity
conversation_states = {}

# Function to initialize the conversation
def initialize_conversation():
    """Initialize a new conversation with the agent."""
    initial_state = {
        "messages": [],
        "applicant_info": {},
        "role_type": None,
        "current_stage": "welcome",
        "requirements_collected": {},
        "ready_for_submission": False
    }
    
    # Create a unique thread ID
    thread_id = "thread_1"
    
    # Store the initial state
    conversation_states[thread_id] = initial_state
    
    # Run the welcome node to get the initial message
    config = {
        "recursion_limit": 50  # Increase from default 25
    }
    result = graph.invoke(initial_state, config=config)
    
    # Update the stored state
    conversation_states[thread_id] = result
    
    return result, thread_id

def continue_conversation(user_input: str, thread_id: str):
    """Continue an existing conversation with the agent."""
    # Get the current state from storage
    if thread_id not in conversation_states:
        print("No existing conversation found. Starting a new one.")
        return initialize_conversation()[0]
    
    current_state = conversation_states[thread_id]
    
    # Add the user input to the conversation
    current_state["messages"].append(HumanMessage(content=user_input))
    
    # Continue the conversation
    config = {
        "recursion_limit": 50  # Increase from default 25
    }
    result = graph.invoke(current_state, config=config)
    
    # Update the stored state
    conversation_states[thread_id] = result
    
    return result
 

# Main function to run the assistant
def main():
    print("Starting TDH Agency Application Assistant...")
    
    # Initialize the conversation
    state, thread_id = initialize_conversation()
    
    # Print the assistant's initial message
    if state["messages"]:
        print(f"Emily: {state['messages'][0].content}")
    
    # Main conversation loop
    while True:
        # Get user input
        user_input = input("\nYou: ")
        
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Emily: Thank you for using the TDH Agency Application Assistant. Goodbye!")
            break
        
        # Continue the conversation
        state = continue_conversation(user_input, thread_id)
        
        # Print the assistant's response
        if state["messages"]:
            print(f"Emily: {state['messages'][-1].content}")
        
        # Check if the conversation is complete
        if state["current_stage"] == "END":
            print("\nApplication process complete. Thank you for using the TDH Agency Application Assistant.")
            break

if __name__ == "__main__":
    main()