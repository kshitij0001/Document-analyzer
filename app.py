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


def create_mind_map_visualization(mind_map_data):
    """Create interactive mind map using Plotly"""
    try:
        # Parse the JSON data from AI response
        if isinstance(mind_map_data, str):
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', mind_map_data, re.DOTALL)
            if json_match:
                mind_map_data = json.loads(json_match.group())
            else:
                # Fallback: create simple structure
                mind_map_data = {"title": "Document Analysis", "main_themes": []}
        
        # Create nodes and edges for the tree
        nodes = []
        edges = []
        positions = []
        
        # Root node
        nodes.append(mind_map_data.get("title", "Document Analysis"))
        positions.append((0, 0))
        
        node_id = 0
        y_offset = -1
        
        # Add main themes
        main_themes = mind_map_data.get("main_themes", [])
        theme_count = len(main_themes)
        
        for i, theme_data in enumerate(main_themes):
            node_id += 1
            theme_name = theme_data.get("theme", f"Theme {i+1}")
            nodes.append(theme_name)
            
            # Position themes around the root
            x_pos = -2 + (4 * i / max(1, theme_count - 1)) if theme_count > 1 else 0
            positions.append((x_pos, y_offset))
            
            # Add edge from root to theme
            edges.append((0, node_id))
            
            # Add key points for this theme
            key_points = theme_data.get("key_points", [])
            for j, point in enumerate(key_points[:3]):  # Limit to 3 key points
                node_id += 1
                nodes.append(point)
                positions.append((x_pos, y_offset - 1 - j * 0.5))
                edges.append((len([n for n in nodes if "Theme" in str(n) or n == mind_map_data.get("title", "")])[-1] if nodes else node_id-len(key_points), node_id))
        
        # Create Plotly figure
        fig = go.Figure()
        
        # Add edges
        for edge in edges:
            x0, y0 = positions[edge[0]]
            x1, y1 = positions[edge[1]]
            fig.add_trace(go.Scatter(
                x=[x0, x1], y=[y0, y1],
                mode='lines',
                line=dict(width=2, color='lightblue'),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        # Add nodes
        x_coords = [pos[0] for pos in positions]
        y_coords = [pos[1] for pos in positions]
        
        fig.add_trace(go.Scatter(
            x=x_coords, y=y_coords,
            mode='markers+text',
            marker=dict(
                size=[30 if i == 0 else 20 if "Theme" in str(nodes[i]) else 15 for i in range(len(nodes))],
                color=['lightcoral' if i == 0 else 'lightgreen' if "Theme" in str(nodes[i]) else 'lightblue' for i in range(len(nodes))],
                line=dict(width=2, color='white')
            ),
            text=nodes,
            textposition="middle center",
            showlegend=False,
            hovertemplate='%{text}<extra></extra>'
        ))
        
        # Update layout
        fig.update_layout(
            title="Interactive Document Mind Map",
            showlegend=False,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='rgba(0,0,0,0)',
            height=600,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating mind map: {e}")
        return None

def generate_mind_map():
    """Generate mind map of all uploaded documents"""
    if not st.session_state.documents:
        st.warning("No documents to analyze")
        return
    
    # Check cache first
    cached_result = get_cached_analysis("mind_map")
    if cached_result:
        st.subheader("🧠 Document Mind Map")
        st.caption("✅ Cached result from previous analysis")
        
        # Create visualization
        fig = create_mind_map_visualization(cached_result["content"])
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write(cached_result["content"])
        
        if st.button("🔄 Regenerate Mind Map"):
            # Clear cache for this analysis type and regenerate
            generate_fresh_mind_map()
        return
    
    generate_fresh_mind_map()

def generate_fresh_mind_map():
    """Generate fresh mind map analysis"""
    with st.spinner("Generating mind map..."):
        # Combine text from all successful documents
        all_text = ""
        for filename, doc_info in st.session_state.documents.items():
            if doc_info["success"]:
                all_text += f"\n\n--- {filename} ---\n{doc_info['text'][:3000]}"  # Limit text
        
        if all_text:
            response = st.session_state.ai_client.analyze_document(all_text, "mind_map")
            
            if response["success"]:
                # Save to cache
                save_analysis_cache("mind_map", response["content"])
                
                st.subheader("🧠 Document Mind Map")
                
                # Create visualization
                fig = create_mind_map_visualization(response["content"])
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.write(response["content"])
            else:
                st.error(f"Failed to generate mind map: {response['error']}")

if __name__ == "__main__":
    main()