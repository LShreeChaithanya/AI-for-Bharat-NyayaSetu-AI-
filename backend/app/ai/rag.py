import niquests

BASE_URL = "http://vdb:9530/vdb/api/v0"

def upload_docs(docs: list[str]) -> bool:
    response = niquests.post(BASE_URL+"/upload-docs", json={"docs": docs})
    json_response = response.json()
    return json_response.get("status")

def download_docs() -> list[tuple[str, str]]:
    response = niquests.get(BASE_URL+"/download-docs")
    json_response = response.json()
    return json_response.get("data")

def retrieve_docs(query: str, limit: int = 20, threshold: float = 0.5) -> list[str]:
    response = niquests.post(BASE_URL+"/retrieve-docs", json={
        "query": query, "limit": limit, "threshold": threshold
    })
    json_response = response.json()
    full_data = json_response.get("data")
    only_texts = [item[0] for item in full_data]
    return only_texts

def reset_vdb() -> bool:
    response = niquests.get(BASE_URL+"/reset-vdb")
    json_response = response.json()
    return json_response.get("status")
