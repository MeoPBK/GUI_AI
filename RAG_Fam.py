import Tools_Lib as tl
import os
from transformers import AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer
import torch
import pickle 
import numpy as np
#import sentencepiece

class RAG:
    def __init__(self, session, data_rag):
        self. session = session
        self.data_rag = data_rag

        # Load the model and tokenizer for embedder
        model_name = 'stella_en_1.5B_v5' #'BAAI/bge-en-icl' # better but don't work without sentencepiece
        model_name ='sentence-transformers/distiluse-base-multilingual-cased-v2' # all-MiniLM-L6-v2')    # Load a pre-trained Sentence Transformer model. This model transforms text into high-dimensional embeddings that capture contextual meaning.
        #model_name = "sentence-t5-base"# "bge-m3" # "BAAI/bge-en-icl"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)#, use_fast=False)
        self.model = AutoModel.from_pretrained(model_name)

        self.chunk_size = 1000
        self.chunk_overlap = 200
    # OPEN QUESTION: Can I combine Adaptive Retrieval and Hierarchical RAG?
    # def rag_with_adaptive_retrieval(pdf_path, query, k=4, user_context=None):
    #     """
    #     Complete RAG pipeline with adaptive retrieval.

    #     """
    #     print("\n=== RAG WITH ADAPTIVE RETRIEVAL ===")
    #     print(f"Query: {query}")
    
    #     # Process the document to extract text, chunk it, and create embeddings
    #     chunks, vector_store = process_document(pdf_path)
    
    #     # Classify the query to determine its type
    #     query_type = classify_query(query)
    #     print(f"Query classified as: {query_type}")
    
    #     # Retrieve documents using the adaptive retrieval strategy based on the query type
    #     retrieved_docs = adaptive_retrieval(query, vector_store, k, user_context)
    
    #     # Generate a response based on the query, retrieved documents, and query type
    #     response = generate_response(query, retrieved_docs, query_type)
    
    #     # Compile the results into a dictionary
    #     result = {
    #         "query": query,
    #         "query_type": query_type,
    #         "retrieved_documents": retrieved_docs,
    #         "response": response
    #     }
    
    #     print("\n=== RESPONSE ===")
    #     print(response)
    
    #     return result
 
    # Split text into overlapping chunks while preserving metadata.
    def chunk_text(text, metadata, chunk_size=1000, overlap=200):
    # Args: text (str): Input text to chunk, metadata (Dict): Metadata to preserve, chunk_size (int): Size of each chunk in characters, overlap (int): Overlap between chunks in characters
        chunks = []  # Initialize an empty list to store the chunks
    
        # Iterate over the text with the specified chunk size and overlap
        for i in range(0, len(text), chunk_size - overlap):
            chunk_text = text[i:i + chunk_size]  # Extract the chunk of text
        
            # Skip very small chunks (less than 50 characters)
            if chunk_text and len(chunk_text.strip()) > 50:
                # Create a copy of metadata and add chunk-specific info
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    "chunk_index": len(chunks),  # Index of the chunk
                    "start_char": i,  # Start character index of the chunk
                    "end_char": i + len(chunk_text),  # End character index of the chunk
                    "is_summary": False  # Flag indicating this is not a summary
                })
            
                # Append the chunk with its metadata to the list
                chunks.append({
                    "text": chunk_text,
                    "metadata": chunk_metadata
                })
        return chunks  # Return the list of chunks with metadata: List[Dict]: List of text chunks with metadata

    # Create embeddings for the given texts. 
    def create_embeddings(self,texts):
        #Args:  texts (List[str]): Input texts, model (str): Embedding model name
        if not texts:           # Handle empty input
            return []
        
        # Process in batches if needed (OpenAI API limits)          # number of samples processed together before the model updates its parameters.
        batch_size = 100
        all_embeddings = []
    
        # Iterate over the input texts in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]  # Get the current batch of texts
        
            response = self.get_embedding(text,batch)             # Create embeddings for the current batch
            # response = client.embeddings.create(
            #     model=model,
            #     input=batch
            # )
            batch_embeddings = [item.embedding for item in response] # .data
            all_embeddings.extend(batch_embeddings)  # Add the batch embeddings to the list
    
        return all_embeddings  # Return all embeddings: List[List[float]]: Embedding vectors

    # Generate a concise summary of a page.
    def generate_page_summary(self, page_text, address, headers): 
        # Args: page_text (str): Text content of the page

        # Define the system prompt to instruct the summarization model
        system_prompt = """You are an expert summarization system.
        Create a detailed summary of the provided text. 
        Focus on capturing the main topics, key information, and important facts.
        Your summary should be comprehensive enough to understand what the page contains
        but more concise than the original."""

        # Truncate input text if it exceeds the maximum token limit
        max_tokens = 6000
        truncated_text = page_text[:max_tokens] if len(page_text) > max_tokens else page_text

        self.data_rag["prompt"] = f"SYSTEM: {system_prompt} \nUSER: Please summarize this text:\n\n{truncated_text}"                         # assign prompt message in JSON

        # Make a request to the OpenAI API to generate the summary
        response = self.session.post(address+"/api/generate", headers, json=self.data_rag) # timeout=10)
        response.raise_for_status()
        response_data = response.json()
        model_output = response_data.get('response', 'No response received.', headers=headers)
        cleaned_output_tmp = tl.clean_response(model_output)

        # response = client.chat.completions.create(
        #     model="meta-llama/Llama-3.2-3B-Instruct",  # Specify the model to use
        #     messages=[
        #         {"role": "system", "content": system_prompt},  # System message to guide the assistant
        #         {"role": "user", "content": f"Please summarize this text:\n\n{truncated_text}"}  # User message with the text to summarize
        #     ],
        #     temperature=0.3  # Set the temperature for response generation
        # )
    
        # Return the generated summary content
        return cleaned_output_tmp #  str: Generated summary

    # Process a document into hierarchical indices.
    def process_document_hierarchically(self, pdf_path, chunk_size=1000, chunk_overlap=200):  
        # Args: pdf_path (str): Path to the PDF file, chunk_size (int): Size of each detailed chunk, chunk_overlap (int): Overlap between chunks
        # Extract pages from PDF
        pages = tl.extract_text_from_pdf(pdf_path)
    
        # Create summaries for each page
        print("Generating page summaries...")
        summaries = []
        for i, page in enumerate(pages):
            print(f"Summarizing page {i+1}/{len(pages)}...")
            summary_text = self.generate_page_summary(page["text"])
        
            # Create summary metadata
            summary_metadata = page["metadata"].copy()
            summary_metadata.update({"is_summary": True})
        
            # Append the summary text and metadata to the summaries list
            summaries.append({
                "text": summary_text,
                "metadata": summary_metadata
            })
    
        # Create detailed chunks for each page
        detailed_chunks = []
        for page in pages:
            # Chunk the text of the page
            page_chunks = self.chunk_text(page["text"], page["metadata"], chunk_size, chunk_overlap)
            # Extend the detailed_chunks list with the chunks from the current page
            detailed_chunks.extend(page_chunks)
    
        print(f"Created {len(detailed_chunks)} detailed chunks")
    
        # Create embeddings for summaries
        print("Creating embeddings for summaries...")
        summary_texts = [summary["text"] for summary in summaries]
        summary_embeddings = self.create_embeddings(summary_texts)
    
        # Create embeddings for detailed chunks
        print("Creating embeddings for detailed chunks...")
        chunk_texts = [chunk["text"] for chunk in detailed_chunks]
        chunk_embeddings = self.create_embeddings(chunk_texts)
    
        # Create vector stores
        summary_store = SimpleVectorStore()
        detailed_store = SimpleVectorStore()
    
        # Add summaries to summary store
        for i, summary in enumerate(summaries):
            summary_store.add_item(
                text=summary["text"],
                embedding=summary_embeddings[i],
                metadata=summary["metadata"]
            )
    
        # Add chunks to detailed store
        for i, chunk in enumerate(detailed_chunks):
            detailed_store.add_item(
                text=chunk["text"],
                embedding=chunk_embeddings[i],
                metadata=chunk["metadata"]
                )
    
        print(f"Created vector stores with {len(summaries)} summaries and {len(detailed_chunks)} chunks")
        return summary_store, detailed_store # Tuple[SimpleVectorStore, SimpleVectorStore]: Summary and detailed vector stores
    
    # Retrieve information using hierarchical indices.
    def retrieve_hierarchically(self, query, summary_store, detailed_store, k_summaries=3, k_chunks=5):
        # Args: query (str): User query, summary_store (SimpleVectorStore): Store of document summaries, detailed_store (SimpleVectorStore): Store of detailed chunks, k_summaries (int): Number of summaries to retrieve, k_chunks (int): Number of chunks to retrieve per summary
        print(f"Performing hierarchical retrieval for query: {query}")
    
        # Create query embedding
        query_embedding = self.create_embeddings(query)
    
        # First, retrieve relevant summaries
        summary_results = summary_store.similarity_search(
            query_embedding, 
            k=k_summaries
        )
    
        print(f"Retrieved {len(summary_results)} relevant summaries")
    
        # Collect pages from relevant summaries
        relevant_pages = [result["metadata"]["page"] for result in summary_results]
    
        # Create a filter function to only keep chunks from relevant pages
        def page_filter(metadata):
            return metadata["page"] in relevant_pages
    
        # Then, retrieve detailed chunks from only those relevant pages
        detailed_results = detailed_store.similarity_search(
            query_embedding, 
            k=k_chunks * len(relevant_pages),
            filter_func=page_filter
        )
    
        print(f"Retrieved {len(detailed_results)} detailed chunks from relevant pages")
    
        # For each result, add which summary/page it came from
        for result in detailed_results:
            page = result["metadata"]["page"]
            matching_summaries = [s for s in summary_results if s["metadata"]["page"] == page]
            if matching_summaries:
                result["summary"] = matching_summaries[0]["text"]
    
        return detailed_results # List[Dict]: Retrieved chunks with relevance scores
    
    # Complete hierarchical RAG pipeline.
    def hierarchical_rag(self, query, pdf_path, chunk_size=1000, chunk_overlap=200,  k_summaries=3, k_chunks=5, regenerate=False):
        # Args: query (str): User query, pdf_path (str): Path to the PDF document, chunk_size (int): Size of each detailed chunk, chunk_overlap (int): Overlap between chunks, k_summaries (int): Number of summaries to retrieve, k_chunks (int): Number of chunks to retrieve per summary, regenerate (bool): Whether to regenerate vector stores
        
        # Create store filenames for caching
        summary_store_file = f"{os.path.basename(pdf_path)}_summary_store.pkl"
        detailed_store_file = f"{os.path.basename(pdf_path)}_detailed_store.pkl"
    
        # Process document and create stores if needed
        if regenerate or not os.path.exists(summary_store_file) or not os.path.exists(detailed_store_file):
            print("Processing document and creating vector stores...")
            # Process the document to create hierarchical indices and vector stores
            summary_store, detailed_store = self.process_document_hierarchically(
                pdf_path, chunk_size, chunk_overlap
            )
        
            # Save the summary store to a file for future use
            with open(summary_store_file, 'wb') as f:
                pickle.dump(summary_store, f)
        
            # Save the detailed store to a file for future use
            with open(detailed_store_file, 'wb') as f:
                pickle.dump(detailed_store, f)
        else:
            # Load existing summary store from file
            print("Loading existing vector stores...")
            with open(summary_store_file, 'rb') as f:
                summary_store = pickle.load(f)
        
            # Load existing detailed store from file
            with open(detailed_store_file, 'rb') as f:
                detailed_store = pickle.load(f)
    
        # Retrieve relevant chunks hierarchically using the query
        retrieved_chunks = self.retrieve_hierarchically(
            query, summary_store, detailed_store, k_summaries, k_chunks
        )
    
        context_parts = []
    
        for i, chunk in enumerate(retrieved_chunks):
            page_num = chunk["metadata"]["page"]  # Get the page number from metadata
            context_parts.append(f"[Page {page_num}]: {chunk['text']}")  # Format the chunk text with page number
    
        # Combine all context parts into a single context string
        context = "\n\n".join(context_parts)
    
        # Define the system message to guide the AI assistant
        system_message = """SYSTEM: You are a helpful AI assistant answering questions based on the provided context.
        Use the information from the context to answer the user's question accurately.
        If the context doesn't contain relevant information, acknowledge that.
        Include page numbers when referencing specific information."""

        context = system_message + f"\nUSER: Context:\n\n{context}\n\nQuestion: {query}"
        return context

        # Generate a response based on the retrieved chunks
        # response = generate_response(query, retrieved_chunks)
    
        # # Return results including the query, response, retrieved chunks, and counts of summaries and detailed chunks
        # print(                            # Dict: Results including response and retrieved chunks
        #     "query": query,
        #     "response": response,
        #     "retrieved_chunks": retrieved_chunks,
        #     "summary_count": len(summary_store.texts),
        #     "detailed_count": len(detailed_store.texts))
    

    def get_embedding(self,text, batch):
        inputs = self.tokenizer(batch, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            embedding = self.model(**inputs).last_hidden_state.mean(dim=1)
        return embedding.numpy()

class SimpleVectorStore:
    """
    A simple vector store implementation using NumPy.
    """
    def __init__(self):
        self.vectors = []  # List to store vector embeddings
        self.texts = []  # List to store text content
        self.metadata = []  # List to store metadata
    
    def add_item(self, text, embedding, metadata=None):
        """
        Add an item to the vector store.
        
        Args:
            text (str): Text content
            embedding (List[float]): Vector embedding
            metadata (Dict, optional): Additional metadata
        """
        self.vectors.append(np.array(embedding))  # Append the embedding as a numpy array
        self.texts.append(text)  # Append the text content
        self.metadata.append(metadata or {})  # Append the metadata or an empty dict if None
    
    def similarity_search(self, query_embedding, k=5, filter_func=None):
        """
        Find the most similar items to a query embedding.
        
        Args:
            query_embedding (List[float]): Query embedding vector
            k (int): Number of results to return
            filter_func (callable, optional): Function to filter results
            
        Returns:
            List[Dict]: Top k most similar items
            """
        if not self.vectors:
            return []  # Return an empty list if there are no vectors
        
        # Convert query embedding to numpy array
        query_vector = np.array(query_embedding)
        
        # Calculate similarities using cosine similarity
        similarities = []
        for i, vector in enumerate(self.vectors):
            # Skip if doesn't pass the filter
            if filter_func and not filter_func(self.metadata[i]):
                continue
                
            # Calculate cosine similarity
            similarity = np.dot(query_vector, vector) / (np.linalg.norm(query_vector) * np.linalg.norm(vector))
            similarities.append((i, similarity))  # Append index and similarity score
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top k results
        results = []
        for i in range(min(k, len(similarities))):
            idx, score = similarities[i]
            results.append({
                "text": self.texts[idx],  # Add the text content
                "metadata": self.metadata[idx],  # Add the metadata
                "similarity": float(score)  # Add the similarity score
            })
        
        return results  # Return the list of top k results

