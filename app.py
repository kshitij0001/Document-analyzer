# -*- coding: utf-8 -*-
# AI Document Analyzer & Chat - Main Streamlit Application
# A NotebookLM-inspired document analysis tool with AI chat capabilities

import streamlit as st
import time
import os
import json
import hashlib
from document_processor import DocumentProcessor
from vector_store import VectorStore
from ai_client import AIClient
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Helper functions for caching
def load_cached_analyses():
    """Load cached analysis results from session state"""
    return {}

def save_cached_analyses(cache_data):
    """Save cached analysis results to session state"""
    if "cached_analyses" in st.session_state:
        st.session_state.cached_analyses = cache_data

def get_cache_key(documents_hash, analysis_type, personality):
    """Generate a unique cache key for analysis results"""
    key_string = f"{documents_hash}_{analysis_type}_{personality}"
    return hashlib.md5(key_string.encode()).hexdigest()

def get_documents_hash():
    """Generate hash of current documents for cache key"""
    if "documents" not in st.session_state:
        return ""
    doc_content = ""
    for filename, doc_info in st.session_state.documents.items():
        if doc_info["success"]:
            doc_content += f"{filename}_{doc_info['word_count']}_"
    return hashlib.md5(doc_content.encode()).hexdigest()

def get_cached_analysis(analysis_type):
    """Get cached analysis if available"""
    try:
        if "cached_analyses" not in st.session_state or "ai_client" not in st.session_state:
            return None
        documents_hash = get_documents_hash()
        personality = st.session_state.ai_client.current_personality
        cache_key = get_cache_key(documents_hash, analysis_type, personality)
        
        cached_data = st.session_state.cached_analyses.get(cache_key)
        if cached_data:
            return cached_data
        return None
    except:
        return None

def save_analysis_cache(analysis_type, content):
    """Save analysis result to cache"""
    try:
        if "cached_analyses" not in st.session_state or "ai_client" not in st.session_state:
            return
        documents_hash = get_documents_hash()
        personality = st.session_state.ai_client.current_personality
        cache_key = get_cache_key(documents_hash, analysis_type, personality)
        
        cache_entry = {
            "content": content,
            "timestamp": time.time(),
            "personality": personality,
            "analysis_type": analysis_type
        }
        
        st.session_state.cached_analyses[cache_key] = cache_entry
    except Exception as e:
        st.error(f"Error saving analysis cache: {e}")

# Page configuration
st.set_page_config(
    page_title="AI Document Analyzer & Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "processor" not in st.session_state:
    st.session_state.processor = DocumentProcessor()
if "vector_store" not in st.session_state:
    st.session_state.vector_store = VectorStore()
if "ai_client" not in st.session_state:
    st.session_state.ai_client = AIClient()
if "documents" not in st.session_state:
    st.session_state.documents = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_document" not in st.session_state:
    st.session_state.current_document = None
if "cached_analyses" not in st.session_state:
    st.session_state.cached_analyses = load_cached_analyses()
if "mindmap_expanded_nodes" not in st.session_state:
    st.session_state.mindmap_expanded_nodes = set()
if "mindmap_visible_levels" not in st.session_state:
    st.session_state.mindmap_visible_levels = 2

def main():
    # Header
    st.title("🤖 AI Document Analyzer & Chat")
    st.markdown("""
    Upload documents (PDF, Word, Text) and chat with them using AI. Get insights, summaries, 
    and answers from your documents with different AI expert personalities.
    """)
    
    # Check API key status and show warning if needed
    service_info = st.session_state.ai_client.get_service_info()
    if "❌" in service_info.get("api_key_status", ""):
        st.error("""
        🔑 **OpenRouter API Key Required** - Please add your API key to `.streamlit/secrets.toml`:
        
        ```toml
        [openrouter]
        api_key = "your-key-here"
        ```
        
        Get your free API key at: https://openrouter.ai/keys
        """)
        st.divider()
    
    # Sidebar for document management and settings
    with st.sidebar:
        st.header("📁 Document Management")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Upload Document",
            type=['pdf', 'docx', 'doc', 'txt'],
            help="Upload PDF, Word, or text files to analyze"
        )
        
        if uploaded_file is not None:
            process_uploaded_file(uploaded_file)
        
        # Show uploaded documents
        if st.session_state.documents:
            st.subheader("📄 Uploaded Documents")
            for filename, doc_info in st.session_state.documents.items():
                with st.expander(f"{filename}"):
                    if doc_info["success"]:
                        st.success("✅ Processed")
                        st.write(f"**Type:** {doc_info['file_type']}")
                        st.write(f"**Words:** {doc_info['word_count']:,}")
                        st.write(f"**Chunks:** {doc_info['chunk_count']}")
                        
                        if st.button(f"Remove {filename}", key=f"remove_{filename}"):
                            remove_document(filename)
                            st.rerun()
                    else:
                        st.error(f"❌ Error: {doc_info['error']}")
        else:
            st.info("No documents uploaded yet")
        
        # AI Settings
        st.header("🎭 AI Settings")
        
        # Personality selection
        personalities = st.session_state.ai_client.get_available_personalities()
        personality_options = {key: data["name"] for key, data in personalities.items()}
        
        selected_personality = st.selectbox(
            "AI Personality",
            options=list(personality_options.keys()),
            format_func=lambda x: personality_options[x],
            help="Choose the AI expert type for analysis"
        )
        
        if selected_personality != st.session_state.ai_client.current_personality:
            st.session_state.ai_client.set_personality(selected_personality)
            st.success(f"Switched to {personality_options[selected_personality]}")
        
        # Show current personality description
        current_desc = personalities[selected_personality]["description"]
        st.caption(f"💡 {current_desc}")
        
        # Model selection dropdown
        service_info = st.session_state.ai_client.get_service_info()
        if service_info["available_models"]:
            available_models = service_info["available_models"]
            model_names = {
                "gpt-oss-120b": "GPT-OSS 120B (Recommended)",
                "deepseek-v3.1": "DeepSeek Chat v3.1",
                "gemini-2.5-flash": "Gemini 2.5 Flash",
                "gpt-oss-20b": "GPT-OSS 20B",
                "qwen-2.5-7b": "Qwen 2.5 7B",
                "llama-3.2-3b": "Llama 3.2 3B",
                "llama-3.2-1b": "Llama 3.2 1B"
            }
            
            selected_model = st.selectbox(
                "Select AI Model",
                options=available_models,
                format_func=lambda x: model_names.get(x, x),
                help="Choose which free AI model to use"
            )
            
            # Update model if changed
            current_model_key = None
            for key, model_id in st.session_state.ai_client.available_models.items():
                if model_id == st.session_state.ai_client.current_model:
                    current_model_key = key
                    break
            
            if selected_model != current_model_key:
                if st.session_state.ai_client.set_model(selected_model):
                    st.success(f"Switched to {model_names.get(selected_model, selected_model)}")
        
        # Show AI service info
        st.caption(f"**Provider:** {service_info['provider']}")
        st.caption(f"**Status:** {service_info['api_key_status']}")
        
        # Clear chat history
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.session_state.ai_client.clear_conversation_history()
            st.success("Chat history cleared!")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Chat interface
        st.subheader("💬 Chat with Your Documents")
        
        # Display chat history
        chat_container = st.container()
        
        with chat_container:
            if st.session_state.chat_history:
                for i, message in enumerate(st.session_state.chat_history):
                    if message["role"] == "user":
                        with st.chat_message("user"):
                            st.write(message["content"])
                    else:
                        with st.chat_message("assistant"):
                            st.write(message["content"])
                            if "personality" in message:
                                st.caption(f"*Response from {message['personality']}*")
            else:
                st.info("👋 Start by uploading a document and asking a question!")
        
        # Chat input
        if st.session_state.documents:
            user_question = st.chat_input("Ask a question about your documents...")
            
            if user_question:
                handle_user_question(user_question)
        else:
            st.warning("⚠️ Please upload a document first to start chatting.")
    
    with col2:
        # Document insights and quick actions
        st.subheader("📊 Document Insights")
        
        if st.session_state.documents:
            # Quick statistics
            total_words = sum(doc["word_count"] for doc in st.session_state.documents.values() if doc["success"])
            total_docs = len([doc for doc in st.session_state.documents.values() if doc["success"]])
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Documents", total_docs)
            with col_b:
                st.metric("Total Words", f"{total_words:,}")
            
            # Quick analysis buttons
            st.subheader("🔍 Quick Analysis")
            
            if st.button("📝 Generate Summary", use_container_width=True):
                generate_document_summary()
            
            if st.button("🎯 Extract Key Points", use_container_width=True):
                extract_key_points()
            
            if st.button("📈 Analyze Sentiment", use_container_width=True):
                analyze_sentiment()
            
            if st.button("🧠 Generate Mind Map", use_container_width=True):
                generate_mind_map()
            
            # Vector store statistics
            stats = st.session_state.vector_store.get_statistics()
            if stats["is_ready"]:
                st.subheader("🔍 Search Stats")
                st.write(f"**Total Chunks:** {stats['total_chunks']}")
                st.write(f"**Vocabulary Size:** {stats['vocabulary_size']:,}")
        else:
            st.info("Upload documents to see insights")

def process_uploaded_file(uploaded_file):
    """Process uploaded file and add to document store"""
    filename = uploaded_file.name
    
    if filename in st.session_state.documents:
        st.warning(f"Document '{filename}' already uploaded!")
        return
    
    with st.spinner(f"Processing {filename}..."):
        # Process document
        doc_info = st.session_state.processor.process_document(uploaded_file, filename)
        
        # Add to session state
        st.session_state.documents[filename] = doc_info
        
        if doc_info["success"]:
            # Add to vector store
            success = st.session_state.vector_store.add_document(doc_info)
            if success:
                st.success(f"✅ Successfully processed '{filename}'!")
                st.session_state.current_document = filename
            else:
                st.error(f"❌ Failed to index '{filename}' for search")
        else:
            st.error(f"❌ Failed to process '{filename}': {doc_info['error']}")

def remove_document(filename):
    """Remove document from all stores"""
    if filename in st.session_state.documents:
        # Remove from vector store
        st.session_state.vector_store.remove_document(filename)
        
        # Remove from session state
        del st.session_state.documents[filename]
        
        # Clear current document if it was removed
        if st.session_state.current_document == filename:
            st.session_state.current_document = None
        
        st.success(f"Removed '{filename}'")

def handle_user_question(question):
    """Handle user question and generate AI response"""
    # Add user message to chat
    st.session_state.chat_history.append({
        "role": "user",
        "content": question
    })
    
    with st.spinner("Thinking..."):
        # Get relevant context from documents
        context = st.session_state.vector_store.get_context_for_query(question)
        
        # Get AI response
        response = st.session_state.ai_client.chat_with_document(
            user_question=question,
            document_context=context,
            max_tokens=1000,
            temperature=0.7
        )
        
        if response["success"]:
            # Add AI response to chat
            personality_name = st.session_state.ai_client.personalities[
                st.session_state.ai_client.current_personality
            ]["name"]
            
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response["content"],
                "personality": personality_name
            })
        else:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"Sorry, I encountered an error: {response['error']}",
                "personality": "System"
            })
    
    st.rerun()

def generate_document_summary():
    """Generate summary of all uploaded documents"""
    if not st.session_state.documents:
        st.warning("No documents to summarize")
        return
    
    # Check cache first
    cached_result = get_cached_analysis("summary")
    if cached_result:
        st.subheader("📝 Document Summary")
        st.caption("✅ Cached result from previous analysis")
        st.write(cached_result["content"])
        
        if st.button("🔄 Regenerate Summary"):
            generate_fresh_summary()
        return
    
    generate_fresh_summary()

def generate_fresh_summary():
    """Generate fresh summary analysis"""
    with st.spinner("Generating summary..."):
        # Combine text from all successful documents
        all_text = ""
        for filename, doc_info in st.session_state.documents.items():
            if doc_info["success"]:
                all_text += f"\n\n--- {filename} ---\n{doc_info['text'][:2000]}"  # Limit text
        
        if all_text:
            response = st.session_state.ai_client.analyze_document(all_text, "summary")
            
            if response["success"]:
                # Save to cache
                save_analysis_cache("summary", response["content"])
                
                st.subheader("📝 Document Summary")
                st.write(response["content"])
            else:
                st.error(f"Failed to generate summary: {response['error']}")

def extract_key_points():
    """Extract key points from documents"""
    if not st.session_state.documents:
        st.warning("No documents to analyze")
        return
    
    # Check cache first
    cached_result = get_cached_analysis("key_points")
    if cached_result:
        st.subheader("🎯 Key Points")
        st.caption("✅ Cached result from previous analysis")
        st.write(cached_result["content"])
        
        if st.button("🔄 Regenerate Key Points"):
            generate_fresh_key_points()
        return
    
    generate_fresh_key_points()

def generate_fresh_key_points():
    """Generate fresh key points analysis"""
    with st.spinner("Extracting key points..."):
        # Get combined text
        all_text = ""
        for filename, doc_info in st.session_state.documents.items():
            if doc_info["success"]:
                all_text += f"\n\n--- {filename} ---\n{doc_info['text'][:2000]}"
        
        if all_text:
            response = st.session_state.ai_client.analyze_document(all_text, "key_points")
            
            if response["success"]:
                # Save to cache
                save_analysis_cache("key_points", response["content"])
                
                st.subheader("🎯 Key Points")
                st.write(response["content"])
            else:
                st.error(f"Failed to extract key points: {response['error']}")

def analyze_sentiment():
    """Analyze sentiment of documents"""
    if not st.session_state.documents:
        st.warning("No documents to analyze")
        return
    
    # Check cache first
    cached_result = get_cached_analysis("sentiment")
    if cached_result:
        st.subheader("📈 Sentiment Analysis")
        st.caption("✅ Cached result from previous analysis")
        st.write(cached_result["content"])
        
        if st.button("🔄 Regenerate Sentiment Analysis"):
            generate_fresh_sentiment()
        return
    
    generate_fresh_sentiment()

def generate_fresh_sentiment():
    """Generate fresh sentiment analysis"""
    with st.spinner("Analyzing sentiment..."):
        # Get combined text
        all_text = ""
        for filename, doc_info in st.session_state.documents.items():
            if doc_info["success"]:
                all_text += f"\n\n--- {filename} ---\n{doc_info['text'][:2000]}"
        
        if all_text:
            response = st.session_state.ai_client.analyze_document(all_text, "sentiment")
            
            if response["success"]:
                # Save to cache
                save_analysis_cache("sentiment", response["content"])
                
                st.subheader("📈 Sentiment Analysis")
                st.write(response["content"])
            else:
                st.error(f"Failed to analyze sentiment: {response['error']}")


def get_pastel_colors():
    """Generate beautiful pastel color palette"""
    return [
        '#FFB3BA',  # Light pink
        '#BAFFC9',  # Light green
        '#BAE1FF',  # Light blue
        '#FFFFBA',  # Light yellow
        '#FFDFBA',  # Light peach
        '#E0BBE4',  # Light purple
        '#FFC9A9',  # Light coral
        '#C9F0FF',  # Light cyan
        '#D4EDDA',  # Light mint
        '#F8D7DA',  # Light rose
        '#CCE5FF',  # Light sky blue
        '#FFECB3'   # Light amber
    ]

def parse_mind_map_data(mind_map_data):
    """Parse AI response into structured mind map data"""
    try:
        if isinstance(mind_map_data, str):
            import re
            json_match = re.search(r'\{.*\}', mind_map_data, re.DOTALL)
            if json_match:
                parsed_data = json.loads(json_match.group())
                # Convert old format to new format if needed
                if 'main_themes' in parsed_data:
                    parsed_data['themes'] = parsed_data.pop('main_themes')
                return parsed_data
            else:
                return {"title": "Document Analysis", "themes": []}
        return mind_map_data
    except:
        return {"title": "Document Analysis", "themes": []}

def count_total_nodes(themes, max_level=None, current_level=0):
    """Count total nodes up to a certain level"""
    if max_level and current_level >= max_level:
        return 0
    
    count = len(themes)
    for theme in themes:
        if 'sub_themes' in theme and theme['sub_themes']:
            count += count_total_nodes(theme['sub_themes'], max_level, current_level + 1)
    return count

def build_node_tree(themes, parent_id="root", level=0, max_level=None, colors=None, expanded_nodes=None):
    """Build tree structure with nodes and edges"""
    if colors is None:
        colors = get_pastel_colors()
    if expanded_nodes is None:
        expanded_nodes = set()
    if max_level and level >= max_level:
        return [], []
    
    nodes = []
    edges = []
    
    for i, theme in enumerate(themes):
        node_id = theme.get('id', f"{parent_id}_theme_{i}")
        theme_name = theme.get('name', f"Theme {i+1}")
        theme_summary = theme.get('summary', '')
        
        # Determine if this node should be visible
        is_expanded = node_id in expanded_nodes
        has_children = 'sub_themes' in theme and theme['sub_themes']
        
        # Create node data
        node = {
            'id': node_id,
            'name': theme_name,
            'summary': theme_summary,
            'level': level,
            'parent_id': parent_id,
            'has_children': has_children,
            'is_expanded': is_expanded,
            'color': colors[level % len(colors)],
            'is_leaf': not has_children
        }
        nodes.append(node)
        
        # Create edge to parent
        if parent_id != "root":
            edges.append((parent_id, node_id))
        
        # Add children if expanded or within visible levels
        if has_children and (is_expanded or level < st.session_state.mindmap_visible_levels):
            child_nodes, child_edges = build_node_tree(
                theme['sub_themes'], 
                node_id, 
                level + 1, 
                max_level,
                colors, 
                expanded_nodes
            )
            nodes.extend(child_nodes)
            edges.extend(child_edges)
    
    return nodes, edges

def calculate_node_positions(nodes, edges):
    """Calculate optimal positions for nodes using a tree layout"""
    positions = {}
    
    # Group nodes by level
    levels = {}
    for node in nodes:
        level = node['level']
        if level not in levels:
            levels[level] = []
        levels[level].append(node)
    
    # Position nodes level by level
    for level, level_nodes in levels.items():
        y_pos = -level * 1.5  # Vertical spacing
        node_count = len(level_nodes)
        
        if node_count == 1:
            positions[level_nodes[0]['id']] = (0, y_pos)
        else:
            # Spread nodes horizontally
            total_width = min(node_count * 2, 8)  # Limit total width
            start_x = -total_width / 2
            
            for i, node in enumerate(level_nodes):
                x_pos = start_x + (i * total_width / max(1, node_count - 1))
                positions[node['id']] = (x_pos, y_pos)
    
    return positions

def create_mind_map_visualization(mind_map_data):
    """Create advanced interactive mind map with unlimited depth"""
    try:
        # Parse the mind map data
        parsed_data = parse_mind_map_data(mind_map_data)
        title = parsed_data.get('title', 'Document Analysis')
        themes = parsed_data.get('themes', [])
        
        if not themes:
            st.warning("No themes found in the mind map data")
            return None
        
        # Check if we need to hide levels due to too many nodes
        total_nodes = count_total_nodes(themes, max_level=4)
        if total_nodes > 50:  # Too many nodes, limit visibility
            st.session_state.mindmap_visible_levels = 2
        elif total_nodes > 25:
            st.session_state.mindmap_visible_levels = 3
        else:
            st.session_state.mindmap_visible_levels = 4
        
        # Build the node tree
        nodes, edges = build_node_tree(
            themes, 
            expanded_nodes=st.session_state.mindmap_expanded_nodes
        )
        
        if not nodes:
            st.warning("No visible nodes to display")
            return None
        
        # Calculate positions
        positions = calculate_node_positions(nodes, edges)
        
        # Create Plotly figure
        fig = go.Figure()
        
        # Add edges (connections between nodes)
        for parent_id, child_id in edges:
            if parent_id in positions and child_id in positions:
                x0, y0 = positions[parent_id]
                x1, y1 = positions[child_id]
                
                # Create curved line
                mid_x = (x0 + x1) / 2
                mid_y = (y0 + y1) / 2 + 0.2  # Slight curve
                
                fig.add_trace(go.Scatter(
                    x=[x0, mid_x, x1], 
                    y=[y0, mid_y, y1],
                    mode='lines',
                    line=dict(width=2, color='rgba(100,100,100,0.5)', shape='spline'),
                    showlegend=False,
                    hoverinfo='skip'
                ))
        
        # Add root node
        fig.add_trace(go.Scatter(
            x=[0], y=[1],
            mode='markers+text',
            marker=dict(
                size=40,
                color='#FF69B4',  # Bright pink for root
                line=dict(width=3, color='white')
            ),
            text=[title],
            textposition="middle center",
            textfont=dict(size=12, color='white'),
            showlegend=False,
            hovertemplate=f'<b>{title}</b><br>Click themes below to explore<extra></extra>',
            customdata=['root']
        ))
        
        # Add theme nodes
        for node in nodes:
            if node['id'] in positions:
                x, y = positions[node['id']]
                
                # Node size based on level (smaller as we go deeper)
                size = max(30 - (node['level'] * 5), 15)
                
                # Different markers for expandable vs leaf nodes
                symbol = 'circle' if not node['has_children'] else ('circle-open' if not node['is_expanded'] else 'circle')
                
                # Hover text
                hover_text = f"<b>{node['name']}</b><br>{node['summary']}"
                if node['has_children'] and not node['is_expanded']:
                    hover_text += "<br><i>Click to expand</i>"
                elif node['is_leaf']:
                    hover_text += "<br><i>Click to generate detailed notes</i>"
                
                fig.add_trace(go.Scatter(
                    x=[x], y=[y],
                    mode='markers+text',
                    marker=dict(
                        size=size,
                        color=node['color'],
                        line=dict(width=2, color='white'),
                        symbol=symbol
                    ),
                    text=[node['name']],
                    textposition="middle center",
                    textfont=dict(size=10, color='black'),
                    showlegend=False,
                    hovertemplate=hover_text + '<extra></extra>',
                    customdata=[node['id']]
                ))
        
        # Update layout
        fig.update_layout(
            title=f"📊 Interactive Mind Map: {title}",
            showlegend=False,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-5, 5]),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=700,
            margin=dict(l=20, r=20, t=60, b=20),
            font=dict(family="Arial, sans-serif", size=12)
        )
        
        # Store the parsed data for click handling
        st.session_state.current_mindmap_data = parsed_data
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating advanced mind map: {e}")
        import traceback
        st.error(traceback.format_exc())
        return None

def handle_mindmap_click(node_id, mind_map_data):
    """Handle clicks on mind map nodes"""
    if node_id == 'root':
        return
    
    # Find the clicked node in the data structure
    def find_node_by_id(themes, target_id):
        for theme in themes:
            if theme.get('id') == target_id:
                return theme
            if 'sub_themes' in theme and theme['sub_themes']:
                result = find_node_by_id(theme['sub_themes'], target_id)
                if result:
                    return result
        return None
    
    clicked_node = find_node_by_id(mind_map_data.get('themes', []), node_id)
    
    if clicked_node:
        has_children = 'sub_themes' in clicked_node and clicked_node['sub_themes']
        
        if has_children:
            # Toggle expansion
            if node_id in st.session_state.mindmap_expanded_nodes:
                st.session_state.mindmap_expanded_nodes.remove(node_id)
                st.success(f"Collapsed: {clicked_node['name']}")
            else:
                st.session_state.mindmap_expanded_nodes.add(node_id)
                st.success(f"Expanded: {clicked_node['name']}")
        else:
            # Leaf node - generate detailed notes
            generate_focused_notes(clicked_node)

def generate_focused_notes(node_data):
    """Generate focused notes for a specific topic and add to chat"""
    topic_name = node_data['name']
    topic_summary = node_data.get('summary', '')
    
    # Create a focused question for the AI
    focused_question = f"Please provide detailed information and insights about '{topic_name}'. {topic_summary}"
    
    # Add to chat history
    st.session_state.chat_history.append({
        "role": "user",
        "content": f"[Mind Map Topic] {topic_name}"
    })
    
    with st.spinner(f"Generating detailed notes about '{topic_name}'..."):
        # Get relevant context from documents
        context = st.session_state.vector_store.get_context_for_query(focused_question)
        
        # Get AI response
        response = st.session_state.ai_client.chat_with_document(
            user_question=focused_question,
            document_context=context,
            max_tokens=1200,
            temperature=0.7
        )
        
        if response["success"]:
            # Add AI response to chat
            personality_name = st.session_state.ai_client.personalities[
                st.session_state.ai_client.current_personality
            ]["name"]
            
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response["content"],
                "personality": personality_name
            })
            st.success(f"Generated detailed notes for '{topic_name}' - check the chat!")
        else:
            st.error(f"Failed to generate notes: {response['error']}")

def generate_mind_map():
    """Generate mind map of all uploaded documents"""
    if not st.session_state.documents:
        st.warning("No documents to analyze")
        return
    
    # Check cache first
    cached_result = get_cached_analysis("mind_map")
    if cached_result:
        st.subheader("🧠 Interactive Document Mind Map")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption("✅ Cached result from previous analysis")
        with col2:
            if st.button("🔄 Regenerate", key="regen_mindmap"):
                generate_fresh_mind_map()
                st.rerun()
        
        # Create visualization
        fig = create_mind_map_visualization(cached_result["content"])
        if fig:
            # Display the mind map
            clicked_data = st.plotly_chart(fig, use_container_width=True, key="mindmap_chart")
            
            # Instructions
            st.info("💡 **How to use:** Click on nodes to expand themes or click leaf nodes (end topics) to generate detailed notes in the chat!")
            
            # Handle clicks (simplified approach using session state)
            if 'current_mindmap_data' in st.session_state:
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("🔍 Expand All Level 1", key="expand_l1"):
                        # Expand first level themes
                        themes = st.session_state.current_mindmap_data.get('themes', [])
                        for theme in themes:
                            node_id = theme.get('id', f"theme_{themes.index(theme)}")
                            st.session_state.mindmap_expanded_nodes.add(node_id)
                        st.rerun()
                
                with col2:
                    if st.button("🔍 Expand All Level 2", key="expand_l2"):
                        # Expand first two levels
                        themes = st.session_state.current_mindmap_data.get('themes', [])
                        def expand_levels(theme_list, max_level, current_level=0):
                            if current_level >= max_level:
                                return
                            for theme in theme_list:
                                node_id = theme.get('id', f"theme_{theme_list.index(theme)}")
                                st.session_state.mindmap_expanded_nodes.add(node_id)
                                if 'sub_themes' in theme and theme['sub_themes']:
                                    expand_levels(theme['sub_themes'], max_level, current_level + 1)
                        expand_levels(themes, 2)
                        st.rerun()
                
                with col3:
                    if st.button("🔄 Collapse All", key="collapse_all"):
                        st.session_state.mindmap_expanded_nodes.clear()
                        st.rerun()
        else:
            st.write(cached_result["content"])
        
        return
    
    generate_fresh_mind_map()

def generate_fresh_mind_map():
    """Generate fresh mind map analysis"""
    # Clear previous state
    st.session_state.mindmap_expanded_nodes.clear()
    
    with st.spinner("Generating comprehensive mind map..."):
        # Combine text from all successful documents
        all_text = ""
        doc_titles = []
        for filename, doc_info in st.session_state.documents.items():
            if doc_info["success"]:
                all_text += f"\n\n=== {filename} ===\n{doc_info['text'][:4000]}"
                doc_titles.append(filename)
        
        if all_text:
            response = st.session_state.ai_client.analyze_document(all_text, "mind_map")
            
            if response["success"]:
                # Save to cache
                save_analysis_cache("mind_map", response["content"])
                
                st.subheader("🧠 Interactive Document Mind Map")
                st.caption(f"Analyzing {len(doc_titles)} documents: {', '.join(doc_titles)}")
                
                # Create visualization
                fig = create_mind_map_visualization(response["content"])
                if fig:
                    # Display the mind map
                    st.plotly_chart(fig, use_container_width=True, key="fresh_mindmap_chart")
                    
                    # Instructions
                    st.info("💡 **How to use:** Use the expansion controls below to explore different levels of detail!")
                    
                    # Control buttons
                    if 'current_mindmap_data' in st.session_state:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button("🔍 Expand Level 1", key="fresh_expand_l1"):
                                themes = st.session_state.current_mindmap_data.get('themes', [])
                                for i, theme in enumerate(themes):
                                    node_id = theme.get('id', f"theme_{i}")
                                    st.session_state.mindmap_expanded_nodes.add(node_id)
                                st.rerun()
                        
                        with col2:
                            if st.button("🔍 Expand Level 2", key="fresh_expand_l2"):
                                themes = st.session_state.current_mindmap_data.get('themes', [])
                                def expand_recursive(theme_list, max_depth, current_depth=0):
                                    if current_depth >= max_depth:
                                        return
                                    for i, theme in enumerate(theme_list):
                                        node_id = theme.get('id', f"theme_{i}")
                                        st.session_state.mindmap_expanded_nodes.add(node_id)
                                        if 'sub_themes' in theme and theme['sub_themes']:
                                            expand_recursive(theme['sub_themes'], max_depth, current_depth + 1)
                                expand_recursive(themes, 2)
                                st.rerun()
                        
                        with col3:
                            if st.button("🔄 Reset View", key="fresh_collapse_all"):
                                st.session_state.mindmap_expanded_nodes.clear()
                                st.rerun()
                else:
                    st.write(response["content"])
            else:
                st.error(f"Failed to generate mind map: {response['error']}")
                st.error("Please check your API key configuration and try again.")

if __name__ == "__main__":
    main()