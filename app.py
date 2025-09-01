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

# FIXED: Regenerate button callback functions
def regenerate_summary():
    """Callback to regenerate summary"""
    clear_analysis_cache("summary")
    st.session_state.force_regenerate_summary = True

def regenerate_key_points():
    """Callback to regenerate key points"""
    clear_analysis_cache("key_points")
    st.session_state.force_regenerate_key_points = True

def regenerate_sentiment():
    """Callback to regenerate sentiment"""
    clear_analysis_cache("sentiment")
    st.session_state.force_regenerate_sentiment = True

def regenerate_mindmap():
    """Callback to regenerate mind map"""
    clear_analysis_cache("mind_map")
    st.session_state.force_regenerate_mindmap = True

def clear_analysis_cache(analysis_type):
    """Clear cache for specific analysis type"""
    try:
        documents_hash = get_documents_hash()
        personality = st.session_state.ai_client.current_personality
        cache_key = get_cache_key(documents_hash, analysis_type, personality)
        if cache_key in st.session_state.cached_analyses:
            del st.session_state.cached_analyses[cache_key]
    except Exception as e:
        st.error(f"Error clearing cache: {e}")

# FIXED: Interactive button callback functions
def explore_topic_callback(topic_data):
    """Callback for explore topic button"""
    st.session_state.pending_exploration = {
        "topic": topic_data,
        "action": "explore",
        "timestamp": time.time()
    }

def generate_details_callback(topic_data):
    """Callback for generate details button"""
    st.session_state.pending_details = {
        "topic": topic_data,
        "action": "details",
        "timestamp": time.time()
    }

def comprehensive_analysis_callback(theme_data):
    """Callback for comprehensive analysis button"""
    st.session_state.pending_analysis = {
        "topic": theme_data,
        "action": "analysis",
        "timestamp": time.time()
    }

def extract_data_points_callback(theme_data):
    """Callback for extract data points button"""
    st.session_state.pending_data_extraction = {
        "topic": theme_data,
        "action": "data_extraction",
        "timestamp": time.time()
    }

def discuss_theme_callback(theme_data):
    """Callback for discuss theme button"""
    st.session_state.pending_discussion = {
        "topic": theme_data,
        "action": "discussion",
        "timestamp": time.time()
    }

# FIXED: Action handlers
def handle_pending_actions():
    """Handle any pending actions set by button callbacks"""
    
    # Handle exploration
    if "pending_exploration" in st.session_state:
        action = st.session_state.pending_exploration
        del st.session_state.pending_exploration
        
        topic = action["topic"]
        question = f"Tell me more about '{topic['name']}'. {topic.get('summary', '')} What are the key insights and details I should know?"
        
        # Add to chat
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []
        st.session_state.chat_messages.append({"role": "user", "message": question})
        st.success(f"💬 Started exploration of '{topic['name']}' - check the Chat tab!")
    
    # Handle details
    if "pending_details" in st.session_state:
        action = st.session_state.pending_details
        del st.session_state.pending_details
        perform_details_generation(action["topic"])
    
    # Handle analysis
    if "pending_analysis" in st.session_state:
        action = st.session_state.pending_analysis
        del st.session_state.pending_analysis
        perform_comprehensive_analysis(action["topic"])
    
    # Handle data extraction
    if "pending_data_extraction" in st.session_state:
        action = st.session_state.pending_data_extraction
        del st.session_state.pending_data_extraction
        perform_data_extraction(action["topic"])
    
    # Handle discussion
    if "pending_discussion" in st.session_state:
        action = st.session_state.pending_discussion
        del st.session_state.pending_discussion
        
        topic = action["topic"]
        question = f"Let's discuss '{topic['name']}' in detail. {topic.get('summary', '')} What are the key aspects and implications?"
        
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []
        st.session_state.chat_messages.append({"role": "user", "message": question})
        st.success(f"💬 Started discussion about '{topic['name']}' - check the Chat tab!")

def perform_comprehensive_analysis(theme_data):
    """Perform comprehensive analysis and display results"""
    try:
        all_text = []
        for filename, doc_info in st.session_state.documents.items():
            if doc_info["success"]:
                all_text.append(doc_info["text"])
        
        if not all_text:
            st.warning("No documents available for analysis")
            return
            
        combined_text = "\n\n".join(all_text)
        theme_name = theme_data["name"]
        
        with st.spinner(f"🔍 Analyzing '{theme_name}'..."):
            analysis_prompt = f"""Provide a comprehensive analysis of '{theme_name}' based on the document content.
            
            Include:
            1. Overview and background
            2. Key findings and insights
            3. Supporting evidence from documents
            4. Implications and significance
            5. Related concepts and connections
            
            Document content: {combined_text[:10000]}"""
            
            response = st.session_state.ai_client._make_api_request(
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=2000,
                temperature=0.7
            )
            
            if response["success"]:
                st.success(f"🔍 Comprehensive Analysis: {theme_name}")
                st.write(response["content"])
            else:
                st.error(f"Analysis failed: {response.get('error', 'Unknown error')}")
                
    except Exception as e:
        st.error(f"Error in comprehensive analysis: {str(e)}")

def perform_data_extraction(theme_data):
    """Extract data points and display results"""
    try:
        all_text = []
        for filename, doc_info in st.session_state.documents.items():
            if doc_info["success"]:
                all_text.append(doc_info["text"])
        
        combined_text = "\n\n".join(all_text)
        theme_name = theme_data["name"]
        
        with st.spinner(f"📊 Extracting data for '{theme_name}'..."):
            data_prompt = f"""Extract all specific data points, statistics, numbers, dates, names, and factual information related to '{theme_name}'.
            
            Format as organized bullet points:
            • **Data Point**: [Specific fact/number/date]
            • **Statistic**: [Another specific fact]
            
            Document content: {combined_text[:10000]}"""
            
            response = st.session_state.ai_client._make_api_request(
                messages=[{"role": "user", "content": data_prompt}],
                max_tokens=1500,
                temperature=0.3
            )
            
            if response["success"]:
                st.success(f"📊 Data Points: {theme_name}")
                st.write(response["content"])
            else:
                st.error(f"Data extraction failed: {response.get('error', 'Unknown error')}")
                
    except Exception as e:
        st.error(f"Error in data extraction: {str(e)}")

def perform_details_generation(sub_theme_data):
    """Generate detailed notes and display results"""
    try:
        all_text = []
        for filename, doc_info in st.session_state.documents.items():
            if doc_info["success"]:
                all_text.append(doc_info["text"])
        
        combined_text = "\n\n".join(all_text)
        topic_name = sub_theme_data["name"]
        
        with st.spinner(f"📋 Generating details for '{topic_name}'..."):
            details_prompt = f"""Generate comprehensive, detailed notes about '{topic_name}' based on the document content.
            
            Include:
            1. Detailed explanation of the concept
            2. Specific examples from the documents
            3. Step-by-step processes if applicable
            4. Key relationships and dependencies
            5. Important considerations
            
            Format as clear, organized notes with headers and bullet points.
            
            Document content: {combined_text[:10000]}"""
            
            response = st.session_state.ai_client._make_api_request(
                messages=[{"role": "user", "content": details_prompt}],
                max_tokens=2000,
                temperature=0.5
            )
            
            if response["success"]:
                st.success(f"📋 Detailed Notes: {topic_name}")
                st.write(response["content"])
            else:
                st.error(f"Details generation failed: {response.get('error', 'Unknown error')}")
                
    except Exception as e:
        st.error(f"Error in details generation: {str(e)}")

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
        
        if mermaid_content and len(mermaid_content.strip()) > 10:
            # Just show the diagram using simple HTML
            streamlit.components.v1.html(f"""
            <script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.0/dist/mermaid.min.js"></script>
            <div class="mermaid">
            {mermaid_content}
            </div>
            <script>
            mermaid.initialize({{startOnLoad:true}});
            </script>
            """, height=500)
            
            # Show code for debugging
            with st.expander("View Mermaid Code"):
                st.code(mermaid_content, language="mermaid")
        else:
            st.error("No valid mermaid content generated")

def display_mind_map_tree(mind_map_data):
    """FIXED: Display mind map as an interactive tree structure with working buttons"""
    
    # CRITICAL: Add this line at the beginning to handle button callbacks
    handle_pending_actions()
    
    title = mind_map_data.get("title", "Mind Map")
    themes = mind_map_data.get("themes", [])
    
    st.markdown(f"### {title}")
    
    if not themes:
        st.warning("No themes found in the mind map")
        return
    
    for i, theme in enumerate(themes):
        with st.expander(f"🎯 {theme['name']}", expanded=False):
            # Theme summary with better formatting
            if theme.get('summary'):
                st.markdown(f"**Summary:** {theme['summary']}")
            else:
                st.markdown("**Summary:** No summary available")
            
            st.markdown("---")
            
            # FIXED: Theme-level action buttons with proper callbacks
            col1, col2, col3 = st.columns(3)
            with col1:
                st.button(
                    "💬 Discuss", 
                    key=f"discuss_{theme['id']}_{i}",
                    help=f"Start a conversation about '{theme['name']}'",
                    on_click=discuss_theme_callback,
                    args=(theme,),
                    use_container_width=True
                )
            with col2:
                st.button(
                    "🔍 Analyze", 
                    key=f"analyze_{theme['id']}_{i}",
                    help=f"Generate comprehensive analysis of '{theme['name']}'",
                    on_click=comprehensive_analysis_callback,
                    args=(theme,),
                    use_container_width=True
                )
            with col3:
                st.button(
                    "📊 Data", 
                    key=f"data_{theme['id']}_{i}",
                    help=f"Extract specific data and facts about '{theme['name']}'",
                    on_click=extract_data_points_callback,
                    args=(theme,),
                    use_container_width=True
                )
            
            # Display sub-themes with improved formatting
            sub_themes = theme.get("sub_themes", [])
            if sub_themes:
                st.markdown("### 🌳 Sub-topics:")
                for j, sub_theme in enumerate(sub_themes):
                    with st.container():
                        # Create a nice card-like appearance for sub-themes
                        st.markdown(f"**• {sub_theme['name']}**")
                        if sub_theme.get('summary'):
                            st.markdown(f"  *{sub_theme['summary']}*")
                        else:
                            st.markdown("  *No summary available*")
                        
                        # FIXED: Sub-theme action buttons with unique keys and callbacks
                        col1, col2 = st.columns(2)
                        with col1:
                            st.button(
                                "💬 Explore", 
                                key=f"explore_{theme['id']}_{j}_{i}",
                                help=f"Deep dive into '{sub_theme['name']}'",
                                on_click=explore_topic_callback,
                                args=(sub_theme,),
                                use_container_width=True
                            )
                        with col2:
                            st.button(
                                "📋 Details", 
                                key=f"detail_{theme['id']}_{j}_{i}",
                                help=f"Generate detailed notes for '{sub_theme['name']}'",
                                on_click=generate_details_callback,
                                args=(sub_theme,),
                                use_container_width=True
                            )

def explore_topic_in_chat(topic_data):
    """Add a topic exploration question to the chat"""
    try:
        topic_name = topic_data['name']
        topic_summary = topic_data.get('summary', '')
        
        # Create a focused question
        question = f"Tell me more about '{topic_name}'. {topic_summary} What are the key insights and details I should know?"
        
        # Add to chat history
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []
        
        st.session_state.chat_messages.append({"role": "user", "message": question})
        
        st.success(f"✅ Added exploration question about '{topic_name}' to chat!")
        
    except Exception as e:
        st.error(f"Error in topic exploration: {str(e)}")

def generate_detailed_notes(topic_data):
    """Generate detailed notes for a specific topic"""
    try:
        topic_name = topic_data['name']
        topic_summary = topic_data.get('summary', '')
        
        question = f"Generate comprehensive, detailed notes about '{topic_name}'. Include specific facts, data, methodologies, and analysis. Context: {topic_summary}"
        
        # Process with AI
        all_text = []
        for filename, doc_info in st.session_state.documents.items():
            if doc_info["success"]:
                all_text.append(doc_info["text"])
        
        if all_text:
            combined_text = "\n\n".join(all_text)
            response = st.session_state.ai_client.chat_with_document(
                question, combined_text[:8000]
            )
            
            if response["success"]:
                st.success(f"📋 Detailed Notes: {topic_name}")
                st.write(response["content"])
            else:
                st.error(f"Failed to generate notes: {response['error']}")
        else:
            st.warning("No documents available for analysis")
            
    except Exception as e:
        st.error(f"Error generating detailed notes: {str(e)}")

def generate_comprehensive_analysis(theme_data):
    """Generate comprehensive analysis for a theme"""
    try:
        theme_name = theme_data['name']
        theme_summary = theme_data.get('summary', '')
        
        question = f"Provide a comprehensive analysis of '{theme_name}'. Include: 1) Overview and context, 2) Key findings and insights, 3) Supporting evidence, 4) Implications and significance, 5) Related concepts. Context: {theme_summary}"
        
        # Process with AI
        all_text = []
        for filename, doc_info in st.session_state.documents.items():
            if doc_info["success"]:
                all_text.append(doc_info["text"])
        
        if all_text:
            combined_text = "\n\n".join(all_text)
            response = st.session_state.ai_client.chat_with_document(
                question, combined_text[:8000]
            )
            
            if response["success"]:
                st.success(f"🔍 Comprehensive Analysis: {theme_name}")
                st.write(response["content"])
            else:
                st.error(f"Failed to generate analysis: {response['error']}")
        else:
            st.warning("No documents available for analysis")
            
    except Exception as e:
        st.error(f"Error in comprehensive analysis: {str(e)}")

def extract_data_points(theme_data):
    """Extract specific data points and facts for a theme"""
    try:
        theme_name = theme_data['name']
        theme_summary = theme_data.get('summary', '')
        
        question = f"Extract all specific data points, statistics, numbers, dates, names, and factual information related to '{theme_name}'. Present as organized bullet points. Context: {theme_summary}"
        
        # Process with AI
        all_text = []
        for filename, doc_info in st.session_state.documents.items():
            if doc_info["success"]:
                all_text.append(doc_info["text"])
        
        if all_text:
            combined_text = "\n\n".join(all_text)
            response = st.session_state.ai_client.chat_with_document(
                question, combined_text[:8000]
            )
            
            if response["success"]:
                st.success(f"📊 Data Points: {theme_name}")
                st.write(response["content"])
            else:
                st.error(f"Failed to extract data points: {response['error']}")
        else:
            st.warning("No documents available for analysis")
            
    except Exception as e:
        st.error(f"Error extracting data points: {str(e)}")

def remove_document(filename):
    """Remove a document from the collection"""
    try:
        if filename in st.session_state.documents:
            del st.session_state.documents[filename]
            # Clear vector store for the removed document
            st.session_state.vector_store.clear()
            # Rebuild vector store with remaining documents
            for fname, doc_info in st.session_state.documents.items():
                if doc_info["success"]:
                    st.session_state.vector_store.add_document(doc_info)
            st.success(f"Removed {filename}")
        else:
            st.error(f"Document {filename} not found")
    except Exception as e:
        st.error(f"Error removing document: {str(e)}")

def upload_document():
    """Handle document upload"""
    uploaded_file = st.file_uploader(
        "Upload a document",
        type=['pdf', 'docx', 'doc', 'txt'],
        help="Supported formats: PDF, Word documents (.docx, .doc), Plain text (.txt)"
    )
    
    if uploaded_file is not None:
        if uploaded_file.name not in st.session_state.documents:
            with st.spinner(f"Processing {uploaded_file.name}..."):
                # Process the document
                doc_result = st.session_state.processor.process_document(
                    uploaded_file, uploaded_file.name
                )
                
                # Store in session state
                st.session_state.documents[uploaded_file.name] = doc_result
                
                # Add to vector store if successful
                if doc_result["success"]:
                    st.session_state.vector_store.add_document(doc_result)
                    st.success(f"✅ Successfully processed {uploaded_file.name}")
                    st.info(f"📄 {doc_result['word_count']} words, {doc_result['chunk_count']} chunks")
                else:
                    st.error(f"❌ Failed to process {uploaded_file.name}: {doc_result['error']}")
        else:
            st.warning(f"Document {uploaded_file.name} already uploaded")

def display_documents():
    """Display uploaded documents"""
    if st.session_state.documents:
        st.write("**Uploaded Documents:**")
        for filename, doc_info in st.session_state.documents.items():
            with st.expander(f"📄 {filename}"):
                if doc_info["success"]:
                    st.write(st.session_state.processor.get_document_summary(doc_info))
                    if st.button(f"Remove {filename}", key=f"remove_{filename}"):
                        remove_document(filename)
                else:
                    st.error(f"Error: {doc_info['error']}")
                    if st.button(f"Remove {filename}", key=f"remove_{filename}"):
                        remove_document(filename)
    else:
        st.info("No documents uploaded yet")

def generate_fresh_summary():
    """Generate fresh document summary"""
    try:
        with st.status("🤖 Generating document summary...", expanded=True) as status:
            all_text = []
            document_titles = []
            
            for filename, doc_info in st.session_state.documents.items():
                if doc_info["success"]:
                    all_text.append(doc_info["text"])
                    document_titles.append(filename)
            
            if not all_text:
                st.warning("No valid documents to analyze")
                return
            
            combined_text = "\n\n=== DOCUMENT SEPARATOR ===\n\n".join(all_text)
            st.write(f"📊 Analyzing {len(document_titles)} document(s)...")
            
            # Generate summary using AI
            response = st.session_state.ai_client.analyze_document(
                combined_text[:15000],  # Increased limit for better analysis
                "summary"
            )
            
            if response["success"]:
                content = response["content"]
                status.update(label="✅ Summary generated!", state="complete")
                
                # Cache the result
                save_analysis_cache("summary", content)
                
                # Display with regenerate option
                col1, col2 = st.columns([3, 1])
                with col2:
                    st.button("🔄 Regenerate", key="regen_summary_new", on_click=regenerate_summary)
                
                st.write(content)
            else:
                st.error(f"Error generating summary: {response['error']}")
                
    except Exception as e:
        st.error(f"Error in summary generation: {str(e)}")

def generate_fresh_key_points():
    """Generate fresh key points analysis"""
    try:
        with st.status("🎯 Extracting key points...", expanded=True) as status:
            all_text = []
            
            for filename, doc_info in st.session_state.documents.items():
                if doc_info["success"]:
                    all_text.append(doc_info["text"])
            
            if not all_text:
                st.warning("No valid documents to analyze")
                return
            
            combined_text = "\n\n".join(all_text)
            st.write("🔍 Identifying key insights and conclusions...")
            
            response = st.session_state.ai_client.analyze_document(
                combined_text[:15000],
                "key_points"
            )
            
            if response["success"]:
                content = response["content"]
                status.update(label="✅ Key points extracted!", state="complete")
                
                save_analysis_cache("key_points", content)
                
                col1, col2 = st.columns([3, 1])
                with col2:
                    st.button("🔄 Regenerate", key="regen_key_points_new", on_click=regenerate_key_points)
                
                st.write(content)
            else:
                st.error(f"Error extracting key points: {response['error']}")
                
    except Exception as e:
        st.error(f"Error in key points extraction: {str(e)}")

def generate_fresh_sentiment():
    """Generate fresh sentiment analysis"""
    try:
        with st.status("📈 Analyzing sentiment and tone...", expanded=True) as status:
            all_text = []
            
            for filename, doc_info in st.session_state.documents.items():
                if doc_info["success"]:
                    all_text.append(doc_info["text"])
            
            if not all_text:
                st.warning("No valid documents to analyze")
                return
            
            combined_text = "\n\n".join(all_text)
            st.write("🎭 Examining emotional tone and attitudes...")
            
            response = st.session_state.ai_client.analyze_document(
                combined_text[:15000],
                "sentiment"
            )
            
            if response["success"]:
                content = response["content"]
                status.update(label="✅ Sentiment analysis complete!", state="complete")
                
                save_analysis_cache("sentiment", content)
                
                col1, col2 = st.columns([3, 1])
                with col2:
                    st.button("🔄 Regenerate", key="regen_sentiment_new", on_click=regenerate_sentiment)
                
                st.write(content)
            else:
                st.error(f"Error analyzing sentiment: {response['error']}")
                
    except Exception as e:
        st.error(f"Error in sentiment analysis: {str(e)}")

def generate_fresh_mind_map():
    """Generate fresh mind map"""
    try:
        all_text = []
        document_titles = []
        
        for filename, doc_info in st.session_state.documents.items():
            if doc_info["success"]:
                all_text.append(doc_info["text"])
                document_titles.append(filename)
        
        if not all_text:
            st.warning("No valid documents to analyze")
            return
        
        combined_text = "\n\n".join(all_text)
        
        # Generate mind map
        mind_map_data = st.session_state.mindmap_generator.generate_mind_map(
            combined_text, document_titles
        )
        
        if mind_map_data and "error" not in mind_map_data:
            # Cache the result
            save_analysis_cache("mind_map", mind_map_data)
            
            # Display with regenerate option
            col1, col2 = st.columns([3, 1])
            with col2:
                st.button("🔄 Regenerate", key="regen_mindmap_new", on_click=regenerate_mindmap)
            
            display_mind_map_results(mind_map_data)
        else:
            st.error(f"Failed to generate mind map: {mind_map_data.get('error', 'Unknown error')}")
            
    except Exception as e:
        st.error(f"Error in mind map generation: {str(e)}")

# FIXED: Main analysis functions with proper regenerate handling
def generate_document_summary():
    """Generate document summary with proper regenerate handling"""
    if not st.session_state.documents:
        st.warning("No documents to analyze")
        return
    
    # Check for forced regeneration
    if st.session_state.get("force_regenerate_summary", False):
        st.session_state.force_regenerate_summary = False
        generate_fresh_summary()
        return
    
    # Check cache
    cached_result = get_cached_analysis("summary")
    if cached_result:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("📄 Using cached analysis")
        with col2:
            st.button("🔄 Regenerate", key="regen_summary", on_click=regenerate_summary)
        
        st.write(cached_result["content"])
        return
    
    generate_fresh_summary()

def extract_key_points():
    """Extract key points with proper regenerate handling"""
    if not st.session_state.documents:
        st.warning("No documents to analyze")
        return
    
    # Check for forced regeneration
    if st.session_state.get("force_regenerate_key_points", False):
        st.session_state.force_regenerate_key_points = False
        generate_fresh_key_points()
        return
    
    # Check cache
    cached_result = get_cached_analysis("key_points")
    if cached_result:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("🎯 Using cached analysis")
        with col2:
            st.button("🔄 Regenerate", key="regen_key_points", on_click=regenerate_key_points)
        
        st.write(cached_result["content"])
        return
    
    generate_fresh_key_points()

def analyze_sentiment():
    """Analyze sentiment with proper regenerate handling"""
    if not st.session_state.documents:
        st.warning("No documents to analyze")
        return
    
    # Check for forced regeneration
    if st.session_state.get("force_regenerate_sentiment", False):
        st.session_state.force_regenerate_sentiment = False
        generate_fresh_sentiment()
        return
    
    # Check cache
    cached_result = get_cached_analysis("sentiment")
    if cached_result:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("📈 Using cached analysis")
        with col2:
            st.button("🔄 Regenerate", key="regen_sentiment", on_click=regenerate_sentiment)
        
        st.write(cached_result["content"])
        return
    
    generate_fresh_sentiment()

def generate_mind_map():
    """Generate mind map with proper regenerate handling"""
    if not st.session_state.documents:
        st.warning("No documents to analyze")
        return
    
    # Check for forced regeneration
    if st.session_state.get("force_regenerate_mindmap", False):
        st.session_state.force_regenerate_mindmap = False
        generate_fresh_mind_map()
        return
    
    # Check cache
    cached_result = get_cached_analysis("mind_map")
    if cached_result:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("🧠 Using cached mind map")
        with col2:
            st.button("🔄 Regenerate", key="regen_mindmap", on_click=regenerate_mindmap)
        
        display_mind_map_results(cached_result["content"])
        return
    
    generate_fresh_mind_map()

# Custom CSS for the layout
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 100%;
    }
    .sources-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e9ecef;
        max-height: 80vh;
        overflow-y: auto;
    }
    .chat-section {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e9ecef;
        max-height: 80vh;
        display: flex;
        flex-direction: column;
    }
    .studio-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e9ecef;
        max-height: 80vh;
        overflow-y: auto;
    }
    .chat-messages {
        flex: 1;
        overflow-y: auto;
        max-height: 60vh;
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .analysis-card {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e9ecef;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Main three-column layout
sources_col, chat_col, studio_col = st.columns([1, 2, 2])

# SOURCES COLUMN (Left)
with sources_col:
    with st.container():
        st.markdown('<div class="sources-section">', unsafe_allow_html=True)
        
        # Sources header with collapse functionality
        sources_expanded = st.checkbox("📁 Sources", value=True)
        
        if sources_expanded:
            # Document upload
            st.markdown("### Add Documents")
            upload_document()
            
            st.markdown("---")
            
            # Document list
            st.markdown("### Documents")
            display_documents()
            
            st.markdown("---")
            
            # AI Settings
            st.markdown("### ⚙️ Settings")
            
            # Model selection
            available_models = st.session_state.ai_client.available_models
            if available_models:
                current_model_key = None
                for key, value in available_models.items():
                    if value == st.session_state.ai_client.current_model:
                        current_model_key = key
                        break
                
                if current_model_key:
                    model_options = list(available_models.keys())
                    current_index = model_options.index(current_model_key)
                    
                    selected_model = st.selectbox(
                        "AI Model",
                        options=model_options,
                        index=current_index,
                        help="Choose the AI model"
                    )
                    
                    if selected_model != current_model_key:
                        if st.session_state.ai_client.set_model(selected_model):
                            st.success(f"Switched to {selected_model}")
                        else:
                            st.error(f"Failed to switch to {selected_model}")
            
            # Personality selection
            personalities = st.session_state.ai_client.get_available_personalities()
            personality_options = list(personalities.keys())
            
            current_personality_index = personality_options.index(st.session_state.ai_client.current_personality)
            
            selected_personality = st.selectbox(
                "AI Personality",
                options=personality_options,
                format_func=lambda x: personalities[x]["name"],
                index=current_personality_index,
                help="Choose AI personality"
            )
            
            if selected_personality != st.session_state.ai_client.current_personality:
                if st.session_state.ai_client.set_personality(selected_personality):
                    st.success(f"Switched to {personalities[selected_personality]['name']}")
                    st.session_state.cached_analyses = {}
                else:
                    st.error(f"Failed to switch personality")
            
            # Clear chat button
            if st.button("🗑️ Clear Chat", use_container_width=True):
                clear_persistent_chat()
                st.success("Chat cleared!")
        
        st.markdown('</div>', unsafe_allow_html=True)

# CHAT COLUMN (Middle)
with chat_col:
    with st.container():
        st.markdown('<div class="chat-section">', unsafe_allow_html=True)
        
        st.markdown('<div class="section-header">💬 Chat</div>', unsafe_allow_html=True)
        
        # Initialize chat messages
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []
        
        # Chat messages container (scrollable)
        st.markdown('<div class="chat-messages">', unsafe_allow_html=True)
        
        if st.session_state.documents:
            # Display chat history
            for i, message in enumerate(st.session_state.chat_messages):
                if message["role"] == "user":
                    with st.chat_message("user"):
                        st.write(message["message"])
                else:
                    with st.chat_message("assistant"):
                        st.write(message["message"])
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Chat input at bottom
            user_question = st.chat_input("Ask a question about your documents...")
            
            if user_question:
                # Add user message to chat
                st.session_state.chat_messages.append({"role": "user", "message": user_question})
                
                # Get relevant context from documents
                with st.spinner("🤖 Thinking..."):
                    # Use vector store to find relevant chunks
                    results = st.session_state.vector_store.search(user_question)
                    
                    if results:
                        context = "\n\n".join([result["chunk"]["text"] for result in results[:3]])
                    else:
                        # Fallback: use first chunk of each document
                        context_parts = []
                        for filename, doc_info in st.session_state.documents.items():
                            if doc_info["success"] and doc_info["chunks"]:
                                context_parts.append(doc_info["chunks"][0]["text"])
                        context = "\n\n".join(context_parts)
                    
                    # Get AI response
                    response = st.session_state.ai_client.chat_with_document(
                        user_question,
                        context,
                        max_tokens=1000
                    )
                    
                    # Add response to chat
                    if response["success"]:
                        ai_message = response["content"]
                        st.session_state.chat_messages.append({"role": "assistant", "message": ai_message})
                        save_chat_history()
                        st.rerun()
                    else:
                        error_message = f"Sorry, I encountered an error: {response['error']}"
                        st.session_state.chat_messages.append({"role": "assistant", "message": error_message})
                        st.rerun()
        else:
            st.markdown('</div>', unsafe_allow_html=True)
            st.write("Upload documents to start chatting!")
        
        st.markdown('</div>', unsafe_allow_html=True)

# STUDIO COLUMN (Right) 
with studio_col:
    with st.container():
        st.markdown('<div class="studio-section">', unsafe_allow_html=True)
        
        # Studio header
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown('<div class="section-header">🎬 Studio</div>', unsafe_allow_html=True)
        with col2:
            if st.button("🔄", help="Refresh all analyses"):
                st.session_state.cached_analyses = {}
                st.rerun()
        
        if st.session_state.documents:
            # Analysis buttons in a grid
            st.markdown("### Generate Analysis")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📝 Summary", use_container_width=True):
                    generate_document_summary()
                    st.rerun()
                if st.button("🎯 Key Points", use_container_width=True):
                    extract_key_points()
                    st.rerun()
            with col2:
                if st.button("🧠 Mind Map", use_container_width=True):
                    generate_mind_map()
                    st.rerun()
                if st.button("📈 Sentiment", use_container_width=True):
                    analyze_sentiment()
                    st.rerun()
            
            st.markdown("---")
            
            # Display cached analyses
            if st.session_state.cached_analyses:
                st.markdown("### Analysis Results")
                
                # Summary section
                summary_cache = get_cached_analysis("summary")
                if summary_cache:
                    with st.expander("📝 Document Summary", expanded=True):
                        st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
                        st.write(summary_cache["content"])
                        st.markdown('</div>', unsafe_allow_html=True)
                
                # Key points section
                key_points_cache = get_cached_analysis("key_points")
                if key_points_cache:
                    with st.expander("🎯 Key Points", expanded=True):
                        st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
                        st.write(key_points_cache["content"])
                        st.markdown('</div>', unsafe_allow_html=True)
                
                # Sentiment section
                sentiment_cache = get_cached_analysis("sentiment")
                if sentiment_cache:
                    with st.expander("📈 Sentiment Analysis", expanded=True):
                        st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
                        st.write(sentiment_cache["content"])
                        st.markdown('</div>', unsafe_allow_html=True)
                
                # Mind map section
                mindmap_cache = get_cached_analysis("mind_map")
                if mindmap_cache:
                    with st.expander("🧠 Mind Map", expanded=True):
                        st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
                        display_mind_map_results(mindmap_cache["content"])
                        st.markdown('</div>', unsafe_allow_html=True)
            
        else:
            st.info("Upload documents to start analyzing!")
            st.markdown("""
            ### Welcome to AI Document Analyzer!
            
            **What you can do:**
            
            🔍 **Analyze Documents**: Extract summaries, key points, and insights  
            🧠 **Generate Mind Maps**: Visual representations of document content  
            💬 **Chat with Documents**: Ask questions and get contextual answers  
            🎭 **Multiple AI Personalities**: Specialized perspectives  
            
            **Supported formats**: PDF, Word documents, Plain text
            
            Upload your documents using the Sources section to begin!
            """)
        
        st.markdown('</div>', unsafe_allow_html=True)