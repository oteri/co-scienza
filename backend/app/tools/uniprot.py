import requests
from urllib.parse import quote
from langchain_core.tools import tool

@tool(parse_docstring=True)
def get_uniprot_data(accession_id: str) -> str:
    """Fetches a record identified by accession_id from UNIPROT;

    Args:
        accession_id: The UniProt accession ID (e.g., "P12345").
    """
    base_url = "https://rest.uniprot.org/uniprotkb/"
    url = f"{base_url}{accession_id}"

    headers = {"Accept": "application/json"}
    print('Fetching:', accession_id)
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        content = response.json()
        return content
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

@tool(parse_docstring=True)
def search_uniprot_data(query: str, size: int) -> str:
    """Searches uniprot for entry matching the query.

    Args:
        query: the query to use for searching uniprot
        size: the number of entry returned by the search
    """    
    base_url = "https://rest.uniprot.org/uniprotkb/search"

    params = {
        "query": query,
        "size": size,
    }
    headers = {"Accept": "application/json"}
  
    try:
        response = requests.get(base_url, params=params, headers=headers)
        response.raise_for_status()
        content = response.json()
        return content
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        print(f"URL: {response.url}")
        return None
    
    
if __name__ == "__main__":    
    query="Insulin AND (reviewed:true)"
    size = 5
    result = search_uniprot_data.invoke(input={"query":query, "size":size})
    assert len(result['results']) == size
    
    query="organism_id:9606 AND keyword:kinase"
    size = 8
    result = search_uniprot_data.invoke(input={"query":query, "size":size})
    assert len(result['results']) == size
