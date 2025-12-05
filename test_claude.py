#!/usr/bin/env python3
"""
Test Claude API key
"""

import anthropic
from anthropic import NotFoundError
import os
from dotenv import load_dotenv

load_dotenv()

def test_claude_api():
    """Test if Claude API key is valid by trying all available models"""
    
    # Get API key from environment
    api_key = os.getenv("CLAUDE_API_KEY")
    
    if not api_key:
        print("❌ CLAUDE_API_KEY not found in .env file")
        print("Add: CLAUDE_API_KEY=your-key-here")
        return False, None
    
    print("🔑 Testing Claude API key...")
    print(f"Key: {api_key[:20]}...{api_key[-4:]}")
    print("\n🔍 Trying all available Claude models...\n")
    
    # All available Claude models
    models_to_test = [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet-20240620",
        "claude-3-sonnet-20240229",
        "claude-3-opus-20240229",
        "claude-3-haiku-20240307",
    ]
    
    # Initialize Claude client
    client = anthropic.Anthropic(api_key=api_key)
    
    for model_name in models_to_test:
        try:
            print(f"Testing: {model_name}...", end=" ")
            
            # Test with a simple message
            message = client.messages.create(
                model=model_name,
                max_tokens=50,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": "Return only the number 0.85"
                    }
                ]
            )
            
            result = message.content[0].text
            print(f"✅ SUCCESS!")
            print(f"\n🎉 Found working model: {model_name}")
            print(f"Response: {result}")
            print(f"Usage: {message.usage}")
            
            return True, model_name
            
        except anthropic.AuthenticationError:
            print("❌ Auth failed")
            return False, None
        except anthropic.RateLimitError:
            print("⚠️  Rate limit (but key valid!)")
            return True, model_name
        except anthropic.NotFoundError:
            print("❌ Not available")
            continue
        except Exception as e:
            print(f"❌ Error: {str(e)[:50]}")
            continue
    
    print("\n❌ No working model found for this API key")
    return False, None

if __name__ == "__main__":
    success, working_model = test_claude_api()
    if success and working_model:
        print(f"\n✅ Ready to integrate Claude into the app!")
        print(f"\n📝 Add this to your config.py:")
        print(f"CLAUDE_MODEL = '{working_model}'")
    elif success:
        print("\n⚠️  API key is valid but rate limited")
    else:
        print("\n❌ Fix the API key issue first")
