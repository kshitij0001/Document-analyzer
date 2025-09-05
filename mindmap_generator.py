# -*- coding: utf-8 -*-

# Simplified Mind Map Generator for Streamlit
# Tree view and markdown export only

import json
import re
import time
from typing import Dict, List, Optional, Any
import streamlit as st
from dataclasses import dataclass
import hashlib

@dataclass
class MindMapTheme:
    """Represents a theme in the mind map"""
    id: str
    name: str
    summary: str
    importance: float = 0.5
    keywords: Optional[List[str]] = None
    subtopics: Optional[List['MindMapSubtopic']] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.subtopics is None:
            self.subtopics = []

@dataclass
class MindMapSubtopic:
    """Represents a subtopic in the mind map"""
    id: str
    name: str
    summary: str
    importance: float = 0.5
    keywords: Optional[List[str]] = None
    details: Optional[List['MindMapDetail']] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.details is None:
            self.details = []

@dataclass
class MindMapDetail:
    """Represents a detail in the mind map"""
    id: str
    name: str
    summary: str
    importance: float = 0.5

class MindMapGenerator:
    """
    Simplified mind map generator with tree view and markdown export
    """
    
    def __init__(self, ai_client):
        """Initialize with AI client"""
        self.ai_client = ai_client
    
    def generate_mind_map(self, document_text: str, document_titles: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive mind map from document content
        
        Args:
            document_text (str): The combined document content
            document_titles (List[str]): List of document titles for context
            
        Returns:
            Dict: Complete mind map data structure
        """
        if not document_text.strip():
            return {"error": "No document content provided"}
        
        try:
            with st.status("Generating mind map...", expanded=True) as status:
                
                # Step 1: Extract structured data
                st.write("Analyzing document structure...")
                structured_data = self._extract_structured_data(document_text, document_titles)
                
                if not structured_data or "error" in structured_data:
                    return {"error": "Failed to extract structured data from document"}
                
                # Step 2: Convert to themes format
                st.write("Building knowledge structure...")
                themes = self._convert_to_themes_format(structured_data)
                
                # Step 3: Prepare final data structure
                mind_map_data = {
                    "title": structured_data.get("title", "Document Mind Map"),
                    "themes": themes,
                    "statistics": self._generate_statistics(themes)
                }
                
                st.write(f"Generated mind map with {len(themes)} themes")
                status.update(label="Mind map generation complete!", state="complete")
                
                return mind_map_data
                
        except Exception as e:
            st.error(f"Error generating mind map: {str(e)}")
            return {"error": str(e)}
    
    def _extract_structured_data(self, document_text: str, document_titles: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Extract structured data using AI analysis"""
        
        context_info = ""
        if document_titles:
            context_info = f"Document(s): {', '.join(document_titles)}\n\n"
        
        # Handle large documents with intelligent sampling
        max_content_length = 20000
        if len(document_text) > max_content_length:
            st.info(f"Large document detected ({len(document_text):,} characters). Using intelligent sampling...")
            processed_text = self._intelligent_document_sampling(document_text, max_content_length)
        else:
            processed_text = document_text
        
        # Enhanced prompt for better structure extraction
        prompt = f"""You are an expert knowledge analyst. Analyze the document content and create a comprehensive knowledge structure.

Generate a JSON response with this EXACT format:

{{
  "title": "Document Knowledge Map",
  "main_themes": [
    {{
      "id": "theme_1",
      "name": "Theme Name (max 40 chars)",
      "summary": "2-3 sentence summary of this theme",
      "importance": 0.9,
      "keywords": ["keyword1", "keyword2", "keyword3"],
      "subtopics": [
        {{
          "id": "theme_1_sub_1",
          "name": "Subtopic Name (max 30 chars)",
          "summary": "1-2 sentence explanation",
          "importance": 0.7,
          "keywords": ["word1", "word2"],
          "details": [
            {{
              "id": "theme_1_sub_1_det_1", 
              "name": "Specific Detail (max 25 chars)",
              "summary": "Brief explanation",
              "importance": 0.5
            }}
          ]
        }}
      ]
    }}
  ]
}}

Instructions:
- Generate 4-6 main themes based on actual content
- Each theme should have 2-4 meaningful subtopics  
- Each subtopic can have 1-3 specific details
- Importance scores: 0.9+ (critical), 0.7+ (important), 0.5+ (relevant)
- Keywords should be actual terms from the document
- Return ONLY valid JSON, no explanations

{context_info}Document Content:
{processed_text}"""

        # Multiple attempts with different parameters
        for attempt in range(3):
            try:
                temperature = 0.1 + (attempt * 0.1)
                max_tokens = 5000 + (attempt * 1000)
                
                response = self.ai_client._make_api_request(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                if response["success"]:
                    structured_data = self._process_structured_response(response["content"])
                    if structured_data:
                        return structured_data
                        
            except Exception as e:
                st.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                continue
        
        # Fallback method
        return self._fallback_structure_extraction(document_text, document_titles)
    
    def _intelligent_document_sampling(self, document_text: str, max_length: int) -> str:
        """Intelligent sampling for large documents"""
        
        # Strategy: Take samples from different parts to capture full context
        sample_size = max_length // 5
        samples = []
        
        # Beginning (introduction/overview)
        samples.append(document_text[:sample_size])
        
        # Distributed samples from middle sections
        doc_length = len(document_text)
        for i in range(1, 4):
            start_pos = (doc_length * i) // 4
            end_pos = start_pos + sample_size
            samples.append(document_text[start_pos:end_pos])
        
        # End (conclusions/summary)
        samples.append(document_text[-sample_size:])
        
        return "\n\n[DOCUMENT SECTION BREAK]\n\n".join(samples)
    
    def _process_structured_response(self, content: str) -> Dict[str, Any]:
        """Process and validate structured response from AI"""
        
        try:
            # Clean the content
            cleaned_content = self._clean_json_response(content)
            
            # Parse JSON
            data = json.loads(cleaned_content)
            
            # Validate structure
            if self._validate_structured_data(data):
                return data
            else:
                return {"error": "Failed to validate structured data"}
                
        except json.JSONDecodeError as e:
            st.warning(f"JSON parsing error: {e}")
            # Try aggressive cleaning
            repaired_content = self._repair_json_content(content)
            if repaired_content:
                try:
                    data = json.loads(repaired_content)
                    if self._validate_structured_data(data):
                        return data
                except:
                    pass
            return {"error": "JSON processing failed"}
        except Exception as e:
            st.warning(f"Structure processing error: {e}")
            return {"error": f"Structure processing error: {e}"}
    
    def _clean_json_response(self, content: str) -> str:
        """Clean AI response to extract valid JSON"""
        
        # Remove markdown code blocks
        content = re.sub(r'```json\s*', '', content, flags=re.IGNORECASE)
        content = re.sub(r'```\s*', '', content)
        
        # Find JSON boundaries
        start_idx = content.find('{')
        if start_idx == -1:
            raise ValueError("No JSON object found")
        
        # Find matching closing brace
        brace_count = 0
        end_idx = -1
        for i, char in enumerate(content[start_idx:], start_idx):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i
                    break
        
        if end_idx == -1:
            raise ValueError("Unmatched JSON braces")
        
        return content[start_idx:end_idx + 1]
    
    def _repair_json_content(self, content: str) -> Optional[str]:
        """Attempt to repair malformed JSON"""
        
        try:
            # Basic repairs
            content = re.sub(r',\s*([}\]])', r'\1', content)  # Remove trailing commas
            content = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', content)  # Quote keys
            
            # Fix common quote issues
            content = re.sub(r':\s*"([^"]*)"([^",}\]]*)"', r': "\1\2"', content)
            
            return content
            
        except Exception:
            return None
    
    def _validate_structured_data(self, data: Dict) -> bool:
        """Validate the structure of extracted data"""
        
        try:
            # Check required fields
            if not isinstance(data, dict):
                return False
            
            if "main_themes" not in data or not isinstance(data["main_themes"], list):
                return False
            
            # Validate themes structure
            for theme in data["main_themes"]:
                if not isinstance(theme, dict):
                    return False
                
                required_fields = ["id", "name", "summary"]
                for field in required_fields:
                    if field not in theme:
                        return False
                
                # Validate subtopics if present
                if "subtopics" in theme:
                    for subtopic in theme["subtopics"]:
                        if not isinstance(subtopic, dict):
                            return False
                        
                        for field in required_fields:
                            if field not in subtopic:
                                return False
            
            return True
            
        except Exception:
            return False
    
    def _convert_to_themes_format(self, structured_data: Dict) -> List[Dict]:
        """Convert structured data to themes format"""
        
        themes = []
        for theme_data in structured_data.get("main_themes", []):
            theme = {
                "id": theme_data["id"],
                "name": theme_data["name"],
                "summary": theme_data["summary"],
                "importance": theme_data.get("importance", 0.8),
                "keywords": theme_data.get("keywords", []),
                "subtopics": []
            }
            
            # Process subtopics
            for subtopic_data in theme_data.get("subtopics", []):
                subtopic = {
                    "id": subtopic_data["id"],
                    "name": subtopic_data["name"],
                    "summary": subtopic_data["summary"],
                    "importance": subtopic_data.get("importance", 0.6),
                    "keywords": subtopic_data.get("keywords", []),
                    "details": []
                }
                
                # Process details
                for detail_data in subtopic_data.get("details", []):
                    detail = {
                        "id": detail_data["id"],
                        "name": detail_data["name"],
                        "summary": detail_data["summary"],
                        "importance": detail_data.get("importance", 0.4)
                    }
                    subtopic["details"].append(detail)
                
                theme["subtopics"].append(subtopic)
            
            themes.append(theme)
        
        return themes
    
    def _generate_statistics(self, themes: List[Dict]) -> Dict:
        """Generate statistics about the mind map"""
        
        total_themes = len(themes)
        total_subtopics = sum(len(theme.get("subtopics", [])) for theme in themes)
        total_details = sum(
            sum(len(subtopic.get("details", [])) for subtopic in theme.get("subtopics", []))
            for theme in themes
        )
        
        return {
            "total_themes": total_themes,
            "total_subtopics": total_subtopics,
            "total_details": total_details,
            "total_nodes": total_themes + total_subtopics + total_details
        }
    
    def _fallback_structure_extraction(self, document_text: str, document_titles: Optional[List[str]] = None) -> Dict:
        """Fallback method for structure extraction"""
        
        st.warning("Using fallback structure extraction method")
        
        # Simple fallback - create basic structure
        title = "Document Analysis" if not document_titles else document_titles[0]
        
        return {
            "title": title,
            "main_themes": [{
                "id": "theme_1",
                "name": "Main Content",
                "summary": "Primary content from the document",
                "importance": 0.8,
                "keywords": ["content", "document", "analysis"],
                "subtopics": [{
                    "id": "theme_1_sub_1",
                    "name": "Key Points",
                    "summary": "Important points identified in the document",
                    "importance": 0.6,
                    "keywords": ["points", "key", "important"],
                    "details": [{
                        "id": "theme_1_sub_1_det_1",
                        "name": "Document Summary",
                        "summary": document_text[:200] + "..." if len(document_text) > 200 else document_text,
                        "importance": 0.5
                    }]
                }]
            }]
        }
    
    def export_to_markdown(self, mind_map_data: Dict) -> str:
        """Export mind map to markdown format"""
        
        if "error" in mind_map_data:
            return f"# Error\n\n{mind_map_data['error']}"
        
        markdown = f"# {mind_map_data.get('title', 'Mind Map')}\n\n"
        
        # Add statistics
        stats = mind_map_data.get('statistics', {})
        if stats:
            markdown += "## Overview\n\n"
            markdown += f"- **Themes:** {stats.get('total_themes', 0)}\n"
            markdown += f"- **Subtopics:** {stats.get('total_subtopics', 0)}\n"
            markdown += f"- **Details:** {stats.get('total_details', 0)}\n\n"
        
        # Add themes
        for theme in mind_map_data.get("themes", []):
            markdown += f"## {theme['name']}\n\n"
            markdown += f"{theme['summary']}\n\n"
            
            if theme.get('keywords'):
                markdown += f"**Keywords:** {', '.join(theme['keywords'])}\n\n"
            
            # Add subtopics
            for subtopic in theme.get("subtopics", []):
                markdown += f"### {subtopic['name']}\n\n"
                markdown += f"{subtopic['summary']}\n\n"
                
                if subtopic.get('keywords'):
                    markdown += f"**Keywords:** {', '.join(subtopic['keywords'])}\n\n"
                
                # Add details
                for detail in subtopic.get("details", []):
                    markdown += f"#### {detail['name']}\n\n"
                    markdown += f"{detail['summary']}\n\n"
        
        return markdown