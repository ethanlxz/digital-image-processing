from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

_paper_dirs = [
    ROOT.parent / "Converted Paper (8)",
    ROOT.parent.parent / "Converted Paper (8)",
]
PAPERS_DIR = next((path for path in _paper_dirs if path.is_dir()), _paper_dirs[0])
PAPER_NAMES = [f"{index:03d}.png" for index in range(1, 9)]

OUT_DIR = ROOT / "outputs" / "paragraphs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Detection thresholds in pixels
MIN_GUTTER_PX = 20
MIN_COL_WIDTH_PX = 100
PARAGRAPH_MIN_GAP_PX = 25
PARAGRAPH_PADDING_PX = 30
SINGLE_LINE_HEIGHT_PX = 80
SINGLE_LINE_GAP_PX = 80
TOP_HEADING_MAX_HEIGHT_PX = 80
TOP_HEADING_GAP_PX = 80

# If a column's last paragraph has its last text line filling at least this
# fraction of the column width, treat it as cut off by the column boundary
# and merge it with the first paragraph of the next column (same paragraph
# continuing, not a new one).
CONTINUATION_WIDTH_RATIO = 0.90