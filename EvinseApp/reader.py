
import fitz


def open_file(filename):
    return fitz.open(filename)
pdf_path="Amarasinghe 2022.pdf"
doc=open_file(pdf_path)
print("successfully open")