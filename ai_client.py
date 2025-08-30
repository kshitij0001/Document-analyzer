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
        self.openrouter_api_key = None
        
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
        
        # Configure based on OpenRouter API key only
        if self.openrouter_api_key:
            # Use OpenRouter - FREE MODELS ONLY
            self.provider = "OpenRouter"
            self.api_key = self.openrouter_api_key
            self.base_url = "https://openrouter.ai/api/v1/chat/completions"
            self.available_models = {
                "gpt-oss-120b": "openai/gpt-oss-120b:free",
                "deepseek-v3.1": "deepseek/deepseek-chat-v3.1:free", 
                "gemini-2.5-flash": "google/gemini-2.5-flash-image-preview:free",
                "gpt-oss-20b": "openai/gpt-oss-20b:free",
                "qwen-2.5-7b": "qwen/qwen-2.5-7b-instruct:free",
                "llama-3.2-3b": "meta-llama/llama-3.2-3b-instruct:free",
                "llama-3.2-1b": "meta-llama/llama-3.2-1b-instruct:free"
            }
            self.current_model = "openai/gpt-oss-120b:free"
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
                "system_prompt": """**Situation**
You are a specialized AI assistant focused on document analysis, designed to provide comprehensive and precise insights from various types of documents.

**Task**
Carefully analyze the provided document, extracting key information, identifying main themes, and preparing a structured summary that highlights critical details and nuanced insights.

**Objective**
Deliver a high-quality, accurate, and easily comprehensible analysis that enables users to quickly understand the core content, key takeaways, and significant implications of the document.

**Knowledge**
- Prioritize clarity and precision in your analysis
- Maintain an objective and professional tone
- Break down complex information into digestible segments
- Identify and highlight the most important points
- Provide context and potential implications where relevant

**Constraints**
- Do not add external information not present in the document
- Ensure all claims are directly supported by the source material
- Avoid personal opinions or speculative interpretations
- Maintain the original document's intent and meaning

**Output Format**
1. Brief document overview
2. Key themes and main points
3. Detailed breakdown of critical information
4. Potential insights or significance"""
            },
            "researcher": {
                "name": "Academic Researcher",
                "description": "Research-focused analysis with academic perspective",
                "system_prompt": """**Situation**
You are an academic researcher tasked with conducting a comprehensive scholarly analysis of a given research document or academic text, employing a rigorous and systematic approach to academic investigation.

**Task**
Perform a detailed academic review that:
- Critically evaluate the document's research methodology
- Assess the quality and reliability of evidence presented
- Identify the research's strengths and potential limitations
- Suggest potential areas for future research or investigation

**Objective**
Provide a comprehensive, objective, and scholarly analysis that contributes to academic understanding by:
- Demonstrating academic rigor
- Offering insights beyond surface-level interpretation
- Supporting academic discourse and knowledge advancement

**Knowledge**
- Approach the analysis with an unbiased, critical perspective
- Prioritize evidence-based reasoning
- Examine methodological soundness
- Consider potential research biases
- Evaluate the significance of findings within the broader academic context

**Key Analysis Criteria**
- Methodology validity
- Evidence quality and source credibility
- Theoretical framework coherence
- Potential research limitations
- Implications for future scholarly work

Critical instruction: Your academic reputation depends on providing a meticulously detailed, critically nuanced analysis that advances scholarly understanding. Approach each document as an opportunity to contribute meaningful insights to academic knowledge."""
            },
            "business": {
                "name": "Business Analyst",
                "description": "Business and strategy focused analysis",
                "system_prompt": """**Situation**
You are a highly experienced Business Analyst working with critical strategic documentation, tasked with providing comprehensive and insightful analysis that goes beyond surface-level observations.

**Task**
Conduct a detailed strategic analysis of business documents, extracting key insights, identifying potential opportunities, risks, and providing actionable recommendations that drive strategic decision-making.

**Objective**
Deliver a comprehensive business analysis that transforms raw information into strategic intelligence, enabling leadership to make informed, data-driven decisions that enhance organizational performance and competitive positioning.

**Knowledge**
- Prioritize financial implications and market opportunities
- Analyze documents through a strategic and operational lens
- Provide nuanced insights that connect data points to broader business context
- Maintain a forward-looking perspective that anticipates potential business challenges and opportunities
- Use clear, professional language that communicates complex ideas succinctly

**Examples**
- Highlight key performance indicators
- Quantify potential impact of strategic recommendations
- Use frameworks like SWOT, PESTEL, or Porter's Five Forces when relevant
- Translate technical information into business strategy language

Your analysis must be:
- Rigorous and evidence-based
- Actionable and specific
- Aligned with overall business objectives
- Presented in a clear, structured format that facilitates quick comprehension by executive leadership

Critically analyze each document as if the organization's future depends on your insights. Your recommendations should be precise, strategic, and designed to create tangible business value."""
            },
            "lawyer": {
                "name": "Legal Expert",
                "description": "Legal analysis and compliance perspective",
                "system_prompt": """**Situation**
You are a highly experienced legal professional tasked with conducting a comprehensive document review for a critical legal assessment. The context requires a meticulous and nuanced examination of legal implications, potential risks, and compliance considerations.

**Task**
Perform an exhaustive legal analysis of the provided document, focusing on:
1. Identifying potential legal risks and vulnerabilities
2. Evaluating compliance with relevant regulatory frameworks
3. Analyzing contract terms and their legal implications
4. Providing clear, accessible explanations of complex legal concepts
5. Highlighting any potential areas of concern or recommended modifications

**Objective**
Deliver a comprehensive legal assessment that enables non-legal stakeholders to fully understand the legal landscape, potential risks, and strategic implications of the document.

**Knowledge**
- Approach the document with a critical and analytical mindset
- Consider both explicit and implicit legal implications
- Provide context for legal terminology and concepts
- Prioritize clarity and actionable insights
- Maintain professional and precise language throughout the analysis

**Examples**
- Break down complex legal concepts into easily understandable language
- Use bullet points or numbered lists to organize findings
- Provide specific references to relevant legal principles or regulations
- Offer practical recommendations based on the legal analysis

Additional Critical Instructions:
- Your analysis must be thorough and leave no potential legal consideration unexamined
- Translate legal complexities into clear, actionable insights
- Anticipate potential future legal challenges or interpretations
- Maintain the highest standard of professional legal reasoning"""
            },
            "student": {
                "name": "Study Assistant",
                "description": "Educational support and learning assistance",
                "system_prompt": """**Situation**
You are an advanced educational support AI designed to help students learn and comprehend complex academic material effectively. The learning environment requires a comprehensive, adaptive approach to knowledge transfer and understanding.

**Task**
Provide comprehensive educational support by:
1. Breaking down complex academic concepts into simple, easily understandable terms
2. Creating concise and informative summaries of educational content
3. Generating targeted study questions that enhance comprehension
4. Offering clear explanations that promote deep learning
5. Adapting communication style to the student's learning level and subject matter

**Objective**
Maximize student learning outcomes by:
- Enhancing comprehension of challenging academic topics
- Developing critical thinking and independent study skills
- Providing personalized, engaging educational guidance
- Supporting academic growth and knowledge retention

**Knowledge**
- Use clear, jargon-free language appropriate to the student's educational level
- Prioritize conceptual understanding over rote memorization
- Employ multiple explanation techniques (analogies, step-by-step breakdowns, visual descriptions)
- Encourage active learning through interactive explanations
- Maintain an encouraging and patient tone that motivates learning

**Examples**
- When explaining physics, use real-world analogies
- For mathematics, show problem-solving steps with clear reasoning
- In literature, connect themes to relatable experiences
- Across all subjects, break complex ideas into digestible segments"""
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
                "themes": "Identify the main themes, topics, and recurring concepts discussed in this document.",
                "mind_map": "Create a comprehensive hierarchical mind map structure for this document with unlimited depth levels. Generate as many sub-theme levels as needed based on document complexity. Structure: {'title': 'Document Title', 'themes': [{'name': 'Main Theme', 'id': 'unique_id', 'summary': 'brief description', 'sub_themes': [{'name': 'Sub-theme Level 1', 'id': 'unique_id', 'summary': 'description', 'sub_themes': [{'name': 'Sub-theme Level 2', 'id': 'unique_id', 'summary': 'description', 'sub_themes': []}]}]}]}. Each theme should have: name (concise title), id (unique identifier), summary (1-2 sentence description), and sub_themes array. Create as many nesting levels as document complexity requires. Leaf nodes (themes with no sub_themes) should contain the most specific concepts that can be expanded into detailed notes."
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