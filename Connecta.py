###### CLASS FOR INTERNET CONNECTION MANAGEMENT ######
# import json
# from re import search
# from string import printable
import time
#import numpy as np
import requests
from Learn import Fuzz 
import Tools_Lib as ts
#from selenium import webdriver
#from selenium.webdriver.chrome.options import Options
#from bs4 import BeautifulSoup
# from googlesearch import search
#import transformers
#import torch
#import torch.nn.functional as F
#from transformers import pipeline

class Connect:
    def __init__(self, session, PROVIDER: str, context_filter, TRIGGER_KEYWORDS: list = None, PROTOTYPE_SENTENCES: list = None, APPEND_WEB: bool = True):
        self.session = session
        self.provider = "google" # PROVIDER
        self.URL = ""
        self.api_keys = ["AIzaSyCa9hVGO7TM6H1GbPq-RYC0-GhzfPhagA8","cefd903bebd8800bf2058aa909a15aff73e5a8b1c81616f1f1507100e972a0d3"]
        self.cse_id = "f61ddf946a3564aee"
        # Constants
        self.trigger_words = TRIGGER_KEYWORDS           # for onlince search activation
 
        # Flags
        self.appendWeb = APPEND_WEB                     # append web resuklt to context?

        # Other Objects
        self.transformer = Fuzz()        
        self.context_filter = context_filter

##### INTERNET COMMUNICATION #####
    # TALK TO WEB
    def talk_to_web(self, user_input: str, tmp_input: str, context: list, role_idx: int, web_threshold: float, context_buffer: int, context_threshold:float)->str:
        
        # check if online web search should activate
        fuzzy_threshold = web_threshold # self.calculate_confidence()

        # web search
        if self.provider and self.online_activation(user_input, fuzzy_threshold):
            try: 
                web_search = self.combined_search(user_input)
                print("web search: " + web_search)
                tmp = ""
                if role_idx > 0:
                    tmp = "USER: "
                tmp_search = tmp + "Web search data: " + web_search
                tmp_input += "\n" + tmp_search + "\n" # user input with web search results in string format for the Json Prompt. #buffer_context_transformer: int, context_threshold: float)->list:
                if self.appendWeb:
                    context.append(tmp + self.context_filter.transformer_context_filter(query = web_search, context= context,buffer_context_transformer=context_buffer,context_threshold = context_threshold)) ### <--- here filter with transformer
                return tmp_input
            except Exception as e:
                print("fail")
                return f"SYSTEM: Search error: {e}"
        else:
            return tmp_input      
    
    # PROVIDER SELECTOR
    def combined_search(self, query: str)->str: #, google_api_key=None, google_cse_id=None, bing_api_key=None):
        try:
            if self.provider == "duckduckgo":
                print(type(query))
                return self.search_duckduckgo(query)           
            elif self.provider == "google":
                if not self.api_keys[0] or not self.cse_id:
                     raise ValueError("Google API key and CSE ID must be provided for Google Custom Search")
                duck_duck = self.search_duckduckgo(query) 
                if duck_duck:
                    return duck_duck
                else: return self.search_google(query, self.api_keys[0], self.cse_id)
            elif self.provider == "serpapi":
                if not self.api_keys[1]:
                    raise ValueError("Serpapi API key must be provided for Serpapi Web Search")
                return self.search_serpapi(query, self.api_keys[1])
            elif self.provider == "None":
                # words = query.split() # Splits on whitespace
                # filtered_words = [word for word in words if word.startswith("http")]
                # if filtered_words:
                #    url = filtered_words[0]
                # else: url = "https://www.google.com/search", https://meta.stackoverflow.com/search?q=, "http://api.duckduckgo.com/?q=x&format=json"  # https://sci-hub.arizonastockbroker.com/#DOI
                #return self.search_advanced(query, found_word)
                # print(search("Google", num_results = 5))
                print("cavallo")
                print(self.search_advanced(query, self.URL))
                
    # Split the string by whitespa()
            else:
                return ""

        except Exception as e:
            # Instead of raising the exception, you can choose to return the error message
            return f"SYSTEM: Combined search error: {e}"

##### SERACH ENGINES #####       
    # DUCKDUCK-GO
    def search_duckduckgo(self, query: str) -> str:
        if not isinstance(query, str):
            raise ValueError("Query must be a string")
        try:
            print(query)
            url = "https://api.duckduckgo.com/"     ## 
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1
            }
            while True:
                response = self.session.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    break
                elif response.status_code == 202:
                    print("Processing... waiting for result.")
                    time.sleep(2)
                else:
                    response.raise_for_status()

            # Try to extract a useful snippet from the AbstractText; if not, join texts from RelatedTopics
            snippet = data.get("AbstractText", "")
            if not snippet:
                topics = data.get("RelatedTopics", [])
                snippet = " ".join(topic.get("Text", "") for topic in topics if topic.get("Text"))
            # print("Snippet:", snippet)  # Debug print to check the value of snippet
            return snippet
        except Exception as e:
            print("ERROR")
            return Exception(f"SYSTEM: Error searching DuckDuckGo: {e}")  

    # GOOGLE
    def search_google(self, query: str, api_key: str, cse_id: str)->str:
        #Define the endpoint URL
        url = "https://www.googleapis.com/customsearch/v1"    
        # Set up the query parameters according to Google's documentation
        params = {
            "key": api_key,    # Your API key
            "cx": cse_id,      # Your custom search engine ID
            "q": query         # The search query
        }    
        try:
            #Send the GET request
            response = self.session.get(url, params=params)
            response.raise_for_status()  # Raise an error for non-200 responses   
            # Parse the JSON response
            data = response.json()
            # print("Full response:", json.dumps(data, indent=4)) # For debugging: print the full response in a readable format
            # Extract the snippet from the first search result, if available
            items = data.get("items", [])
            if items:
                snippet = items[0].get("snippet", "No snippet found.")
                return snippet
            else:
                return "No search results found."
        except Exception as e:
            return f"Error: {e}"
    
    # SERPAPI
    def search_serpapi(self, query: str, api_key: str)->str:
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "engine": "google",
            "api_key": self.api_key
        }
        response = self.session.get(url, params=params)
        response.raise_for_status()  # Raise error for bad responses
        return response.json()
    
    # ADVANCED RESEARCH directly on the browsers
    def search_advanced(self, query: str, url)->str:
        headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/87.0.4280.66 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer':  url
        ## 'DNT': '1' # (Do Not Track)
        ## 'Upgrade-Insecure-Requests': '1'  # Instructs the server to redirect to HTTPS if available
        }   
        # params = {
        # "q": query  # Replace with your actual query
    
        try:
            self.session.headers.update(headers)
            response = self.session.get(url, params = params, timeout = 10)
            response.raise_for_status()
            print("Rsp: ")
            print(response.text)
            info = Tools.extract_info_fromHTML(response.text)
        except requests.RequestException as e:
            info = f"Error fetching data: {e}"
        return info

##### LOGIC FOR INTERNET #####
    # DECIDES IF TO ACTIVATE WEB SEARCH: checks in Trigger_keywords_vector and compares the calculated confidence
    def online_activation(self, query: str, fuzzy_threshold: float)->bool:
        if not isinstance(query, str):
            raise ValueError("Query must be a string")
        # Simple List comparison
        key_trigger = 0
        # key_trigger = any(keyword in query.lower() for keyword in self.trigger_words)
        
        # Compute the semantic similarity score.
        web_confidence, time_related_confidence, best_category, confidence = self.transformer.transformer_classify_word(word = query)
        if best_category == "web" or best_category == "time-related":
            key_trigger = 1
        # Compute the fuzzy logic trigger confidence using the similarity score.
        # trigger_confidence =  self.fuzzy.fuzzy_trigger_confidence(similarity_score)

        web_trigger = max(web_confidence,time_related_confidence) >= fuzzy_threshold
         
            #print(confidence)
            #print(conf_trigger)
        confidence = key_trigger or web_trigger
        return confidence


