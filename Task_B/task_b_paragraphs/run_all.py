from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "scripts"))

import cv2
import config
from histogram import crop_paragraph, extract_paragraphs


def main() -> None:
    for name in config.PAPER_NAMES:
        paper_path = config.PAPERS_DIR / name
        if not paper_path.exists():
            print(f"{name}: missing, skipping")
            continue

        image = cv2.imread(str(paper_path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            print(f"{name}: could not be read, skipping")
            continue

        boxes = extract_paragraphs(
            image,
            min_gutter=config.MIN_GUTTER_PX,
            min_col_width=config.MIN_COL_WIDTH_PX,
            paragraph_min_gap=config.PARAGRAPH_MIN_GAP_PX,
            short_para_height=config.SINGLE_LINE_HEIGHT_PX,
            short_para_gap=config.SINGLE_LINE_GAP_PX,
            top_heading_max_height=config.TOP_HEADING_MAX_HEIGHT_PX,
            top_heading_gap=config.TOP_HEADING_GAP_PX,
            continuation_width_ratio=config.CONTINUATION_WIDTH_RATIO,
        )

        output_dir = config.OUT_DIR / paper_path.stem
        output_dir.mkdir(parents=True, exist_ok=True)
        for old_crop in output_dir.glob("paragraph *.png"):
            old_crop.unlink()

        for index, segments in enumerate(boxes, start=1):
            crop = crop_paragraph(image, segments, config.PARAGRAPH_PADDING_PX)
            cv2.imwrite(str(output_dir / f"paragraph {index}.png"), crop)

        print(f"{name}: {len(boxes)} paragraphs -> {output_dir}")


if __name__ == "__main__":
    main()