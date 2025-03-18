import requests
import argparse
import os
import json
import cmd

def setup_api_key(url, api_key):
    """Set up API key for the RAG application"""
    response = requests.post(
        f"{url}/api/setup",
        json={"api_key": api_key}
    )
    return response.json()

def load_urls(url, urls):
    """Load URLs into the RAG application"""
    response = requests.post(
        f"{url}/api/load-url",
        json={"urls": urls}
    )
    return response.json()

def ask_question(url, question):
    """Ask a question to the RAG application"""
    response = requests.post(
        f"{url}/api/ask",
        json={"question": question}
    )
    return response.json()

class RagShell(cmd.Cmd):
    intro = 'Welcome to the RAG client shell. Type help or ? to list commands.\n'
    prompt = 'RAG> '
    
    def __init__(self, server_url, api_key=None):
        super().__init__()
        self.server_url = server_url
        self.api_key = api_key
        self.loaded_urls = []
        
        if api_key:
            self.do_setup(api_key)
    
    def do_setup(self, arg):
        """Set up the API key: setup YOUR_API_KEY"""
        api_key = arg.strip() or self.api_key
        if not api_key:
            print("Error: API key is required")
            return
        
        print("Setting up API key...")
        result = setup_api_key(self.server_url, api_key)
        print(json.dumps(result, indent=2))
        self.api_key = api_key
    
    def do_load(self, arg):
        """Load URLs into the RAG system: load URL1 URL2..."""
        urls = arg.split()
        if not urls:
            print("Error: Please provide at least one URL")
            return
        
        print(f"Loading URLs: {urls}")
        result = load_urls(self.server_url, urls)
        print(json.dumps(result, indent=2))
        
        if result.get("success"):
            self.loaded_urls = result.get("loaded_urls", [])
    
    def do_ask(self, arg):
        """Ask a question: ask YOUR QUESTION HERE"""
        if not arg:
            print("Error: Please provide a question")
            return
        
        print(f"Asking: {arg}")
        result = ask_question(self.server_url, arg)
        
        if "error" in result:
            print(f"Error: {result['error']}")
            return
            
        print("\nRAG Answer:")
        print(result.get("rag_answer", "Error: No RAG answer returned"))
        
        print("\nBasic Answer:")
        print(result.get("basic_answer", "Error: No basic answer returned"))
    
    def do_urls(self, arg):
        """Show currently loaded URLs"""
        if not self.loaded_urls:
            print("No URLs currently loaded")
        else:
            print("Currently loaded URLs:")
            for i, url in enumerate(self.loaded_urls):
                print(f"{i+1}. {url}")
    
    def do_exit(self, arg):
        """Exit the program"""
        print("Goodbye!")
        return True
    
    def do_quit(self, arg):
        """Exit the program"""
        return self.do_exit(arg)
    
    def emptyline(self):
        """Do nothing on empty line"""
        pass

def main():
    parser = argparse.ArgumentParser(description="Interactive client for RAG API")
    parser.add_argument("--server", default="http://localhost:5000", help="Server URL")
    parser.add_argument("--api-key", help="OpenAI API Key")
    parser.add_argument("--urls", nargs="+", help="URLs to load into RAG initially")
    parser.add_argument("--question", help="Initial question to ask (optional)")
    
    args = parser.parse_args()
    
    # Get API key from args or environment
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    
    print(f"Connecting to RAG service at {args.server}")
    shell = RagShell(args.server, api_key)
    
    # Load URLs if provided
    if args.urls:
        url_str = " ".join(args.urls)
        shell.do_load(url_str)
    
    # Ask initial question if provided
    if args.question:
        shell.do_ask(args.question)
    
    # Start the interactive shell
    shell.cmdloop()

if __name__ == "__main__":
    main()