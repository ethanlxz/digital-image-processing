# DIP Task B: Paragraph Extraction

This program extracts paragraphs from `Converted Paper (8)/001.png` to
`008.png`. It supports single-, double- and triple-column layouts and saves
the results in column-by-column reading order.

## Method

1. Convert each page to a binary image using Otsu's threshold.
2. Use the column projection to locate column gutters.
3. Use the row projection inside each column to locate paragraph gaps.
4. Save the crops from left to right and top to bottom.

## Layouts detected in the eight papers

| Paper | Layout  | Paragraphs |
|-------|---------|-----------:|
| 001   | single  |  6 |
| 002   | triple  |  8 |
| 003   | double  |  7 |
| 004   | double with spanning table |  8 |
| 005   | single  |  5 |
| 006   | triple  |  8 |
| 007   | double  |  **8** |
| 008   | double  |  **8** |

## How to run

```bash
cd task_b_paragraphs
python3 run_all.py
```

Outputs are saved as
`task_b_paragraphs/outputs/paragraphs/<paper>/paragraph <number>.png`.

## Repository layout

```
.
├── README.md
├── .gitignore
├── Converted Paper (8)/
└── task_b_paragraphs/
    ├── requirements.txt
    ├── run_all.py
    └── scripts/
        ├── config.py
        └── histogram.py
```

## Allowed libraries (per the assignment brief)

- Python Standard Library
- OpenCV
- NumPy

## Settings

All thresholds live in `task_b_paragraphs/scripts/config.py`:

| Constant                | Default | Effect                                                           |
|-------------------------|--------:|------------------------------------------------------------------|
| `MIN_GUTTER_PX`         |     20  | Minimum horizontal empty run to count as a column gutter.        |
| `MIN_COL_WIDTH_PX`      |    100  | Skip any "column" narrower than this (rejects noise).            |
| `PARAGRAPH_MIN_GAP_PX`  |     25  | Minimum vertical empty run to count as a paragraph break.        |
| `PARAGRAPH_PADDING_PX`  |     30  | Padding pixels around each saved crop.                           |
| `SINGLE_LINE_HEIGHT_PX` |     80  | Shorter paragraphs glued onto the next block.                    |
| `SINGLE_LINE_GAP_PX`    |     80  | Gap threshold for the in-body short-paragraph merge.             |
| `TOP_HEADING_MAX_HEIGHT_PX` | 80 | Max height for the first paragraph of a column to be kept separate. `0` disables the rule. |
| `TOP_HEADING_GAP_PX`    |     80  | Gap threshold for the top-of-column heading rule.                |
