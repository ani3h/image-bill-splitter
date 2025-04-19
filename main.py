from imageprocessing import extract_text
from billparsing import extract_invoice_data

text = extract_text("bill4.jpeg")
invoice_data = extract_invoice_data(text)

print(text)
print(invoice_data)
