# English to Sinhala Document Translator

This application translates English documents to Sinhala with OCR support for scanned documents.

## Features

- 📄 Support for multiple file formats: PDF, DOCX, TXT, and images
- 🔍 OCR support for scanned documents and images
- 🌐 Automatic translation from English to Sinhala
- 💾 Download translated text as TXT file

## Supported File Types

- PDF documents (.pdf)
- Word documents (.docx)
- Text files (.txt)
- Images (.jpg, .jpeg, .png, .bmp, .tiff)

## How to Use

1. Upload your English document
2. Enable "Use OCR" option if your document is scanned or image-based
3. Click "Translate" button
4. View and download the translated Sinhala text

## Local Installation

```bash
pip install -r requirements.txt
python app.py
```

## Note

- For OCR functionality, you need Tesseract OCR installed on your system
- Translation powered by Google Translate
- Large documents may take longer to process
