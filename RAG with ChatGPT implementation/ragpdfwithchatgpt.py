import os
import pickle  # Import pickle for serialization
import time  # Import time for measuring execution time

import requests
from bs4 import BeautifulSoup
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma  # Updated import
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama
from langchain_openai import OpenAIEmbeddings  # Updated import
from openai import OpenAI

# Initialize client as None - will be set when API key is provided
client = None

# Define paths for serialized data
SPLIT_DOCS_PATH = 'split_documents_web.pkl'  # Path to save split documents
VECTOR_STORE_DIR = 'chroma_vectorstore_web'  # Directory to save Chroma data

# Default URLs (can be changed at runtime)
default_urls = [
    "https://en.wikipedia.org/wiki/Artificial_intelligence"
]

def fetch_webpage_content(url):
    """Fetch and parse webpage content using BeautifulSoup"""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for bad status codes
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract text content (customize this as needed)
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
            
        # Get text
        text = soup.get_text(separator='\n')
        
        # Clean up text (remove extra whitespace)
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def load_and_split_documents_web(urls, split_docs_path):
    """Load and split documents from web URLs"""
    if os.path.exists(split_docs_path):
        print("Loading existing split documents...")
        with open(split_docs_path, 'rb') as f:
            doc_splits = pickle.load(f)
    else:
        print("Loading and splitting documents from web URLs...")
        documents = []
        
        # Method 1: Using WebBaseLoader from langchain
        try:
            loader = WebBaseLoader(urls)
            langchain_docs = loader.load()
            documents.extend(langchain_docs)
        except Exception as e:
            print(f"WebBaseLoader failed: {e}")
            
            # Method 2: Fallback to manual loading with BeautifulSoup
            for url in urls:
                text = fetch_webpage_content(url)
                if text:
                    # Create a Document object with the text and metadata
                    doc = Document(
                        page_content=text,
                        metadata={"source": url}
                    )
                    documents.append(doc)
        
        if not documents:
            print("Failed to load any content from the provided URLs")
            return []
            
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=500, chunk_overlap=50  # Larger chunks for web content
        )
        doc_splits = text_splitter.split_documents(documents)

        # Save split documents to disk
        with open(split_docs_path, 'wb') as f:
            pickle.dump(doc_splits, f)
        print(f"Split documents saved to {split_docs_path}.")
    return doc_splits

# The following will only run when this file is executed directly
# In the Flask app, this will be replaced by explicit calls
if __name__ == "__main__":
    # Load or split and save documents
    doc_splits = load_and_split_documents_web(default_urls, SPLIT_DOCS_PATH)

# Step 2: Create or Load Vector Store with Embeddings using Chroma
def create_or_load_vectorstore(vector_store_dir, doc_splits):
    # If no documents were provided, return None
    if not doc_splits:
        print("No documents to create vector store from.")
        return None
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not set. Please set up your API key first.")
        
    if os.path.exists(vector_store_dir):
        print("Loading existing Chroma vector store...")
        embedding = OpenAIEmbeddings(openai_api_key=api_key)
        vectorstore = Chroma(
            persist_directory=vector_store_dir,
            embedding_function=embedding
        )
    else:
        print("Creating new Chroma vector store...")
        embedding = OpenAIEmbeddings(openai_api_key=api_key)
        vectorstore = Chroma.from_documents(
            documents=doc_splits,
            embedding=embedding,
            persist_directory=vector_store_dir
        )
        # Save the vector store to disk
        print(f"Chroma vector store saved to {vector_store_dir}.")
    return vectorstore

# Create vector store and retriever only when running directly
if __name__ == "__main__":
    vectorstore = create_or_load_vectorstore(VECTOR_STORE_DIR, doc_splits)
    if vectorstore:
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})  # Retrieve top 4 relevant documents

# Step 3: Define Prompt Template for the Language Model
prompt_template = PromptTemplate(
    template="""You are an AI assistant that engages in natural conversation while also answering medical-related questions **strictly based on the provided medical knowledge base**.

Instructions:
- If the user asks a **general** question, respond naturally as a helpful AI assistant.
- If the user asks a **medical-related question** (e.g., symptoms, diagnosis, treatment, medications, conditions), use ONLY the retrieved medical knowledge base to respond.
- If the relevant information is NOT found in the medical knowledge base, respond with: 
  **"I am sorry, I can only provide information from the given medical knowledge base, and I don't have data on that topic. Do you want me to forward this question to your healthcare provider?"**
- Do NOT generate medical information beyond what is retrieved.

NEVER share the source of your response.
Do not include document in your response.

Question: {question}
Documents: {documents}
Answer:
""",
    input_variables=["question", "documents"]
)

prompt_template_og = PromptTemplate(
    template="""You are an assistant for question-answering tasks.

Question: {question}
Answer:
""",
    input_variables=["question"]
)

# Step 4: Define a function to interact with OpenAI's ChatGPT API
def ask_chatgpt(question, documents, model="gpt-4o"):
    global client
    
    # Ensure client is initialized
    if client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not set. Please set up your API key first.")
        client = OpenAI(api_key=api_key)
    
    # Format the prompt with question and documents
    prompt = prompt_template.format(question=question, documents=documents)
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content

# Step 5: Define Application Classes
class RAGApplication:
    def __init__(self, retriever):
        self.retriever = retriever
        self.has_documents = retriever is not None

    def run(self, question):
        if not self.has_documents:
            # If no documents are available, fall back to basic LLM
            return BasicLLMApplication().run(question) + "\n\n[Note: No documents were loaded for RAG enhancement]"
            
        # Retrieve relevant documents using the 'invoke' method
        documents = self.retriever.invoke(question)
        # Extract content from retrieved documents
        doc_texts = "\n".join([doc.page_content for doc in documents])
        # Get the answer from the language model
        answer = ask_chatgpt(question, doc_texts)
        return answer
    
    def update_retriever(self, new_retriever):
        """Update the retriever with a new one (after loading new docs)"""
        self.retriever = new_retriever
        self.has_documents = new_retriever is not None
        return self.has_documents

# Original LLM pipeline (without RAG) for comparison
class BasicLLMApplication:
    def __init__(self, model="gpt-4o"):
        self.model = model

    def run(self, question):
        global client
        
        # Ensure client is initialized
        if client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not set. Please set up your API key first.")
            client = OpenAI(api_key=api_key)
            
        prompt = prompt_template_og.format(question=question)
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return response.choices[0].message.content

# Step 6: Test the Application with Interactive Loop
if __name__ == "__main__":
    try:
        # Initialize the RAG application
        rag_application = RAGApplication(retriever)
        
        # Initialize the original LLM without RAG
        basic_llm_application = BasicLLMApplication()
        
        # Welcome message and instructions
        print("Welcome to the RAG Question-Answering System!")
        print("Type your questions below. To exit, type 'exit' or 'quit'.\n")
        
        while True:
            # Prompt user for input
            question = input("Your question: ")
            
            # Handle exit commands
            if question.lower() in ['exit', 'quit']:
                print("Exiting the application. Goodbye!")
                break
            elif question.strip() == "":
                print("Please enter a valid question.\n")
                continue
            
            # Measure Basic LLM response time
            start_basic = time.perf_counter()
            basic_answer = basic_llm_application.run(question)
            end_basic = time.perf_counter()
            basic_time = end_basic - start_basic
            # Measure RAG response time
            start_rag = time.perf_counter()
            rag_answer = rag_application.run(question)
            end_rag = time.perf_counter()
            rag_time = end_rag - start_rag
            

            
            # Display the answers with elapsed times
            print("\nAnswer with RAG:")
            print(rag_answer)
            print(f"Time taken: {rag_time:.2f} seconds\n")
            
            print("Original Model Answer:")
            print(basic_answer)
            print(f"Time taken: {basic_time:.2f} seconds\n")
    
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\nInterrupted by user. Exiting the application. Goodbye!")
    except Exception as e:
        print(f"An error occurred during execution: {e}")
