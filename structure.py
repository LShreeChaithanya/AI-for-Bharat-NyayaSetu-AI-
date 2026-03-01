from pathlib import Path

# Root project folder (change name if needed)
ROOT = Path("backend")

STRUCTURE = {
    "pyproject.toml": None,
    "uv.lock": None,
    ".env": None,
    ".env.example": None,
    "Dockerfile": None,
    "docker-compose.yml": None,

    "app": {
        "main.py": None,
        "config.py": None,

        "api": {
            "router.py": None,
            "routes.py": None,
        },

        "schemas": {
            "ai.py": None,
        },

        "ai": {
            "service.py": None,
            "registry.py": None,
            "agents.py": None,
            "chains.py": None,
            "rag.py": None,
            "evaluation.py": None,

            "prompts": {
                "system": {},
                "tasks": {},
            },
        },

        "db": {
            "mongo.py": None,
            "neo4j.py": None,
            "redis.py": None,
        },

        "repositories": {
            "document_repo.py": None,
        },

        "workers": {
            "broker.py": None,
            "tasks.py": None,
        },

        "utils": {},
    },

    "tests": {
        "unit": {},
        "integration": {},
    },
}


def create_structure(base_path: Path, structure: dict):
    for name, content in structure.items():
        path = base_path / name

        if content is None:
            # File
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
                print(f"Created file: {path}")
        else:
            # Directory
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {path}")

            create_structure(path, content)


if __name__ == "__main__":
    if not ROOT.exists():
        ROOT.mkdir()
        print(f"Created root directory: {ROOT}")

    create_structure(ROOT, STRUCTURE)
    print("\nScaffolding complete.")