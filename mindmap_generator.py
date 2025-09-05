# -*- coding: utf-8 -*-

# NotebookLM-Style Mind Map Generator for Streamlit
# Enhanced version with interactive visualizations and modern UI

import json
import re
import time
import uuid
from typing import Dict, List, Optional, Any, Tuple
import streamlit as st
import networkx as nx
from dataclasses import dataclass
import hashlib

# Try to import visualization libraries
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    go = None
    px = None

try:
    import pyvis.network as net
    PYVIS_AVAILABLE = True
except ImportError:
    PYVIS_AVAILABLE = False

@dataclass
class MindMapNode:
    """Represents a node in the mind map"""
    id: str
    name: str
    summary: str
    level: int
    parent_id: Optional[str] = None
    children: Optional[List[str]] = None
    node_type: str = "topic"  # topic, subtopic, detail
    importance: float = 0.5  # 0-1 scale
    keywords: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.keywords is None:
            self.keywords = []

class NotebookLMMindMapGenerator:
    """
    NotebookLM-style mind map generator with interactive visualizations
    """
    
    def __init__(self, ai_client):
        """Initialize with AI client"""
        self.ai_client = ai_client
        self.nodes = {}
        self.edges = []
        self.max_depth = 3
        self.color_palette = {
            0: "#FF6B6B",  # Red for main topics
            1: "#4ECDC4",  # Teal for subtopics  
            2: "#45B7D1",  # Blue for details
            3: "#96CEB4"   # Green for specifics
        }
    
    def generate_mind_map(self, document_text: str, document_titles: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive mind map from document content
        
        Args:
            document_text (str): The combined document content
            document_titles (List[str]): List of document titles for context
            
        Returns:
            Dict: Complete mind map data structure with nodes and visualization data
        """
        if not document_text.strip():
            return {"error": "No document content provided"}
        
        try:
            with st.status("🧠 Generating NotebookLM-style mind map...", expanded=True) as status:
                
                # Step 1: Extract structured data
                st.write("🔍 Analyzing document structure...")
                structured_data = self._extract_structured_data(document_text, document_titles)
                
                if not structured_data or "error" in structured_data:
                    return {"error": "Failed to extract structured data from document"}
                
                # Step 2: Build node graph
                st.write("🌐 Building knowledge graph...")
                self._build_node_graph(structured_data)
                
                # Step 3: Generate visualizations
                st.write("🎨 Creating interactive visualizations...")
                visualizations = self._generate_visualizations()
                
                # Step 4: Prepare final data structure
                mind_map_data = {
                    "title": structured_data.get("title", "Document Mind Map"),
                    "nodes": {node_id: self._node_to_dict(node) for node_id, node in self.nodes.items()},
                    "edges": self.edges,
                    "visualizations": visualizations,
                    "statistics": self._generate_statistics(),
                    "export_formats": ["json", "markdown", "mermaid", "graphml"]
                }
                
                st.write(f"✅ Generated mind map with {len(self.nodes)} nodes and {len(self.edges)} connections")
                status.update(label="✅ Mind map generation complete!", state="complete")
                
                return mind_map_data
                
        except Exception as e:
            st.error(f"Error generating mind map: {str(e)}")
            return {"error": str(e)}
    
    def _extract_structured_data(self, document_text: str, document_titles: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Extract structured data using advanced AI analysis"""
        
        context_info = ""
        if document_titles:
            context_info = f"Document(s): {', '.join(document_titles)}\n\n"
        
        # Handle large documents with intelligent sampling
        max_content_length = 20000
        if len(document_text) > max_content_length:
            st.info(f"📄 Large document detected ({len(document_text):,} characters). Using intelligent sampling...")
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
  ],
  "connections": [
    {{"from": "theme_1", "to": "theme_2", "relationship": "relates_to", "strength": 0.6}}
  ]
}}

Instructions:
- Generate 4-6 main themes based on actual content
- Each theme should have 2-4 meaningful subtopics  
- Each subtopic can have 1-3 specific details
- Importance scores: 0.9+ (critical), 0.7+ (important), 0.5+ (relevant)
- Keywords should be actual terms from the document
- Connections show relationships between themes
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
    
    def _build_node_graph(self, structured_data: Dict):
        """Build the node graph from structured data"""
        
        self.nodes = {}
        self.edges = []
        
        # Create root node
        root_id = "root"
        root_node = MindMapNode(
            id=root_id,
            name=structured_data.get("title", "Document Mind Map"),
            summary="Root node of the knowledge map",
            level=0,
            node_type="root",
            importance=1.0
        )
        self.nodes[root_id] = root_node
        
        # Process main themes
        for theme_data in structured_data.get("main_themes", []):
            theme_node = self._create_theme_node(theme_data, root_id)
            self.nodes[theme_node.id] = theme_node
            self.edges.append({
                "from": root_id,
                "to": theme_node.id,
                "relationship": "contains",
                "strength": 1.0
            })
            
            # Process subtopics
            for subtopic_data in theme_data.get("subtopics", []):
                subtopic_node = self._create_subtopic_node(subtopic_data, theme_node.id)
                self.nodes[subtopic_node.id] = subtopic_node
                self.edges.append({
                    "from": theme_node.id,
                    "to": subtopic_node.id,
                    "relationship": "contains", 
                    "strength": 0.8
                })
                
                # Process details
                for detail_data in subtopic_data.get("details", []):
                    detail_node = self._create_detail_node(detail_data, subtopic_node.id)
                    self.nodes[detail_node.id] = detail_node
                    self.edges.append({
                        "from": subtopic_node.id,
                        "to": detail_node.id,
                        "relationship": "contains",
                        "strength": 0.6
                    })
        
        # Add cross-connections
        for connection in structured_data.get("connections", []):
            if connection["from"] in self.nodes and connection["to"] in self.nodes:
                self.edges.append({
                    "from": connection["from"],
                    "to": connection["to"],
                    "relationship": connection.get("relationship", "relates_to"),
                    "strength": connection.get("strength", 0.5)
                })
    
    def _create_theme_node(self, theme_data: Dict, parent_id: str) -> MindMapNode:
        """Create a theme node"""
        return MindMapNode(
            id=theme_data["id"],
            name=theme_data["name"][:40],
            summary=theme_data["summary"],
            level=1,
            parent_id=parent_id,
            node_type="theme",
            importance=theme_data.get("importance", 0.8),
            keywords=theme_data.get("keywords", [])
        )
    
    def _create_subtopic_node(self, subtopic_data: Dict, parent_id: str) -> MindMapNode:
        """Create a subtopic node"""
        return MindMapNode(
            id=subtopic_data["id"],
            name=subtopic_data["name"][:30],
            summary=subtopic_data["summary"],
            level=2,
            parent_id=parent_id,
            node_type="subtopic",
            importance=subtopic_data.get("importance", 0.6),
            keywords=subtopic_data.get("keywords", [])
        )
    
    def _create_detail_node(self, detail_data: Dict, parent_id: str) -> MindMapNode:
        """Create a detail node"""
        return MindMapNode(
            id=detail_data["id"],
            name=detail_data["name"][:25],
            summary=detail_data["summary"],
            level=3,
            parent_id=parent_id,
            node_type="detail",
            importance=detail_data.get("importance", 0.4)
        )
    
    def _generate_visualizations(self) -> Dict[str, Any]:
        """Generate different visualization formats"""
        
        visualizations = {}
        
        # 1. Interactive Network Graph (Plotly)
        if PLOTLY_AVAILABLE:
            visualizations["network_graph"] = self._create_network_graph()
            visualizations["hierarchical_tree"] = self._create_hierarchical_tree()
            visualizations["circular_layout"] = self._create_circular_layout()
        
        # 2. HTML/JS Interactive Visualization
        visualizations["interactive_html"] = self._create_interactive_html()
        
        # 3. Mermaid Diagram
        visualizations["mermaid"] = self._create_mermaid_diagram()
        
        return visualizations
    
    def _create_network_graph(self) -> Dict:
        """Create interactive network graph using Plotly"""
        
        if not PLOTLY_AVAILABLE or go is None:
            return {"error": "Plotly not available"}
        
        # Create networkx graph
        G = nx.DiGraph()
        
        # Add nodes
        for node_id, node in self.nodes.items():
            G.add_node(node_id, 
                      label=node.name,
                      summary=node.summary,
                      level=node.level,
                      importance=node.importance,
                      node_type=node.node_type)
        
        # Add edges
        for edge in self.edges:
            G.add_edge(edge["from"], edge["to"], 
                      relationship=edge["relationship"],
                      strength=edge["strength"])
        
        # Generate layout
        pos = nx.spring_layout(G, k=3, iterations=50, seed=42)
        
        # Create traces for nodes
        node_traces = []
        for level in range(4):
            level_nodes = [n for n in G.nodes() if G.nodes[n]['level'] == level]
            if not level_nodes:
                continue
                
            node_x = [pos[node][0] for node in level_nodes]
            node_y = [pos[node][1] for node in level_nodes]
            node_text = [G.nodes[node]['label'] for node in level_nodes]
            node_hover = [f"<b>{G.nodes[node]['label']}</b><br>{G.nodes[node]['summary']}" 
                         for node in level_nodes]
            node_sizes = [max(20, G.nodes[node]['importance'] * 40) for node in level_nodes]
            
            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text',
                text=node_text,
                textposition='middle center',
                hovertext=node_hover,
                hoverinfo='text',
                marker=dict(
                    size=node_sizes,
                    color=self.color_palette.get(level, '#CCCCCC'),
                    line=dict(width=2, color='white')
                ),
                name=f"Level {level}",
                textfont=dict(size=10, color='white')
            )
            node_traces.append(node_trace)
        
        # Create edge trace
        edge_x, edge_y = [], []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='rgba(125,125,125,0.5)'),
            hoverinfo='none',
            mode='lines',
            showlegend=False
        )
        
        # Create figure
        fig = go.Figure(data=[edge_trace] + node_traces,
                       layout=go.Layout(
                           title="Interactive Knowledge Network",
                           showlegend=True,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           annotations=[ dict(
                               text="Drag nodes to explore connections",
                               showarrow=False,
                               xref="paper", yref="paper",
                               x=0.005, y=-0.002,
                               xanchor="left", yanchor="bottom",
                               font=dict(color="#888888", size=12)
                           )],
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           plot_bgcolor='white',
                           height=600
                       ))
        
        return {"figure": fig, "type": "plotly"}
    
    def _create_hierarchical_tree(self) -> Dict:
        """Create hierarchical tree layout"""
        
        if not PLOTLY_AVAILABLE or go is None:
            return {"error": "Plotly not available"}
        
        # Build tree structure
        tree_data = self._build_tree_structure()
        
        fig = go.Figure(go.Treemap(
            ids=[node["id"] for node in tree_data],
            labels=[node["name"] for node in tree_data],
            parents=[node["parent"] for node in tree_data],
            values=[node["importance"] for node in tree_data],
            textinfo="label+value",
            hovertemplate='<b>%{label}</b><br>Importance: %{value}<extra></extra>',
            maxdepth=4,
            pathbar_thickness=20
        ))
        
        fig.update_layout(
            title="Hierarchical Knowledge Structure",
            font_size=12,
            height=500
        )
        
        return {"figure": fig, "type": "plotly"}
    
    def _create_circular_layout(self) -> Dict:
        """Create circular/radial layout"""
        
        if not PLOTLY_AVAILABLE or go is None:
            return {"error": "Plotly not available"}
        
        # Create sunburst chart
        tree_data = self._build_tree_structure()
        
        fig = go.Figure(go.Sunburst(
            ids=[node["id"] for node in tree_data],
            labels=[node["name"] for node in tree_data],
            parents=[node["parent"] for node in tree_data],
            values=[node["importance"] for node in tree_data],
            hovertemplate='<b>%{label}</b><br>%{text}<extra></extra>',
            maxdepth=4
        ))
        
        fig.update_layout(
            title="Circular Knowledge Map",
            font_size=12,
            height=600
        )
        
        return {"figure": fig, "type": "plotly"}
    
    def _build_tree_structure(self) -> List[Dict]:
        """Build tree structure for hierarchical visualizations"""
        
        tree_data = []
        
        # Add all nodes
        for node_id, node in self.nodes.items():
            tree_data.append({
                "id": node_id,
                "name": node.name,
                "parent": node.parent_id if node.parent_id else "",
                "importance": node.importance,
                "summary": node.summary
            })
        
        return tree_data
    
    def _create_interactive_html(self) -> Dict:
        """Create interactive HTML visualization"""
        
        # Create a simple HTML structure for the mind map
        html_content = f"""
        <div class="mindmap-container" style="width: 100%; height: 500px; border: 1px solid #ddd; overflow: auto;">
            <div class="mindmap-title" style="text-align: center; padding: 10px; background: #f5f5f5; font-weight: bold;">
                Interactive Mind Map
            </div>
            <div class="mindmap-content" style="padding: 20px;">
        """
        
        # Add nodes in hierarchical structure
        root_nodes = [node for node in self.nodes.values() if node.node_type == "root"]
        for root in root_nodes:
            html_content += self._build_html_node(root, 0)
        
        html_content += """
            </div>
        </div>
        <style>
            .mindmap-node { margin: 10px 0; padding: 10px; border-left: 3px solid #4ECDC4; background: #f9f9f9; }
            .mindmap-node.level-0 { border-left-color: #FF6B6B; }
            .mindmap-node.level-1 { border-left-color: #4ECDC4; margin-left: 20px; }
            .mindmap-node.level-2 { border-left-color: #45B7D1; margin-left: 40px; }
            .mindmap-node.level-3 { border-left-color: #96CEB4; margin-left: 60px; }
            .node-title { font-weight: bold; color: #333; }
            .node-summary { color: #666; margin-top: 5px; font-size: 0.9em; }
            .node-keywords { color: #888; margin-top: 5px; font-size: 0.8em; font-style: italic; }
        </style>
        """
        
        return {"html": html_content, "type": "html"}
    
    def _build_html_node(self, node: MindMapNode, depth: int) -> str:
        """Build HTML representation of a node"""
        
        html = f"""
        <div class="mindmap-node level-{node.level}">
            <div class="node-title">{node.name}</div>
            <div class="node-summary">{node.summary}</div>
        """
        
        if node.keywords:
            html += f'<div class="node-keywords">Keywords: {", ".join(node.keywords)}</div>'
        
        # Add children
        children = [n for n in self.nodes.values() if n.parent_id == node.id]
        for child in children:
            html += self._build_html_node(child, depth + 1)
        
        html += "</div>"
        return html
    
    def _create_mermaid_diagram(self) -> Dict:
        """Create Mermaid diagram representation"""
        
        mermaid_content = ["graph TD"]
        
        # Add nodes with styling
        for node_id, node in self.nodes.items():
            clean_id = node_id.replace("-", "_").replace(" ", "_")
            clean_name = node.name.replace('"', "'")
            
            if node.node_type == "root":
                mermaid_content.append(f'    {clean_id}["{clean_name}"]')
                mermaid_content.append(f'    class {clean_id} root-node')
            elif node.node_type == "theme":
                mermaid_content.append(f'    {clean_id}("{clean_name}")')
                mermaid_content.append(f'    class {clean_id} theme-node')
            elif node.node_type == "subtopic":
                mermaid_content.append(f'    {clean_id}["{clean_name}"]')
                mermaid_content.append(f'    class {clean_id} subtopic-node')
            else:
                mermaid_content.append(f'    {clean_id}("{clean_name}")')
                mermaid_content.append(f'    class {clean_id} detail-node')
        
        # Add edges
        for edge in self.edges:
            from_clean = edge["from"].replace("-", "_").replace(" ", "_")
            to_clean = edge["to"].replace("-", "_").replace(" ", "_")
            mermaid_content.append(f'    {from_clean} --> {to_clean}')
        
        # Add styling
        mermaid_content.extend([
            "",
            "    classDef root-node fill:#FF6B6B,stroke:#333,stroke-width:3px,color:white",
            "    classDef theme-node fill:#4ECDC4,stroke:#333,stroke-width:2px,color:white", 
            "    classDef subtopic-node fill:#45B7D1,stroke:#333,stroke-width:2px,color:white",
            "    classDef detail-node fill:#96CEB4,stroke:#333,stroke-width:1px,color:white"
        ])
        
        return {"diagram": "\n".join(mermaid_content), "type": "mermaid"}
    
    def _node_to_dict(self, node: MindMapNode) -> Dict:
        """Convert MindMapNode to dictionary"""
        return {
            "id": node.id,
            "name": node.name,
            "summary": node.summary,
            "level": node.level,
            "parent_id": node.parent_id,
            "children": node.children,
            "node_type": node.node_type,
            "importance": node.importance,
            "keywords": node.keywords
        }
    
    def _generate_statistics(self) -> Dict[str, Any]:
        """Generate statistics about the mind map"""
        
        stats = {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "max_depth": max([node.level for node in self.nodes.values()]) if self.nodes else 0,
            "total_keywords": sum([len(node.keywords) for node in self.nodes.values()]),
            "nodes_by_level": {},
            "nodes_by_type": {},
            "average_importance": sum([node.importance for node in self.nodes.values()]) / len(self.nodes) if self.nodes else 0
        }
        
        # Count by level
        for node in self.nodes.values():
            level = node.level
            stats["nodes_by_level"][level] = stats["nodes_by_level"].get(level, 0) + 1
            
            node_type = node.node_type
            stats["nodes_by_type"][node_type] = stats["nodes_by_type"].get(node_type, 0) + 1
        
        return stats
    
    def _fallback_structure_extraction(self, document_text: str, document_titles: Optional[List[str]] = None) -> Dict[str, Any]:
        """Fallback method for structure extraction when AI fails"""
        
        # Simple text-based analysis
        lines = document_text.split('\n')
        themes = []
        current_theme = None
        
        for line in lines[:100]:  # Analyze first 100 lines
            if len(line) > 10 and len(line) < 100:
                # Potential theme/topic
                if current_theme is None or len(current_theme.get("subtopics", [])) >= 3:
                    current_theme = {
                        "id": f"theme_{len(themes) + 1}",
                        "name": line.strip()[:40],
                        "summary": f"Analysis of {line.strip()[:30]}",
                        "importance": 0.7,
                        "keywords": [],
                        "subtopics": []
                    }
                    themes.append(current_theme)
                else:
                    # Add as subtopic
                    subtopic = {
                        "id": f"theme_{len(themes)}_sub_{len(current_theme['subtopics']) + 1}",
                        "name": line.strip()[:30],
                        "summary": f"Details about {line.strip()[:20]}",
                        "importance": 0.5,
                        "keywords": [],
                        "details": []
                    }
                    current_theme["subtopics"].append(subtopic)
            
            if len(themes) >= 5:  # Limit fallback themes
                break
        
        if not themes:
            themes.append({
                "id": "theme_1",
                "name": "Document Analysis",
                "summary": "General analysis of the document content",
                "importance": 0.8,
                "keywords": [],
                "subtopics": []
            })
        
        return {
            "title": document_titles[0] if document_titles else "Document Mind Map",
            "main_themes": themes,
            "connections": []
        }
    
    def export_to_markdown(self, mind_map_data: Dict) -> str:
        """Export mind map to markdown format"""
        
        lines = [f"# {mind_map_data.get('title', 'Mind Map')}", ""]
        
        # Add statistics
        stats = mind_map_data.get('statistics', {})
        lines.extend([
            "## Overview",
            f"- **Total Concepts**: {stats.get('total_nodes', 0)}",
            f"- **Connections**: {stats.get('total_edges', 0)}",
            f"- **Depth Levels**: {stats.get('max_depth', 0)}",
            f"- **Keywords**: {stats.get('total_keywords', 0)}",
            ""
        ])
        
        # Add nodes by level
        nodes = mind_map_data.get('nodes', {})
        
        def add_node_markdown(node_id: str, level: int = 2):
            if node_id not in nodes:
                return
                
            node = nodes[node_id]
            header = "#" * level
            lines.append(f"{header} {node['name']}")
            lines.append(f"{node['summary']}")
            lines.append("")
            
            if node.get('keywords'):
                lines.append(f"**Keywords**: {', '.join(node['keywords'])}")
                lines.append("")
            
            # Add children
            children = [nid for nid, n in nodes.items() if n.get('parent_id') == node_id]
            for child_id in children:
                add_node_markdown(child_id, level + 1)
        
        # Start with root node
        root_nodes = [nid for nid, n in nodes.items() if not n.get('parent_id') or n.get('node_type') == 'root']
        for root_id in root_nodes:
            children = [nid for nid, n in nodes.items() if n.get('parent_id') == root_id]
            for child_id in children:
                add_node_markdown(child_id, 2)
        
        return "\n".join(lines)
    
    def export_to_graphml(self, mind_map_data: Dict) -> str:
        """Export mind map to GraphML format for advanced graph analysis tools"""
        
        graphml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns
         http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">
  
  <key id="name" for="node" attr.name="name" attr.type="string"/>
  <key id="summary" for="node" attr.name="summary" attr.type="string"/>
  <key id="importance" for="node" attr.name="importance" attr.type="double"/>
  <key id="level" for="node" attr.name="level" attr.type="int"/>
  <key id="node_type" for="node" attr.name="node_type" attr.type="string"/>
  
  <key id="relationship" for="edge" attr.name="relationship" attr.type="string"/>
  <key id="strength" for="edge" attr.name="strength" attr.type="double"/>
  
  <graph id="mindmap" edgedefault="directed">
'''
        
        # Add nodes
        nodes = mind_map_data.get('nodes', {})
        for node_id, node in nodes.items():
            graphml_content += f'''    <node id="{node_id}">
      <data key="name">{node['name']}</data>
      <data key="summary">{node['summary']}</data>
      <data key="importance">{node['importance']}</data>
      <data key="level">{node['level']}</data>
      <data key="node_type">{node['node_type']}</data>
    </node>
'''
        
        # Add edges
        edges = mind_map_data.get('edges', [])
        for i, edge in enumerate(edges):
            graphml_content += f'''    <edge id="e{i}" source="{edge['from']}" target="{edge['to']}">
      <data key="relationship">{edge['relationship']}</data>
      <data key="strength">{edge['strength']}</data>
    </edge>
'''
        
        graphml_content += '''  </graph>
</graphml>'''
        
        return graphml_content

# For backward compatibility, create an alias
MindMapGenerator = NotebookLMMindMapGenerator