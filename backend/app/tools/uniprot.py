from app.tools.uniprot_tools import uniprot_search, uniprot_get_fasta, uniprot_get_data
from dotenv import load_dotenv
from langchain.agents import initialize_agent, AgentType
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI

load_dotenv()

llm  = ChatGoogleGenerativeAI(temperature=1, model="gemini-1.5-pro")

# Create a list of tools
tools = [uniprot_search, uniprot_get_fasta, uniprot_get_data]

# Initialize the agent
agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)
# Example usage
if __name__ == "__main__":
    # Use the agent
    result = agent.run("Search for the protein insulin in humans and get its FASTA sequence")
    print(result)