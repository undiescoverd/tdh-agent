# test_llama.py
from langchain_ollama import OllamaLLM  # Changed from Ollama to OllamaLLM

def test_ollama_connection():
    # Initialize the Ollama client with the local model
    llm = OllamaLLM(model="llama3.1:8b-instruct-q4_0")  # Updated to use OllamaLLM
    
    # Simple test prompt
    response = llm.invoke("You are a talent agent assistant. Respond with a greeting in 1-2 sentences.")
    
    print("==== LLM Response ====")
    print(response)
    print("======================")
    
    return "Connection successful!" if response else "Connection failed!"

if __name__ == "__main__":
    print("Testing connection to Ollama...")
    result = test_ollama_connection()
    print(result)