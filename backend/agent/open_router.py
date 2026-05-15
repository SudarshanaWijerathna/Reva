import requests
import json
from dotenv import load_dotenv
load_dotenv()
import os
OPEN_ROUTER_API_KEY = (os.getenv("OPEN_ROUTER_API_KEY") or "").strip()

# First API call with reasoning
def call_open_router(prompt: str=None) -> str:
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPEN_ROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
            "messages": [
                {
                    "role": "user",
                    "content": prompt 
                }
            ],
            "reasoning": {"enabled": True}
        })
    )

    try:
        data = response.json()
    except json.JSONDecodeError:
        raise RuntimeError(
            f"OpenRouter returned non-JSON response. Status={response.status_code}, Body={response.text}"
        )

    if response.status_code >= 400:
        raise RuntimeError(f"OpenRouter error. Status={response.status_code}, Body={data}")

    choices = data.get("choices")
    if not choices:
        raise RuntimeError(f"OpenRouter response missing choices. Status={response.status_code}, Body={data}")

    # extract assistant message (including reasoning_details if present)
    content = choices[0].get("message", {}).get("content")
    if content is None:
        raise RuntimeError(
            f"OpenRouter response missing message content. Status={response.status_code}, Body={data}"
        )
    return content.strip()

# Extract the assistant message with reasoning_details
#response = response.json()
#response = response['choices'][0]['message']

# Preserve the assistant message with reasoning_details
'''
if __name__ == "__main__":
    print("checking response")
    
    prompt = f"""
            You are a real-estate assistant. Your task is to fetch the required data based on the intent, context and user query provided.

            Important instructions for data fetching:
            - Fetch the required data based on the intent, context and user query provided.
            - Extract a JSON object ONLY (no prose, no code fences) with keys given in the Required fields to fetch section 
            - Only fetch data that is explicitly mentioned in the conversation history or is commonly required for the identified intent.
            - Do not fetch any data that is not relevant to the user's request or is not commonly required for the identified intent.

            Some pre defined data
            - property_type: land, housing, rental

            Conversation context : None
            User query: "Can you find me a land in colombo?"
            Intent: prediction
            Required fields to fetch: ["property_type", "location"]

            ex:
            Required fields to fetch: ["property_type", "location"]
            user message: "Can you find me a land in colombo?"
            Response will be like
            {{"property_type": "land", "location": "colombo"}}

            Fetch the required data and provide it in a structured format.
        """
    results=call_open_router(prompt).replace("```json", "").replace("```", "").strip()
    print(json.loads(results))
  '''