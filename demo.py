from filestruct.document import PDFDocument

doc = PDFDocument("samples/sample.pdf")
data = doc.to_json()
print(data)
print(doc)
