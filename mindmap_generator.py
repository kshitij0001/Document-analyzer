# -*- coding: utf-8 -*-
# Mind Map Generator Module for Streamlit
# Based on https://github.com/Dicklesworthstone/mindmap-generator
# Adapted to work with existing OpenRouter API integration

import json
import re
import time
from typing import Dict, List, Optional, Any, Tuple
import streamlit as st

# Try to import fuzzywuzzy, use simple fallback if not available
try:
    from fuzzywuzzy import fuzz
    FUZZYWUZZY_AVAILABLE = True
except ImportError:
    FUZZYWUZZY_AVAILABLE = False
    # Simple fallback similarity function
    def fuzz_ratio(a, b):
        """Simple similarity ratio fallback"""
        a, b = a.lower().strip(), b.lower().strip()
        if a == b:
            return 100
        if a in b or b in a:
            return 80
        # Count common words
        words_a = set(a.split())
        words_b = set(b.split())
        if not words_a or not words_b:
            return 0
        common = len(words_a.intersection(words_b))
        total = len(words_a.union(words_b))
        return int((common / total) * 100) if total > 0 else 0

class MindMapGenerator:
    """
    Generate sophisticated mind maps from document content using AI analysis.
    Adapted from the Dicklesworthstone/mindmap-generator project for Streamlit integration.
    """
    
    def __init__(self, ai_client):
        """Initialize with the existing AI client."""
        self.ai_client = ai_client
        self.similarity_threshold = 75  # For detecting duplicates
        
        # Set up similarity function
        if FUZZYWUZZY_AVAILABLE:
            self.similarity_func = fuzz.ratio
        else:
            self.similarity_func = fuzz_ratio
        
    def generate_mind_map(self, document_text: str, document_titles: List[str] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive mind map from document content.
        
        Args:
            document_text (str): The combined document content
            document_titles (List[str]): List of document titles for context
            
        Returns:
            Dict: Complete mind map data structure
        """
        if not document_text.strip():
            return {"error": "No document content provided"}
            
        try:
            # Step 1: Extract main themes/topics
            with st.status("🔍 Analyzing document structure...", expanded=True) as status:
                st.write("Identifying main themes and topics...")
                main_themes = self._extract_main_themes(document_text, document_titles)
                
                if not main_themes:
                    return {"error": "Failed to extract main themes from document"}
                
                st.write(f"Found {len(main_themes)} main themes")
                
                # Step 2: Generate subtopics for each theme
                st.write("Extracting subtopics for each theme...")
                mind_map_data = {
                    "title": self._generate_title(document_titles),
                    "themes": []
                }
                
                for i, theme in enumerate(main_themes, 1):
                    st.write(f"Processing theme {i}/{len(main_themes)}: {theme['name']}")
                    
                    # Extract subtopics for this theme
                    subtopics = self._extract_subtopics(document_text, theme)
                    
                    theme_data = {
                        "id": f"theme_{i}",
                        "name": theme["name"],
                        "summary": theme["summary"],
                        "sub_themes": []
                    }
                    
                    # Process subtopics
                    for j, subtopic in enumerate(subtopics, 1):
                        subtopic_data = {
                            "id": f"theme_{i}_sub_{j}",
                            "name": subtopic["name"],
                            "summary": subtopic["summary"],
                            "sub_themes": []
                        }
                        
                        # Extract details for this subtopic (third level)
                        if len(subtopics) <= 5:  # Only go deeper if not too many subtopics
                            details = self._extract_details(document_text, theme, subtopic)
                            for k, detail in enumerate(details, 1):
                                detail_data = {
                                    "id": f"theme_{i}_sub_{j}_detail_{k}",
                                    "name": detail["name"],
                                    "summary": detail["summary"],
                                    "sub_themes": []
                                }
                                subtopic_data["sub_themes"].append(detail_data)
                        
                        theme_data["sub_themes"].append(subtopic_data)
                    
                    mind_map_data["themes"].append(theme_data)
                
                status.update(label="✅ Mind map generation completed!", state="complete")
                
            return mind_map_data
            
        except Exception as e:
            st.error(f"Error generating mind map: {str(e)}")
            return {"error": str(e)}
    
    def _extract_main_themes(self, document_text: str, document_titles: List[str] = None) -> List[Dict[str, str]]:
        """Extract main themes from the document using AI analysis."""
        
        context_info = ""
        if document_titles:
            context_info = f"Documents being analyzed: {', '.join(document_titles)}\n\n"
        
        prompt = f"""Analyze the following document(s) and identify 4-7 main themes or topics that capture the core content and structure.

{context_info}For each theme, provide:
1. A concise name (2-5 words)
2. A brief summary (1-2 sentences)

Return your response as a JSON array with this exact format:
[
  {{"name": "Theme Name", "summary": "Brief description of what this theme covers"}},
  {{"name": "Another Theme", "summary": "Description of this theme"}}
]

Document content:
{document_text[:4000]}"""  # Limit to prevent token overflow

        try:
            response = self.ai_client._make_api_request(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3
            )
            
            if response["success"]:
                # Try to parse JSON response
                content = response["content"].strip()
                
                # Extract JSON from response if it's wrapped in text
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    themes = json.loads(json_str)
                    
                    # Validate structure
                    valid_themes = []
                    for theme in themes:
                        if isinstance(theme, dict) and "name" in theme and "summary" in theme:
                            valid_themes.append(theme)
                    
                    return valid_themes
                
            # Fallback: extract themes from text response
            return self._fallback_theme_extraction(response.get("content", ""))
            
        except Exception as e:
            st.warning(f"AI theme extraction failed: {e}")
            return self._fallback_theme_extraction(document_text)
    
    def _extract_subtopics(self, document_text: str, theme: Dict[str, str]) -> List[Dict[str, str]]:
        """Extract subtopics for a specific theme."""
        
        prompt = f"""Based on the document content, identify 3-6 specific subtopics that fall under the theme: "{theme['name']}"

Theme description: {theme['summary']}

For each subtopic, provide:
1. A specific name (2-4 words)
2. A brief summary explaining what this subtopic covers

Return as JSON array:
[
  {{"name": "Subtopic Name", "summary": "What this subtopic covers"}},
  {{"name": "Another Subtopic", "summary": "Description"}}
]

Focus only on content that relates to: {theme['name']}

Document content:
{document_text[:3000]}"""

        try:
            response = self.ai_client._make_api_request(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3
            )
            
            if response["success"]:
                content = response["content"].strip()
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    subtopics = json.loads(json_str)
                    
                    valid_subtopics = []
                    for subtopic in subtopics:
                        if isinstance(subtopic, dict) and "name" in subtopic and "summary" in subtopic:
                            valid_subtopics.append(subtopic)
                    
                    return valid_subtopics[:6]  # Limit to 6 subtopics
            
            # Fallback
            return [{"name": f"{theme['name']} Details", "summary": f"Key details about {theme['name']}"}]
            
        except Exception:
            return [{"name": f"{theme['name']} Analysis", "summary": f"Analysis of {theme['name']}"}]
    
    def _extract_details(self, document_text: str, theme: Dict[str, str], subtopic: Dict[str, str]) -> List[Dict[str, str]]:
        """Extract specific details for a subtopic."""
        
        prompt = f"""Find 2-4 specific details, findings, or key points related to the subtopic "{subtopic['name']}" within the theme "{theme['name']}".

Subtopic focus: {subtopic['summary']}

Return as JSON array with specific, actionable details:
[
  {{"name": "Specific Detail", "summary": "Explanation of this detail"}},
  {{"name": "Key Finding", "summary": "What this finding means"}}
]

Document content:
{document_text[:2000]}"""

        try:
            response = self.ai_client._make_api_request(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.3
            )
            
            if response["success"]:
                content = response["content"].strip()
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    details = json.loads(json_str)
                    
                    valid_details = []
                    for detail in details:
                        if isinstance(detail, dict) and "name" in detail and "summary" in detail:
                            valid_details.append(detail)
                    
                    return valid_details[:4]  # Limit to 4 details
            
            return []  # Return empty if no valid details found
            
        except Exception:
            return []
    
    def _fallback_theme_extraction(self, text: str) -> List[Dict[str, str]]:
        """Fallback method to extract themes when AI parsing fails."""
        themes = []
        
        # Look for patterns that might indicate themes
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        potential_themes = []
        for line in lines:
            # Look for lines that seem like headings or important points
            if (len(line) > 10 and len(line) < 100 and 
                (line[0].isupper() or 
                 any(word in line.lower() for word in ['key', 'main', 'important', 'analysis', 'finding']) or
                 line.startswith(('1.', '2.', '3.', '4.', '5.', '-', '*')))):
                
                clean_line = re.sub(r'^[\d\.\-\*\s]+', '', line).strip()
                if len(clean_line) > 5:
                    potential_themes.append(clean_line)
        
        # Take the first few as themes
        for i, theme_text in enumerate(potential_themes[:6]):
            themes.append({
                "name": theme_text[:50] + ("..." if len(theme_text) > 50 else ""),
                "summary": f"Key topic extracted from document content"
            })
        
        # If no themes found, create generic ones
        if not themes:
            themes = [
                {"name": "Document Overview", "summary": "Main content and structure of the document"},
                {"name": "Key Points", "summary": "Important findings and conclusions"},
                {"name": "Analysis", "summary": "Analysis and interpretation of the content"}
            ]
        
        return themes
    
    def _generate_title(self, document_titles: List[str] = None) -> str:
        """Generate a title for the mind map."""
        if document_titles:
            if len(document_titles) == 1:
                return f"Mind Map: {document_titles[0]}"
            else:
                return f"Mind Map: {len(document_titles)} Documents"
        return "Document Mind Map"
    
    def export_to_mermaid(self, mind_map_data: Dict[str, Any]) -> str:
        """Export mind map to Mermaid syntax for interactive visualization."""
        if "error" in mind_map_data:
            return f"graph TD\n    A[Error: {mind_map_data['error']}]"
        
        mermaid_lines = ["graph TD"]
        mermaid_lines.append(f"    Root[\"{mind_map_data['title']}\"]")
        
        def add_node_to_mermaid(node_data: Dict, parent_id: str = "Root", level: int = 1):
            node_id = node_data["id"].replace("_", "")
            node_name = node_data["name"][:30] + ("..." if len(node_data["name"]) > 30 else "")
            
            # Add the node
            mermaid_lines.append(f"    {node_id}[\"{node_name}\"]")
            mermaid_lines.append(f"    {parent_id} --> {node_id}")
            
            # Add sub-themes recursively
            for sub_theme in node_data.get("sub_themes", []):
                add_node_to_mermaid(sub_theme, node_id, level + 1)
        
        # Add all themes
        for theme in mind_map_data.get("themes", []):
            add_node_to_mermaid(theme)
        
        return "\n".join(mermaid_lines)
    
    def export_to_markdown(self, mind_map_data: Dict[str, Any]) -> str:
        """Export mind map to markdown format."""
        if "error" in mind_map_data:
            return f"# Error\n\n{mind_map_data['error']}"
        
        markdown_lines = [f"# {mind_map_data['title']}", ""]
        
        def add_theme_to_markdown(theme_data: Dict, level: int = 1):
            indent = "#" * (level + 1)
            markdown_lines.append(f"{indent} {theme_data['name']}")
            markdown_lines.append(f"\n{theme_data['summary']}\n")
            
            for sub_theme in theme_data.get("sub_themes", []):
                add_theme_to_markdown(sub_theme, level + 1)
        
        for theme in mind_map_data.get("themes", []):
            add_theme_to_markdown(theme)
        
        return "\n".join(markdown_lines)