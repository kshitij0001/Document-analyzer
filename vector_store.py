# -*- coding: utf-8 -*-
# Vector Store Module for AI Document Analyzer
# Handles document embeddings and similarity search using TF-IDF

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Dict, Optional, Tuple
import pickle

class VectorStore:
    """
    Handles document vectorization and similarity search using TF-IDF.
    Provides efficient search functionality for finding relevant document chunks.
    """
    
    def __init__(self, max_features: int = 5000, stop_words: str = 'english'):
        """
        Initialize the vector store.
        
        Args:
            max_features (int): Maximum number of features for TF-IDF
            stop_words (str): Language for stop words removal
        """
        self.max_features = max_features
        self.stop_words = stop_words
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            stop_words=stop_words,
            ngram_range=(1, 2),  # Include unigrams and bigrams
            lowercase=True,
            strip_accents='unicode'
        )
        self.document_vectors = None
        self.chunks = []
        self.is_fitted = False
    
    def add_document(self, doc_info: Dict) -> bool:
        """
        Add a processed document to the vector store.
        
        Args:
            doc_info (Dict): Processed document information from DocumentProcessor
            
        Returns:
            bool: True if successfully added, False otherwise
        """
        try:
            if not doc_info.get("success", False) or not doc_info.get("chunks"):
                return False
            
            # Extract text from chunks
            chunk_texts = [chunk["text"] for chunk in doc_info["chunks"]]
            
            # Add document metadata to chunks
            enhanced_chunks = []
            for i, chunk in enumerate(doc_info["chunks"]):
                enhanced_chunk = chunk.copy()
                enhanced_chunk.update({
                    "document_name": doc_info["filename"],
                    "file_type": doc_info["file_type"],
                    "global_index": len(self.chunks) + i
                })
                enhanced_chunks.append(enhanced_chunk)
            
            # If this is the first document, fit the vectorizer
            if not self.is_fitted:
                self.document_vectors = self.vectorizer.fit_transform(chunk_texts)
                self.chunks = enhanced_chunks
                self.is_fitted = True
            else:
                # Transform new chunks and concatenate with existing vectors
                new_vectors = self.vectorizer.transform(chunk_texts)
                
                # Combine vectors
                if self.document_vectors is not None:
                    from scipy.sparse import vstack
                    self.document_vectors = vstack([self.document_vectors, new_vectors])
                else:
                    self.document_vectors = new_vectors
                
                # Add chunks
                self.chunks.extend(enhanced_chunks)
            
            return True
            
        except Exception as e:
            print(f"Error adding document to vector store: {str(e)}")
            return False
    
    def search(self, query: str, top_k: int = 3, min_score: float = 0.1) -> List[Dict]:
        """
        Search for relevant document chunks based on query.
        
        Args:
            query (str): Search query
            top_k (int): Number of top results to return
            min_score (float): Minimum similarity score threshold
            
        Returns:
            List[Dict]: Ranked list of relevant chunks with scores
        """
        if not self.is_fitted or not query.strip():
            return []
        
        try:
            # Vectorize the query
            query_vector = self.vectorizer.transform([query])
            
            # Calculate cosine similarity
            similarities = cosine_similarity(query_vector, self.document_vectors).flatten()
            
            # Get top results above threshold
            results = []
            for i, score in enumerate(similarities):
                if score >= min_score:
                    results.append({
                        "chunk": self.chunks[i],
                        "similarity_score": float(score),
                        "rank": 0  # Will be set after sorting
                    })
            
            # Sort by similarity score
            results.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            # Add rank information and limit results
            for i, result in enumerate(results[:top_k]):
                result["rank"] = i + 1
            
            return results[:top_k]
            
        except Exception as e:
            print(f"Error during search: {str(e)}")
            return []
    
    def get_context_for_query(self, query: str, max_context_length: int = 2000) -> str:
        """
        Get relevant context text for a query to send to AI model.
        
        Args:
            query (str): User's question
            max_context_length (int): Maximum length of context text
            
        Returns:
            str: Relevant context text from documents
        """
        # Get relevant chunks
        search_results = self.search(query, top_k=5, min_score=0.05)
        
        if not search_results:
            return "No relevant context found in the uploaded documents."
        
        # Combine relevant chunks into context
        context_parts = []
        total_length = 0
        
        for result in search_results:
            chunk_text = result["chunk"]["text"]
            doc_name = result["chunk"].get("document_name", "Unknown")
            
            # Format chunk with source information
            formatted_chunk = f"[From {doc_name}]: {chunk_text}"
            
            # Check if adding this chunk would exceed length limit
            if total_length + len(formatted_chunk) > max_context_length:
                # Try to add a truncated version
                remaining_space = max_context_length - total_length - 20  # Leave space for "..."
                if remaining_space > 100:  # Only add if there's meaningful space
                    truncated = formatted_chunk[:remaining_space] + "..."
                    context_parts.append(truncated)
                break
            
            context_parts.append(formatted_chunk)
            total_length += len(formatted_chunk)
        
        # Join all context parts
        context = "\n\n".join(context_parts)
        
        # Add metadata about the search
        if len(search_results) > 0:
            best_score = search_results[0]["similarity_score"]
            context = f"Relevant information from documents (confidence: {best_score:.2f}):\n\n{context}"
        
        return context
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about the vector store.
        
        Returns:
            Dict: Statistics including document count, chunk count, etc.
        """
        if not self.is_fitted:
            return {
                "total_chunks": 0,
                "total_documents": 0,
                "vocabulary_size": 0,
                "is_ready": False
            }
        
        # Count unique documents
        document_names = set(chunk.get("document_name", "Unknown") for chunk in self.chunks)
        
        return {
            "total_chunks": len(self.chunks),
            "total_documents": len(document_names),
            "vocabulary_size": len(self.vectorizer.vocabulary_) if hasattr(self.vectorizer, 'vocabulary_') else 0,
            "is_ready": True,
            "document_names": list(document_names)
        }
    
    def clear(self):
        """Clear all stored documents and reset the vector store."""
        self.document_vectors = None
        self.chunks = []
        self.is_fitted = False
        # Reset vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            stop_words=self.stop_words,
            ngram_range=(1, 2),
            lowercase=True,
            strip_accents='unicode'
        )
    
    def remove_document(self, document_name: str) -> bool:
        """
        Remove a specific document from the vector store.
        
        Args:
            document_name (str): Name of the document to remove
            
        Returns:
            bool: True if document was found and removed, False otherwise
        """
        if not self.is_fitted:
            return False
        
        try:
            # Find chunks belonging to this document
            indices_to_remove = []
            for i, chunk in enumerate(self.chunks):
                if chunk.get("document_name") == document_name:
                    indices_to_remove.append(i)
            
            if not indices_to_remove:
                return False  # Document not found
            
            # Remove chunks
            self.chunks = [chunk for i, chunk in enumerate(self.chunks) if i not in indices_to_remove]
            
            # Remove corresponding vectors
            if self.document_vectors is not None:
                mask = np.ones(self.document_vectors.shape[0], dtype=bool)
                mask[indices_to_remove] = False
                self.document_vectors = self.document_vectors[mask]
            
            # If no chunks remain, reset the store
            if len(self.chunks) == 0:
                self.clear()
            
            return True
            
        except Exception as e:
            print(f"Error removing document: {str(e)}")
            return False
    
    def get_chunk_preview(self, chunk_index: int, preview_length: int = 200) -> str:
        """
        Get a preview of a specific chunk.
        
        Args:
            chunk_index (int): Index of the chunk
            preview_length (int): Length of preview text
            
        Returns:
            str: Preview text of the chunk
        """
        if not self.is_fitted or chunk_index >= len(self.chunks):
            return ""
        
        chunk_text = self.chunks[chunk_index]["text"]
        if len(chunk_text) <= preview_length:
            return chunk_text
        
        return chunk_text[:preview_length] + "..."