import gradio as gr
import pytesseract
from PIL import Image
import PyPDF2
from pdf2image import convert_from_path
from googletrans import Translator
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import os
import tempfile

translator = Translator()

def extract_text_from_pdf(pdf_file, use_ocr=False):
    """Extract text from PDF file"""
    text = ""
    try:
        if use_ocr:
            # Convert PDF to images and use OCR
            with tempfile.TemporaryDirectory() as path:
                images = convert_from_path(pdf_file.name, output_folder=path)
                for img in images:
                    text += pytesseract.image_to_string(img) + "\n"
        else:
            # Direct text extraction
            pdf_reader = PyPDF2.PdfReader(pdf_file.name)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        return f"Error extracting PDF: {str(e)}"
    return text

def extract_text_from_docx(docx_file):
    """Extract text from DOCX file"""
    try:
        doc = Document(docx_file.name)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        return f"Error extracting DOCX: {str(e)}"

def extract_text_from_image(image_file):
    """Extract text from image using OCR"""
    try:
        img = Image.open(image_file.name)
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        return f"Error extracting image: {str(e)}"

def translate_text(text, src_lang='en', dest_lang='si'):
    """Translate text to Sinhala"""
    try:
        # Split text into chunks (Google Translate has limits)
        max_length = 4500
        chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
        
        translated_chunks = []
        for chunk in chunks:
            if chunk.strip():
                translation = translator.translate(chunk, src=src_lang, dest=dest_lang)
                translated_chunks.append(translation.text)
        
        return "\n".join(translated_chunks)
    except Exception as e:
        return f"Translation error: {str(e)}"

def create_txt_file(text):
    """Create a downloadable TXT file"""
    txt_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8')
    txt_file.write(text)
    txt_file.close()
    return txt_file.name

def process_document(file, use_ocr):
    """Main processing function"""
    if file is None:
        return "Please upload a file", None
    
    # Extract text based on file type
    file_extension = os.path.splitext(file.name)[1].lower()
    
    if file_extension == '.pdf':
        extracted_text = extract_text_from_pdf(file, use_ocr)
    elif file_extension == '.docx':
        extracted_text = extract_text_from_docx(file)
    elif file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
        extracted_text = extract_text_from_image(file)
    elif file_extension == '.txt':
        with open(file.name, 'r', encoding='utf-8') as f:
            extracted_text = f.read()
    else:
        return "Unsupported file format. Please upload PDF, DOCX, TXT, or image files.", None
    
    if not extracted_text or extracted_text.startswith("Error"):
        return extracted_text, None
    
    # Translate to Sinhala
    translated_text = translate_text(extracted_text, src_lang='en', dest_lang='si')
    
    # Create downloadable file
    output_file = create_txt_file(translated_text)
    
    return translated_text, output_file

# Create Gradio interface
with gr.Blocks(title="English to Sinhala Document Translator", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 📄 English to Sinhala Document Translator
        
        Upload your document (PDF, DOCX, TXT, or Image) and get it translated to Sinhala!
        
        **Features:**
        - Support for PDF, DOCX, TXT, and image files
        - OCR support for scanned documents
        - Download translated text as TXT file
        """
    )
    
    with gr.Row():
        with gr.Column():
            file_input = gr.File(
                label="Upload Document",
                file_types=[".pdf", ".docx", ".txt", ".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
            )
            ocr_checkbox = gr.Checkbox(
                label="Use OCR (for scanned PDFs or images with text)",
                value=False
            )
            translate_btn = gr.Button("Translate", variant="primary", size="lg")
        
        with gr.Column():
            output_text = gr.Textbox(
                label="Translated Text (Sinhala)",
                lines=15,
                max_lines=20
            )
            download_file = gr.File(label="Download Translated Document")
    
    gr.Markdown(
        """
        ### Instructions:
        1. Upload your document (English text)
        2. Check "Use OCR" if your document is a scanned image or PDF
        3. Click "Translate" to convert to Sinhala
        4. Download the translated text file
        
        **Note:** This app uses Google Translate API for translation.
        """
    )
    
    translate_btn.click(
        fn=process_document,
        inputs=[file_input, ocr_checkbox],
        outputs=[output_text, download_file]
    )

if __name__ == "__main__":
    demo.launch()