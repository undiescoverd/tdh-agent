from typing import Dict, List, TypedDict, Literal, Optional, Union, Any, Tuple
import re
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# Load environment variables
load_dotenv()

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
    # Additional state for conditional routing
    has_spotlight: Optional[bool]
    has_representation: Optional[bool]
    work_preferences: Dict[str, bool]
    # Track which materials have been collected
    materials_collected: Dict[str, str]

# Initialize the LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

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

# Routing functions for conditional edges
def route_after_role_classification(state: AgentState) -> str:
    """Route after role classification based on role type."""
    role_type = state["role_type"]
    
    if role_type == "Dancer":
        return "dancer_requirements"
    elif role_type == "Dancer Who Sings":
        return "dancer_who_sings_requirements"
    elif role_type == "Singer/Actor":
        return "singer_actor_requirements"
    else:
        return "request_role_clarification"

def route_after_spotlight_check(state: AgentState) -> str:
    """Route after checking Spotlight profile status."""
    has_spotlight = state["has_spotlight"]
    
    if has_spotlight is True:
        return "collect_spotlight_link"
    else:
        return "representation_check"

def route_after_representation_check(state: AgentState) -> str:
    """Route after checking current representation status."""
    has_representation = state["has_representation"]
    
    if has_representation is True:
        return "collect_representation_details"
    else:
        return "work_preferences"

def route_after_work_preferences(state: AgentState) -> str:
    """Route after collecting work preferences."""
    role_type = state["role_type"]
    
    if role_type in ["Dancer", "Dancer Who Sings"]:
        return "dancer_materials"
    elif role_type == "Singer/Actor":
        return "singer_actor_materials"
    else:
        # Instead of circular routing, end the conversation with an error
        return "final_questions"

def route_after_materials_collection(state: AgentState) -> str:
    """Route after collecting all required materials."""
    # Check if all required materials are collected
    requirements = state["requirements_collected"]
    
    # If no requirements dict exists or it's empty, assume materials not ready
    if not requirements:
        return "collect_requirements"
    
    all_collected = all(requirements.values())
    
    if all_collected:
        return "research_questions"
    else:
        return "collect_requirements"  # Continue collecting materials

def route_after_research(state: AgentState) -> str:
    """Route after research questions."""
    return "final_questions"

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
    # Always process - stage checking is handled by graph routing
    
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
            4. Work authorization status
            
            Current information collected:
            Name: {name}
            Email: {email}
            Phone: {phone}
            Work Authorization: {work_auth}
            
            Based on what's missing, ask for one piece of information at a time.
            Once all basic information is collected, ask what type of performer they are: Dancer, Dancer Who Sings, or Singer/Actor.
            
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
                work_auth=updated_info.get("work_auth", "Not provided")
            )
        )
        
        # Update the state with the assistant's response
        state["messages"].append(AIMessage(content=str(response)))
        
        # Check if we're ready to move to role classification
        has_name = "name" in updated_info and updated_info["name"]
        has_email = "email" in updated_info and updated_info["email"]
        has_phone = "phone" in updated_info and updated_info["phone"]
        
        # Check if user mentioned a role type, indicating they're answering the role question
        user_message = last_message.content.lower()
        mentioned_role = any(phrase in user_message for phrase in 
                           ["dancer", "singer", "actor", "perform", "dance", "sing", "act"])
        
        if has_name and has_email and has_phone:
            if mentioned_role:
                state["current_stage"] = "role_classification"
            elif "performer" in str(response).lower() or "dancer" in str(response).lower():
                # Emily is asking about role, stay in basic_info but prepare for role classification
                pass
    
    return state

def classify_role(state: AgentState) -> AgentState:
    """Determine the performer type and set appropriate requirements."""
    # Always process - stage checking is handled by graph routing
    
    # Get the most recent human message
    human_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
    if not human_messages:
        return state
    
    last_human_message = human_messages[-1]
    
    if isinstance(last_human_message, HumanMessage):
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
        user_message = last_human_message.content.lower()
        
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
                input=last_human_message.content
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
                # Mark the requirement as collected and store the material
                requirements[current_requirement] = True
                state["requirements_collected"] = requirements
                state["materials_collected"][current_requirement] = user_message
                
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
                    # All requirements collected - move to research questions
                    response_text = f"{feedback}\n\nExcellent! You've provided all the required materials. Let me ask you a few final questions."
                    # Set stage to trigger research questions
                    state["current_stage"] = "research_questions"
            else:
                # Material is invalid, provide feedback
                response_text = feedback
        else:
            # All requirements collected
            response_text = "You've already provided all the required materials. Let me ask you a few final questions."
            state["current_stage"] = "research_questions"
        
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

def continue_materials_collection(state: AgentState) -> AgentState:
    """Continue collecting materials when not all are collected."""
    # This node just routes back to collect_requirements
    # The actual logic is handled in collect_requirements
    return state

# New nodes for conditional branching
def request_role_clarification(state: AgentState) -> AgentState:
    """Request clarification when role type is unclear."""
    prompt = ChatPromptTemplate.from_template(
        """You are Emily, the TDH Agency Application Assistant.
        
        I need to clarify what type of performer you are. Please choose one of these options:
        
        1. **Dancer** - You primarily dance and may have some singing/acting skills
        2. **Dancer Who Sings** - You dance and sing, with strong abilities in both
        3. **Singer/Actor** - You primarily sing and act, with some movement abilities
        
        Please respond with the number or the full description of which category best describes you."""
    )
    
    response = llm.invoke(prompt.format())
    state["messages"].append(AIMessage(content=str(response)))
    
    return state

def dancer_requirements(state: AgentState) -> AgentState:
    """Explain requirements for Dancers."""
    requirements_text = """For your application as a Dancer, you'll need to provide:

1. CV (PDF or Word format only)
2. Dance reel/self tape (YouTube/Vimeo link only) - Footage must show technique and varying styles. Solo studio footage is preferred.
3. Vocal reel/self tape (YouTube/Vimeo link only) - 16 Bar minimum of any song choice that highlights your vocal tone and range.
4. Acting reel/self tape (YouTube/Vimeo link only) - Short monologue or scene that shows your acting ability.

Only direct unlisted YouTube or Vimeo links are accepted. Applications with downloadable files (Dropbox, WeTransfer, etc.) will be deleted.

Let's start by checking if you have a Spotlight profile."""
    
    state["messages"].append(AIMessage(content=requirements_text))
    state["current_stage"] = "spotlight_check"
    
    return state

def dancer_who_sings_requirements(state: AgentState) -> AgentState:
    """Explain requirements for Dancers Who Sing."""
    requirements_text = """For your application as a Dancer Who Sings, you'll need to provide:

1. CV (PDF or Word format only)
2. Dance reel/self tape (YouTube/Vimeo link only) - Footage must show technique and varying styles. Solo studio footage is preferred.
3. Vocal reel/self tape (YouTube/Vimeo link only) - 16 Bar minimum of any song choice that highlights your vocal tone and range.
4. Acting reel/self tape (YouTube/Vimeo link only) - Short monologue or scene that shows your acting ability.

Only direct unlisted YouTube or Vimeo links are accepted. Applications with downloadable files (Dropbox, WeTransfer, etc.) will be deleted.

Let's start by checking if you have a Spotlight profile."""
    
    state["messages"].append(AIMessage(content=requirements_text))
    state["current_stage"] = "spotlight_check"
    
    return state

def singer_actor_requirements(state: AgentState) -> AgentState:
    """Explain requirements for Singer/Actor."""
    requirements_text = """For your application as a Singer/Actor, you'll need to provide:

1. CV (PDF or Word format only)
2. Vocal reel/self tape (YouTube/Vimeo link only) - 16 Bar minimum of any song choice that highlights your vocal tone and range. Multiple songs are advised.
3. Acting reel/self tape (YouTube/Vimeo link only) - Short monologue or scene that shows your acting ability.
4. Movement reel/footage (Optional) (YouTube/Vimeo link only)

Only direct unlisted YouTube or Vimeo links are accepted. Applications with downloadable files (Dropbox, WeTransfer, etc.) will be deleted.

Let's start by checking if you have a Spotlight profile."""
    
    state["messages"].append(AIMessage(content=requirements_text))
    state["current_stage"] = "spotlight_check"
    
    return state

def spotlight_check(state: AgentState) -> AgentState:
    """Check if applicant has a Spotlight profile."""
    # Get the last message from the user
    last_message = state["messages"][-1]
    
    if isinstance(last_message, HumanMessage):
        user_message = last_message.content.lower()
        
        # Determine if they have Spotlight
        if any(phrase in user_message for phrase in ["yes", "i have", "i do", "i'm on spotlight"]):
            state["has_spotlight"] = True
            response_text = "Great! Please provide your Spotlight profile link."
        elif any(phrase in user_message for phrase in ["no", "i don't", "i don't have", "not on spotlight"]):
            state["has_spotlight"] = False
            response_text = "No problem! Let's move on to checking your current representation status."
        else:
            response_text = "I need to know if you have a Spotlight profile. Please answer yes or no."
        
        state["messages"].append(AIMessage(content=response_text))
    
    return state

def collect_spotlight_link(state: AgentState) -> AgentState:
    """Collect Spotlight profile link."""
    # Get the last message from the user
    last_message = state["messages"][-1]
    
    if isinstance(last_message, HumanMessage):
        # Extract Spotlight link
        spotlight_pattern = r"(?:https?://)?(?:www\.)?(?:portal\.)?spotlight\.com\S*"
        match = re.search(spotlight_pattern, last_message.content)
        
        if match:
            state["applicant_info"]["spotlight"] = match.group(0)
            response_text = "Perfect! I've noted your Spotlight link. Now let's check your current representation status."
        else:
            response_text = "I couldn't find a valid Spotlight link. Please provide the direct URL to your Spotlight profile."
        
        state["messages"].append(AIMessage(content=response_text))
    
    return state

def representation_check(state: AgentState) -> AgentState:
    """Check if applicant has current representation."""
    # Get the last message from the user
    last_message = state["messages"][-1]
    
    if isinstance(last_message, HumanMessage):
        user_message = last_message.content.lower()
        
        # Determine if they have representation
        if any(phrase in user_message for phrase in ["yes", "i have", "i do", "i'm represented"]):
            state["has_representation"] = True
            response_text = "I see you have current representation. Please tell me the agency name and what they represent you for."
        elif any(phrase in user_message for phrase in ["no", "i don't", "i don't have", "not represented"]):
            state["has_representation"] = False
            response_text = "No problem! Let's move on to your work preferences."
        else:
            response_text = "I need to know if you currently have representation. Please answer yes or no."
        
        state["messages"].append(AIMessage(content=response_text))
    
    return state

def collect_representation_details(state: AgentState) -> AgentState:
    """Collect current representation details."""
    # Get the last message from the user
    last_message = state["messages"][-1]
    
    if isinstance(last_message, HumanMessage):
        # Extract agency information
        state["applicant_info"]["current_agency"] = last_message.content
        response_text = "Thank you for that information. Now let's discuss your work preferences."
        state["messages"].append(AIMessage(content=response_text))
    
    return state

def work_preferences(state: AgentState) -> AgentState:
    """Collect work preferences."""
    prompt = ChatPromptTemplate.from_template(
        """You are Emily, the TDH Agency Application Assistant.
        
        Now I need to know about your work preferences. Please tell me which of these types of work you're interested in:
        
        - Musical Theatre
        - Working Abroad
        - Cruises
        - TV/Film
        - Commercial Dance Work
        
        You can say "all of them" or list the specific ones you're interested in."""
    )
    
    response = llm.invoke(prompt.format())
    state["messages"].append(AIMessage(content=str(response)))
    
    return state

def dancer_materials(state: AgentState) -> AgentState:
    """Collect materials for Dancers."""
    # Initialize requirements for dancers
    state["requirements_collected"] = {
        "cv": False,
        "dance_reel": False,
        "vocal_reel": False,
        "acting_reel": False
    }
    
    response_text = """Now let's collect your materials. I'll need:

1. Your CV (PDF or Word format)
2. Dance reel (YouTube/Vimeo link)
3. Vocal reel (YouTube/Vimeo link) 
4. Acting reel (YouTube/Vimeo link)

Let's start with your CV. Do you have it ready in PDF or Word format?"""
    
    state["messages"].append(AIMessage(content=response_text))
    state["current_stage"] = "collect_requirements"
    
    return state

def singer_actor_materials(state: AgentState) -> AgentState:
    """Collect materials for Singer/Actor."""
    # Initialize requirements for singer/actor
    state["requirements_collected"] = {
        "cv": False,
        "vocal_reel": False,
        "acting_reel": False,
        "movement_reel": False  # Optional
    }
    
    response_text = """Now let's collect your materials. I'll need:

1. Your CV (PDF or Word format)
2. Vocal reel (YouTube/Vimeo link)
3. Acting reel (YouTube/Vimeo link)
4. Movement reel (Optional - YouTube/Vimeo link)

Let's start with your CV. Do you have it ready in PDF or Word format?"""
    
    state["messages"].append(AIMessage(content=response_text))
    state["current_stage"] = "collect_requirements"
    
    return state

def research_questions(state: AgentState) -> AgentState:
    """Ask research questions."""
    prompt = ChatPromptTemplate.from_template(
        """You are Emily, the TDH Agency Application Assistant.
        
        Great! You've provided all the required materials. Now I have a few final questions:
        
        1. Who do you know that is currently represented by us?
        2. What is your dream job?
        3. What work are you not interested in and why?
        4. How did you hear about us?
        
        Please answer these questions to help us get to know you better."""
    )
    
    response = llm.invoke(prompt.format())
    state["messages"].append(AIMessage(content=str(response)))
    
    return state

def final_questions(state: AgentState) -> AgentState:
    """Handle final questions and conclude."""
    # Get the last message from the user
    last_message = state["messages"][-1]
    
    if isinstance(last_message, HumanMessage):
        # Store the research answers
        state["applicant_info"]["research_answers"] = last_message.content
        
        # Create final summary
        summary = f"""Perfect! I've collected all the information for your TDH Agency application.

Here's a summary of what we have:

**Personal Information:**
- Name: {state['applicant_info'].get('name', 'Not provided')}
- Email: {state['applicant_info'].get('email', 'Not provided')}
- Phone: {state['applicant_info'].get('phone', 'Not provided')}
- Role Type: {state['role_type']}

**Materials Collected:**
"""
        
        for req, collected in state["requirements_collected"].items():
            if collected:
                formatted_req = req.replace("_", " ").title()
                summary += f"- {formatted_req}: ✓\n"
        
        summary += """
Your application is ready! You can now submit it to info@tdhagency.com with all the materials we've collected.

Thank you for using the TDH Agency Application Assistant!"""
        
        state["messages"].append(AIMessage(content=summary))
        state["ready_for_submission"] = True
    
    return state


# Create the graph
builder = StateGraph(AgentState)

# Add nodes
builder.add_node("welcome", welcome_node)
builder.add_node("collect_basic_info", collect_basic_info)
builder.add_node("classify_role", classify_role)
builder.add_node("request_role_clarification", request_role_clarification)
builder.add_node("dancer_requirements", dancer_requirements)
builder.add_node("dancer_who_sings_requirements", dancer_who_sings_requirements)
builder.add_node("singer_actor_requirements", singer_actor_requirements)
builder.add_node("spotlight_check", spotlight_check)
builder.add_node("collect_spotlight_link", collect_spotlight_link)
builder.add_node("representation_check", representation_check)
builder.add_node("collect_representation_details", collect_representation_details)
builder.add_node("work_preferences", work_preferences)
builder.add_node("dancer_materials", dancer_materials)
builder.add_node("singer_actor_materials", singer_actor_materials)
builder.add_node("collect_requirements", collect_requirements)
builder.add_node("continue_materials_collection", continue_materials_collection)
builder.add_node("research_questions", research_questions)
builder.add_node("final_questions", final_questions)

# Simplified edges to prevent recursion
builder.add_edge(START, "welcome")
builder.add_edge("welcome", "collect_basic_info")
builder.add_edge("collect_basic_info", "classify_role")

# Conditional edge after role classification
builder.add_conditional_edges("classify_role", route_after_role_classification)

# Direct edges for role clarification
builder.add_edge("request_role_clarification", "classify_role")

# Direct edges for requirements explanation
builder.add_edge("dancer_requirements", "spotlight_check")
builder.add_edge("dancer_who_sings_requirements", "spotlight_check")
builder.add_edge("singer_actor_requirements", "spotlight_check")

# Conditional edge after spotlight check
builder.add_conditional_edges("spotlight_check", route_after_spotlight_check)

# Direct edge for spotlight link collection
builder.add_edge("collect_spotlight_link", "representation_check")

# Conditional edge after representation check
builder.add_conditional_edges("representation_check", route_after_representation_check)

# Direct edge for representation details
builder.add_edge("collect_representation_details", "work_preferences")

# Conditional edge after work preferences
builder.add_conditional_edges("work_preferences", route_after_work_preferences)

# Conditional edges for materials collection
builder.add_conditional_edges("dancer_materials", route_after_materials_collection)
builder.add_conditional_edges("singer_actor_materials", route_after_materials_collection)

# Edge for continuing materials collection
builder.add_edge("continue_materials_collection", "collect_requirements")

# Direct edge to research questions after all materials collected
builder.add_edge("collect_requirements", "research_questions")

# Direct edge for research questions
builder.add_edge("research_questions", "final_questions")

# Final edge
builder.add_edge("final_questions", END)

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
        "ready_for_submission": False,
        "has_spotlight": None,
        "has_representation": None,
        "work_preferences": {},
        "materials_collected": {}
    }
    
    # Create a unique thread ID
    thread_id = "thread_1"
    
    # Store the initial state
    conversation_states[thread_id] = initial_state
    
    # Manually run just the welcome node to get the initial message
    welcome_result = welcome_node(initial_state)
    
    # Update the stored state
    conversation_states[thread_id] = welcome_result
    
    return welcome_result, thread_id

def determine_next_node(state: AgentState) -> str:
    """Determine which node to execute next based on current state."""
    current_stage = state["current_stage"]
    
    if current_stage == "basic_info":
        return "collect_basic_info"
    elif current_stage == "role_classification":
        return "classify_role"
    elif current_stage == "explain_requirements":
        # Route to appropriate requirements explanation based on role
        role_type = state["role_type"]
        if role_type == "Dancer":
            return "dancer_requirements"
        elif role_type == "Dancer Who Sings":
            return "dancer_who_sings_requirements"
        elif role_type == "Singer/Actor":
            return "singer_actor_requirements"
        else:
            return "request_role_clarification"
    elif current_stage == "spotlight_check":
        return "spotlight_check"
    elif current_stage == "collect_spotlight":
        return "collect_spotlight_link"
    elif current_stage == "representation_check":
        return "representation_check"
    elif current_stage == "collect_representation":
        return "collect_representation_details"
    elif current_stage == "work_preferences":
        return "work_preferences"
    elif current_stage == "materials_collection":
        role_type = state["role_type"]
        if role_type in ["Dancer", "Dancer Who Sings"]:
            return "dancer_materials"
        else:
            return "singer_actor_materials"
    elif current_stage == "collect_requirements":
        return "collect_requirements"
    elif current_stage == "research_questions":
        return "research_questions"
    elif current_stage == "final_questions":
        return "final_questions"
    else:
        return "END"

def execute_node(node_name: str, state: AgentState) -> AgentState:
    """Execute a specific node function."""
    node_functions = {
        "collect_basic_info": collect_basic_info,
        "classify_role": classify_role,
        "request_role_clarification": request_role_clarification,
        "dancer_requirements": dancer_requirements,
        "dancer_who_sings_requirements": dancer_who_sings_requirements,
        "singer_actor_requirements": singer_actor_requirements,
        "spotlight_check": spotlight_check,
        "collect_spotlight_link": collect_spotlight_link,
        "representation_check": representation_check,
        "collect_representation_details": collect_representation_details,
        "work_preferences": work_preferences,
        "dancer_materials": dancer_materials,
        "singer_actor_materials": singer_actor_materials,
        "collect_requirements": collect_requirements,
        "continue_materials_collection": continue_materials_collection,
        "research_questions": research_questions,
        "final_questions": final_questions
    }
    
    if node_name in node_functions:
        return node_functions[node_name](state)
    else:
        # Unknown node, return state unchanged
        return state

def continue_conversation(user_input: str, thread_id: str):
    """Continue an existing conversation with the agent."""
    # Get the current state from storage
    if thread_id not in conversation_states:
        print("No existing conversation found. Starting a new one.")
        return initialize_conversation()[0]
    
    current_state = conversation_states[thread_id]
    
    # Add the user input to the conversation
    current_state["messages"].append(HumanMessage(content=user_input))
    
    # Keep executing nodes until the stage stops changing
    max_iterations = 3  # Prevent infinite loops
    iterations = 0
    
    while iterations < max_iterations:
        original_stage = current_state["current_stage"]
        
        # Determine the next node to execute based on current stage
        next_node = determine_next_node(current_state)
        
        # Execute the next node
        if next_node == "END":
            current_state["current_stage"] = "END"
            break
        else:
            current_state = execute_node(next_node, current_state)
        
        # If stage didn't change, we're done processing
        if current_state["current_stage"] == original_stage:
            break
            
        iterations += 1
    
    # Update the stored state
    conversation_states[thread_id] = current_state
    
    return current_state
 

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