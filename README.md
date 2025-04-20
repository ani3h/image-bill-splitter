# Image Bill Splitter

Image Bill Splitter is a web application that uses Computer Vision and OCR technology to automatically identify and process restaurant bills from images. Upload a photo of your receipt, and the application extracts itemized details and provides an intuitive interface to split costs among friends or colleagues fairly.

## Features

- **OCR-Powered Text Extraction** - Uses Tesseract and OpenCV to extract text from bill images
- **Intelligent Bill Parsing** - Automatically identifies items, quantities, prices, and taxes
- **User-Friendly Interface** - Clean Bootstrap UI makes splitting bills intuitive
- **Fair Cost Distribution** - Splits taxes proportionally based on each person's items
- **Responsive Design** - Works on both desktop and mobile devices

## Installation

### Prerequisites

- Python 3.8+
- Tesseract OCR
- OpenCV

### Setup

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/image-bill-splitter.git
   cd image-bill-splitter
   ```

2. Create and activate a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Install Tesseract OCR
   - **Windows**: Download from [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)
   - **macOS**: `brew install tesseract`
   - **Linux**: `sudo apt install tesseract-ocr`

5. Run the application
   ```bash
   python app.py
   ```

6. Open your browser and navigate to `http://127.0.0.1:5000`

## Usage Guide

1. **Upload Bill** - Take a clear photo of your receipt and upload it
2. **Add People** - Enter the names of people who will split the bill
3. **Assign Items** - Check boxes to indicate who had which item
4. **Get Results** - View how much each person owes with a detailed breakdown

## Project Structure

```
image-bill-splitter/
├── app.py                 # Main Flask application
├── src/
│   ├── imageprocessing.py # Image preprocessing and OCR
│   └── billparsing.py     # Bill data extraction logic
├── templates/             # HTML templates
│   ├── base.html
│   ├── home.html
│   ├── upload.html 
│   ├── add_people.html
│   ├── assign_items.html
│   └── results.html
├── uploads/               # Directory for uploaded images
├── static/                # Static assets (CSS, JS, images)
└── README.md
```

## OCR and Image Processing

The application uses a multi-stage image processing pipeline to maximize text extraction accuracy:

1. **Grayscale Conversion** - Simplifies the image for better processing
2. **Thresholding** - Enhances contrast between text and background
3. **Gaussian Blur** - Reduces noise while preserving text edges
4. **OCR Processing** - Tesseract extracts text from the processed image

## Bill Parsing

The bill parsing module uses sophisticated regular expressions to identify:

- Item names, quantities, and prices
- Tax lines (CGST, SGST, etc.)
- Subtotal and total amounts
