import requests
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

