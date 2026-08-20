# DIP Task B: Paragraph Extraction

This folder contains the Task B paragraph-extraction program. The program reads
the given paper images from `Task_B_Input/`, detects the paragraph regions, and
saves each extracted paragraph into the output folder.

## Files

- `run_all.py` runs the full Task B paragraph-extraction program.
- `scripts/config.py` contains the input folder, output folder, and detection
  settings.
- `scripts/histogram.py` contains the paragraph detection and cropping
  functions.
- `Task_B_Input/` contains the given input paper images, from `001.png` to
  `008.png`.
- `Task_B_Output/` contains the extracted paragraph images and is also the
  default output folder.
- `task_b_paragraphs/` contains another copy of the Task B program files.

## Requirements

Install the required Python libraries before running:

```bash
pip install opencv-python numpy
```

## How to run

Run from inside the `Task_B` folder:

```bash
python run_all.py
```

The extracted paragraphs are saved in:

```text
Task_B_Output/paragraphs/<paper>/paragraph <number>.png
```

For example, paragraphs from `Task_B_Input/001.png` are saved in
`Task_B_Output/paragraphs/001/`.

## Method

1. Convert each page to a binary image using Otsu's threshold.
2. Use the column projection to locate column gutters.
3. Use the row projection inside each column to locate paragraph gaps.
4. Save the crops from left to right and top to bottom.

## Layouts detected in the eight papers

| Paper | Layout  | Paragraphs |
|-------|---------|-----------:|
| 001   | single  |  6 |
| 002   | triple  |  6 |
| 003   | double  |  6 |
| 004   | double with spanning table |  7 |
| 005   | single  |  5 |
| 006   | triple  |  6 |
| 007   | double  |  7 |
| 008   | double  |  7 |

## Settings

All thresholds live in `scripts/config.py`:

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
