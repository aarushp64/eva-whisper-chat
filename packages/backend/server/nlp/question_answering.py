from transformers import pipeline
import nltk
from nltk.tokenize import sent_tokenize
import re
import spacy
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
import os

# Download NLTK resources if needed
try:
    nltk.data.find('punkt')
except LookupError:
    nltk.download('punkt')

# Load SpaCy model
try:
    nlp = spacy.load("en_core_web_md")
except OSError:
    # Download if not available
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_md"])
    nlp = spacy.load("en_core_web_md")

# Initialize HuggingFace QA pipeline
qa_pipeline = None

def initialize_qa_pipeline():
    """Initialize the HuggingFace QA pipeline"""
    global qa_pipeline
    try:
        qa_pipeline = pipeline("question-answering", model="deepset/roberta-base-squad2")
    except Exception as e:
        print(f"Error initializing QA pipeline: {str(e)}")
        # Try a smaller model as fallback
        try:
            qa_pipeline = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")
        except Exception as e:
            print(f"Error initializing fallback QA pipeline: {str(e)}")

def answer_question_huggingface(question, context):
    """
    Answer a question using HuggingFace QA pipeline
    
    Args:
        question (str): The question to answer
        context (str): The context to extract the answer from
        
    Returns:
        dict: Answer information including the answer text, score, and start/end positions
    """
    global qa_pipeline
    
    if qa_pipeline is None:
        initialize_qa_pipeline()
        if qa_pipeline is None:
            return None
    
    try:
        # Check if context is too long for the model (typically 512 tokens)
        max_context_length = 512
        words = context.split()
        
        if len(words) > max_context_length:
            # Split context into chunks and run QA on each chunk
            chunk_size = max_context_length - 50  # Leave room for question
            chunks = [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
            
            best_answer = None
            best_score = 0
            
            for chunk in chunks:
                result = qa_pipeline(question=question, context=chunk)
                
                if result['score'] > best_score:
                    best_score = result['score']
                    best_answer = result
            
            return best_answer
        else:
            # If context is short enough, run QA directly
            return qa_pipeline(question=question, context=context)
    except Exception as e:
        print(f"Error in HuggingFace QA: {str(e)}")
        return None

def answer_question_langchain(question, documents, use_openai=False):
    """
    Answer a question using LangChain and document retrieval
    
    Args:
        question (str): The question to answer
        documents (list): List of document texts to search for the answer
        use_openai (bool): Whether to use OpenAI API for answering
        
    Returns:
        dict: Answer information including the answer text and source
    """
    try:
        # Create embeddings
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
        
        # Create vector store
        texts = []
        metadatas = []
        
        for i, doc in enumerate(documents):
            # Split documents into chunks
            sentences = sent_tokenize(doc)
            chunk_size = 5  # Number of sentences per chunk
            
            for j in range(0, len(sentences), chunk_size):
                chunk = ' '.join(sentences[j:j+chunk_size])
                texts.append(chunk)
                metadatas.append({"source": f"document_{i}", "chunk": j//chunk_size})
        
        # Create FAISS vector store
        vectorstore = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
        
        # Create retriever
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        
        # Create QA chain
        if use_openai and os.environ.get("OPENAI_API_KEY"):
            llm = OpenAI(temperature=0)
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True
            )
            
            # Run the chain
            result = qa_chain({"query": question})
            
            return {
                "answer": result["result"],
                "sources": [doc.metadata["source"] for doc in result["source_documents"]],
                "method": "langchain_openai"
            }
        else:
            # Retrieve relevant documents
            docs = retriever.get_relevant_documents(question)
            
            # Use HuggingFace QA on the retrieved documents
            context = " ".join([doc.page_content for doc in docs])
            
            hf_result = answer_question_huggingface(question, context)
            
            if hf_result:
                return {
                    "answer": hf_result["answer"],
                    "score": hf_result["score"],
                    "sources": [docs[i].metadata["source"] for i in range(len(docs))],
                    "method": "langchain_huggingface"
                }
            else:
                return None
    except Exception as e:
        print(f"Error in LangChain QA: {str(e)}")
        return None

def extract_question_type(question):
    """
    Determine the type of question being asked
    
    Args:
        question (str): The question to analyze
        
    Returns:
        str: Question type
    """
    question = question.lower().strip()
    
    # Check for question words
    if re.match(r'^(what|which|whose)\b', question):
        return "factoid"
    elif re.match(r'^(where)\b', question):
        return "location"
    elif re.match(r'^(when)\b', question):
        return "temporal"
    elif re.match(r'^(who|whom)\b', question):
        return "person"
    elif re.match(r'^(why)\b', question):
        return "reason"
    elif re.match(r'^(how)\b', question):
        if any(word in question for word in ["many", "much", "long", "old", "far"]):
            return "quantity"
        else:
            return "method"
    elif re.match(r'^(can|could|would|will|shall|should|is|are|do|does|did|have|has|had)\b', question):
        return "boolean"
    else:
        return "other"

def answer_question(question, context=None, documents=None, method="auto"):
    """
    Answer a question using the best available method
    
    Args:
        question (str): The question to answer
        context (str): Optional context to extract the answer from
        documents (list): Optional list of document texts to search for the answer
        method (str): Method to use - "huggingface", "langchain", "openai", or "auto"
        
    Returns:
        dict: Answer information
    """
    # Determine question type
    question_type = extract_question_type(question)
    
    # Choose method based on question type and available context
    if method == "auto":
        if context and len(context.split()) < 1000:
            method = "huggingface"
        elif documents and len(documents) > 0:
            # Check if OpenAI API key is available
            if os.environ.get("OPENAI_API_KEY"):
                method = "openai"
            else:
                method = "langchain"
        else:
            method = "huggingface"
    
    # Answer using the selected method
    if method == "huggingface":
        if not context:
            if documents:
                # Combine documents into a single context
                context = " ".join(documents)
            else:
                return {
                    "answer": "I don't have enough information to answer that question.",
                    "method": "fallback"
                }
        
        result = answer_question_huggingface(question, context)
        
        if result:
            return {
                "answer": result["answer"],
                "score": result["score"],
                "start": result["start"],
                "end": result["end"],
                "method": "huggingface",
                "question_type": question_type
            }
        else:
            return {
                "answer": "I couldn't find an answer to that question in the provided context.",
                "method": "fallback",
                "question_type": question_type
            }
    
    elif method == "langchain" or method == "openai":
        if not documents:
            if context:
                # Split context into sentences to create documents
                documents = [context]
            else:
                return {
                    "answer": "I don't have enough information to answer that question.",
                    "method": "fallback",
                    "question_type": question_type
                }
        
        use_openai = (method == "openai")
        result = answer_question_langchain(question, documents, use_openai)
        
        if result:
            return {
                **result,
                "question_type": question_type
            }
        else:
            return {
                "answer": "I couldn't find an answer to that question in the provided documents.",
                "method": "fallback",
                "question_type": question_type
            }
    
    # Fallback
    return {
        "answer": "I don't have enough information to answer that question.",
        "method": "fallback",
        "question_type": question_type
    }
