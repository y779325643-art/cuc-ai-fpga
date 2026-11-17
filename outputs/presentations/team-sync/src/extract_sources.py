import argparse
from pathlib import Path



ROOT = Path(__file__).resolve().parents[4] / "reports" / "manuscripts" / "drafts"
OUT = Path(__file__).resolve().parents[1] / "sources"

SOURCE_FILES = [
    "HNAI-FPGA_商业企划书.docx",
    "HNAI_FPGA_IEEE_Access_Manuscript_1_中文翻译.docx",
    "HNAI_FPGA_IEEE_Access_Manuscript_1_副本.docx",
]


def extract_docx(path: Path) -> str:
    from docx import Document

    doc = Document(path)
    blocks = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            blocks.append(text)

    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip().replace("\n", " / ") for cell in row.cells]
            row_text = " | ".join(cell for cell in cells if cell)
            if row_text:
                blocks.append(row_text)
    return "\n".join(blocks)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract the historical team-sync source documents.")
    parser.add_argument("--source-dir", type=Path, default=ROOT)
    args = parser.parse_args()
    missing = [name for name in SOURCE_FILES if not (args.source_dir / name).is_file()]
    if missing:
        parser.error("Missing source documents: " + ", ".join(missing))
    OUT.mkdir(parents=True, exist_ok=True)
    parts = []
    for name in SOURCE_FILES:
        path = args.source_dir / name
        text = extract_docx(path)
        parts.append(f"# {name}\n\n{text}\n")
        (OUT / f"{path.stem}.txt").write_text(text, encoding="utf-8")

    (OUT / "combined_sources.txt").write_text("\n\n".join(parts), encoding="utf-8")


if __name__ == "__main__":
    main()
