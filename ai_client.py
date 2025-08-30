# -*- coding: utf-8 -*-
# AI Client Module for Document Analyzer
# Handles communication with OpenRouter free AI models

import requests
import json
from typing import Dict, List, Optional
import time
import streamlit as st

class AIClient:
    """
    Handles communication with OpenRouter free AI models for document analysis and chat.
    Provides different AI personalities and chat functionality.
    """
    
    def __init__(self):
        """Initialize the AI client with API key from Streamlit secrets"""
        # Get API keys from Streamlit secrets or environment
        try:
            # Try nested format first (user's format)
            self.openrouter_api_key = st.secrets["openrouter"]["api_key"]
        except:
            try:
                # Fallback to flat format
                self.openrouter_api_key = st.secrets.get('OPENROUTER_API_KEY')
            except:
                # Fallback to environment variables (Replit secrets)
                import os
                self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        
        try:
            # Try nested format first
            self.openai_api_key = st.secrets["openai"]["api_key"]
        except:
            try:
                # Fallback to flat format
                self.openai_api_key = st.secrets.get('OPENAI_API_KEY')
            except:
                # Fallback to environment variables (Replit secrets)
                import os
                self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Configure based on which API key is provided
        if self.openai_api_key:
            # Use OpenAI directly
            self.provider = "OpenAI"
            self.api_key = self.openai_api_key
            self.base_url = "https://api.openai.com/v1/chat/completions"
            self.available_models = {
                "gpt-4o-mini": "gpt-4o-mini",
                "gpt-4o": "gpt-4o",
                "gpt-3.5-turbo": "gpt-3.5-turbo"
            }
            self.current_model = "gpt-4o-mini"
        elif self.openrouter_api_key:
            # Use OpenRouter
            self.provider = "OpenRouter"
            self.api_key = self.openrouter_api_key
            self.base_url = "https://openrouter.ai/api/v1/chat/completions"
            self.available_models = {
                "gpt-4o-mini": "openai/gpt-4o-mini",
                "gpt-4o": "openai/gpt-4o",
                "claude-3.5-sonnet": "anthropic/claude-3.5-sonnet",
                "llama-3.2-3b": "meta-llama/llama-3.2-3b-instruct:free",
                "qwen-2.5-7b": "qwen/qwen-2.5-7b-instruct:free"
            }
            self.current_model = "openai/gpt-4o-mini"
        else:
            # No API key provided
            self.provider = "None"
            self.api_key = None
            self.base_url = None
            self.available_models = {}
            self.current_model = None
        
        # AI Personalities
        self.personalities = {
            "general": {
                "name": "General Assistant",
                "description": "Helpful general-purpose AI assistant",
                "system_prompt": """You are a helpful AI assistant specializing in document analysis. 
                Provide clear, accurate, and helpful responses based on the document content provided. 
                Focus on being informative and easy to understand."""
            },
            "researcher": {
                "name": "Academic Researcher",
                "description": "Research-focused analysis with academic perspective",
                "system_prompt": """You are an academic researcher and analyst. Approach documents with 
                scholarly rigor, focusing on methodology, evidence quality, citations, and research validity. 
                Provide critical analysis and identify strengths, limitations, and areas for further investigation."""
            },
            "business": {
                "name": "Business Analyst",
                "description": "Business and strategy focused analysis",
                "system_prompt": """You are a business analyst with expertise in strategy, operations, and 
                market analysis. Focus on business implications, financial aspects, market opportunities, 
                strategic insights, and practical applications when analyzing documents."""
            },
            "lawyer": {
                "name": "Legal Expert",
                "description": "Legal analysis and compliance perspective",
                "system_prompt": """You are a legal expert specializing in document review. Focus on legal 
                implications, compliance issues, contract terms, regulatory aspects, and potential legal risks. 
                Provide clear explanations of legal concepts for non-lawyers."""
            },
            "student": {
                "name": "Study Assistant",
                "description": "Educational support and learning assistance",
                "system_prompt": """You are a study assistant helping with learning and comprehension. 
                Break down complex concepts into simple terms, create summaries, suggest study questions, 
                and help with understanding the material. Focus on educational value and clarity."""
            }
        }
        
        self.current_personality = "general"
        self.conversation_history = []
    
    def set_personality(self, personality_key: str) -> bool:
        """
        Set the AI personality for responses.
        
        Args:
            personality_key (str): Key for the personality to use
            
        Returns:
            bool: True if personality was set successfully
        """
        if personality_key in self.personalities:
            self.current_personality = personality_key
            return True
        return False
    
    def get_available_personalities(self) -> Dict[str, Dict]:
        """Get list of available AI personalities"""
        return self.personalities
    
    def set_model(self, model_key: str) -> bool:
        """
        Set the AI model to use.
        
        Args:
            model_key (str): Key for the model to use
            
        Returns:
            bool: True if model was set successfully
        """
        if model_key in self.available_models:
            self.current_model = self.available_models[model_key]
            return True
        return False
    
    def chat_with_document(
        self, 
        user_question: str, 
        document_context: str, 
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Dict[str, any]:
        """
        Chat about document content using AI.
        
        Args:
            user_question (str): User's question
            document_context (str): Relevant document content
            max_tokens (int): Maximum tokens in response
            temperature (float): Response creativity (0.0-1.0)
            
        Returns:
            Dict: Response with AI answer and metadata
        """
        try:
            # Get current personality
            personality = self.personalities[self.current_personality]
            
            # Prepare messages
            messages = [
                {
                    "role": "system",
                    "content": f"""{personality['system_prompt']}
                    
                    You will be provided with document content and a user question. Base your response 
                    on the document content provided. If the document doesn't contain relevant information 
                    to answer the question, clearly state that and explain what information would be needed.
                    
                    Be conversational but informative. Cite specific parts of the document when relevant.
                    """
                },
                {
                    "role": "user",
                    "content": f"""Document Content:
{document_context}

Question: {user_question}

Please answer the question based on the document content above."""
                }
            ]
            
            # Make API request
            response = self._make_api_request(messages, max_tokens, temperature)
            
            if response["success"]:
                # Add to conversation history
                self.conversation_history.append({
                    "user": user_question,
                    "ai": response["content"],
                    "personality": personality["name"],
                    "timestamp": time.time()
                })
            
            return response
            
        except Exception as e:
            return {
                "success": False,
                "content": "",
                "error": f"Error in chat: {str(e)}",
                "usage": {}
            }
    
    def analyze_document(self, document_text: str, analysis_type: str = "summary") -> Dict[str, any]:
        """
        Perform specific analysis on document content.
        
        Args:
            document_text (str): Full document text or relevant excerpts
            analysis_type (str): Type of analysis ('summary', 'key_points', 'sentiment', 'themes')
            
        Returns:
            Dict: Analysis results
        """
        try:
            personality = self.personalities[self.current_personality]
            
            analysis_prompts = {
                "summary": "Provide a comprehensive summary of this document, highlighting the main points and key takeaways.",
                "key_points": "Extract and list the key points, findings, or conclusions from this document in a clear, organized format.",
                "sentiment": "Analyze the tone and sentiment of this document. Consider the emotional undertones and overall attitude.",
                "themes": "Identify the main themes, topics, and recurring concepts discussed in this document."
            }
            
            prompt = analysis_prompts.get(analysis_type, analysis_prompts["summary"])
            
            messages = [
                {
                    "role": "system",
                    "content": f"{personality['system_prompt']}\n\nProvide a thorough analysis based on your expertise."
                },
                {
                    "role": "user",
                    "content": f"{prompt}\n\nDocument:\n{document_text}"
                }
            ]
            
            return self._make_api_request(messages, max_tokens=1500, temperature=0.3)
            
        except Exception as e:
            return {
                "success": False,
                "content": "",
                "error": f"Error in analysis: {str(e)}",
                "usage": {}
            }
    
    def _make_api_request(
        self, 
        messages: List[Dict], 
        max_tokens: int = 1000, 
        temperature: float = 0.7
    ) -> Dict[str, any]:
        """
        Make request to OpenRouter API.
        
        Args:
            messages (List[Dict]): Chat messages
            max_tokens (int): Maximum tokens in response
            temperature (float): Response creativity
            
        Returns:
            Dict: API response with success status and content
        """
        try:
            # Check if API key is configured
            if not self.api_key:
                return {
                    "success": False,
                    "content": "",
                    "error": "🔑 Please configure an API key in .streamlit/secrets.toml:\nOPENROUTER_API_KEY = \"your-key-here\"\nor\nOPENAI_API_KEY = \"your-key-here\"",
                    "usage": {}
                }
            
            # Prepare request data
            data = {
                "model": self.current_model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False
            }
            
            # Prepare headers with API key
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Add OpenRouter specific headers if using OpenRouter
            if self.provider == "OpenRouter":
                headers["HTTP-Referer"] = "https://document-analyzer.streamlit.app"
                headers["X-Title"] = "AI Document Analyzer"
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            # Check response status
            if response.status_code == 200:
                result = response.json()
                
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    
                    return {
                        "success": True,
                        "content": content,
                        "error": None,
                        "usage": result.get("usage", {}),
                        "model": self.current_model
                    }
                else:
                    return {
                        "success": False,
                        "content": "",
                        "error": "No response content received",
                        "usage": {}
                    }
            else:
                error_msg = f"API request failed with status {response.status_code}"
                try:
                    error_detail = response.json().get("error", {}).get("message", "")
                    if error_detail:
                        error_msg += f": {error_detail}"
                except:
                    pass
                
                # Provide helpful error message for authentication issues
                if response.status_code == 401:
                    error_msg = """🔑 API Key Required: OpenRouter now requires an API key even for free models.

To fix this:
1. Go to https://openrouter.ai/keys
2. Create a free account and generate an API key
3. Add it to your .streamlit/secrets.toml file:
   OPENROUTER_API_KEY = "your-api-key-here"

Free models give you 50 requests/day (1000 with $10+ credits)."""
                
                return {
                    "success": False,
                    "content": "",
                    "error": error_msg,
                    "usage": {}
                }
                
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "content": "",
                "error": "Request timed out. Please try again.",
                "usage": {}
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "content": "",
                "error": "Connection error. Please check your internet connection.",
                "usage": {}
            }
        except Exception as e:
            return {
                "success": False,
                "content": "",
                "error": f"Unexpected error: {str(e)}",
                "usage": {}
            }
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict]:
        """
        Get recent conversation history.
        
        Args:
            limit (int): Maximum number of conversations to return
            
        Returns:
            List[Dict]: Recent conversation history
        """
        return self.conversation_history[-limit:] if self.conversation_history else []
    
    def clear_conversation_history(self):
        """Clear the conversation history"""
        self.conversation_history = []
    
    def get_service_info(self) -> Dict[str, any]:
        """
        Get information about the current AI service being used.
        
        Returns:
            Dict: Service information including provider, model, and API status
        """
        if self.api_key:
            return {
                "provider": self.provider,
                "model": self.current_model,
                "api_key_status": "✅ Ready",
                "available_models": list(self.available_models.keys())
            }
        else:
            return {
                "provider": "Not Configured",
                "model": "None",
                "api_key_status": "❌ API Key Required",
                "available_models": []
            }
    
    def test_connection(self) -> Dict[str, any]:
        """
        Test the connection to OpenRouter API.
        
        Returns:
            Dict: Test results
        """
        test_messages = [
            {
                "role": "user",
                "content": "Hello, this is a connection test. Please respond with 'Connection successful'."
            }
        ]
        
        response = self._make_api_request(test_messages, max_tokens=50, temperature=0.1)
        
        return {
            "success": response["success"],
            "message": "Connection test completed",
            "details": response.get("error", "Connected successfully"),
            "model": self.current_model
        }