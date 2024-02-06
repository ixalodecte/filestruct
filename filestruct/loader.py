import fitz


def load_PyMuPDF(filename):
    doc = fitz.open(filename)
    page_id = 0
    paragraph_id = 0
    line_id = 0
    span_id = 0
    spans = []
    for page in doc:
        txt = page.get_text("dict", flags=4, sort=True)["blocks"]
        for paragraph in txt:
            if paragraph["type"] == 0:
                for line in paragraph["lines"]:
                    for span in line["spans"]:
                        d = {
                            "size": span["size"],
                            "flags": span["flags"],
                            "font": span["font"],
                            "color": span["color"],
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
    return spans
