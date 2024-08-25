from textwrap import dedent
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI

load_dotenv()

llm  = ChatGoogleGenerativeAI(temperature=1, model="gemini-1.5-pro")

message = """Your name is co-scienza and you are a helpful assistant 
        for common retrieval tasks. 
        This is the user question to answer:
        {user_question}"""

prompt = ChatPromptTemplate.from_template(message)
chain = prompt | llm
