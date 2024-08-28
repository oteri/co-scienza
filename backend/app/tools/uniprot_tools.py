from __future__ import annotations
from bioservices import UniProt
from langchain.tools import tool
from langchain.pydantic_v1 import BaseModel, Field
from typing import List, Union, Dict

uniprot = UniProt(verbose=False)

class SearchInput(BaseModel):
    query: str = Field(description="UniProt search query")
    frmt: str = Field(default="tsv", description="Output format (tsv, fasta, json)")
    columns: str = Field(default=None, description="Columns to retrieve")
    limit: int = Field(default=None, description="Limit the number of results")

class GetFastaInput(BaseModel):
    uniprot_id: str = Field(description="A valid UniProt ID")

class GetDataInput(BaseModel):
    uniprot_ids: str = Field(description="UniProt ID(s) to retrieve data for")
    columns: str = Field(default=None, description="Columns to retrieve")

@tool("uniprot_search", args_schema=SearchInput)
def uniprot_search(query: str, frmt: str = "tsv", columns: str = None, limit: int = None) -> str:
    """
    Perform a search query on UniProt.

    This tool allows you to search the UniProt database using various fields and criteria.
    For a list of available search fields and query syntax, use the 'uniprot_search_help' tool.

    Args:
        query (str): UniProt search query
        frmt (str): Output format (tsv, fasta, json)
        columns (str): Columns to retrieve
        limit (int): Limit the number of results

    Returns:
        str: Search results in the specified format
    """
    return uniprot.search(query, frmt=frmt, columns=columns, limit=limit)

@tool("uniprot_get_fasta", args_schema=GetFastaInput)
def uniprot_get_fasta(uniprot_id: str) -> str:
    """
    Retrieve the FASTA sequence for a given UniProt ID.

    Args:
        uniprot_id (str): A valid UniProt ID

    Returns:
        str: FASTA sequence
    """
    return uniprot.get_fasta(uniprot_id)

@tool("uniprot_get_data", args_schema=GetDataInput)
def uniprot_get_data(uniprot_ids: str, columns: str = None) -> Dict:
    """
    Retrieve data for given UniProt ID(s).

    Args:
        uniprot_ids (str): UniProt ID(s) to retrieve data for
        columns (str): Columns to retrieve

    Returns:
        Dict: Data for the specified UniProt IDs
    """
    if isinstance(uniprot_ids, str):
        uniprot_ids = [uniprot_ids]
    
    return uniprot.get_df(uniprot_ids, columns=columns)


# Example usage
if __name__ == "__main__":
# Example search    
    search_results = uniprot_search.invoke(input={"query":"insulin AND organism_name:human", 
                                                  "frmt":"tsv",
                                                  "columns":["id","accession","length","gene_names"]
                                                  })
    print("\nSearch Results:")
    #print(search_results)

# Example get_fasta
    fasta_sequence = uniprot_get_fasta.invoke(input={'uniprot_id':"P38398"})
    print("\nFASTA Sequence for P38398 (BRCA1_HUMAN):")
    print(fasta_sequence)

# Example get_data
    data = uniprot_get_data.invoke(input={'uniprot_ids':"P38398", 
                                          'columns':["Entry","Entry Name","Sequence"]})
    print("\nData for P38398 (BRCA1_HUMAN):")
    print(data)