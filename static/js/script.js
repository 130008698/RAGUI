document.addEventListener('DOMContentLoaded', function() {
    // API Key elements
    const apiKeyInput = document.getElementById('api-key-input');
    const setupApiBtn = document.getElementById('setup-api-btn');
    const apiKeyStatus = document.getElementById('api-key-status');
    const apiKeyCard = document.querySelector('.card:nth-child(1)'); // First card (API key)
    
    // Question asking elements
    const questionInput = document.getElementById('question-input');
    const submitBtn = document.getElementById('submit-btn');
    const ragAnswer = document.getElementById('rag-answer');
    const basicAnswer = document.getElementById('basic-answer');
    const loading = document.getElementById('loading');
    
    // URL handling elements
    const urlInput = document.getElementById('url-input');
    const addUrlBtn = document.getElementById('add-url-btn');
    const loadUrlsBtn = document.getElementById('load-urls-btn');
    const urlList = document.getElementById('url-list');
    const loadingUrls = document.getElementById('loading-urls');
    const loadedUrlsContainer = document.getElementById('loaded-urls-container');
    const loadedUrlsList = document.getElementById('loaded-urls-list');
    
    // API key setup state
    let apiKeySet = false;
    
    // URLs to be loaded
    let urlsToLoad = [];
    
    // Check if API key is already set on the server
    checkServerApiKey();
    
    // Set up API key
    setupApiBtn.addEventListener('click', setupApiKey);
    apiKeyInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            setupApiKey();
        }
    });
    
    // Disable URL and question inputs initially
    disableInteraction();
    
    // Function to check if API key is already set on the server
    function checkServerApiKey() {
        fetch('/api/setup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ api_key: "" }), // Send empty key to check if server has one
        })
        .then(response => response.json())
        .then(data => {
            if (data.message && data.message === "API key set successfully") {
                // Server already has API key set, hide API key input
                apiKeyStatus.innerHTML = '<div class="alert alert-success mb-0">API key already configured on server!</div>';
                apiKeySet = true;
                enableInteraction();
                
                // Optionally hide the API key card completely
                // apiKeyCard.style.display = 'none';
            }
        })
        .catch(error => {
            console.log('Server API key not set:', error);
            // We'll use the manual input form
        });
    }
    
    
    // Add URL to the list
    addUrlBtn.addEventListener('click', addUrlToList);
    urlInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            addUrlToList();
        }
    });
    
    // Load URLs
    loadUrlsBtn.addEventListener('click', loadUrls);
    
    // Submit question on button click
    submitBtn.addEventListener('click', askQuestion);
    
    // Submit question on Enter key press
    questionInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            askQuestion();
        }
    });
    
    // Add URL to the list function
    function addUrlToList() {
        const url = urlInput.value.trim();
        
        if (!url) {
            alert('Please enter a URL');
            return;
        }
        
        // Validate URL
        try {
            new URL(url);
        } catch (e) {
            alert('Please enter a valid URL (include http:// or https://)');
            return;
        }
        
        // Add to array if not already present
        if (!urlsToLoad.includes(url)) {
            urlsToLoad.push(url);
            
            // Add to UI
            const urlItem = document.createElement('div');
            urlItem.className = 'alert alert-info d-flex justify-content-between align-items-center mb-2';
            
            const urlText = document.createElement('span');
            urlText.textContent = url;
            
            const removeBtn = document.createElement('button');
            removeBtn.className = 'btn btn-sm btn-danger';
            removeBtn.innerHTML = '&times;';
            removeBtn.addEventListener('click', function() {
                // Remove from array
                urlsToLoad = urlsToLoad.filter(u => u !== url);
                // Remove from UI
                urlList.removeChild(urlItem);
            });
            
            urlItem.appendChild(urlText);
            urlItem.appendChild(removeBtn);
            urlList.appendChild(urlItem);
            
            // Clear input
            urlInput.value = '';
        } else {
            alert('URL already in the list');
        }
    }
    
    // Load URLs function
    function loadUrls() {
        if (urlsToLoad.length === 0) {
            alert('Please add at least one URL');
            return;
        }
        
        if (!apiKeySet) {
            alert('Please set up your OpenAI API key first');
            return;
        }
        
        // Show loading indicator
        loadingUrls.classList.remove('d-none');
        loadUrlsBtn.disabled = true;
        addUrlBtn.disabled = true;
        urlInput.disabled = true;
        
        // Send API request to load URLs
        fetch('/api/load-url', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ urls: urlsToLoad }),
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.error || 'Failed to load URLs');
                });
            }
            return response.json();
        })
        .then(data => {
            // Display loaded URLs
            loadedUrlsContainer.classList.remove('d-none');
            loadedUrlsList.innerHTML = '';
            
            data.loaded_urls.forEach(url => {
                const li = document.createElement('li');
                li.className = 'list-group-item';
                li.textContent = url;
                loadedUrlsList.appendChild(li);
            });
            
            // Clear URL list since they're now loaded
            urlList.innerHTML = '';
            urlsToLoad = [];
            
            alert(`Successfully loaded ${data.loaded_urls.length} URLs for RAG processing!`);
        })
        .catch(error => {
            console.error('Error:', error);
            alert(`Error: ${error.message}`);
        })
        .finally(() => {
            // Hide loading indicator
            loadingUrls.classList.add('d-none');
            loadUrlsBtn.disabled = false;
            addUrlBtn.disabled = false;
            urlInput.disabled = false;
        });
    }

    // Function to disable interaction with the app until API key is set
    function disableInteraction() {
        questionInput.disabled = true;
        submitBtn.disabled = true;
        urlInput.disabled = true;
        addUrlBtn.disabled = true;
        loadUrlsBtn.disabled = true;
    }
    
    // Function to enable interaction with the app
    function enableInteraction() {
        questionInput.disabled = false;
        submitBtn.disabled = false;
        urlInput.disabled = false;
        addUrlBtn.disabled = false;
        loadUrlsBtn.disabled = false;
    }
    
    // Setup API key function
    function setupApiKey() {
        const apiKey = apiKeyInput.value.trim();
        
        if (!apiKey) {
            alert('Please enter an OpenAI API key');
            return;
        }
        
        if (!apiKey.startsWith('sk-')) {
            alert('This doesn\'t look like a valid OpenAI API key. It should start with "sk-"');
            return;
        }
        
        // Show loading status
        apiKeyStatus.innerHTML = '<div class="spinner-border spinner-border-sm text-primary" role="status"><span class="visually-hidden">Loading...</span></div> Setting up API key...';
        setupApiBtn.disabled = true;
        
        // Send API request to setup the API key
        fetch('/api/setup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ api_key: apiKey }),
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.error || 'Failed to set API key');
                });
            }
            return response.json();
        })
        .then(data => {
            // Update status and enable interaction
            apiKeyStatus.innerHTML = '<div class="alert alert-success mb-0">API key set successfully!</div>';
            apiKeySet = true;
            enableInteraction();
        })
        .catch(error => {
            console.error('Error:', error);
            apiKeyStatus.innerHTML = `<div class="alert alert-danger mb-0">Error: ${error.message}</div>`;
            setupApiBtn.disabled = false;
        });
    }

    function askQuestion() {
        const question = questionInput.value.trim();
        
        if (!question) {
            alert('Please enter a question');
            return;
        }
        
        if (!apiKeySet) {
            alert('Please set up your OpenAI API key first');
            return;
        }
        
        // Show loading indicator
        loading.classList.remove('d-none');
        submitBtn.disabled = true;
        
        // Clear previous answers
        ragAnswer.innerHTML = 'Loading...';
        basicAnswer.innerHTML = 'Loading...';
        
        // Send API request
        fetch('/api/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: question }),
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.error || 'Failed to get answer');
                });
            }
            return response.json();
        })
        .then(data => {
            // Display answers with formatting (convert newlines to <br>)
            ragAnswer.innerHTML = data.rag_answer.replace(/\n/g, '<br>');
            basicAnswer.innerHTML = data.basic_answer.replace(/\n/g, '<br>');
            
            // Update the loaded URLs display if available
            if (data.loaded_urls && data.loaded_urls.length > 0) {
                loadedUrlsContainer.classList.remove('d-none');
                loadedUrlsList.innerHTML = '';
                
                data.loaded_urls.forEach(url => {
                    const li = document.createElement('li');
                    li.className = 'list-group-item';
                    li.textContent = url;
                    loadedUrlsList.appendChild(li);
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            ragAnswer.textContent = `Error: ${error.message}`;
            basicAnswer.textContent = `Error: ${error.message}`;
        })
        .finally(() => {
            // Hide loading indicator
            loading.classList.add('d-none');
            submitBtn.disabled = false;
        });
    }
});