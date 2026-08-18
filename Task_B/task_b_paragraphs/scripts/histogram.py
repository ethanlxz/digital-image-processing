from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import cv2
import numpy as np


@dataclass(frozen=True)
class BBox:
    """Inclusive image coordinates."""

    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def width(self) -> int:
        return self.x2 - self.x1 + 1

    @property
    def height(self) -> int:
        return self.y2 - self.y1 + 1

    @property
    def area(self) -> int:
        return self.width * self.height

    def as_tuple(self) -> Tuple[int, int, int, int]:
        return self.x1, self.y1, self.x2, self.y2


def binarize(gray: np.ndarray) -> np.ndarray:
    """Convert a grayscale image to binary with foreground pixels at 255."""
    if gray.ndim != 2:
        raise ValueError(f"need 2-D grayscale, got shape {gray.shape}")

    _, binary = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )
    return binary


def row_histogram(binary: np.ndarray) -> np.ndarray:
    return binary.sum(axis=1)


def column_histogram(binary: np.ndarray) -> np.ndarray:
    return binary.sum(axis=0)


def _zero_runs(mask: np.ndarray) -> List[Tuple[int, int]]:
    zeros = np.where(mask == 0)[0]
    if zeros.size == 0:
        return []

    runs: List[Tuple[int, int]] = []
    start = previous = int(zeros[0])
    for value in zeros[1:]:
        value = int(value)
        if value == previous + 1:
            previous = value
        else:
            runs.append((start, previous))
            start = previous = value
    runs.append((start, previous))
    return runs


def text_segments(
    mask: np.ndarray,
    min_gap: int,
    min_width: int = 1,
) -> List[Tuple[int, int]]:
    """Split a projection histogram at sufficiently long empty runs."""
    segments: List[Tuple[int, int]] = []
    cursor = 0

    for gap_start, gap_end in _zero_runs(mask):
        if gap_end - gap_start + 1 < min_gap:
            continue

        text_end = gap_start - 1
        if text_end - cursor + 1 >= min_width:
            segments.append((cursor, text_end))
        cursor = gap_end + 1

    if len(mask) - cursor >= min_width:
        segments.append((cursor, len(mask) - 1))
    return segments


def detect_columns(
    binary: np.ndarray,
    min_gutter: int,
    min_col_width: int,
) -> List[Tuple[int, int]]:
    """Find text columns from the vertical projection."""
    ink = np.count_nonzero(binary, axis=0)
    non_empty = ink[ink > 0]

    if non_empty.size:
        near_blank_limit = max(1, int(np.median(non_empty) * 0.30))
        near_blank = (ink <= near_blank_limit).astype(np.uint8)[None, :]
        near_blank = cv2.morphologyEx(
            near_blank,
            cv2.MORPH_CLOSE,
            np.ones((1, 5), dtype=np.uint8),
        )[0]
        projection = (near_blank == 0).astype(np.uint8)
    else:
        projection = ink

    return text_segments(projection, min_gutter, min_col_width)


def detect_full_width_ruled_blocks(
    binary: np.ndarray,
    columns: List[Tuple[int, int]],
) -> List[BBox]:
    """Find ruled tables that span multiple body columns."""
    if len(columns) < 2:
        return []

    page_x1, page_x2 = columns[0][0], columns[-1][1]
    span_width = page_x2 - page_x1 + 1
    row_ink = np.count_nonzero(binary[:, page_x1 : page_x2 + 1], axis=1)
    rule_rows = np.where(row_ink >= span_width * 0.80)[0]
    if rule_rows.size < 3:
        return []

    blocks: List[BBox] = []
    group_start = group_end = int(rule_rows[0])
    group_count = 1

    def add_group(start: int, end: int, count: int) -> None:
        if count < 3:
            return

        start = max(0, start - 1)
        end = min(binary.shape[0] - 1, end + 1)
        ink_columns = np.where(np.any(binary[start : end + 1] > 0, axis=0))[0]
        if ink_columns.size:
            blocks.append(
                BBox(int(ink_columns[0]), start, int(ink_columns[-1]), end)
            )

    for row in rule_rows[1:]:
        row = int(row)
        if row - group_end <= 60:
            group_end = row
            group_count += 1
        else:
            add_group(group_start, group_end, group_count)
            group_start = group_end = row
            group_count = 1

    add_group(group_start, group_end, group_count)
    return blocks


def detect_paragraphs_in_column(
    column_binary: np.ndarray,
    min_gap: int,
    min_height: int = 1,
) -> List[Tuple[int, int]]:
    return text_segments(row_histogram(column_binary), min_gap, min_height)


def _last_line_width_ratio(binary: np.ndarray, box: "BBox", col_width: int) -> float | None:
    """How much of the column width the paragraph's last text line fills.

    A paragraph that ends naturally almost always wraps early on its last
    line (it runs out of sentence before it runs out of margin). A paragraph
    that gets cut off by a column boundary instead has its last line packed
    all the way to the column edge, because the text simply kept going. This
    ratio is the signal used to tell the two cases apart.
    """
    sub = binary[box.y1 : box.y2 + 1, box.x1 : box.x2 + 1]
    row_ink = row_histogram(sub)
    text_rows = np.where(row_ink > 0)[0]
    if text_rows.size == 0:
        return None

    end = int(text_rows[-1])
    start = end
    row_set = set(int(r) for r in text_rows)
    while (start - 1) in row_set:
        start -= 1

    last_line = sub[start : end + 1, :]
    ink_cols = np.where(np.any(last_line > 0, axis=0))[0]
    if ink_cols.size == 0:
        return None

    return (int(ink_cols[-1]) - int(ink_cols[0]) + 1) / col_width


def merge_short_paragraphs(
    paragraphs: List[Tuple[int, int]],
    next_gap_threshold: int,
    short_height: int,
    top_heading_max_height: int = 0,
    top_heading_gap: int = 0,
) -> List[Tuple[int, int]]:
    """Merge short body blocks while preserving a short first-column block."""
    if not paragraphs:
        return []

    merged: List[List[int]] = [[paragraphs[0][0], paragraphs[0][1]]]
    start_index = 1

    if top_heading_max_height > 0 and len(paragraphs) >= 2:
        first_height = paragraphs[0][1] - paragraphs[0][0] + 1
        first_gap = paragraphs[1][0] - paragraphs[0][1] - 1
        if first_height < top_heading_max_height and first_gap < top_heading_gap:
            merged.append([paragraphs[1][0], paragraphs[1][1]])
            start_index = 2

    for y1, y2 in paragraphs[start_index:]:
        previous = merged[-1]
        gap = y1 - previous[1] - 1
        previous_height = previous[1] - previous[0] + 1
        if previous_height < short_height and gap < next_gap_threshold:
            previous[1] = y2
        else:
            merged.append([y1, y2])

    return [(y1, y2) for y1, y2 in merged]


def extract_paragraphs(
    image: np.ndarray,
    min_gutter: int,
    min_col_width: int,
    paragraph_min_gap: int,
    short_para_height: int,
    short_para_gap: int,
    top_heading_max_height: int = 0,
    top_heading_gap: int = 0,
    continuation_width_ratio: float = 0.90,
) -> List[List[BBox]]:
    """Return paragraphs in column-by-column reading order.

    Each paragraph is a list of one or more BBoxes: normally just one, but
    two when a paragraph runs past the bottom of a column and its text
    continues at the top of the next column (common in multi-column
    layouts) - see `_last_line_width_ratio`.
    """
    gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    binary = binarize(gray)
    columns = detect_columns(binary, min_gutter, min_col_width)

    spanning_blocks = detect_full_width_ruled_blocks(binary, columns)
    body_binary = binary.copy()
    for block in spanning_blocks:
        body_binary[block.y1 : block.y2 + 1, :] = 0

    per_column_paragraphs: List[List[Tuple[int, int]]] = []
    for x1, x2 in columns:
        paragraphs = detect_paragraphs_in_column(
            body_binary[:, x1 : x2 + 1], paragraph_min_gap
        )
        paragraphs = merge_short_paragraphs(
            paragraphs,
            next_gap_threshold=short_para_gap,
            short_height=short_para_height,
            top_heading_max_height=top_heading_max_height,
            top_heading_gap=top_heading_gap,
        )
        per_column_paragraphs.append(paragraphs)

    paragraphs_out: List[List[BBox]] = [[block] for block in spanning_blocks]
    carry: List[BBox] = []

    for ci, (x1, x2) in enumerate(columns):
        col_paragraphs = list(per_column_paragraphs[ci])
        col_width = x2 - x1 + 1
        has_next_column = ci < len(columns) - 1

        if carry:
            if col_paragraphs:
                y1, y2 = col_paragraphs.pop(0)
                carry.append(BBox(x1, y1, x2, y2))
            still_continuing = False
            if carry and not col_paragraphs and has_next_column:
                ratio = _last_line_width_ratio(body_binary, carry[-1], col_width)
                if ratio is not None and ratio >= continuation_width_ratio:
                    still_continuing = True
            if not still_continuing:
                paragraphs_out.append(carry)
                carry = []

        while col_paragraphs:
            y1, y2 = col_paragraphs.pop(0)
            box = BBox(x1, y1, x2, y2)
            if not col_paragraphs and has_next_column:
                ratio = _last_line_width_ratio(body_binary, box, col_width)
                if ratio is not None and ratio >= continuation_width_ratio:
                    carry = [box]
                    break
            paragraphs_out.append([box])

    if carry:
        paragraphs_out.append(carry)

    return paragraphs_out


def crop_with_padding(
    image: np.ndarray,
    bbox: BBox,
    padding: int,
) -> np.ndarray:
    height, width = image.shape[:2]
    x1 = max(0, bbox.x1 - padding)
    y1 = max(0, bbox.y1 - padding)
    x2 = min(width - 1, bbox.x2 + padding)
    y2 = min(height - 1, bbox.y2 + padding)
    return image[y1 : y2 + 1, x1 : x2 + 1].copy()


def crop_paragraph(
    image: np.ndarray,
    segments: List[BBox],
    padding: int,
) -> np.ndarray:
    """Crop a paragraph, stitching multiple column segments into one image.

    Most paragraphs are a single segment. A paragraph split across a column
    boundary (see `extract_paragraphs`) has two segments; they are cropped
    separately, then stacked vertically so the saved image reads as one
    continuous paragraph.
    """
    crops = [crop_with_padding(image, segment, padding) for segment in segments]
    if len(crops) == 1:
        return crops[0]

    max_width = max(crop.shape[1] for crop in crops)
    padded = []
    for crop in crops:
        if crop.shape[1] < max_width:
            crop = cv2.copyMakeBorder(
                crop,
                0, 0, 0, max_width - crop.shape[1],
                cv2.BORDER_CONSTANT,
                value=255,
            )
        padded.append(crop)
    return cv2.vconcat(padded)