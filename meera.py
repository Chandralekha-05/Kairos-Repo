import streamlit as st
from openai import OpenAI
import requests
from bs4 import BeautifulSoup

# Initialize OpenAI client
client = OpenAI(
  base_url="https://integrate.api.nvidia.com/v1",
   api_key="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"
)

# Streamlit UI
st.title("CHAT WITH MEERA")

# Initialize session state for conversation history, user input, and URL
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""
if 'url_content' not in st.session_state:
    st.session_state.url_content = ""

# Function to fetch content from a URL
def fetch_url_content(url):
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
def get_response(messages):
    with st.spinner("Thinking..."):
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

# URL input
url_input = st.text_input("Enter URL to fetch content from:", "")

if st.button("Fetch URL Content") and url_input:
    st.session_state.url_content = fetch_url_content(url_input)
    st.write("URL Content Fetched Successfully!")
    st.write(st.session_state.url_content[:1000] + "...")  # Display first 1000 characters

# Display conversation history
for msg in st.session_state.messages:
    if msg['role'] == 'user':
        st.write(f"You: {msg['content']}")
    else:
        st.write(f"Bot: {msg['content']}")

# Input for user message
user_input = st.text_input("You:", st.session_state.user_input)

if st.button("Send") and user_input:
    # Add user message to conversation history
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Check if URL content is available
    if st.session_state.url_content:
        # Add URL content to messages
        st.session_state.messages.insert(0, {"role": "system", "content": f"Content from the URL: {st.session_state.url_content}"})

        # Get bot response
        bot_response = get_response(st.session_state.messages)
        
        # Add bot response to conversation history
        st.session_state.messages.append({"role": "assistant", "content": bot_response})

        # Clear the input field and update session state
        st.session_state.user_input = ""
    else:
        st.write("Please fetch URL content first.")

if not user_input:
    st.write("Type your message and press 'Send'.")
