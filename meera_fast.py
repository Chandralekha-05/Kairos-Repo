from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
from typing import List, Optional

# Initialize OpenAI client
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="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"
)

app = FastAPI()

# Store the state in-memory
class ConversationState:
    def __init__(self):
        self.messages = []
        self.url_content = ""

state = ConversationState()

# Pydantic models for request bodies
class FetchURLRequest(BaseModel):
    url: str

class QueryRequest(BaseModel):
    question: str

# Function to fetch content from a URL
def fetch_url_content(url: str) -> str:
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text()
            return text[:2000]  # Limit to first 2000 characters to avoid too much data
        else:
            return "Failed to fetch content from the URL."
    except Exception as e:
        return str(e)

# Function to get response from OpenAI
def get_response(messages: List[dict]) -> str:
    try:
        completion = client.chat.completions.create(
            model="meta/llama-3.1-405b-instruct",
            messages=messages,
            temperature=0.2,
            top_p=0.7,
            max_tokens=1024,
            stream=True
        )

        # Collect the response
        response_text = ""
        for chunk in completion:
            if chunk.choices[0].delta.content is not None:
                response_text += chunk.choices[0].delta.content

        return response_text
    except Exception as e:
        return str(e)

# Endpoint to fetch URL content
@app.post("/fetch_url")
async def fetch_url(request: FetchURLRequest):
    url = request.url
    state.url_content = fetch_url_content(url)
    return {"message": "URL content fetched successfully", "content": state.url_content[:1000] + "..."}

# Endpoint to send user query
@app.post("/send_query")
async def send_query(request: QueryRequest):
    user_input = request.question
    if not user_input:
        raise HTTPException(status_code=400, detail="Question is required")

    if state.url_content:
        # Add user message to conversation history
        state.messages.append({"role": "user", "content": user_input})
        
        # Add URL content to messages for context
        state.messages.insert(0, {"role": "system", "content": f"Content from the URL: {state.url_content}"})

        # Get bot response
        bot_response = get_response(state.messages)
        
        # Add bot response to conversation history
        state.messages.append({"role": "assistant", "content": bot_response})

        # Clear the input field
        state.messages = []
        return {"response": bot_response}
    else:
        return {"response": "Please fetch URL content first."}
