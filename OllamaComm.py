# -*- coding: utf-8 -*-
"""
@author: meoai and iacop
"""
import requests 
import re

HEADERS = {"Content-Type": "application/json"}
MAX_CONTEXT_LEN = 50;
PROVIDER = None # "duckduckgo"
ROLES_ATTRIBUTE = [
    ["","",""],
    ["","",""],
    ["You are an helpful assistant and you'll answer my questions.","",""],
    ["You are a precise scientist and engineer.", "You always double check your soruces and you quote them.","You base your research on scientific papers and highly reliable data."],
    ["You are a software engineer and you'll help me with my code.", "",""], 
    ["You are a software engineer and you'll help me with my code.", "You work in a very readable way.",""],
    ["You are a gourmet chef, you'll help me with recipes explain step by step.", "",""],
    ["You are a story teller.","",""]
    ]

OllamaData = {
        "model":  "deepseek-r1:7b", #Specifica il modello LLM che desideri utilizzare
        "prompt": "Prova" ,         #Il testo di input o la domanda che desideri inviare al LLM
        "temperature": 0.7,         #Controlla la casualità dell'output. Valori più alti (es. 1.0) rendono l'output più casuale e creativo, mentre valori più bassi (es. 0.2) lo rendono più deterministico e focalizzato
        "max_tokens": 8192,         #Specifica il numero massimo di token (parole o parti di parole) nella risposta generata
        "top_p": 1.0,               #Come compilarlo: Scegli un valore compreso tra 0.0 e 1.0. Un valore di 1.0 considera tutti i token, mentre valori più bassi considerano solo i token con probabilità più alta
        "frequency_penalty": 0.0,   #Come compilarlo: Scegli un valore compreso tra -2.0 e 2.0. Valori positivi riducono la ripetizione
        "presence_penalty": 0.0,    #Come compilarlo: Scegli un valore compreso tra -2.0 e 2.0. Valori positivi incoraggiano la diversità
        "stop": ["\n\n", "###"],    #Come compilarlo: Inserisci un array di stringhe che rappresentano le sequenze di stop. Ad esempio, ["\n\n", "###"] potrebbe indicare che il modello dovrebbe smettere di generare output quando incontra due newline o la sequenza "###"
        "stream": False             #come compilarlo: imposta a true se vuoi ricevere la risposta in parti, oppure a false se vuoi riceverla tutta in una volta
}

class OllamaPOST:
        def __init__(self):
            self.session = requests.Session()  # Persistent session for efficiency
            self.context = []
            self.role_flag = 0
            self.answer = ""
            self.address = ""
            self.model = ""
            self.role = []
            self.max_context_length = MAX_CONTEXT_LEN   # max length of context buffer
            self.role_buffer = len(ROLES_ATTRIBUTE[5])     # length role buffer

        # Rimuove il contenuto tra i tag <think> e </think> dalla risposta.
        def clean_response(self, response): 
            # Usa una regex per trovare e rimuovere tutto ciò che è tra <think> e </think>
            cleaned_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
            return cleaned_response.strip()  # Rimuove spazi bianchi extra

        # assistant context manager (called in manage_context())
        def assistant_manager(self, assist_input, role_idx):
            clean_input = assist_input.replace("\n","")
            if role_idx == 0:
                self.context.append(clean_input)
            else:
                self.context.append("ASSISTANT: " + clean_input)
            self.answer = assist_input
       
        # role manager for context (called in manage_context())
        def role_manager(self,user_input, role_idx):
            # CASE 1: if role = "one of the selection" (but not "None" nor "User Defined")
                    if role_idx !=0 and role_idx !=1:                       
                        if self.role_flag == 0:         # if the role description-mode is still active
                            self.context.append("USER: " + user_input) 
                        else:
                            for role in ROLES_ATTRIBUTE[role_idx]:
                                if role:           
                                    self.context.append("SYSTEM: " + role)
                                    self.role.append("SYSTEM: " + role)
                                else: break
                            self.role_flag = 0

                    # CASE 2: if role == "User Defined"
                    elif role_idx ==1:                                      
                        tmp = ["system","user"]     
                        size = len(user_input)
                        N = len(tmp[0]) +1                   # can be more clean
                        N2 = len(tmp[1]) +1
                        if size<=N-1: 
                            N = 1
                            N2 = 1
                            tmp = ["sy","us"] 

                        if tmp[0] in user_input[:N].lower():
                            new_input = user_input[N:]
                            self.context.append("SYSTEM: " + new_input)
                            self.role.append("SYSTEM: " + new_input)
                        elif tmp[1] in user_input[:N2].lower():
                            new_input = user_input[N2:]
                            self.context.append("USER: " + new_input )
                        else: self.context.append("USER: " + new_input) 

                    # CASE 3: if role == "None"
                    else:                               
                        self.context.append(user_input) 
                
        # function to manage the context length and the roles assignation with "USER, SYSTEM, ASSISTANT"
        def manage_context(self,user_input, role_idx = 0, assist_input = None):
            ## CONTEXT ON ##
            if self.max_context_length != 0: 
                # if assistant is talking
                if assist_input:    
                    self.assistant_manager(assist_input,role_idx)
                # if user or sys are talking
                else:           
                    self.role_manager(user_input, role_idx)
                # manages the buffer for the context
                if len(self.context) > self.max_context_length:
                    self.context = self.context[-self.max_context_length:]
                    self.context[-self.role_buffer:] = self.role[:self.role_buffer]
                    # print("End BUffer reached")            
            ## CONTEXT OFF ## -> just returns itself
            else:
                self.context = [user_input]  
            return "\n".join(self.context)

        # manages ollama communication
        def talk_to_ollama(self, user_input, role_idx = 0):          
            OllamaData["model"]  = self.model
            new_input = ""

            # changes input format based on role on/off and what role:
            tmp_input = self.manage_context(user_input,role_idx)
            
            # web search
            web_search = self.talk_to_web(user_input,PROVIDER)
            print(web_search)
            if web_search:
                new_input = "\n ".join(web_search)
                print(new_input)
                self.context.append(web_search)
            else:
                new_input = tmp_input

            OllamaData["prompt"] = new_input    # assign prompt message
            #print(new_input)
            try:
            # Make the POST request
            #response = self.session.post(api_key, headers=HEADERS, json=data, timeout=10)
                response = self.session.post(self.address+"/api/generate", headers=HEADERS, json=OllamaData)
                response.raise_for_status()
                response_data = response.json()
                model_output = response_data.get('response', 'No response received.')
                cleaned_output_tmp = self.clean_response(model_output)
                self.manage_context(user_input, role_idx, cleaned_output_tmp)
                cleaned_output = self.answer
                return cleaned_output
               
            except requests.exceptions.RequestException as e:
                return f"API Error: {e}"

        def get_ollama_models(self, api_key="http://localhost:11434"):
            try:
                response = self.session.get(api_key+"/api/tags")
                models_data = response.json()
                # Extract model names from the response
                models = [model['name'] for model in models_data['models']]
                return models
            except requests.exceptions.RequestException as e:
                return []

    ### INTERNET COMMUNICATION ###
        # DUCKDUCK-GO
        def search_duckduckgo(query):
            try:
                url = "https://api.duckduckgo.com/"
                params = {
                    "q": query,
                    "format": "json",
                    "no_html": 1,
                    "skip_disambig": 1
                }
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                # Try to extract a useful snippet from the AbstractText; if not, join texts from RelatedTopics
                snippet = data.get("AbstractText", "")
                if not snippet:
                    topics = data.get("RelatedTopics", [])
                    snippet = " ".join(topic.get("Text", "") for topic in topics if topic.get("Text"))
                return snippet
            except Exception as e:
                raise Exception(f"Error searching DuckDuckGo: {e}")
        
        # PROVIDER SELECTOR
        def combined_search(self, query, provider=None): #, google_api_key=None, google_cse_id=None, bing_api_key=None):
            try:
                if provider == "duckduckgo":
                    return self.search_duckduckgo(query)
                 
                #elif provider == "google":
                   # if not google_api_key or not google_cse_id:
                   #     raise ValueError("Google API key and CSE ID must be provided for Google Custom Search")
                   # return search_google(query, google_api_key, google_cse_id)
                #elif provider == "bing":
                    #if not bing_api_key:
                     #   raise ValueError("Bing API key must be provided for Bing Web Search")
                    #return search_bing(query, bing_api_key)
                else:
                    return ""

            except Exception as e:
                # Instead of raising the exception, you can choose to return the error message
                return f"SYSTEM: Combined search error: {e}"

        #### TALK TO WEB
        def talk_to_web(self, user_message,PROVIDER = None):
            try:
                web_context = self.combined_search(user_message,PROVIDER)
                return web_context
            except Exception as e:
                web_context = ""
                return f"SYSTEM: Search error: {e}"
    