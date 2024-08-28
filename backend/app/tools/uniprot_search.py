import json
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional, List, Dict, Any
import requests
from requests.adapters import HTTPAdapter, Retry
import re


class UniProtSearchTool:
    BASE_URL = "https://rest.uniprot.org/uniprotkb/search"
    
    def __init__(self):
        self.session = requests.Session()
        retries = Retry(total=5, backoff_factor=0.25, status_forcelist=[500, 502, 503, 504])
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.re_next_link = re.compile(r'<(.+)>; rel="next"')

    def search_uniprot_data(
        self,
        query: str,
        format: str = "json",
        fields: Optional[List[str]] = None,
        include_isoform: bool = False,
        size: int = 500,
        compressed: bool = False,
        paginate: bool = False
    ) -> Dict[str, Any]:
        """
        Searches UniProt for entries matching the query.

        Args:
            query: The query to use for searching UniProt.
            format: The format of the returned data (e.g., "json", "xml", "tsv", "fasta").
            fields: List of specific fields to retrieve (only for TSV, JSON formats).
            include_isoform: Whether to include isoforms in the search results.
            size: The number of entries to return per page.
            compressed: Whether to request compressed results.
            paginate: If True, return an iterator for all results. If False, return only the first page.

        Returns:
            A dictionary containing the search results and metadata.
        """
        params = {
            "query": query,
            "format": format,
            "size": size,
            "includeIsoform": str(include_isoform).lower(),
            "compressed": str(compressed).lower()
        }
        
        if fields:
            params["fields"] = ",".join(fields)
        
        headers = {"Accept": "application/json" if format == "json" else "text/plain"}
        
        if paginate:
            return self._paginated_search(params, headers)
        else:
            return self._single_page_search(params, headers)

    def _single_page_search(self, params: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        try:
            response = self.session.get(self.BASE_URL, params=params, headers=headers)
            response.raise_for_status()
            return {
                "content": response.json() if params["format"] == "json" else response.text,
                "total_results": int(response.headers.get("x-total-results", 0)),
                "next_page": self._get_next_link(response.headers)
            }
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return {"error": str(e)}

    def _paginated_search(self, params: Dict[str, Any], headers: Dict[str, str]):
        while True:
            result = self._single_page_search(params, headers)
            yield result
            if not result.get("next_page"):
                break
            params["cursor"] = self._extract_cursor(result["next_page"])

    def _get_next_link(self, headers: Dict[str, str]) -> Optional[str]:
        if "Link" in headers:
            match = self.re_next_link.match(headers["Link"])
            if match:
                return match.group(1)
        return None

    def _extract_cursor(self, next_link: str) -> str:
        return next_link.split("cursor=")[1].split("&")[0]


class UniProtSearchInput(BaseModel):
    query: str = Field(..., description="The query to use for searching UniProt")
    format: str = Field("json", description="The format of the returned data (e.g., 'json', 'xml', 'tsv', 'fasta')")
    fields: Optional[List[str]] = Field(None, description="List of specific fields to retrieve (only for TSV, JSON formats)")
    include_isoform: bool = Field(False, description="Whether to include isoforms in the search results")
    size: int = Field(500, description="The number of entries to return")
    compressed: bool = Field(False, description="Whether to request compressed results")
    paginate: bool = Field(False, description="If True, return all results. If False, return only the first page")


class UniProtLangChainTool(BaseTool):
    name = "uniprot_search"
    description = "Searches UniProt for protein information based on a given query"
    args_schema: Type[BaseModel] = UniProtSearchInput
    uniprot_tool: UniProtSearchTool = Field(default_factory=UniProtSearchTool)


    def __init__(self, **data):
        super().__init__(**data)
        self.uniprot_tool = UniProtSearchTool()

    def _run(self, input_str: str) -> str:
        try:
            # Try to parse input as JSON
            try:
                input_dict = json.loads(input_str)
                search_input = UniProtSearchInput(**input_dict)
            except json.JSONDecodeError:
                # If JSON parsing fails, treat input as a plain query string
                search_input = UniProtSearchInput(query=input_str)

            results = self.uniprot_tool.search_uniprot_data(
                query=search_input.query,
                format=search_input.format,
                fields=search_input.fields,
                include_isoform=search_input.include_isoform,
                size=search_input.size,
                compressed=search_input.compressed,
                paginate=search_input.paginate
            )

            if search_input.paginate:
                # For paginated results, we'll return a summary of the first page
                first_page = next(results)
                return (f"Total results: {first_page['total_results']}. "
                        f"First page content: {first_page['content'][:500]}... "
                        f"Use paginate=False to get full first page or process pages manually.")
            else:
                # For JSON format, let's extract and return specific information
                if search_input.format == "json":
                    entries = results['content'].get('results', [])
                    if entries:
                        entry = entries[0]  # Get the first entry
                        protein_name = entry.get('proteinDescription', {}).get('recommendedName', {}).get('fullName', {}).get('value', 'N/A')
                        gene_names = ', '.join([gene.get('value', '') for gene in entry.get('genes', []) if 'value' in gene])
                        organism = entry.get('organism', {}).get('scientificName', 'N/A')
                        
                        summary = (f"Total results: {results['total_results']}. "
                                   f"First entry: Protein: {protein_name}, "
                                   f"Gene(s): {gene_names}, Organism: {organism}. "
                                   f"Use different parameters to get more detailed information.")
                        return summary
                    else:
                        return "No results found for the given query."
                else:
                    return f"Total results: {results['total_results']}. Content: {results['content'][:500]}..."
        except Exception as e:
            return f"An error occurred: {str(e)}"

    async def _arun(self, input_str: str) -> str:
        # For simplicity, we're calling the synchronous version here.
        # In a production environment, you might want to implement a truly asynchronous version.
        return self._run(input_str)
    
if __name__ == "__main__":
    # Example usage within a LangChain agent or chain
    from langchain.agents import Tool
    from langchain.agents import AgentType
    from langchain.agents import initialize_agent
    from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
    from dotenv import load_dotenv
    load_dotenv()
    # Initialize the UniProt tool
    uniprot_tool = UniProtLangChainTool()

    # Create a LangChain tool from our custom tool
    tools = [
        Tool(
            name="UniProt Search",
            func=uniprot_tool._run,
            description="Useful for searching protein information in the UniProt database. Input should be a query string."
        )
    ]

    llm  = ChatGoogleGenerativeAI(temperature=1, model="gemini-1.5-pro")

    # Create an agent that uses the UniProt tool
    agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)

    # Use the agent to perform a UniProt search
    result = agent.run("Find information about the human insulin protein in UniProt")
    print(result)