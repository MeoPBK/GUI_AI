# -*- coding: utf-8 -*-
"""
@author: meoai and iacop
"""
# from asyncio import new_event_loop
import requests 
import re
import json
from Connecta import Connect
from Learn import Fuzz
from RAG_Fam import RAG

# from createJSON import TRIGGER_KEYWORDS
#import webbrowser
# from mem0 import Memory
# from qdrant_client import QdrantClient
# import os
# config = {
#     "vector_store": {
#         "provider": "qdrant",
#         "config":{
#             "collection_name": "memories",
#             "host": "localhost",
#              #"storage_path": "./qdrant_data",  # Ensures data is stored locally
#             "port": 6333,
#             "embedding_model_dims": 768, # Adjust based on your embedding model
#         },
#     },
#     "llm": {
#         "provider": "ollama",
#         "config": {
#             #"base_url": "http://localhost:11434",  # Local DeepSeek instance
#             "model": "deepseek-r1:1.5b",
#             "temperature": 0.7,  # Adjust for randomness
#             "max_tokens": 2048,  # Set based on DeepSeek's context window
#             "ollama_base_url": "http://localhost:11434",
#             "top_p": 0.9,
#         },
#     },
#     "embedder": {
#         "provider": "ollama",
#         "config": {
#             "model": "nomic-embed-text:latest",
#             # Alternatively, you can use "snowflake-arctic-embed:latest"
#             "ollama_base_url": "http://localhost:11434",
#         # "provider": "huggingface",
#         # "config": {
#         #     "model": "sentence-transformers/all-MiniLM-L6-v2"  # Fallback if DeepSeek embeddings are not available
#         },
#     },
# }

##### INI JSON #####
with open("ini_data.json", "r", encoding="utf-8") as f:
    INI = json.load(f)

class OllamaPOST:
    # initialize OllamaPOST PROPERTIES    
    def __init__(self, OLLAMA_URL = INI["OLLAMA_URL"], PROVIDER = INI["DEFAULT_PROVIDER"], OLLAMA_DATA = INI["OLLAMA_DATA"], 
                 MAX_CONTEXT_LEN = INI["MAX_CONTEXT_LEN"], ROLES_ATTRIBUTE = INI["ROLES_ATTRIBUTE"], TRIGGER_KEYWORDS = INI["TRIGGER_KEYWORDS"],
                 PROTOTYPE_SENTENCES = INI["PROTOTYPE_SENTENCES"], HEADERS =  INI["HEADERS"]):
        # System 
        self.session = requests.Session()           # Persistent session for efficiency
        self.address = OLLAMA_URL      
        self.data = OLLAMA_DATA
        self.headers = HEADERS

        # RAG
        self.data_rag = INI['RAG_DATA']

        # Constants
        self.max_context_length = 0 # MAX_CONTEXT_LEN   # max length of context buffer
        self.role_buffer = len(ROLES_ATTRIBUTE[5])  # length role buffer
       
       # Flags
        self.role_flag = 0                          # true: trascription of roles on, false: end of trascription roles, user input now
        # self.memory_ai_agent = True                 # true: memory on, false: memory off
        
        # Variables
        self.pdf_path = ""#r"C:\Users\meoai\Documents\GUI_AI_SPIACCICONE\files\documentation\fuzzy_logic_py_lib_paper.pdf"                          # path of the pdf file
        self.web_threshold = 0.35                   # when considered web research given output of transformer    
        self.context = []  
        self.answer = ""                            # model answer
        self.role_index = 0                         # index of the role in the list
        self.role = []                              # save roles description
        
        # Other Classes Objects:                    # NOTE: posso dichiararla zero e poi creare obj solo con la connecta e salvarlo qui? ## NB. Argomenti funzione da gestire
        self.context_filter = Fuzz(sentence_categorization=False)
        self.web_search = Connect(self.session, PROVIDER, self.context_filter, TRIGGER_KEYWORDS, PROTOTYPE_SENTENCES)
        self.rag_fam = RAG(self.session, self.data_rag)
        # self.memory = Memory.from_config(config)
        # self.client = QdrantClient(":memory:")  # Runs in RAM (no Docker needed)

        # Transformer Context Filter
        self.context_filter_threshold = 0.5
        self.context_buffer = 2

##### TALK TO OLLAMA #####
    # manages ollama communication
    def talk_to_ollama(self, user_input: str, stream_callback=None)->str:          
        # changes input format based on role on/off and what role:
        tmp_input = self.manage_context(user_input=user_input)
        # changes input format based on role on/off and what role: #    def talk_to_web(  web_thresholf: float, emptycontext_threshold: int)->str:
        new_userinput = self.web_search.talk_to_web(user_input = user_input, tmp_input = tmp_input, context = self.context, role_idx = self.role_index, web_threshold=self.web_threshold, context_buffer = self.context_buffer, context_threshold = self.context_filter_threshold) # len(words_transformers)
        streaming_active = self.data["stream"] # check activate streaming
        print(self.context)
        # print("input: " + new_userinput)
        #new_userinput = self.chat_with_memories(new_userinput)     # qdrant + mem0

        if self.pdf_path:
            new_userinput = rag_fam.hierarchical_rag(self, new_userinput, self.pdf_path)

        self.data["prompt"] = new_userinput                         # assign prompt message in JSON
        
        # NO STREAMING in chat
        if not streaming_active:
            try:
                # Make the POST request
                response = self.session.post(self.address+"/api/generate", self.headers, json=self.data) # timeout=10)
                response.raise_for_status()
                response_data = response.json()
                model_output = response_data.get('response', 'No response received.', headers=self.headers)
                cleaned_output_tmp = self.clean_response(model_output)
                self.manage_context(user_input=user_input, assist_input = cleaned_output_tmp)
                print(len(self.context))
                cleaned_output = self.answer
                return cleaned_output       
            except requests.exceptions.RequestException as e:
                return f"API Error: {e}"
        # STREAMING in chat
        else:
            try:
                # Make the POST request with streaming enabled
                complete_response = ""
                response = self.session.post(self.address + "/api/generate", headers=self.headers, json=self.data, stream=True)
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        try:
                            # Parse the JSON object from each line
                            decoded_line = line.decode('utf-8')
                            json_data = json.loads(decoded_line)                               
                            # Extract just the response field
                            if 'response' in json_data:
                                response_chunk = json_data['response']
                                complete_response += response_chunk
                                # Call the callback with just the cleaned response text
                                if stream_callback:
                                    stream_callback(response_chunk)
                                # print("response_chunk: " + str(response_chunk))

                        except json.JSONDecodeError:
                            # Skip lines that aren't valid JSON
                            continue    
                # After all chunks are processed, update the context with the complete response
                final_response = self.clean_response(complete_response)
                self.manage_context(user_input = user_input, assist_input = final_response)
                self.answer = final_response
                # return final_response
            except requests.exceptions.RequestException as e:
                return f"API Error: {e}"

##### MODELS ##### 
    def get_ollama_models(self):
        try:
            response = self.session.get(self.address+"/api/tags",headers = self.headers)
            models_data = response.json()
            # Extract model names from the response
            models = [model['name'] for model in models_data['models']]
            return models
        except requests.exceptions.RequestException as e:
            return []

##### ROLES #####
    # assistant context manager (called in manage_context())
    def assistant_manager(self, assist_input: str): 
        clean_input = assist_input.replace("\n","")
        if self.role_index == 0:# query, context: list ,threshol
            self.context.append(self.context_filter.transformer_context_filter(query = clean_input,context = self.context, buffer_context_transformer = self.context_buffer, context_threshold = self.context_filter_threshold)) # query, context: list ,threshol
        else:
            self.context.append("ASSISTANT: " + self.context_filter.transformer_context_filter(query = clean_input,context = self.context, buffer_context_transformer = self.context_buffer, context_threshold=self.context_filter_threshold))
        self.answer = assist_input
       
    # role manager for context (called in manage_context())
    def role_manager(self, user_input: str):
        # CASE 1: if role = "one of the selection" (but not "None" nor "User Defined")
        if self.role_index >1:                       
            if self.role_flag == 0:         # if the role description-mode is still active
                self.context.append("USER: " + self.context_filter.transformer_context_filter(query = user_input, context = self.context, buffer_context_transformer = self.context_buffer, context_threshold=self.context_filter_threshold)) 
            else:
                for role in INI["ROLES_ATTRIBUTE"][self.role_index]:
                    if role:           
                        self.context.append("SYSTEM: " + role)
                        self.role.append("SYSTEM: " + role)
                    else: break
                self.role_flag = 0

        # CASE 2: if role == "User Defined"
        elif self.role_index == 1:                                      
            tmp = ["system","user"]     
            size = len(user_input)
            N = len(tmp[0]) + 1                   # can be more clean
            N2 = len(tmp[1]) + 1
            if size<= N-1: 
                N = 1
                N2 = 1
                tmp = ["sy","us"] 

            if tmp[0] in user_input[:N].lower():
                new_input = user_input[N:]
                self.context.append("SYSTEM: " + self.context_filter.transformer_context_filter(query =  new_input,context = self.context, buffer_context_transformer = self.context_buffer, context_threshold=self.context_filter_threshold))
                self.role.append("SYSTEM: " + self.context_filter.transformer_context_filter(query =  new_input,context = self.context, buffer_context_transformer = self.context_buffer, context_threshold=self.context_filter_threshold))
            elif tmp[1] in user_input[:N2].lower():
                new_input = user_input[N2:]
                self.context.append("USER: " + self.context_filter.transformer_context_filter(user_input,self.context,buffer_context_transformer = self.context_buffer, context_threshold=self.context_filter_threshold)) 
            else: self.context.append("USER: " + self.context_filter.transformer_context_filter(user_input,self.context,buffer_context_transformer = self.context_buffer, context_threshold=self.context_filter_threshold))
                
        # CASE 3: if role == "None"
        else:                               
            self.context.append(user_input) 
                
    # function to manage the context length and the roles assignation with "USER, SYSTEM, ASSISTANT"
    def manage_context(self, user_input: str = None, assist_input: str =None)->str:
        ## CONTEXT ON ##
        if self.max_context_length != 0: 
            # if assistant is talking
            if assist_input:    
                self.assistant_manager(assist_input)
            # if user or sys are talking
            elif user_input:      
                self.role_manager(user_input)
            # manages the buffer for the context
            if len(self.context) > self.max_context_length:
                self.context = self.context[-self.max_context_length:]
                self.context[-self.role_buffer:] = self.role[:self.role_buffer]
                # print("End BUffer reached")            
        ## CONTEXT OFF ## -> just returns itself
        else:
            self.context = [user_input]  
        return "\n".join(self.context)  # string format for model prompt

##### DEBUG & SETTINGS #####
    # check my class objects by prining them
    def checkObj(self):
        print(self.__dict__)

    # Rimuove il contenuto tra i tag <think> e </think> dalla risposta.
    def clean_response(self, response: str)->str: 
        # Usa una regex per trovare e rimuovere tutto ciò che è tra <think> e </think>
        cleaned_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        return cleaned_response.strip()  # Rimuove spazi bianchi extra
    
    def remove_articles(sentence):
        return sentence
        #return re.sub(r'\b(a|an|the)\b\s*', '', sentence, flags=re.IGNORECASE)

    ## QDRANT + MEM0 ##
    # def chat_with_memories(self, message: str, user_id: str = "default_user")->str:
    #     relevant_memories = self.memory.search(query=message,user_id=user_id,limit= 3)
    #     memories_str = "\n".join(f"- {entry["memory"]}" for entry in relevant_memories["results"])
    #     sys_prompt = f"You are a helpful AI. Answer my question based on query and memories.\n User Memories: \n {memories_str}"
    #     messages = ""
    #     if self.role_index > 0:
    #         messages = "\nSYSTEM: " + sys_prompt + "\nUSER: " + message
    #     else:
    #         messages = "\nSYSTEM: " + sys_prompt + "\n" + message
    #     self.context.append("SYSTEM: " + sys_prompt, "USER: " + message)
    #     return messages