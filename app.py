# -*- coding: utf-8 -*-
# AI Document Analyzer & Chat - Main Streamlit Application
# A NotebookLM-inspired document analysis tool with AI chat capabilities

import streamlit as st
import streamlit.components.v1
import time
import os
import json
import hashlib
from document_processor import DocumentProcessor
from vector_store import VectorStore
from ai_client import AIClient
from mindmap_generator import MindMapGenerator
# Optional plotly imports for mind map visualization
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError as e:
    PLOTLY_AVAILABLE = False
    go = None
    make_subplots = None
except Exception as e:
    PLOTLY_AVAILABLE = False
    go = None
    make_subplots = None

# Helper functions for caching and chat persistence
def load_cached_analyses():
    """Load cached analysis results from session state"""
    return {}

def save_cached_analyses(cache_data):
    """Save cached analysis results to session state"""
    if "cached_analyses" in st.session_state:
        st.session_state.cached_analyses = cache_data

def load_chat_history():
    """Load chat history from persistent storage"""
    try:
        if os.path.exists("chat_history.json"):
            with open("chat_history.json", "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading chat history: {e}")
    return []

def save_chat_history():
    """Save chat history to persistent storage"""
    try:
        with open("chat_history.json", "w", encoding="utf-8") as f:
            json.dump(st.session_state.chat_history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Error saving chat history: {e}")

def clear_persistent_chat():
    """Clear persistent chat history"""
    try:
        if os.path.exists("chat_history.json"):
            os.remove("chat_history.json")
        st.session_state.chat_history = []
        st.session_state.ai_client.clear_conversation_history()
    except Exception as e:
        st.error(f"Error clearing chat history: {e}")

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
if "mindmap_generator" not in st.session_state:
    st.session_state.mindmap_generator = MindMapGenerator(st.session_state.ai_client)
if "documents" not in st.session_state:
    st.session_state.documents = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_chat_history()
if "current_document" not in st.session_state:
    st.session_state.current_document = None
if "cached_analyses" not in st.session_state:
    st.session_state.cached_analyses = load_cached_analyses()
if "mindmap_data" not in st.session_state:
    st.session_state.mindmap_data = None

def display_mind_map_results(mind_map_data):
    """Display mind map results in multiple formats"""
    if isinstance(mind_map_data, str):
        st.error("Mind map data is in text format, not structured data")
        st.text_area("Raw Response", mind_map_data, height=200)
        return
    
    if "error" in mind_map_data:
        st.error(f"Error in mind map data: {mind_map_data['error']}")
        return
    
    # Store in session state for potential reuse
    st.session_state.mindmap_data = mind_map_data
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["🌳 Tree View", "📋 Markdown", "🔗 Mermaid Diagram"])
    
    with tab1:
        st.write("**Interactive Mind Map Structure**")
        display_mind_map_tree(mind_map_data)
    
    with tab2:
        st.write("**Markdown Export**")
        markdown_content = st.session_state.mindmap_generator.export_to_markdown(mind_map_data)
        st.markdown(markdown_content)
        st.download_button(
            "📄 Download Markdown",
            markdown_content,
            "mindmap.md",
            "text/markdown"
        )
    
    with tab3:
        st.write("**Interactive Mermaid Diagram**")
        mermaid_content = st.session_state.mindmap_generator.export_to_mermaid(mind_map_data)
        
        # Create interactive Mermaid diagram
        mermaid_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
            <style>
                body {{
                    margin: 0;
                    padding: 20px;
                    font-family: Arial, sans-serif;
                }}
                .mermaid {{
                    text-align: center;
                    background: white;
                }}
                .mermaid svg {{
                    max-width: 100%;
                    height: auto;
                }}
            </style>
        </head>
        <body>
            <div class="mermaid">
{mermaid_content}
            </div>
            <script>
                mermaid.initialize({{
                    startOnLoad: true,
                    theme: 'default',
                    flowchart: {{
                        useMaxWidth: true,
                        htmlLabels: true,
                        curve: 'basis'
                    }},
                    securityLevel: 'loose'
                }});
                
                // Force render after initialization
                mermaid.run();
            </script>
        </body>
        </html>
        """
        
        streamlit.components.v1.html(mermaid_html, height=600, scrolling=True)
        
        # Also provide code and download options
        with st.expander("🔧 View/Export Code"):
            st.code(mermaid_content, language="mermaid")
            st.download_button(
                "📊 Download Mermaid Code",
                mermaid_content,
                "mindmap.mmd",
                "text/plain"
            )
            st.info("💡 You can also copy the code above and paste it into [Mermaid Live Editor](https://mermaid.live) for further customization!")
            

def display_mind_map_tree(mind_map_data):
    """Display mind map as an interactive tree structure"""
    title = mind_map_data.get("title", "Mind Map")
    themes = mind_map_data.get("themes", [])
    
    st.markdown(f"### {title}")
    
    if not themes:
        st.warning("No themes found in the mind map")
        return
    
    for i, theme in enumerate(themes):
        # Show more prominent theme header with metrics
        with st.expander(f"🎯 **{theme['name']}**", expanded=i < 2):  # Auto-expand first 2 for better focus
            # Enhanced theme display with structured information
            st.markdown(f"**Overview:** {theme.get('summary', 'No summary available')}")
            
            sub_themes = theme.get('sub_themes', [])
            if sub_themes:
                st.markdown(f"**Analysis Depth:** {len(sub_themes)} key areas identified")
                st.markdown("---")
                
                for j, sub_theme in enumerate(sub_themes):
                    # More detailed sub-theme display
                    st.markdown(f"### 📌 {sub_theme['name']}")
                    
                    # Use columns for better layout
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Key Insights:** {sub_theme.get('summary', 'No summary available')}")
                        
                        # Show details if they exist
                        details = sub_theme.get('sub_themes', [])
                        if details:
                            st.markdown("**Specific Details:**")
                            for k, detail in enumerate(details):
                                st.markdown(f"   {k+1}. **{detail['name']}**: {detail.get('summary', 'No details available')}")
                        else:
                            # If no details, try to generate some insights based on the summary
                            if len(sub_theme.get('summary', '')) > 50:
                                st.markdown("**Analysis Notes:**")
                                st.markdown(f"   • This area contains significant information requiring deeper analysis")
                                st.markdown(f"   • Consider exploring this topic through the chat interface for detailed insights")
                    
                    with col2:
                        # Action buttons in a more organized way
                        if st.button(f"💬 Explore", key=f"explore_{theme['id']}_{j}", help=f"Deep dive into '{sub_theme['name']}'"):
                            explore_topic_in_chat(sub_theme)
                        
                        if st.button(f"📋 Details", key=f"detail_{theme['id']}_{j}", help=f"Generate detailed notes for '{sub_theme['name']}'"):
                            generate_detailed_notes(sub_theme)
                    
                    if j < len(sub_themes) - 1:  # Add separator between sub-themes
                        st.markdown("---")
            else:
                st.warning("Limited analysis depth available - this may indicate the theme needs more detailed exploration")
                st.info("💡 **Tip:** Try using the 'Regenerate' button to get more detailed analysis, or explore this theme in chat.")
            
            # Enhanced main theme exploration
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"💬 Discuss Theme", key=f"discuss_{theme['id']}", help=f"Start a conversation about '{theme['name']}'"):
                    explore_topic_in_chat(theme)
            with col2:
                if st.button(f"🔍 Deep Analysis", key=f"analyze_{theme['id']}", help=f"Generate comprehensive analysis of '{theme['name']}'"):
                    generate_comprehensive_analysis(theme)
            with col3:
                if st.button(f"📊 Data Points", key=f"data_{theme['id']}", help=f"Extract specific data and facts about '{theme['name']}'"):
                    extract_data_points(theme)

def explore_topic_in_chat(topic_data):
    """Add a topic exploration question to the chat"""
    topic_name = topic_data['name']
    topic_summary = topic_data.get('summary', '')
    
    # Create a focused question
    question = f"Tell me more about '{topic_name}'. {topic_summary} What are the key insights and details about this topic from the documents?"
    
    # Add to chat history
    st.session_state.chat_history.append({
        "role": "user",
        "content": f"[Mind Map Topic] {topic_name}"
    })
    
    with st.spinner(f"Exploring '{topic_name}'..."):
        # Get relevant context from documents
        context = st.session_state.vector_store.get_context_for_query(question)
        
        # Get AI response
        response = st.session_state.ai_client.chat_with_document(
            user_question=question,
            document_context=context,
            max_tokens=2000,
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
            # Save chat history persistently
            save_chat_history()
            st.success(f"✅ Added detailed discussion about '{topic_name}' to the chat! **Scroll up to see the conversation.**")
            # Don't rerun - let user see the success message and manually check chat
        else:
            st.error(f"Failed to explore topic: {response['error']}")

def generate_detailed_notes(topic_data):
    """Generate detailed notes for a specific topic"""
    topic_name = topic_data['name']
    topic_summary = topic_data.get('summary', '')
    
    question = f"Generate comprehensive, detailed notes about '{topic_name}'. Include specific facts, data, methodologies, and actionable insights. Break down the information into organized sections with bullet points and structured details."
    
    with st.spinner(f"Generating detailed notes for '{topic_name}'..."):
        context = st.session_state.vector_store.get_context_for_query(question)
        response = st.session_state.ai_client.chat_with_document(
            user_question=question,
            document_context=context,
            max_tokens=2500,
            temperature=0.5
        )
        
        if response["success"]:
            personality_name = st.session_state.ai_client.personalities[
                st.session_state.ai_client.current_personality
            ]["name"]
            
            st.session_state.chat_history.append({
                "role": "user",
                "content": f"[Detailed Notes] {topic_name}"
            })
            
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response["content"],
                "personality": personality_name
            })
            save_chat_history()
            st.success(f"✅ Generated detailed notes for '{topic_name}' - **scroll up to see the new content in the chat!**")
            # Don't rerun - let user see the success message and manually check chat
        else:
            st.error(f"Failed to generate notes: {response['error']}")

def generate_comprehensive_analysis(theme_data):
    """Generate comprehensive analysis for a theme"""
    theme_name = theme_data['name']
    theme_summary = theme_data.get('summary', '')
    
    question = f"Provide a comprehensive analysis of '{theme_name}'. Include: 1) Overview and context, 2) Key findings and insights, 3) Supporting evidence and data, 4) Implications and significance, 5) Related concepts and connections. Be thorough and analytical."
    
    with st.spinner(f"Generating comprehensive analysis for '{theme_name}'..."):
        context = st.session_state.vector_store.get_context_for_query(question)
        response = st.session_state.ai_client.chat_with_document(
            user_question=question,
            document_context=context,
            max_tokens=3000,
            temperature=0.4
        )
        
        if response["success"]:
            personality_name = st.session_state.ai_client.personalities[
                st.session_state.ai_client.current_personality
            ]["name"]
            
            st.session_state.chat_history.append({
                "role": "user",
                "content": f"[Comprehensive Analysis] {theme_name}"
            })
            
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response["content"],
                "personality": personality_name
            })
            save_chat_history()
            st.success(f"✅ Generated comprehensive analysis for '{theme_name}' - **scroll up to see the new content in the chat!**")
            # Don't rerun - let user see the success message and manually check chat
        else:
            st.error(f"Failed to generate analysis: {response['error']}")

def extract_data_points(theme_data):
    """Extract specific data points and facts for a theme"""
    theme_name = theme_data['name']
    theme_summary = theme_data.get('summary', '')
    
    question = f"Extract all specific data points, statistics, numbers, dates, names, and factual information related to '{theme_name}'. Present as organized lists with clear categories. Include quantitative data, qualitative findings, and cited sources where available."
    
    with st.spinner(f"Extracting data points for '{theme_name}'..."):
        context = st.session_state.vector_store.get_context_for_query(question)
        response = st.session_state.ai_client.chat_with_document(
            user_question=question,
            document_context=context,
            max_tokens=2000,
            temperature=0.2  # Lower temperature for factual extraction
        )
        
        if response["success"]:
            personality_name = st.session_state.ai_client.personalities[
                st.session_state.ai_client.current_personality
            ]["name"]
            
            st.session_state.chat_history.append({
                "role": "user",
                "content": f"[Data Points] {theme_name}"
            })
            
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response["content"],
                "personality": personality_name
            })
            save_chat_history()
            st.success(f"✅ Extracted data points for '{theme_name}' - **scroll up to see the new content in the chat!**")
            # Don't rerun - let user see the success message and manually check chat
        else:
            st.error(f"Failed to extract data points: {response['error']}")

def add_debug_info(message):
    """Add debug information to global debug log"""
    pass  # Simplified - debug info not needed with new implementation

def main():
    # Hide heading links with enhanced CSS
    st.html("""
    <style>
    /* Completely hide anchor links in headings */
    .stMarkdown h1 a,
    .stMarkdown h2 a,
    .stMarkdown h3 a,
    .stMarkdown h4 a,
    .stMarkdown h5 a,
    .stMarkdown h6 a {
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }

    /* Remove all link styling and behavior from headings */
    .stMarkdown h1,
    .stMarkdown h2,
    .stMarkdown h3,
    .stMarkdown h4,
    .stMarkdown h5,
    .stMarkdown h6 {
        text-decoration: none !important;
        color: inherit !important;
        cursor: default !important;
        pointer-events: auto !important;
    }

    /* Hide all types of anchor elements */
    .stMarkdown .anchor-link,
    .stMarkdown .anchor-link-text {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Target specific Streamlit header containers */
    div[data-testid="stMarkdownContainer"] h1 a,
    div[data-testid="stMarkdownContainer"] h2 a,
    div[data-testid="stMarkdownContainer"] h3 a {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Override any header link behavior */
    .element-container h1,
    .element-container h2,
    .element-container h3 {
        position: relative;
    }
    
    .element-container h1:hover,
    .element-container h2:hover,
    .element-container h3:hover {
        cursor: default !important;
    }
    </style>
    """)

    # Header
    st.markdown("<h1 style='margin-bottom: 1rem; color: inherit; text-decoration: none;'>🤖 AI Document Analyzer & Chat</h1>", unsafe_allow_html=True)
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
            clear_persistent_chat()
            st.success("Chat history cleared!")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    
    with col1:
        # Chat interface
        st.markdown("<h3 style='margin-bottom: 1rem; color: inherit; text-decoration: none;'>💬 Chat with Your Documents</h3>", unsafe_allow_html=True)
        
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
        st.markdown("<h3 style='margin-bottom: 1rem; color: inherit; text-decoration: none;'>📊 Document Insights</h3>", unsafe_allow_html=True)
        
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
            max_tokens=2500,
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
    
    # Save chat history persistently
    save_chat_history()
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
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption("✅ Cached result from previous analysis")
        with col2:
            if st.button("🔄 Regenerate", key="regen_summary"):
                # Clear cache and regenerate immediately
                documents_hash = get_documents_hash()
                personality = st.session_state.ai_client.current_personality
                cache_key = get_cache_key(documents_hash, "summary", personality)
                if cache_key in st.session_state.cached_analyses:
                    del st.session_state.cached_analyses[cache_key]
                generate_fresh_summary()
                return
        
        st.write(cached_result["content"])
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
                st.caption("🆕 Freshly generated analysis")
                st.write(response["content"])
                st.success("✅ Summary regenerated successfully!")
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
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption("✅ Cached result from previous analysis")
        with col2:
            if st.button("🔄 Regenerate", key="regen_key_points"):
                # Clear cache and regenerate immediately
                documents_hash = get_documents_hash()
                personality = st.session_state.ai_client.current_personality
                cache_key = get_cache_key(documents_hash, "key_points", personality)
                if cache_key in st.session_state.cached_analyses:
                    del st.session_state.cached_analyses[cache_key]
                generate_fresh_key_points()
                return
        
        st.write(cached_result["content"])
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
                st.caption("🆕 Freshly generated analysis")
                st.write(response["content"])
                st.success("✅ Key points regenerated successfully!")
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
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption("✅ Cached result from previous analysis")
        with col2:
            if st.button("🔄 Regenerate", key="regen_sentiment"):
                # Clear cache and regenerate immediately
                documents_hash = get_documents_hash()
                personality = st.session_state.ai_client.current_personality
                cache_key = get_cache_key(documents_hash, "sentiment", personality)
                if cache_key in st.session_state.cached_analyses:
                    del st.session_state.cached_analyses[cache_key]
                generate_fresh_sentiment()
                return
        
        st.write(cached_result["content"])
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
                st.caption("🆕 Freshly generated analysis")
                st.write(response["content"])
                st.success("✅ Sentiment analysis regenerated successfully!")
            else:
                st.error(f"Failed to analyze sentiment: {response['error']}")




def create_themes_from_text_with_debug(text_response):
    """Extract themes from text response when JSON parsing fails - with debugging"""
    
    try:
        # Add to global debug info  
        add_debug_info("**Text Extraction:** Starting text-based theme extraction")
        add_debug_info("Method: Extracting themes from text patterns")
        
        # Simple extraction based on common patterns
        lines = text_response.strip().split('\n')
        
        with st.expander("📝 **Debug Info** - Text-Based Theme Extraction", expanded=False):
            st.write(f"Found {len(lines)} lines to analyze")
        
        themes = []
        current_theme = None
        theme_id = 0
        processed_lines = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            processed_lines += 1
                
            # Look for theme indicators (bold text, numbered items, bullet points)
            if any(indicator in line.lower() for indicator in ['theme', 'topic', 'section', 'main', 'key']):
                if current_theme:
                    themes.append(current_theme)
                
                theme_id += 1
                current_theme = {
                    'id': f'theme_{theme_id}',
                    'name': line.replace('*', '').replace('#', '').strip()[:50],
                    'summary': f'Key theme extracted from document analysis',
                    'sub_themes': []
                }
            elif line.startswith(('-', '*', '•', '◦')) or line[0].isdigit():
                # This looks like a sub-point
                if current_theme:
                    sub_theme = {
                        'id': f'sub_theme_{theme_id}_{len(current_theme["sub_themes"])}',
                        'name': line.lstrip('- *•◦0123456789. ').strip()[:50],
                        'summary': 'Sub-theme from document analysis',
                        'sub_themes': []
                    }
                    current_theme['sub_themes'].append(sub_theme)
        
        # Add the last theme
        if current_theme:
            themes.append(current_theme)
        
        with st.expander("📝 **Debug Info** - Text-Based Theme Extraction", expanded=False):
            st.write(f"Processed {processed_lines} meaningful lines")
            st.write(f"Found {len(themes)} main themes from text analysis")
        
        # If no structured themes found, create some basic ones
        if not themes:
            with st.expander("📝 **Debug Info** - Text-Based Theme Extraction", expanded=False):
                st.warning("No structured themes found, extracting from sentences")
                
            # Try multiple extraction strategies
            
            # Strategy 1: Extract sentences as themes
            sentences = [s.strip() for s in text_response.split('.') if s.strip() and len(s.strip()) > 10]
            
            # Strategy 2: Extract lines that look like headings or important points
            lines = [line.strip() for line in text_response.split('\n') if line.strip() and len(line.strip()) > 5]
            meaningful_lines = []
            for line in lines:
                # Look for lines that seem important (capitalized, numbered, have keywords)
                if (line[0].isupper() or 
                    any(word in line.lower() for word in ['analysis', 'finding', 'conclusion', 'result', 'key', 'main', 'important']) or
                    line.startswith(tuple('123456789')) or
                    line.startswith('-') or line.startswith('*')):
                    meaningful_lines.append(line)
            
            # Use meaningful lines first, then sentences
            content_sources = meaningful_lines if meaningful_lines else sentences[:5]
            
            with st.expander("📝 **Debug Info** - Text-Based Theme Extraction", expanded=False):
                st.write(f"Found {len(meaningful_lines)} meaningful lines, {len(sentences)} sentences")
                st.write(f"Using {len(content_sources)} content sources for themes")
                
            for i, content in enumerate(content_sources[:7]):  # Max 7 themes
                if content and len(content.strip()) > 3:
                    clean_content = content.replace('*', '').replace('#', '').replace('-', '').strip()
                    themes.append({
                        'id': f'auto_theme_{i+1}',
                        'name': clean_content[:60] + ("..." if len(clean_content) > 60 else ""),
                        'summary': 'Theme extracted from document content',
                        'sub_themes': []
                    })
        
        result = {
            'title': 'Document Analysis (Text Fallback)',
            'themes': themes
        }
        
        with st.expander("📝 **Debug Info** - Text-Based Theme Extraction", expanded=False):
            if themes:
                st.success(f"✅ Successfully extracted {len(themes)} themes from text")
            else:
                st.error("❌ Failed to extract any themes")
            
        return result
        
    except Exception as e:
        with st.expander("📝 **Debug Info** - Text-Based Theme Extraction", expanded=True):
            st.error(f"❌ Text extraction failed: {str(e)}")
            st.write("Creating emergency fallback theme")
        return {
            'title': 'Document Analysis',
            'themes': [{
                'id': 'fallback_theme',
                'name': 'Document Content',
                'summary': 'Content analysis available - click to explore in chat',
                'sub_themes': []
            }]
        }

def parse_mind_map_data(mind_map_data):
    """Parse AI response into structured mind map data with optional debugging"""
    
    try:
        # Add to global debug info
        add_debug_info("**JSON Parsing Step 1:** Analyzing AI Response")
        add_debug_info(f"Response type: {type(mind_map_data)}")
        add_debug_info(f"Response length: {len(str(mind_map_data))} characters")
        preview = str(mind_map_data)[:200] + ("..." if len(str(mind_map_data)) > 200 else "")
        add_debug_info(f"Response preview: {preview}")
        
        if isinstance(mind_map_data, str):
            import re
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', mind_map_data, re.DOTALL)
            if json_match:
                with st.expander("🔧 **Debug Info** - JSON Parsing Details", expanded=False):
                    st.success("✅ Found potential JSON structure")
                
                try:
                    json_text = json_match.group()
                    
                    with st.expander("🔧 **Debug Info** - JSON Parsing Details", expanded=False):
                        st.write("**Step 3:** Original JSON found:")
                        st.code(json_text[:300] + ("..." if len(json_text) > 300 else ""), language="json")
                        st.write("**Step 4:** Applying JSON fixes")
                    
                    # Fix common JSON issues
                    original_json = json_text
                    
                    # Fix single quotes to double quotes
                    json_text = re.sub(r"'([^']*)':", r'"\1":', json_text)  # Fix property names
                    json_text = re.sub(r":\s*'([^']*)'", r': "\1"', json_text)  # Fix string values
                    
                    # Remove any markdown code blocks
                    json_text = re.sub(r'```json\s*', '', json_text)
                    json_text = re.sub(r'```\s*$', '', json_text)
                    
                    # Fix trailing commas
                    json_text = re.sub(r',\s*}', '}', json_text)  # Remove trailing commas before }
                    json_text = re.sub(r',\s*]', ']', json_text)  # Remove trailing commas before ]
                    
                    # Fix missing quotes around property names
                    json_text = re.sub(r'(\w+):', r'"\1":', json_text)
                    
                    # Fix incomplete JSON structures
                    open_braces = json_text.count('{')
                    close_braces = json_text.count('}')
                    if open_braces > close_braces:
                        json_text += '}' * (open_braces - close_braces)
                    
                    open_brackets = json_text.count('[')
                    close_brackets = json_text.count(']')
                    if open_brackets > close_brackets:
                        json_text += ']' * (open_brackets - close_brackets)
                    
                    with st.expander("🔧 **Debug Info** - JSON Parsing Details", expanded=False):
                        if original_json != json_text:
                            st.info("🔧 Applied quote fixes (single → double quotes)")
                            st.write("Fixed JSON preview:")
                            st.code(json_text[:300] + ("..." if len(json_text) > 300 else ""), language="json")
                        else:
                            st.info("ℹ️ No quote fixes needed")
                        
                        st.write("**Step 5:** Parsing JSON")
                    
                    parsed_data = json.loads(json_text)
                    
                    with st.expander("🔧 **Debug Info** - JSON Parsing Details", expanded=False):
                        st.success("✅ JSON parsed successfully!")
                        st.write("**Step 6:** Validating structure")
                    
                    # Convert old format to new format if needed
                    if 'main_themes' in parsed_data:
                        with st.expander("🔧 **Debug Info** - JSON Parsing Details", expanded=False):
                            st.info("🔄 Converting old format (main_themes → themes)")
                        parsed_data['themes'] = parsed_data.pop('main_themes')
                    
                    # Show final structure info
                    with st.expander("🔧 **Debug Info** - JSON Parsing Details", expanded=False):
                        st.write("**Final Structure:**")
                        st.write(f"- Title: {parsed_data.get('title', 'N/A')}")
                        st.write(f"- Number of main themes: {len(parsed_data.get('themes', []))}")
                        
                        # Count total themes and sub-themes
                        def count_all_themes(themes):
                            count = len(themes)
                            for theme in themes:
                                if theme.get('sub_themes'):
                                    count += count_all_themes(theme['sub_themes'])
                            return count
                        
                        total_themes = count_all_themes(parsed_data.get('themes', []))
                        st.write(f"- Total themes (including sub-themes): {total_themes}")
                        
                        if total_themes > 0:
                            st.success("🎉 Mind map data successfully parsed!")
                        else:
                            st.warning("⚠️ No themes found in parsed data")
                    
                    return parsed_data
                        
                except json.JSONDecodeError as e:
                    with st.expander("🔧 **Debug Info** - JSON Parsing Details", expanded=True):
                        st.error(f"❌ **JSON Parse Error:** {str(e)}")
                        st.write(f"Error at position: {e.pos if hasattr(e, 'pos') else 'unknown'}")
                        st.write("**Step 7:** Falling back to text extraction")
                    return create_themes_from_text_with_debug(mind_map_data)
            else:
                with st.expander("🔧 **Debug Info** - JSON Parsing Details", expanded=False):
                    st.warning("⚠️ No JSON structure found in AI response")
                    st.write("**Step 3:** Falling back to text extraction")
                return create_themes_from_text_with_debug(mind_map_data)
        else:
            with st.expander("🔧 **Debug Info** - JSON Parsing Details", expanded=False):
                st.info("ℹ️ Response is already structured data")
            return mind_map_data
            
    except Exception as e:
        with st.expander("🔧 **Debug Info** - JSON Parsing Details", expanded=True):
            st.error(f"❌ **Unexpected Error:** {str(e)}")
            st.write("**Emergency Fallback:** Creating basic structure")
        return create_themes_from_text_with_debug(str(mind_map_data))

def get_pastel_colors():
    """Return a list of pastel colors for mind map visualization"""
    return [
        '#FFB3BA',  # Light pink
        '#BAFFC9',  # Light green
        '#BAE1FF',  # Light blue
        '#FFFFBA',  # Light yellow
        '#FFD1BA',  # Light orange
        '#E0BBE4',  # Light purple
        '#B5EAD7',  # Light teal
        '#FFC9DE',  # Light rose
        '#C7CEEA',  # Light lavender
        '#B9FBC0'   # Light mint
    ]

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

def create_text_mind_map(mind_map_data):
    """Create text-based mind map when plotly is not available"""
    try:
        # Parse the mind map data
        parsed_data = parse_mind_map_data(mind_map_data)
        title = parsed_data.get('title', 'Document Analysis')
        themes = parsed_data.get('themes', [])
        
        if not themes:
            return "No themes found in the mind map data"
        
        # Create text-based mind map
        text_output = f"# 🧠 {title}\n\n"
        
        def format_theme_text(theme_list, level=0):
            result = ""
            indent = "  " * level
            bullet = "•" if level == 0 else ("◦" if level == 1 else "-")
            
            for theme in theme_list:
                name = theme.get('name', 'Unnamed Theme')
                summary = theme.get('summary', '')
                result += f"{indent}{bullet} **{name}**"
                if summary:
                    result += f": {summary}"
                result += "\n"
                
                # Add sub-themes recursively
                if theme.get('sub_themes'):
                    result += format_theme_text(theme['sub_themes'], level + 1)
            
            return result
        
        text_output += format_theme_text(themes)
        text_output += "\n\n💡 *Interactive visualization requires plotly package. Text version shown above.*"
        
        return text_output
        
    except Exception as e:
        return f"Error creating text mind map: {str(e)}"

def create_mind_map_visualization(mind_map_data):
    """Create advanced interactive mind map with unlimited depth"""
    # Check if plotly is available
    if not PLOTLY_AVAILABLE:
        st.warning(f"🔧 Plotly not available (PLOTLY_AVAILABLE={PLOTLY_AVAILABLE}). Using text fallback.")
        return create_text_mind_map(mind_map_data)
    
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
        if not PLOTLY_AVAILABLE or go is None:
            st.warning("Plotly not available, showing text version")
            return create_text_mind_map(mind_map_data)
        
        try:
            fig = go.Figure()
        except Exception as e:
            st.error(f"Failed to create plotly figure: {e}")
            return create_text_mind_map(mind_map_data)
        
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
            max_tokens=2500,
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
            # Save chat history persistently
            save_chat_history()
            st.success(f"Generated detailed notes for '{topic_name}' - check the chat!")
        else:
            st.error(f"Failed to generate notes: {response['error']}")

def generate_mind_map():
    """Generate mind map of all uploaded documents using the new MindMapGenerator"""
    if not st.session_state.documents:
        st.warning("No documents to analyze")
        return
    
    # Check cache first
    cached_result = get_cached_analysis("mind_map")
    if cached_result:
        st.subheader("🧠 Document Mind Map")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption("✅ Cached result from previous analysis")
        with col2:
            if st.button("🔄 Regenerate", key="regen_mindmap"):
                # Clear cache and regenerate immediately
                documents_hash = get_documents_hash()
                personality = st.session_state.ai_client.current_personality
                cache_key = get_cache_key(documents_hash, "mind_map", personality)
                if cache_key in st.session_state.cached_analyses:
                    del st.session_state.cached_analyses[cache_key]
                st.rerun()
        
        # Display the cached mind map
        display_mind_map_results(cached_result["content"])
        return
    
    # Generate fresh mind map
    generate_fresh_mind_map()

def generate_fresh_mind_map():
    """Generate fresh mind map using the new MindMapGenerator"""
    # Combine text from all successful documents
    all_text = ""
    doc_titles = []
    
    for filename, doc_info in st.session_state.documents.items():
        if doc_info["success"]:
            doc_text = doc_info['text'][:15000]  # Increase limit for more detailed analysis
            all_text += f"\n\n=== {filename} ===\n{doc_text}"
            doc_titles.append(filename)
    
    if all_text:
        # Generate mind map using the new generator
        mind_map_data = st.session_state.mindmap_generator.generate_mind_map(all_text, doc_titles)
        
        if "error" not in mind_map_data:
            # Save to cache
            save_analysis_cache("mind_map", mind_map_data)
            
            st.subheader("🧠 Document Mind Map")
            st.caption(f"🆕 Freshly analyzed {len(doc_titles)} documents: {', '.join(doc_titles)}")
            
            # Display the mind map
            display_mind_map_results(mind_map_data)
            st.success("✅ Mind map regenerated successfully!")
        else:
            st.error(f"❌ Failed to generate mind map: {mind_map_data['error']}")
    else:
        st.error("❌ No document content available for analysis")

if __name__ == "__main__":
    main()