import numpy as np
import fitz
from collections import defaultdict
from functools import total_ordering


def load_PyMuPDF(filename):
    doc = fitz.open(filename)
    page_id = 0
    paragraph_id = 0
    line_id = 0
    span_id = 0
    spans = []
    style_set = []
    for page in doc:
        txt = page.get_text("dict", flags=4, sort=True)["blocks"]
        for paragraph in txt:
            if paragraph["type"] == 0:
                for line in paragraph["lines"]:
                    for span in line["spans"]:
                        # If all text is upper it is likely to be a title
                        upper = span["text"] == span["text"].upper()

                        # Text is in bold
                        bold = "bold" in span["font"]

                        style = Style(
                            span["size"], span["font"], span["color"], bold, upper
                        )
                        if style in style_set:
                            style = style_set[style_set.index(style)]
                        else:
                            style_set.append(style)
                        style.add_char(len(span["text"]))
                        d = {
                            "style": style,
                            "flags": span["flags"],
                            "text": span["text"],
                            "x": span["bbox"][0],
                            "y": span["bbox"][1],
                            "w": span["bbox"][2],
                            "h": span["bbox"][3],
                            "page_id": page_id,
                            "paragraph_id": paragraph_id,
                            "page_id": page_id,
                            "line_id": line_id,
                            "span_id": span_id,
                        }
                        spans.append(d)
                        span_id += 1
                    line_id += 1
                paragraph_id += 1
        page_id += 1
    return {"span": spans, "style_set": style_set}


class Style:
    style_attribute = ["size", "font", "color", "bold", "upper", "score", "level"]

    def __init__(self, size, font, color, bold=False, upper=False):
        self.size = size
        self.font = font
        self.color = color
        self.bold = bold
        self.upper = upper
        self.score = 0
        self.level = 0
        self.num_char = 0

    def add_char(self, num_char_inc):
        self.num_char += num_char_inc

    def __eq__(self, o):
        return (
            self.size == o.size
            and self.font == o.font
            and self.color == o.color
            and self.bold == o.bold
        )

    def __hash__(self):
        return (self.size, self.font, self.color, self.bold).__hash__()

    def __str__(self):
        res = f"{round(self.size, 2)}px | {self.font} | {self.color}"
        if self.bold:
            res += " | bold"
        if self.upper:
            res += " | upper"
        return res
