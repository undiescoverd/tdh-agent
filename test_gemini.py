#!/usr/bin/env python3
"""
Test script to verify Gemini API integration.
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv()

def test_gemini_connection():
    """Test the Gemini API connection and basic functionality."""
    print("Testing Gemini 2.5 Flash connection...")
    
    # Check if API key is set
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your-gemini-api-key-here":
        print("❌ ERROR: Please set your actual Gemini API key in the .env file")
        return False
    
    try:
        # Initialize the LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.7,
            google_api_key=api_key
        )
        
        # Test with a simple prompt
        response = llm.invoke("Hello! Please respond with 'Gemini connection successful' if you can receive this message.")
        
        print(f"✅ Connection successful!")
        print(f"Response: {response}")
        
        # Test with a more complex prompt similar to what the app uses
        complex_response = llm.invoke("""You are Emily, the TDH Agency Application Assistant. 
        Respond with a brief, friendly greeting and explain that you help talent apply to TDH Agency.""")
        
        print(f"\n✅ Complex prompt test successful!")
        print(f"Response: {complex_response}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Failed to connect to Gemini API")
        print(f"Error details: {str(e)}")
        return False

def test_updated_requirements():
    """Test if all required packages are available."""
    print("\nTesting required packages...")
    
    try:
        import langchain_google_genai
        print("✅ langchain-google-genai imported successfully")
        
        from dotenv import load_dotenv
        print("✅ python-dotenv imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ ERROR: Missing required package")
        print(f"Please run: pip install -r requirements.txt")
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("TDH Agent - Gemini API Integration Test")
    print("=" * 50)
    
    # Test package imports
    packages_ok = test_updated_requirements()
    
    if packages_ok:
        # Test API connection
        connection_ok = test_gemini_connection()
        
        if connection_ok:
            print("\n🎉 All tests passed! Your Gemini integration is ready.")
            print("\nYou can now run the main application with:")
            print("python tdh_agent.py")
        else:
            print("\n⚠️  Please check your API key and try again.")
    else:
        print("\n⚠️  Please install missing packages and try again.")