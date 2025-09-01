# -*- coding: utf-8 -*-

# Mind Map Generator Module for Streamlit
# Based on https://github.com/Dicklesworthstone/mindmap-generator
# Adapted to work with existing OpenRouter API integration

import json
import re
import time
from typing import Dict, List, Optional, Any, Tuple
import streamlit as st

# SVG Icon Component Function
def get_svg_icon(icon_name, size=16, color="currentColor"):
    """Generate SVG icons to replace emojis"""
    icons = {
        "refresh": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="m3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>',
        "rocket": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"></path><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"></path><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"></path><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"></path></svg>',
        "check": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>',
        "warning": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
        "info": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><ellipse cx="12" cy="5" rx="3" ry="3"></ellipse><path d="m2 13 20 6-6-20A20 20 0 0 0 2 13"></path><path d="M20 2c-4.6 5.5-6.3 11.2-5 17"></path></svg>'
    }
    return icons.get(icon_name, f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><circle cx="12" cy="12" r="10"></circle></svg>')

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
        Generate a comprehensive mind map from document content using optimized single API call.
        
        Args:
            document_text (str): The combined document content
            document_titles (List[str]): List of document titles for context
            
        Returns:
            Dict: Complete mind map data structure
        """
        if not document_text.strip():
            return {"error": "No document content provided"}
        
        try:
            with st.status("Generating mind map (optimized)...", expanded=True) as status:
                st.write("Creating comprehensive mind map structure...")
                
                # Generate complete mind map in ONE API call instead of 50+
                mind_map_data = self._generate_complete_mind_map(document_text, document_titles)
                
                if mind_map_data and "themes" in mind_map_data:
                    st.write(f"Generated {len(mind_map_data['themes'])} themes with subtopics")
                    status.update(label="Mind map completed in seconds!", state="complete")
                    return mind_map_data
                else:
                    # Fallback to original method if optimized version fails
                    st.write("Falling back to detailed analysis...")
                    return self._generate_mind_map_fallback(document_text, document_titles)
                    
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

    def _generate_complete_mind_map(self, document_text: str, document_titles: List[str] = None) -> Dict[str, Any]:
        """FIXED: Generate complete mind map structure with enhanced large document support."""
        
        context_info = ""
        if document_titles:
            context_info = f"Analyzing: {', '.join(document_titles)}\n\n"
        
        # Enhanced document processing for large files
        max_content_length = 15000  # Increased from 8000
        
        if len(document_text) > max_content_length:
            st.info(f"Large document detected ({len(document_text):,} characters). Using intelligent sampling...", icon="ℹ️")
            
            # Intelligent sampling strategy
            sample_size = max_content_length // 4
            samples = []
            
            # Strategic samples from different parts
            samples.append(document_text[:sample_size])  # Beginning
            samples.append(document_text[len(document_text)//4:len(document_text)//4 + sample_size])  # Quarter
            samples.append(document_text[len(document_text)//2:len(document_text)//2 + sample_size])  # Middle  
            samples.append(document_text[-sample_size:])  # End
            
            processed_text = "\n\n[DOCUMENT SECTION]\n\n".join(samples)
        else:
            processed_text = document_text
        
        # Enhanced prompt with clearer instructions
        prompt = f"""Analyze the document content and create a detailed mind map structure.

IMPORTANT: Return ONLY the JSON object, no explanations.

{{
  "title": "Document Mind Map",
  "themes": [
    {{
      "id": "theme_1", 
      "name": "Theme Name",
      "summary": "Brief description",
      "sub_themes": [
        {{
          "id": "theme_1_sub_1",
          "name": "Subtopic Name",
          "summary": "Brief description", 
          "sub_themes": []
        }}
      ]
    }}
  ]
}}

Instructions:
- Create 4-6 main themes based on actual document content
- Each theme should have 2-4 meaningful subtopics
- Keep names under 40 characters
- Keep summaries under 100 characters
- Ensure perfect JSON syntax

{context_info}Document Content:
{processed_text}"""

        # Multiple attempts with progressive parameters
        for attempt in range(3):
            try:
                temperature = 0.05 + (attempt * 0.05)
                max_tokens = 4000 + (attempt * 500)
                
                response = self.ai_client._make_api_request(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                if response["success"]:
                    content = response["content"].strip()
                    mind_map = self._process_json_response(content, attempt + 1)
                    if mind_map:
                        return mind_map
                        
            except Exception as e:
                st.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                continue
        
        # Fallback method
        st.warning("Optimized generation failed, using fallback method...", icon="⚠")
        return self._generate_mind_map_fallback(document_text, document_titles)

    def _process_json_response(self, content: str, attempt_num: int) -> Dict[str, Any]:
        """Process JSON response with multiple repair strategies"""
        
        # Strategy 1: Clean and direct parse
        try:
            cleaned_content = self._enhanced_json_cleaning(content)
            mind_map = json.loads(cleaned_content)
            if self._validate_and_fix_mind_map_structure(mind_map):
                return mind_map
        except:
            pass
        
        # Strategy 2: Aggressive repair
        try:
            repaired_content = self._aggressive_json_repair(content)
            if repaired_content:
                mind_map = json.loads(repaired_content)
                if self._validate_and_fix_mind_map_structure(mind_map):
                    return mind_map
        except:
            pass
        
        return None

    def _enhanced_json_cleaning(self, content: str) -> str:
        """Enhanced JSON cleaning with better error handling"""
        # Remove code blocks
        content = re.sub(r'```(?:json)?\s*', '', content, flags=re.IGNORECASE)
        content = re.sub(r'```\s*$', '', content, flags=re.MULTILINE)
        
        # Find JSON boundaries accurately  
        start_idx = content.find('{')
        if start_idx > 0:
            content = content[start_idx:]
        
        # Balance braces
        brace_count = 0
        end_idx = -1
        
        for i, char in enumerate(content):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i
                    break
        
        if end_idx != -1:
            content = content[:end_idx + 1]
        
        # Fix common JSON issues
        content = re.sub(r',\s*([}\]])', r'\1', content)  # Trailing commas
        content = re.sub(r'"([^"]*)"([^",:}\]]*)"', r'"\1\2"', content)  # Broken quotes
        
        return content.strip()

    def _aggressive_json_repair(self, content: str) -> str:
        """More aggressive JSON repair for malformed content"""
        
        # Remove everything before first {
        start_idx = content.find('{')
        if start_idx > 0:
            content = content[start_idx:]
        
        # Remove everything after last }
        end_idx = content.rfind('}')
        if end_idx != -1:
            content = content[:end_idx + 1]
        
        # Apply multiple repair patterns
        repairs = [
            (r'"([^"]*)"([^",:}\]]*)"([^",:}\]]*)"', r'"\1\2\3"'),  # Fix broken quotes
            (r',\s*([}\]])', r'\1'),  # Remove trailing commas
            (r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*):',  r'\1"\2":'),  # Quote unquoted keys
        ]
        
        for pattern, replacement in repairs:
            content = re.sub(pattern, replacement, content)
        
        return content

    def _clean_json_response(self, content: str) -> str:
        """Clean AI response to extract valid JSON."""
        # Remove markdown code blocks
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        
        # Remove any text before first {
        start_idx = content.find('{')
        if start_idx > 0:
            content = content[start_idx:]
        
        # Remove any text after last }
        end_idx = content.rfind('}')
        if end_idx != -1:
            content = content[:end_idx + 1]
        
        return content.strip()

    def _fix_json_issues(self, json_str: str) -> str:
        """Fix common JSON formatting issues."""
        # Fix single quotes to double quotes
        json_str = re.sub(r"'([^']*)':", r'"\1":', json_str)
        json_str = re.sub(r":\s*'([^']*)'", r': "\1"', json_str)
        
        # Remove trailing commas before } and ]
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # Fix unescaped quotes in strings
        json_str = re.sub(r':\s*"([^"]*)"([^",}\]]*)"([^",}\]]*)"', r': "\1\2\3"', json_str)
        
        # Ensure proper comma placement
        json_str = re.sub(r'}\s*{', r'}, {', json_str)
        json_str = re.sub(r']\s*\[', r'], [', json_str)
        
        return json_str

    def _emergency_json_fix(self, json_str: str) -> str:
        """Emergency JSON fix for severely malformed JSON."""
        try:
            # Count braces and brackets to ensure they're balanced
            open_braces = json_str.count('{')
            close_braces = json_str.count('}')
            open_brackets = json_str.count('[')
            close_brackets = json_str.count(']')
            
            # Add missing closing braces/brackets
            if open_braces > close_braces:
                json_str += '}' * (open_braces - close_braces)
            if open_brackets > close_brackets:
                json_str += ']' * (open_brackets - close_brackets)
            
            # Remove extra closing braces/brackets
            if close_braces > open_braces:
                for _ in range(close_braces - open_braces):
                    json_str = json_str.rsplit('}', 1)[0]
            if close_brackets > open_brackets:
                for _ in range(close_brackets - open_brackets):
                    json_str = json_str.rsplit(']', 1)[0]
            
            return json_str
        except:
            return None

    def _validate_and_fix_mind_map_structure(self, mind_map: Dict) -> bool:
        """Validate and fix mind map structure."""
        try:
            # Ensure required keys exist
            if "title" not in mind_map:
                mind_map["title"] = "Document Mind Map"
                
            if "themes" not in mind_map:
                mind_map["themes"] = []
                
            if not isinstance(mind_map["themes"], list):
                mind_map["themes"] = []
            
            # Fix each theme structure
            fixed_themes = []
            for i, theme in enumerate(mind_map["themes"]):
                if not isinstance(theme, dict):
                    continue
                
                # Ensure theme has required fields
                fixed_theme = {
                    "id": theme.get("id", f"theme_{i+1}"),
                    "name": str(theme.get("name", f"Theme {i+1}"))[:100],  # Limit length
                    "summary": str(theme.get("summary", "Analysis theme"))[:200],  # Limit length
                    "sub_themes": []
                }
                
                # Fix sub-themes
                if "sub_themes" in theme and isinstance(theme["sub_themes"], list):
                    for j, sub_theme in enumerate(theme["sub_themes"]):
                        if isinstance(sub_theme, dict):
                            fixed_sub_theme = {
                                "id": sub_theme.get("id", f"theme_{i+1}_sub_{j+1}"),
                                "name": str(sub_theme.get("name", f"Subtopic {j+1}"))[:100],
                                "summary": str(sub_theme.get("summary", "Analysis subtopic"))[:200],
                                "sub_themes": sub_theme.get("sub_themes", [])
                            }
                            fixed_theme["sub_themes"].append(fixed_sub_theme)
                
                fixed_themes.append(fixed_theme)
            
            mind_map["themes"] = fixed_themes
            
            # Ensure we have at least one theme
            if len(mind_map["themes"]) == 0:
                mind_map["themes"].append({
                    "id": "theme_1",
                    "name": "Document Analysis",
                    "summary": "Key insights from the document",
                    "sub_themes": []
                })
            
            return True
            
        except Exception as e:
            st.warning(f"Structure validation failed: {e}")
            return False

    def _generate_mind_map_fallback(self, document_text: str, document_titles: List[str] = None) -> Dict[str, Any]:
        """Fallback method using original approach but optimized."""
        # Simplified fallback - fewer API calls
        main_themes = self._extract_main_themes(document_text, document_titles)
        
        if not main_themes:
            return {"error": "Failed to extract themes"}
        
        mind_map_data = {
            "title": self._generate_title(document_titles),
            "themes": []
        }
        
        # Process only top 5 themes for speed
        for i, theme in enumerate(main_themes[:5], 1):
            theme_data = {
                "id": f"theme_{i}",
                "name": theme["name"],
                "summary": theme["summary"],
                "sub_themes": []
            }
            
            # Generate simple subtopics without deep details
            subtopics = self._extract_subtopics(document_text, theme)
            for j, subtopic in enumerate(subtopics[:4], 1):  # Limit to 4 subtopics
                subtopic_data = {
                    "id": f"theme_{i}_sub_{j}",
                    "name": subtopic["name"],
                    "summary": subtopic["summary"],
                    "sub_themes": []  # Skip details for speed
                }
                theme_data["sub_themes"].append(subtopic_data)
            
            mind_map_data["themes"].append(theme_data)
        
        return mind_map_data

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
            return f"graph TD\n A[Error: {mind_map_data['error']}]"
        
        mermaid_lines = ["graph TD"]
        
        # Clean title and ensure mermaid compatibility
        clean_title = mind_map_data['title'][:35].replace('"', "'")
        mermaid_lines.append(f"    Root[\"{clean_title}\"]")
        
        def add_node_to_mermaid(node_data: Dict, parent_id: str = "Root", level: int = 1):
            # Create safer node ID - replace problematic characters and ensure uniqueness
            base_id = re.sub(r'[^a-zA-Z0-9]', '', node_data["id"])
            node_id = f"N{level}_{base_id[:10]}" if level > 0 else base_id[:10]
            
            # Clean node name and escape quotes
            node_name = node_data["name"][:25].replace('"', "'") + ("..." if len(node_data["name"]) > 25 else "")
            
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