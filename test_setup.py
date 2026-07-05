from dotenv import load_dotenv
import os

load_dotenv()

print("LangSmith key loaded:", bool(os.getenv("LANGCHAIN_API_KEY")))
print("Tavily key loaded:", bool(os.getenv("TAVILY_API_KEY")))

# Test Ollama
from langchain_ollama import ChatOllama

llm = ChatOllama(model="llama3.1:8b")
response = llm.invoke("Say hello in one sentence.")
print("Ollama response:", response.content)