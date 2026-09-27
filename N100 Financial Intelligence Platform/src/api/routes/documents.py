from pathlib import Path

from fastapi import APIRouter


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


ROOT = Path(__file__).resolve().parents[3]


@router.get("/")
def get_documents():
    """Return available platform output documents."""

    output_dir = ROOT / "output"

    documents = []

    if output_dir.exists():
        for file_path in sorted(output_dir.iterdir()):
            if file_path.is_file():
                documents.append(
                    {
                        "name": file_path.name,
                        "type": file_path.suffix.lower(),
                        "size_bytes": file_path.stat().st_size,
                    }
                )

    return {
        "count": len(documents),
        "documents": documents,
    }