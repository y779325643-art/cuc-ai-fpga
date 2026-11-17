from pathlib import Path
from PIL import Image

BASE = Path(__file__).resolve().parents[1]
PREVIEW_DIR = BASE / "preview"
OUTPUT = BASE / "deliverables" / "HNAI-FPGA_项目讲解_清晰重排版.pdf"


def slide_number(path: Path) -> int:
    stem = path.stem
    return int(stem.split("-")[-1])


def main() -> None:
    slide_paths = sorted(PREVIEW_DIR.glob("slide-*.png"), key=slide_number)
    if len(slide_paths) != 37:
        raise RuntimeError(f"Expected 37 slide previews, found {len(slide_paths)}")

    images = []
    for slide_path in slide_paths:
        image = Image.open(slide_path).convert("RGB")
        images.append(image)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    first, rest = images[0], images[1:]
    first.save(OUTPUT, "PDF", save_all=True, append_images=rest, resolution=100.0)

    for image in images:
        image.close()

    print(OUTPUT)


if __name__ == "__main__":
    main()
