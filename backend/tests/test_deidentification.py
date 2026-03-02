"""
Test script for de-identification API.

- Reads PDFs from the `doc` folder (backend/doc or project root doc).
- Calls the de-identification API for each document.
- Saves response JSON to backend/tests/results/<document_basename>_result.json.
"""
import json
import sys
from pathlib import Path

import requests

# Paths: PDFs go in backend/doc; results go to backend/tests/results
BACKEND_DIR = Path(__file__).resolve().parent.parent
DOC_FOLDER = BACKEND_DIR / "doc"
RESULTS_DIR = Path(__file__).resolve().parent / "results"

API_URL = "http://localhost:8000/api/v1/ai/deidentify"
HEALTH_URL = "http://localhost:8000/api/v1/ai/health"


def ensure_doc_and_results():
    """Ensure doc and results directories exist."""
    DOC_FOLDER.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def test_health():
    """Test health endpoint."""
    print("Testing health endpoint...")
    response = requests.get(HEALTH_URL, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()
    return response.status_code == 200


def test_deidentification(file_path: Path) -> dict | None:
    """
    Call de-identification API for one document and return response JSON.

    Args:
        file_path: Path to document file (PDF, JPG, PNG).

    Returns:
        Response JSON dict if successful, None otherwise.
    """
    print(f"Processing: {file_path.name}")

    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f, "application/octet-stream")}
        response = requests.post(API_URL, files=files, timeout=120)

    print(f"  Status: {response.status_code}")

    if response.status_code != 200:
        print(f"  Error: {response.text}")
        return None

    result = response.json()
    return result


def save_result(document_basename: str, result: dict) -> Path:
    """Save result JSON to tests/results/<basename>_result.json."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_name = f"{Path(document_basename).stem}_result.json"
    out_path = RESULTS_DIR / out_name
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)
    return out_path


def main():
    """Run tests: health check, then de-identify all PDFs in doc folder and save results."""
    print("=" * 60)
    print("NyayaSetu AI - De-identification Service Test")
    print("=" * 60)
    print()

    ensure_doc_and_results()

    if not DOC_FOLDER.exists():
        print(f"Doc folder not found: {DOC_FOLDER}")
        print("Create it and add PDFs to test.")
        sys.exit(1)

    # Health check
    try:
        if not test_health():
            print("Health check failed. Is the server running?")
            print("Start with: python -m uvicorn app.main:app --reload --app-dir backend")
            sys.exit(1)
    except requests.RequestException as e:
        print(f"Health check failed: {e}")
        print("Make sure the server is running: python backend/app/main.py")
        sys.exit(1)

    # Find PDFs in doc folder
    pdfs = list(DOC_FOLDER.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {DOC_FOLDER}")
        print("Add one or more PDF files there and run this script again.")
        sys.exit(0)

    print(f"Found {len(pdfs)} PDF(s) in {DOC_FOLDER}")
    print()

    for file_path in sorted(pdfs):
        result = test_deidentification(file_path)
        if result is not None:
            out_path = save_result(file_path.name, result)
            print(f"  Result saved: {out_path}")
        print()

    print("Done.")


if __name__ == "__main__":
    main()
