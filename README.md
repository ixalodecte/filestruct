# FileStruct

**FileStruct** is a high-level Python library that aims to extract the overall structure of documents, particularly PDFs, based on visual information such as size, color and font.

## How does it work ?

As clever human beings, we are able to detect titles, subtitles, and paragraphs using the visual appearence of the document. A big text in red most certainly represent a title (or subtitle). Using these heuristics, we are able to structure a document : _This paragraph belongs to this section_. The same method is used by this package to provide an automated, while realistic way to structure a document. The method is described bellow :

1.  **Text and style extraction :** We rely on lower level librairies (like PyMuPDF) for the extraction of the text and style information, and the ordering of each block of text.
2.  **Tree creation :** A tree is created, in which each block of text is a node of the tree. A child of a node in the tree is a subsection of a section in the document.
3.  **Data exportation :** The data can be exported in JSON format.

For now, filestruct can only read formats that are supported by PyMuPDF. This includes pdf, epub, xps, mobi, fb2, cbz and svg. I plan to add more file formats in the future.

## Installation

Install **FileStruct** using **pip** :

```sh
pip install filestruct
```


## Getting Started

Bellow, a basic usage for a PDF document :

```python
from filestruct.document import PDFDocument

doc = Document("PATH_TO_YOUR_FILE.pdf")
data = doc.to_json()   # Export the tree into json format
print(data)
print(doc)
```

