# -*- coding: utf-8 -*-
# AI Document Analyzer & Chat - Main Streamlit Application
# A NotebookLM-inspired document analysis tool with AI chat capabilities

import streamlit as st
import time
import os
from document_processor import DocumentProcessor
from vector_store import VectorStore
from ai_client import AIClient

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
    
    with st.spinner("Generating summary..."):
        # Combine text from all successful documents
        all_text = ""
        for filename, doc_info in st.session_state.documents.items():
            if doc_info["success"]:
                all_text += f"\n\n--- {filename} ---\n{doc_info['text'][:2000]}"  # Limit text
        
        if all_text:
            response = st.session_state.ai_client.analyze_document(all_text, "summary")
            
            if response["success"]:
                st.subheader("📝 Document Summary")
                st.write(response["content"])
            else:
                st.error(f"Failed to generate summary: {response['error']}")

def extract_key_points():
    """Extract key points from documents"""
    if not st.session_state.documents:
        st.warning("No documents to analyze")
        return
    
    with st.spinner("Extracting key points..."):
        # Get combined text
        all_text = ""
        for filename, doc_info in st.session_state.documents.items():
            if doc_info["success"]:
                all_text += f"\n\n--- {filename} ---\n{doc_info['text'][:2000]}"
        
        if all_text:
            response = st.session_state.ai_client.analyze_document(all_text, "key_points")
            
            if response["success"]:
                st.subheader("🎯 Key Points")
                st.write(response["content"])
            else:
                st.error(f"Failed to extract key points: {response['error']}")

def analyze_sentiment():
    """Analyze sentiment of documents"""
    if not st.session_state.documents:
        st.warning("No documents to analyze")
        return
    
    with st.spinner("Analyzing sentiment..."):
        # Get combined text
        all_text = ""
        for filename, doc_info in st.session_state.documents.items():
            if doc_info["success"]:
                all_text += f"\n\n--- {filename} ---\n{doc_info['text'][:2000]}"
        
        if all_text:
            response = st.session_state.ai_client.analyze_document(all_text, "sentiment")
            
            if response["success"]:
                st.subheader("📈 Sentiment Analysis")
                st.write(response["content"])
            else:
                st.error(f"Failed to analyze sentiment: {response['error']}")

if __name__ == "__main__":
    main()