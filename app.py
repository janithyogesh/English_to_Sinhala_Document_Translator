import streamlit as st
from deep_translator import GoogleTranslator
import pytesseract
from PIL import Image
import PyPDF2
from pdf2image import convert_from_path
from docx import Document
import tempfile
import os
import shutil
import io
import requests

# --- PDF Generation using WeasyPrint (proper complex script support via Pango/HarfBuzz) ---
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

# --- Configuration ---
st.set_page_config(
    page_title="Sinhala Document & Text Translation",
    page_icon="🇱🇰",
    layout="wide"
)

# --- AUTO-DOWNLOAD SINHALA FONT ---
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
FONT_PATH = os.path.join(FONT_DIR, "NotoSansSinhala-Regular.ttf")
# Note: Using the variable font URL for better compatibility, the function handles the download.
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/notosanssinhala/NotoSansSinhala%5Bwdth%2Cwght%5D.ttf"

@st.cache_resource
def download_sinhala_font():
    """Download Noto Sans Sinhala font from Google Fonts."""
    if os.path.exists(FONT_PATH):
        return FONT_PATH
    
    try:
        os.makedirs(FONT_DIR, exist_ok=True)
        response = requests.get(FONT_URL, timeout=30)
        response.raise_for_status()
        
        with open(FONT_PATH, 'wb') as f:
            f.write(response.content)
        
        return FONT_PATH
    except Exception as e:
        # In a professional app, logging or a less intrusive error might be preferred
        st.error(f"Configuration Error: Failed to download Sinhala font for PDF generation. Check internet connection and deployment environment. Details: {e}")
        return None

font_path = download_sinhala_font()

# --- CORE FUNCTIONS (UNCHANGED) ---

def translate_text(text, source_lang='en', target_lang='si'):
    """Translate text between specified languages."""
    if not text or not text.strip():
        return "Please enter some text to translate."
    
    try:
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        max_length = 4500
        
        if len(text) <= max_length:
            return translator.translate(text)
        
        chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
        translated = []
        
        for chunk in chunks:
            if chunk.strip():
                translated.append(translator.translate(chunk))
        
        return " ".join(translated)
    
    except Exception as e:
        return f"Translation error: {str(e)}"

def extract_text(file, use_ocr=False, ocr_lang='eng'):
    """Extract text from uploaded file."""
    tmp_paths_to_cleanup = []
    extracted_text = ""

    try:
        file_ext = os.path.splitext(file.name)[1].lower()
        
        if file_ext == '.txt':
            stringio = io.StringIO(file.getvalue().decode("utf-8", errors='ignore'))
            extracted_text = stringio.read()
        
        elif file_ext == '.pdf':
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                shutil.copyfileobj(file, tmp)
                tmp_path = tmp.name
            tmp_paths_to_cleanup.append(tmp_path)
            
            if use_ocr:
                with tempfile.TemporaryDirectory() as tmpdir:
                    # Note: pdf2image dependencies (Poppler) must be installed on the system
                    images = convert_from_path(tmp_path, fmt='jpeg', output_folder=tmpdir)
                    for img in images:
                        # Note: pytesseract dependencies (Tesseract) must be installed on the system
                        extracted_text += pytesseract.image_to_string(img, lang=ocr_lang) + "\n"
            else:
                with open(tmp_path, 'rb') as f:
                    pdf = PyPDF2.PdfReader(f)
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            extracted_text += page_text + "\n"
        
        elif file_ext == '.docx':
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
                shutil.copyfileobj(file, tmp)
                tmp_path = tmp.name
            tmp_paths_to_cleanup.append(tmp_path)
            
            doc = Document(tmp_path)
            extracted_text = "\n".join([p.text for p in doc.paragraphs])
            
        elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            img = Image.open(file)
            extracted_text = pytesseract.image_to_string(img, lang=ocr_lang)
            
        else:
            return f"Unsupported file type: {file_ext}"
            
        return extracted_text.strip() if extracted_text.strip() else "No text found in file."
        
    except Exception as e:
        return f"Extraction Error: {str(e)}"
    finally:
        for tmp_path in tmp_paths_to_cleanup:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

def generate_sinhala_pdf(text_content):
    """
    Generate PDF with proper Sinhala Unicode support using WeasyPrint.
    WeasyPrint uses Pango + HarfBuzz for proper complex script text shaping.
    """
    if not font_path:
        # Error handled in the download_sinhala_font function, returning None here
        return None
    
    try:
        # Escape HTML special characters
        import html
        safe_text = html.escape(text_content)
        
        # Convert newlines to HTML paragraphs
        paragraphs = safe_text.split('\n')
        # Use more robust line breaking by replacing consecutive newlines with <br> and wrapping text in <p>
        html_paragraphs = ''.join([f'<p>{p}</p>' if p.strip() else '<br>' for p in paragraphs])
        
        # Create HTML with embedded font
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @font-face {{
                    font-family: 'NotoSansSinhala';
                    src: url('file://{font_path}');
                }}
                body {{
                    font-family: 'NotoSansSinhala', sans-serif;
                    font-size: 14px;
                    line-height: 1.8;
                    margin: 40px;
                    padding: 0;
                }}
                p {{
                    margin-bottom: 12px;
                    text-align: justify;
                }}
            </style>
        </head>
        <body>
            {html_paragraphs}
        </body>
        </html>
        '''
        
        # Generate PDF using WeasyPrint
        font_config = FontConfiguration()
        html_doc = HTML(string=html_content)
        
        # Write to bytes buffer
        pdf_buffer = io.BytesIO()
        pdf_buffer.name = 'sinhala_translation.pdf' # Give the buffer a name for better downloading
        html_doc.write_pdf(pdf_buffer, font_config=font_config)
        pdf_buffer.seek(0)
        
        return pdf_buffer.getvalue()
        
    except Exception as e:
        st.error(f"PDF Generation Failed: {e}")
        return None

# --- UI ---

st.title("🌐 Sinhala Document and Text Processing Suite")
st.subheader("High-Quality English-to-Sinhala Translation and OCR for Documents")

st.markdown("---")


tab1, tab2, tab3 = st.tabs(["📄 Document Translation (EN → SI)", "✍️ Text Translation (EN → SI)", "🔍 Sinhala OCR Text Extraction"])

# --- TAB 1: Document Translation ---
with tab1:
    st.markdown("### English Document to Sinhala Translation")
    st.markdown("Upload your document (PDF, DOCX, TXT, or Image) for translation. The output is a clean, translated PDF/TXT.")

    uploaded_file = st.file_uploader(
        "Upload Source File (English)",
        type=['pdf', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'bmp', 'tiff'],
        key="upload_en"
    )
    
    col_ocr_doc, col_placeholder = st.columns([1, 3])
    with col_ocr_doc:
        use_ocr_en = st.checkbox("Enable OCR for scanned documents/images", value=False, key="ocr_en")
    
    st.markdown("---")

    if uploaded_file is not None:
        if st.button("🚀 Process and Translate Document", type="primary", key="translate_doc_btn"):
            
            with st.spinner("Step 1: Extracting English text..."):
                extracted = extract_text(uploaded_file, use_ocr=use_ocr_en, ocr_lang='eng')
            
            st.markdown("#### Translation Results")
            col1, col2 = st.columns(2)
            
            with col1:
                st.info("📝 Extracted English Text")
                st.text_area("Original Content", extracted, height=350, key="extracted_en")
            
            if not extracted.startswith("Error") and not extracted.startswith("No text"):
                with st.spinner("Step 2: Translating content to Sinhala..."):
                    translated = translate_text(extracted, source_lang='en', target_lang='si')
                
                with col2:
                    st.success("🇱🇰 Sinhala Translation")
                    st.text_area("Translated Content", translated, height=350, key="translated_doc")
                    
                    st.markdown("---")
                    st.subheader("Download Options")

                    # Generate PDF button/process
                    with st.spinner("Step 3: Generating clean, complex-script PDF..."):
                        pdf_bytes = generate_sinhala_pdf(translated)

                    if pdf_bytes:
                        st.download_button(
                            label="⬇️ Download Translated Text as PDF (Recommended)",
                            data=pdf_bytes,
                            file_name="sinhala_document_translation.pdf",
                            mime="application/pdf",
                            help="This ensures correct Sinhala Unicode rendering."
                        )
                    
                    st.download_button(
                        label="⬇️ Download Translated Text as TXT",
                        data=translated.encode('utf-8'),
                        file_name="sinhala_document_translation.txt",
                        mime="text/plain"
                    )
            else:
                 with col2:
                    st.error("Translation Failed: Could not extract valid text from the document.")

# --- TAB 2: Text Translation ---
with tab2:
    st.markdown("### Quick Text Translation")
    st.markdown("Paste short to medium-length English text below for instant Sinhala translation.")
    
    input_text = st.text_area(
        "English Source Text",
        height=250,
        placeholder="Enter your English text here...",
        key="input_text_paste"
    )
    
    st.markdown("---")

    if st.button("🚀 Translate Text", type="primary", key="translate_text_btn"):
        if input_text and input_text.strip() != "Please enter some text to translate.":
            with st.spinner("Translating..."):
                result = translate_text(input_text, source_lang='en', target_lang='si')
            
            st.subheader("🇱🇰 Sinhala Translation Output")
            st.text_area("Translated Text", result, height=250, key="translated_text_paste")
            
            st.markdown("---")
            st.subheader("Download Output")

            # PDF Download
            with st.spinner("Generating PDF..."):
                pdf_bytes = generate_sinhala_pdf(result)

            if pdf_bytes:
                st.download_button(
                    label="⬇️ Download as PDF",
                    data=pdf_bytes,
                    file_name="sinhala_text_translation.pdf",
                    mime="application/pdf"
                )
            
            # TXT Download
            st.download_button(
                label="⬇️ Download as TXT",
                data=result.encode('utf-8'),
                file_name="sinhala_text_translation.txt",
                mime="text/plain"
            )
        else:
            st.warning("Please enter valid English text to translate.")

# --- TAB 3: Sinhala OCR ---
with tab3:
    st.markdown("### Sinhala Optical Character Recognition (OCR)")
    st.markdown("Upload a scanned Sinhala PDF or Image file to extract the text content.")
    
    uploaded_sinhala_file = st.file_uploader(
        "Upload Sinhala Source File (Scanned PDF, Image, or TXT)",
        type=['pdf', 'txt', 'jpg', 'jpeg', 'png', 'bmp', 'tiff'],
        key="upload_si"
    )
    
    st.markdown("---")

    if uploaded_sinhala_file is not None:
        if st.button("🔎 Extract Sinhala Text", type="primary", key="extract_sinhala_btn"):
            file_ext = os.path.splitext(uploaded_sinhala_file.name)[1].lower()
            # Only use OCR if it's not a plain text file
            use_ocr = file_ext != '.txt' 

            with st.spinner("Performing Sinhala OCR... (This may take a moment for large files)"):
                extracted_si = extract_text(uploaded_sinhala_file, use_ocr=use_ocr, ocr_lang='sin')
            
            st.markdown("#### Extracted Content")
            st.text_area("🇱🇰 Extracted Sinhala Text", extracted_si, height=350, key="extracted_si")
            
            st.markdown("---")

            if not extracted_si.startswith("Error") and not extracted_si.startswith("No text"):
                st.download_button(
                    label="💾 Download Extracted Text (.txt)",
                    data=extracted_si.encode('utf-8'),
                    file_name="extracted_sinhala.txt",
                    mime="text/plain"
                )
            else:
                st.error("Extraction failed. Check if Tesseract and the Sinhala language pack (`sin`) are correctly installed and configured in your deployment environment.")

st.markdown("---")
