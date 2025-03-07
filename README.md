# Web-based RAG UI

A web-based user interface for the Retrieval-Augmented Generation (RAG) system with ChatGPT, now supporting web pages as knowledge sources.

## Features

- Web interface for querying the RAG system
- Add any webpage URLs as knowledge sources for RAG
- Side-by-side comparison between RAG-enhanced and basic LLM answers
- Uses Flask for the backend API
- Simple and responsive UI with Bootstrap

## Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Set your OpenAI API key as an environment variable:

```bash
export OPENAI_API_KEY=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
```

3. Run the Flask application:

```bash
python app.py
```

4. Open your browser and navigate to http://127.0.0.1:5000

## Usage

1. Add webpage URLs:

   - Enter URLs in the "Add Web Content" section
   - Click "Add URL" to add them to the list
   - Click "Load URLs" to process the content for RAG

2. Ask questions:
   - Enter your question in the input field
   - Click "Ask" or press Enter
   - View the answers from both the RAG-enhanced model and the basic LLM
   - Compare the quality and relevance of the answers

## Project Structure

- `app.py` - Flask application with API endpoints
- `templates/index.html` - Main HTML template
- `static/css/style.css` - Custom CSS styles
- `static/js/script.js` - Client-side JavaScript
- `RAG with ChatGPT implementation/` - RAG implementation files
  - `ragpdfwithchatgpt.py` - Core RAG logic (now supporting webpages)

## How It Works

1. Web pages are fetched using BeautifulSoup and processed into text chunks
2. Text chunks are embedded using OpenAI embeddings and stored in a Chroma vector store
3. When a question is asked, the RAG system:
   - Retrieves the most relevant text chunks using semantic search
   - Passes these chunks along with the question to ChatGPT
   - Returns an enhanced answer informed by the webpage content
4. For comparison, the basic LLM simply processes the question without any additional context
