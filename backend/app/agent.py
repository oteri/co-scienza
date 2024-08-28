from typing import Annotated, List, TypedDict, Union
from dotenv import load_dotenv
from langchain_core.messages import AIMessage,SystemMessage,HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
import operator
from app.tools.uniprot_tools import uniprot_search, uniprot_get_fasta, uniprot_get_data

from langserve.pydantic_v1 import BaseModel, Field

load_dotenv()

class InputChat(BaseModel):
    """Input for the chat endpoint."""

    messages: List[Union[HumanMessage, AIMessage, SystemMessage]] = Field(
        ...,
        description="The chat messages representing the current conversation.",
    )


class ChatState(TypedDict):
    messages: Annotated[list[HumanMessage, AIMessage, SystemMessage], operator.add]

toolbox = [uniprot_search, 
           uniprot_get_fasta, 
           uniprot_get_data
        ]

llm  = ChatGoogleGenerativeAI(temperature=1, model="gemini-1.5-pro")
llm_with_tools = llm.bind_tools(toolbox) 

messages = [
    SystemMessage(content="""Your name is co-scienza and you are a helpful assistant for common retrieval tools.
    
    - You are friendly and always perform the needed parameter conversion to use tools.
      Example:
      The user provides "XXXX", but the tool needs a list of string. You convert the parameter to ["XXXX"]
    
    If you lack some parameter to use a tool, ask it to the user and then perform the call.
    
    Always interpret the output of the tools and provide a nice description.
    """), 
    ("placeholder", "{messages}")                
]
prompt = ChatPromptTemplate.from_messages(messages=messages)  
chain = prompt | llm_with_tools


def chatbot(state: ChatState) -> ChatState: 
    message = chain.invoke(input=state)
    print("Message:",message, end="\n\n")
    return {'messages':[message]}

tool_node = ToolNode(tools=toolbox)

graph_builder = StateGraph(ChatState)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)

graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("tools", "chatbot")  

graph_builder.add_edge("chatbot", END)

graph = graph_builder.compile()


# Define a custom chain to handle input and invoke the graph
def agent_chain(message: InputChat) -> str:
    response = graph.invoke(input=message)
    return response['messages'][-1].content