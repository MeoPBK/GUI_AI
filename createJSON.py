import json

HEADERS = {"Content-Type": "application/json"}
MAX_CONTEXT_LEN = 50;
DEFAULT_PROVIDER = "duckduckgo" 
OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "deepseek-r1:7b"  # Default model to use

PROVIDERS = ["duckduckgo", "bing", "google"]
ROLES_ATTRIBUTE = [
    ["","",""],
    ["","",""],
    ["You are an helpful assistant and you'll answer my questions.","",""],
    ["You are a precise scientist and engineer.", "You always double check your soruces and you quote them.","You base your research on scientific papers and highly reliable data."],
    ["You are a software engineer and you'll help me with my code.", "You're expert in python specialized in ML and DL.",""], 
    ["You are a software engineer and you'll help me with my code.", "Always comment your code and structure it well.",""],
    ["You are a gourmet chef, you'll help me with recipes and explain step by step.", "",""],
    ["You are a story teller.","",""]
    ]
OLLAMA_DATA = {
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
TRIGGER_KEYWORDS = [
    "latest", "current", "breaking", "today", "now", "live", "recent", "trending",
    "update", "updates", "news", "happening", "just in", "in progress", "real-time",
    "live update", "live news", "flash", "alert", "emergency", "today's", "this morning",
    "this afternoon", "this evening", "up-to-date", "live coverage", "currently",
    "ongoing", "developing", "newly", "instant", "immediate", "as it happens", "tomorrow", 
    "internet", "web", "online"
]
ROLES =["None",
        "User Defined",
        "Basic Assistant",
        "Precise Scientist & Engineer", 
        "Python Expert (ML,DL,Opt)", 
        "Software Engineer (full)", 
        "Chef",
        "Story Teller"]

ini_data = { "ROLES": ROLES,
            "OLLAMA_DATA": OLLAMA_DATA,
            "TRIGGER_KEYWORDS": TRIGGER_KEYWORDS,
            "ROLES": ROLES,
            "PROVIDERS": PROVIDERS,
            "HEADERS": HEADERS,
            "MAX_CONTEXT_LEN": MAX_CONTEXT_LEN,
            "OLLAMA_URL": OLLAMA_URL,
            "DEFAULT_MODEL": DEFAULT_MODEL,
            "DEFAULT_PROVIDER": DEFAULT_PROVIDER,
            "ROLES_ATTRIBUTE": ROLES_ATTRIBUTE
    }

with open("ini_data.json", "w", encoding="utf-8") as f:
    json.dump(ini_data, f) # indent=4) <- no indent: more efficient
