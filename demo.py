from filestruct.document import Document

doc = Document()
doc.open("samples/sample.pdf")
data = doc.to_json()
print(data)
print(doc)