# Web-based RAG UI

A web-based user interface for the Retrieval-Augmented Generation (RAG) system with ChatGPT, now supporting web pages as knowledge sources.

## Features

- Web interface for querying the RAG system
- Add any webpage URLs as knowledge sources for RAG
- Side-by-side comparison between RAG-enhanced and basic LLM answers
- Uses Flask for the backend API
- Simple and responsive UI with Bootstrap
- RESTful API for programmatic access

## Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Set your OpenAI API key as an environment variable:

```bash
export OPENAI_API_KEY="YOUR_OPENAI_KEY"
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

## API Integration

The RAG system exposes a RESTful API that can be used by other applications:

- `POST /api/setup` - Set up the OpenAI API key
- `POST /api/load-url` - Load URLs as knowledge sources
- `POST /api/ask` - Ask questions to the RAG system

### Interactive Client

An interactive command-line client is available to interact with the API (either for the hosted render website or local server):

1. Run the client:

```bash (for hosted website)
python client_test.py --server "https://"https://ragui.onrender.com"
```

```bash (for local server)
python client_test.py
```

2. Available commands:
   - `setup YOUR_API_KEY` - Set your OpenAI API key
   - `load URL1 URL2` - Load URLs into the RAG system
   - `ask YOUR QUESTION` - Ask a question
   - `urls` - Show currently loaded URLs
   - `help` - Show available commands
   - `exit` or `quit` - Exit the program

Example session:

```
RAG> setup sk-yourapikey123
RAG> load https://en.wikipedia.org/wiki/Retrieval-augmented_generation
RAG> ask What is RAG?
RAG> load https://en.wikipedia.org/wiki/Large_language_model
RAG> ask How do RAG and LLMs work together?
```

## Project Structure

- `app.py` - Flask application with API endpoints
- `client_test.py` - Interactive API client
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
