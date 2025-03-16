# Import necessary libraries
# import numpy as np
from sentence_transformers import SentenceTransformer, util
import simpful as sf

class Fuzz:
    def __init__(self, PROTOTYPE_SENTENCES: list = None, fuzz_trigger: bool = False, sentence_categorization: bool = True ):
        self.prototype_sentences = PROTOTYPE_SENTENCES

    ## Transformer for word classification  
        # SEMANTIC SIMILARITIES SETUP
        self.model = SentenceTransformer('distiluse-base-multilingual-cased-v2') # all-MiniLM-L6-v2')    # Load a pre-trained Sentence Transformer model. This model transforms text into high-dimensional embeddings that capture contextual meaning.
        if sentence_categorization:
            self.categories = ["web", "time-related", "financial", "scientific", "mathematics", "article", "greetings", "other"]
            self.category_embeddings = self.model.encode(self.categories, normalize_embeddings=True)
        else:
            self.top_k = 5
            self.context_embeddings = []
            #self.model = SentenceTransformer('all-MiniLM-L6-v2') # msmarco-distilbert-base-v4 # parahrase-MiniLM-L6-v2 ## 22M, all-mpnet-base-v2, paraphrase-mpnet-base-v2 ## 110M, distiluse-base-multilingual-cased-v2 ## 134M
    
## TRANSFORMERS ##
    # Transformer used for the classification of words
    def transformer_classify_word(self, word):
        word_embedding = self.model.encode([word], normalize_embeddings=True)
        similarity_scores = util.pytorch_cos_sim(word_embedding, self.category_embeddings)[0]
    
        best_category_index = similarity_scores.argmax().item()
        best_category = self.categories[best_category_index]
        best_confidence = similarity_scores[best_category_index].item()
        web_confidence = similarity_scores[0].item()
        time_related_confidence = similarity_scores[1].item()
        print("wc: " + str(web_confidence) + ", bc: " + str(best_confidence) + " " + str(best_category))
        return web_confidence, time_related_confidence, best_category, best_confidence
    
    def transformer_context_filter(self,query: str, context: list , buffer_context_transformer: int, context_threshold: float)->list:
        # Tokenize query into words
        if len(context) <= buffer_context_transformer:
            return query
        else: 
            self.context_embeddings = self.model.encode(context, convert_to_tensor=True)
            words = query.split()  # Simple split, can use NLP tokenizer if needed
            relevant_results = {}
            relevant_words = []
            for word in words:
                # Encode the single word
                word_embedding = self.model.encode(word, convert_to_tensor=True)
                # Compute cosine similarity between word and stored contexts
                similarity_scores = util.cos_sim(word_embedding, self.context_embeddings)[0].cpu().numpy()
                # Pair each context with its similarity score and sort
                sorted_contexts = sorted(zip(context, similarity_scores), key=lambda x: x[1], reverse=True)
                # Filter by threshold and limit to top-k
                relevant_contexts = [(ctx, score) for ctx, score in sorted_contexts if score >= context_threshold][:self.top_k]
                # Store results in dictionary
                relevant_results[word] = relevant_contexts if relevant_contexts else [("", 0.0)]
                if  relevant_contexts:
                    print("pennuto")
                    if word not in relevant_words:
                        relevant_words.append(word) 
            relevant_words = " ".join(relevant_words)
            #print(relevant_results)
            # for item in relevant_results.items():
            #     print("sergio")
            #     print(item)
                #relevant_words = " ".join(item)

            #relevant_words = " ".join(dir(relevant_results))
            print(relevant_words)
            return relevant_words

## FUZZY LOGIC SYSTEM SETUP ##              - for triggering confidence
        self.fuzz_trigger = fuzz_trigger
        if self.fuzz_trigger:
            self.FS = sf.FuzzySystem()
            # Define fuzzy rules to map similarity values to trigger confidence.
            rules = [
                "IF ((web_similarity IS low) AND (time_similarity IS low)) THEN (trigger IS low)",
                "IF ",
                "IF ((web_similarity IS medium) OR (time_similarity IS medium))  THEN (trigger IS medium)",
                "IF ((web_similarity IS high) OR (time_similarity IS high)) THEN (trigger IS high)"
            ]      
            # NOTE:The final function can be written as a look-up table
            self.FS.add_rules(rules)

    def fuzziSettings(self, similarity_score: float)->float:
        try: 
            # Add triangular membership functions for "similarity": low, medium, and high.
            ## NOTE: open question: how should i set the gaussian distribution
            S_1 = sf.FuzzySet(function=sf.Triangular_MF(a=0.0,b= 0.0, c=0.5), term="not similar")
            S_2 = sf.FuzzySet(function=sf.Triangular_MF(a=0.3, b=0.5, c=0.7), term="similar")
            S_3 = sf.FuzzySet(function=sf.Triangular_MF(a=0.5, b=1.0, c=1.0), term="very similar") # .Gaussian_MF(mu =1, sigma=0.5)
            # Set up the fuzzy input variable "similarity" on the domain [0, 1].
            self.FS.add_linguistic_variable("similarity", sf.LinguisticVariable([S_1,S_2,S_3],concept="Words similarity",universe_of_discourse = [0, 1]))

            # Add triangular membership functions for "trigger": low, medium, and high.
            T_1 = sf.FuzzySet(function=sf.Triangular_MF(a=0.0, b=0.0, c=0.5), term="low")
            T_2 = sf.FuzzySet(function=sf.Triangular_MF(a=0.3, b=0.5, c=0.7), term="medium")
            T_3 = sf.FuzzySet(function=sf.Triangular_MF(a=0.5, b=1.0, c=1.0), term="high")

            # Set up the fuzzy output variable "trigger" on the domain [0, 1].
            self.FS.add_linguistic_variable("trigger", sf.LinguisticVariable([T_1,T_2,T_3],concept="Trigger confidence",universe_of_discourse = [0, 1]))
        except:
            return ("ERROR")

    ## IDEA:
    # Computes the cosine similarity between a user's input and the prototype centroid.
    # def compute_similarity(self, user_input: str)->float:    
    #     # Compute the embedding for the user input.
    #     input_embedding = self.model.encode(user_input, convert_to_tensor=True)
    #     # Calculate cosine similarity between the input embedding and the prototype centroid.
    #     similarity = util.cos_sim(input_embedding, self.prototype())
    #     # Convert the tensor output to a Python float.
    #     similarity_score = similarity.item()
    #     return similarity_score     # (float): A value between 0 and 1 representing the semantic similarity.

    # Computes a fuzzy logic–based confidence value (trigger) using Simpful based on the semantic similarity score.
    def defuzzify_output(self, similarity_score: float)->float:
        # Set the "similarity" variable in the fuzzy system.
        #self.FS.set_variable("similarity", similarity_score)
        # Execute the fuzzy inference process.
        tmp = self.FS.inference()
        print(self.FS.inference())
        trigger_value = tmp['trigger']
        # Retrieve and return the fuzzy output for "trigger".
        # trigger_value = self.FS.linguistic_variable["trigger"]      # trigger_value (float): A fuzzy output value between 0 and 1 representing trigger confidence.
        return trigger_value


