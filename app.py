import streamlit as st
from deep_translator import GoogleTranslator
import pytesseract
from PIL import Image
import PyPDF2
from pdf2image import convert_from_path
from docx import Document
import tempfile
import os

st.set_page_config(
    page_title="English to Sinhala Translator",
    page_icon="📄",
    layout="wide"
)

def translate_text(text):
    """Translate English to Sinhala"""
    if not text or not text.strip():
        return "Please enter some text to translate."
    
    try:
        translator = GoogleTranslator(source='en', target='si')
        
        # Handle long text by chunking
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

def extract_text(file, use_ocr=False):
    """Extract text from uploaded file"""
    file_ext = os.path.splitext(file.name)[1].lower()
    extracted_text = ""
    
    try:
        if file_ext == '.txt':
            extracted_text = file.read().decode('utf-8', errors='ignore')
        
        elif file_ext == '.pdf':
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                tmp.write(file.read())
                tmp_path = tmp.name
            
            if use_ocr:
                with tempfile.TemporaryDirectory() as tmpdir:
                    images = convert_from_path(tmp_path, output_folder=tmpdir)
                    for img in images:
                        extracted_text += pytesseract.image_to_string(img) + "\n"
            else:
                with open(tmp_path, 'rb') as f:
                    pdf = PyPDF2.PdfReader(f)
                    for page in pdf.pages:
                        extracted_text += page.extract_text() + "\n"
            
            os.unlink(tmp_path)
        
        elif file_ext == '.docx':
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
                tmp.write(file.read())
                tmp_path = tmp.name
            
            doc = Document(tmp_path)
            extracted_text = "\n".join([p.text for p in doc.paragraphs])
            os.unlink(tmp_path)
        
        elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            img = Image.open(file)
            extracted_text = pytesseract.image_to_string(img)
        
        else:
            return "Unsupported file type."
        
        return extracted_text if extracted_text.strip() else "No text found in file."
    
    except Exception as e:
        return f"Error: {str(e)}"

# UI
st.title("📄 English to Sinhala Document Translator")
st.markdown("### 100% FREE - No API Keys Required!")

tab1, tab2 = st.tabs(["📁 Upload Document", "✏️ Paste Text"])

with tab1:
    st.markdown("Upload your document and translate it to Sinhala")
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['pdf', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'bmp', 'tiff']
    )
    
    use_ocr = st.checkbox("Use OCR (for scanned documents/images)", value=False)
    
    if uploaded_file is not None:
        if st.button("🚀 Translate Document", type="primary"):
            with st.spinner("Extracting text..."):
                extracted = extract_text(uploaded_file, use_ocr)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📝 Extracted Text")
                st.text_area("Original", extracted, height=300, key="extracted")
            
            if not extracted.startswith("Error") and not extracted.startswith("No text"):
                with st.spinner("Translating to Sinhala..."):
                    translated = translate_text(extracted)
                
                with col2:
                    st.subheader("🇱🇰 Sinhala Translation")
                    st.text_area("Translation", translated, height=300, key="translated_doc")
                    
                    # Download button
                    st.download_button(
                        label="💾 Download Translation",
                        data=translated,
                        file_name="translation_sinhala.txt",
                        mime="text/plain"
                    )

with tab2:
    st.markdown("Type or paste your English text below")
    
    input_text = st.text_area(
        "English Text",
        height=200,
        placeholder="Enter your English text here..."
    )
    
    if st.button("🚀 Translate Text", type="primary", key="translate_text"):
        if input_text:
            with st.spinner("Translating..."):
                result = translate_text(input_text)
            
            st.subheader("🇱🇰 Sinhala Translation")
            st.text_area("Translation", result, height=200, key="translated_text")
            
            st.download_button(
                label="💾 Download Translation",
                data=result,
                file_name="translation_sinhala.txt",
                mime="text/plain"
            )

st.markdown("---")
st.markdown("""
### ✨ Features:
- 📝 Direct text translation
- 📄 PDF, DOCX, TXT file support  
- 🖼️ Image OCR (JPG, PNG, etc.)
- 🆓 100% Free - No API keys needed
- 💾 Download translations
### 📋 Supported Formats:
PDF, DOCX, TXT, JPG, PNG, BMP, TIFF
""")