import os
from flask import Flask, request, jsonify, render_template
import sys
import time
import subprocess
sys.path.append('RAG with ChatGPT implementation')
import openai

# Import but don't initialize yet
from ragpdfwithchatgpt import (
    RAGApplication, BasicLLMApplication, create_or_load_vectorstore, 
    load_and_split_documents_web, VECTOR_STORE_DIR, SPLIT_DOCS_PATH, default_urls
)

app = Flask(__name__)

# Set to None initially - will be initialized when API key is provided
rag_application = None
basic_llm_application = None

# Track loaded URLs
loaded_urls = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/setup', methods=['POST'])
def setup():
    global rag_application, basic_llm_application
    data = request.json
    api_key = data.get('api_key', '')
    
    if not api_key:
        return jsonify({"error": "No API key provided"}), 400
    
    try:
        # Set the API key
        os.environ["OPENAI_API_KEY"] = api_key
        openai.api_key = api_key
        
        # Now initialize the applications
        from ragpdfwithchatgpt import RAGApplication, BasicLLMApplication
        rag_application = RAGApplication(None)
        basic_llm_application = BasicLLMApplication()
        
        return jsonify({"message": "API key set successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ask', methods=['POST'])
def ask():
    global rag_application, basic_llm_application
    data = request.json
    question = data.get('question', '')
    
    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    if not rag_application or not basic_llm_application:
        return jsonify({"error": "Please set up your API key first"}), 400
    
    try:
        # Get answers from both approaches
        rag_answer = rag_application.run(question)
        basic_answer = basic_llm_application.run(question)
        
        return jsonify({
            "rag_answer": rag_answer,
            "basic_answer": basic_answer,
            "loaded_urls": loaded_urls
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/load-url', methods=['POST'])
def load_url():
    global rag_application, loaded_urls
    data = request.json
    urls = data.get('urls', [])
    
    if not urls:
        return jsonify({"error": "No URLs provided"}), 400
        
    if not rag_application:
        return jsonify({"error": "Please set up your API key first"}), 400
    
    try:
        # Create a timestamp-based split docs path to avoid conflicts
        timestamp = int(time.time())
        split_docs_path = f'split_documents_web_{timestamp}.pkl'
        vector_store_dir = f'chroma_vectorstore_web_{timestamp}'
        
        # Load and process the URLs
        doc_splits = load_and_split_documents_web(urls, split_docs_path)
        
        if not doc_splits:
            return jsonify({"error": "Failed to load content from the provided URLs"}), 400
            
        vectorstore = create_or_load_vectorstore(vector_store_dir, doc_splits)
        
        if not vectorstore:
            return jsonify({"error": "Failed to create vector store from documents"}), 500
            
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
        
        # Update the existing RAG application with the new retriever
        success = rag_application.update_retriever(retriever)
        
        # Update loaded URLs
        loaded_urls = urls
        
        return jsonify({
            "success": success,
            "message": f"Successfully loaded {len(doc_splits)} document chunks from {len(urls)} URLs",
            "loaded_urls": loaded_urls
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)