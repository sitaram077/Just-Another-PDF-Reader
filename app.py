from flask import Flask, render_template, request, jsonify
import requests
from PyPDF2 import PdfReader
from config import Config
import markdown
app = Flask(__name__)
app.config.from_object(Config)


# Route to render the upload form
@app.route('/')
def index():
    return render_template('upload.html')


# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ''
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text


# Function to chunk text into smaller pieces (e.g., 500 words per chunk)
def chunk_text(text, chunk_size=500):
    words = text.split()
    chunks = [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    return chunks


# Function to summarize each chunk using the GEMINI API
def summarize_chunk(chunk):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=AIzaSyAsg4gpsBHgHO7Wqm63yhI3NigJgkueYkM"
    headers = {
        'Content-Type': 'application/json'
    }
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": chunk
                    }
                ]
            }
        ]
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        return response.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text',
                                                                                                       'No summary generated')
    else:
        return f"Error: {response.status_code}, {response.json()}"


# Route to handle PDF upload and summarize its content
@app.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    if 'pdf' not in request.files:
        return render_template('upload.html', generated_text="No PDF uploaded.")

    pdf_file = request.files['pdf']
    extracted_text = extract_text_from_pdf(pdf_file)

    # Chunk the extracted text
    text_chunks = chunk_text(extracted_text)

    # Summarize each chunk
    summarized_texts = [summarize_chunk(chunk) for chunk in text_chunks]
    summarized_text = ' '.join(summarized_texts)

    # Convert Markdown to HTML
    html_output = markdown.markdown(summarized_text)  # Convert the summarized text to HTML

    return render_template('upload.html', generated_text=html_output)


if __name__ == '__main__':
    app.run(debug=True)
