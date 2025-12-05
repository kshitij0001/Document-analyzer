# AI Document Analyzer & Chat

## Overview

This project is a NotebookLM-inspired document analysis tool built with Streamlit that allows users to upload documents (PDF, Word, text files) and interact with them through AI-powered chat. The application extracts text from documents, processes them into searchable chunks, and provides intelligent responses using free AI models from OpenRouter. It features multiple AI personalities (General Assistant, Academic Researcher, Business Analyst) to provide specialized perspectives on document content.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

**Frontend Framework**: Streamlit-based web application with a clean, user-friendly interface featuring document upload, chat functionality, and sidebar controls for document management and AI settings.

**Document Processing Pipeline**: Multi-format document processor supporting PDF (PyPDF2), Word documents (python-docx), and plain text files. Documents are automatically chunked into manageable segments with configurable overlap for better context preservation during analysis.

**Vector Search System**: TF-IDF based vector store implementation using scikit-learn for document similarity search. This lightweight approach provides efficient text retrieval without requiring external vector databases, making it suitable for local deployment.

**AI Integration**: OpenRouter API integration using free AI models (Llama 3.2 variants and Qwen 2.5) for document analysis and chat responses. The system supports multiple AI personalities with specialized system prompts for different analysis perspectives.

**Session Management**: Streamlit session state management for maintaining document collections, chat history, and user preferences across interactions.

**Text Processing**: Comprehensive text extraction and cleaning pipeline with chunking strategies optimized for maintaining context while enabling efficient search and retrieval.

## External Dependencies

**AI Services**: OpenRouter API for accessing free AI models (meta-llama/llama-3.2-3b-instruct:free, meta-llama/llama-3.2-1b-instruct:free, qwen/qwen-2.5-7b-instruct:free)

**Document Processing Libraries**: PyPDF2 for PDF text extraction, python-docx for Word document processing

**Machine Learning**: scikit-learn for TF-IDF vectorization and cosine similarity calculations

**Web Framework**: Streamlit for the web interface and user interaction management

**HTTP Client**: requests library for API communication with OpenRouter services

**Additional Components**: The codebase includes a separate title generation module using OpenAI's GPT-5 model, though this appears to be a standalone component not integrated with the main document analyzer workflow.
