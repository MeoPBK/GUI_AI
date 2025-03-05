###### CLASS FOR INTERNET CONNECTION MANAGEMENT ######
import json
import transformers
import torch
import torch.nn.functional as F
from transformers import pipeline

##### INI JSON #####
with open("ini_data.json", "r", encoding="utf-8") as f:
    INI = json.load(f)

class OConnect:
    def __init__(self, session, PROVIDER, APPEND_WEB = True, TRIGGER_KEYWORDS = INI["TRIGGER_KEYWORDS"]):
        self.session = session
         
        # Constants
        self.trigger_words = TRIGGER_KEYWORDS           # for onlince search activation
 
        # Flags
        self.appendWeb = APPEND_WEB                     # append web resuklt to context?
        
        self.provider = PROVIDER
        self.URL = ""

##### INTERNET COMMUNICATION #####
    # TALK TO WEB
    def talk_to_web(self, user_input: str, tmp_input: str)->str:
        
        # check if onmline should activate
        confidence = 1 # self.calculate_confidence()
        # web search
        if self.provider and self.online_activation(user_input, confidence):
            print("gambero")
            try: 
                web_search = self.combined_search(user_input)
                print(web_search)
                tmp_input += "\n " + web_search + "\n "
                #print(tmp_input)
                if self.appendWeb:
                    print("if")
                   #context.append(web_search)
            except Exception as e:
                print("fail")
                return f"SYSTEM: Search error: {e}"
        else:
            return user_input      
    
    # PROVIDER SELECTOR
    def combined_search(self, query: str)->str: #, google_api_key=None, google_cse_id=None, bing_api_key=None):
        try:
            if self.provider == "duckduckgo":
                print(type(query))
                return self.search_duckduckgo(query)
                 
            elif self.provider == "google":
                if not google_api_key or not google_cse_id:
                     raise ValueError("Google API key and CSE ID must be provided for Google Custom Search")
                return self.search_google(query, google_api_key, google_cse_id)
            elif self.provider == "bing":
                if not bing_api_key:
                    raise ValueError("Bing API key must be provided for Bing Web Search")
                return self.search_bing(query, bing_api_key)
            else:
                return ""

        except Exception as e:
            # Instead of raising the exception, you can choose to return the error message
            return f"SYSTEM: Combined search error: {e}"

##### SERACH ENGINES #####       
    # DUCKDUCK-GO
    def search_duckduckgo(self, query: str) -> str:
        print(query)
        data = None
        if not isinstance(query, str):
            raise ValueError("Query must be a string")
        try:
            print(query)
            url = "http://api.duckduckgo.com/?q=x&format=json"  #"https://api.duckduckgo.com/"     ##
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1
            }
            while True:
                response = self.session.get(url, params=params)
                print(response.status_code)
                if response.status_code == 200:
                    #print("done")
                    data = response.json()
                    print("Response data:" + json.dumps(data, indent=4))  # Debug print to check the structure of the response
                    break
                elif response.status_code == 202:
                    print("Processing... waiting for result.")
                    time.sleep(2)
                else:
                    response.raise_for_status()

            print("Response body:" + response.text)
            print(data["RelatedTopics"])
            # Try to extract a useful snippet from the AbstractText; if not, join texts from RelatedTopics
            snippet = data.get("AbstractText", "")
            if not snippet:
                topics = data.get("RelatedTopics", [])
                snippet = " ".join(topic.get("Text", "") for topic in topics if topic.get("Text"))
            print("Snippet:", snippet)  # Debug print to check the value of snippet
            return snippet
        except Exception as e:
            print("ERROR")
            return Exception(f"SYSTEM: Error searching DuckDuckGo: {e}")  
    
    # GOOGLE
    def search_google(self, query: str, api_key: str, cse_id: str)->str:
    # Define the endpoint URL
        url = "https://www.googleapis.com/customsearch/v1"    
        # Set up the query parameters according to Google's documentation
        params = {
            "key": api_key,    # Your API key
            "cx": cse_id,      # Your custom search engine ID
            "q": query         # The search query
        }    
        try:
            # Send the GET request
            response = self.session.get(url, params=params)
            response.raise_for_status()  # Raise an error for non-200 responses   
            # Parse the JSON response
            data = response.json()
            # For debugging: print the full response in a readable format
            print("Full response:", json.dumps(data, indent=4))
        
            # Extract the snippet from the first search result, if available
            items = data.get("items", [])
            if items:
                snippet = items[0].get("snippet", "No snippet found.")
                return snippet
            else:
                return "No search results found."
        except Exception as e:
            return f"Error: {e}"
    
    # BING
    def search_bing(self, query: str, api_key: str)->str:
        api_key
        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {"Ocp-Apim-Subscription-Key": api_key}
        params = {"q": query, "textDecorations": True, "textFormat": "HTML"}
    
        try:
            response = self.session.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            # Uncomment the next line for debugging:
            # print(json.dumps(data, indent=4))
            items = data.get("webPages", {}).get("value", [])
            return items[0].get("snippet", "No snippet found.") if items else "No search results found."
        except Exception as e:
            return f"Error: {e}"
    
    # MULTI
    def serpapi_search(self, query: str, api_key: str)->str:
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "engine": "google",
            "api_key": api_key
        }
        response = self.session.get(url, params=params)
        response.raise_for_status()  # Raise error for bad responses
        return response.json()

##### LOGIC FOR INTERNET #####
    # DECIDES IF TO ACTIVATE WEB SEARCH: checks in Trigger_keywords_vector and compares the calculated confidence
    def online_activation(self, query: str, confidence=1)->bool:
        if not isinstance(query, str):
            raise ValueError("Query must be a string")
        key_trigger = any(keyword in query.lower() for keyword in self.trigger_words)
        if confidence: 
            conf_trigger = confidence <0.7
            #print(confidence)
            #print(conf_trigger)
        return key_trigger or conf_trigger
    
    # machine learning algorithm (softmax or log-barrier) for calculating confidence of the model towards a word
    def calculate_confidence(self, user_input: str)->float:
        # Load the pre-trained tokenizer and model
        tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
        model = GPT2LMHeadModel.from_pretrained("gpt2")

        vocab = tokenizer.get_vocab()  # returns a dict {token: index}
        sorted_vocab = sorted(vocab.items(), key=lambda x: x[1])
        for token, index in sorted_vocab[:10]:  # print first 10 tokens
            print(index, token)
        model.eval()  # Set the model to evaluation mode
        input_ids = tokenizer.encode(user_input,return_tensor="pt")
        # Alternative: You could also use tokenizer(text, return_tensors="pt") for more flexibility.

        with torch.no_grad():
            outputs = model(input_ids)
        # Pass the input through the model to get outputs
        with torch.no_grad():
            outputs = model(input_ids)
        # Extract logits from the outputs (shape: [batch_size, sequence_length, vocab_size])
        logits = outputs.logits
        print(logits)
        # For example, if you want the logits for the next token prediction:
        # Get the logits for the last token in the sequence
        last_token_logits = logits[0, -1, :]
        # Convert logits to probabilities using softmax
        probs = F.softmax(last_token_logits, dim=0)
        # Get the maximum probability (i.e., the confidence for the chosen token)
        return probs.max().item()





