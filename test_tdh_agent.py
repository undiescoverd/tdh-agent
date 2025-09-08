# test_tdh_agent.py
from tdh_agent import initialize_conversation, continue_conversation
import time

def run_test_scenario(scenario_name, test_inputs):
    """Run through a predefined test scenario with a list of inputs."""
    print(f"\n===== Testing Scenario: {scenario_name} =====\n")
    
    # Initialize conversation
    state, thread_id = initialize_conversation()
    
    # Print initial response
    if state["messages"]:
        print(f"Emily: {state['messages'][0].content}")
    
    # Process each test input
    for user_input in test_inputs:
        print(f"\nYou: {user_input}")
        
        # Simulate slight delay for readability
        time.sleep(0.5)
        
        # Continue conversation with this input
        state = continue_conversation(user_input, thread_id)
        
        # Print response
        if state["messages"]:
            print(f"Emily: {state['messages'][-1].content}")
    
    # Print final state information
    print("\n--- Final State Information ---")
    print(f"Role Type: {state['role_type']}")
    print(f"Current Stage: {state['current_stage']}")
    print(f"Ready for Submission: {state['ready_for_submission']}")
    print(f"Requirements Collected: {state['requirements_collected']}")
    
    return state

# Define test scenarios
dancer_scenario = [
    "Hi, I'd like to apply",
    "My name is Jane Smith",
    "jane.smith@email.com",
    "+44 7700 900123",
    "I don't have a Spotlight link",
    "I'm a Dancer",
    "Yes, I have my CV in PDF format",
    "Here's my dance reel: https://youtube.com/watch?v=abcd1234",
    "Here's my vocal reel: https://vimeo.com/567890",
    "Here's my acting reel: https://youtube.com/watch?v=efgh5678",
    "How do I format the email?"
]

singer_actor_scenario = [
    "Hello, I want to join TDH Agency",
    "John Doe, johndoe@example.com, +1 555-123-4567",
    "No Spotlight profile yet",
    "I'm a Singer/Actor",
    "I have my CV as a Word document",
    "My vocal reel is at https://youtube.com/watch?v=vocal12345",
    "Acting reel: https://vimeo.com/acting6789",
    "I don't have a movement reel yet",
    "What happens after I submit?"
]

invalid_materials_scenario = [
    "Hi, I'm Alex Garcia",
    "alex@example.com",
    "+61 4 1234 5678",
    "Dancer Who Sings",
    "I have my CV on Google Drive, is that okay?",  # Invalid format
    "Oh, I'll convert it to PDF. Here it is now",
    "My dance videos are on TikTok",  # Invalid platform
    "I see, here's my YouTube link instead: https://youtube.com/watch?v=dance123",
    "https://vimeo.com/vocal456",
    "https://youtube.com/watch?v=acting789"
]

# Run the test scenarios
if __name__ == "__main__":
    print("Running TDH Agent Test Scenarios...")
    
    # Choose which scenario to run
    scenario_choice = input("Choose a test scenario (1=Dancer, 2=Singer/Actor, 3=Invalid Materials): ")
    
    if scenario_choice == "1":
        run_test_scenario("Dancer Application", dancer_scenario)
    elif scenario_choice == "2":
        run_test_scenario("Singer/Actor Application", singer_actor_scenario)
    elif scenario_choice == "3":
        run_test_scenario("Invalid Materials Handling", invalid_materials_scenario)
    else:
        print("Invalid choice. Running Dancer scenario by default.")
        run_test_scenario("Dancer Application", dancer_scenario)