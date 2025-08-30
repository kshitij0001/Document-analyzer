# AI Document Analyzer - Deployment Guide

This guide shows you how to deploy your AI Document Analyzer on Streamlit Community Cloud and Hugging Face Spaces.

## 🚀 Option 1: Streamlit Community Cloud (Recommended)

### Prerequisites
- GitHub account
- All your project files in a GitHub repository

### Step-by-Step Instructions

1. **Prepare Your Repository**
   ```bash
   # Create a requirements.txt file
   streamlit==1.28.1
   PyPDF2==3.0.1
   python-docx==1.2.0
   requests==2.31.0
   scikit-learn==1.7.1
   numpy==1.24.3
   scipy==1.11.4
   ```

2. **Upload to GitHub**
   - Create a new GitHub repository
   - Upload all your project files:
     - `app.py`
     - `document_processor.py`
     - `vector_store.py`
     - `ai_client.py`
     - `requirements.txt`
     - `.streamlit/config.toml`

3. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Connect your GitHub account
   - Select your repository
   - Set main file path: `app.py`
   - Click "Deploy!"

4. **Configuration**
   Your app will be available at: `https://your-app-name.streamlit.app`

### Expected Timeline
- Setup: 5 minutes
- Deployment: 2-3 minutes
- Total: ~10 minutes

---

## 🤗 Option 2: Hugging Face Spaces

### Prerequisites
- Hugging Face account (free)
- Basic understanding of Git

### Step-by-Step Instructions

1. **Create a New Space**
   - Go to [huggingface.co/spaces](https://huggingface.co/spaces)
   - Click "Create new Space"
   - Choose "Streamlit" as the SDK
   - Set your space name (e.g., "ai-document-analyzer")
   - Choose "Public" (free)

2. **Clone and Setup**
   ```bash
   # Clone your space
   git clone https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
   cd YOUR_SPACE_NAME
   
   # Copy your files
   cp /path/to/your/app.py .
   cp /path/to/your/document_processor.py .
   cp /path/to/your/vector_store.py .
   cp /path/to/your/ai_client.py .
   ```

3. **Create Requirements File**
   ```bash
   # Create requirements.txt
   echo "streamlit==1.28.1
   PyPDF2==3.0.1
   python-docx==1.2.0
   requests==2.31.0
   scikit-learn==1.7.1
   numpy==1.24.3
   scipy==1.11.4" > requirements.txt
   ```

4. **Create Configuration**
   ```bash
   # Create .streamlit directory and config
   mkdir .streamlit
   echo "[server]
   headless = true
   address = \"0.0.0.0\"
   port = 7860
   maxUploadSize = 200" > .streamlit/config.toml
   ```

5. **Deploy**
   ```bash
   # Commit and push
   git add .
   git commit -m "Add AI Document Analyzer"
   git push
   ```

6. **Access Your App**
   Your app will be available at: `https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME`

### Expected Timeline
- Setup: 10 minutes
- Deployment: 5 minutes
- Total: ~15 minutes

---

## 🛠️ Local Development

### Setup
```bash
# Clone your repository
git clone YOUR_REPO_URL
cd your-project

# Install dependencies
pip install -r requirements.txt

# Run locally
streamlit run app.py
```

### Access
- Local URL: `http://localhost:8501`

---

## 📋 Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all dependencies are in `requirements.txt`
   - Check Python version compatibility

2. **File Upload Issues**
   - Verify `maxUploadSize` in config.toml
   - Check file permissions

3. **AI API Errors**
   - Ensure internet connection
   - Check OpenRouter API status
   - Verify free model availability

### Performance Tips

1. **Optimize for Speed**
   - Use smaller chunk sizes for large documents
   - Limit document size (recommended: < 10MB)
   - Cache processed documents

2. **Memory Management**
   - Clear chat history regularly
   - Remove old documents from vector store
   - Monitor memory usage

---

## 🔧 Customization

### Changing AI Models
Edit `ai_client.py`:
```python
self.free_models = {
    "llama-3.2-3b": "meta-llama/llama-3.2-3b-instruct:free",
    "your-model": "your-model-path:free"
}
```

### Adding New File Types
Edit `document_processor.py`:
```python
# Add new file extension
elif filename.lower().endswith('.your_extension'):
    text = self._extract_your_format(file)
    file_type = "Your Format"
```

### Custom AI Personalities
Edit `ai_client.py`:
```python
"your_personality": {
    "name": "Your Expert",
    "description": "Your description",
    "system_prompt": "Your custom prompt..."
}
```

---

## 📊 Monitoring

### Streamlit Cloud
- View app logs in the Streamlit Cloud dashboard
- Monitor app health and usage statistics
- Check deployment status

### Hugging Face Spaces
- View logs in the Space settings
- Monitor community engagement
- Track space analytics

---

## 💡 Tips for Success

1. **Choose the Right Platform**
   - **Streamlit Cloud**: Better for professional portfolios
   - **Hugging Face**: Better for AI community exposure

2. **Optimize Performance**
   - Keep documents under 10MB
   - Use efficient chunk sizes
   - Monitor memory usage

3. **User Experience**
   - Add clear instructions
   - Handle errors gracefully
   - Provide feedback on processing

4. **Portfolio Value**
   - Document your process
   - Share deployment links
   - Explain technical decisions

---

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review platform-specific documentation
3. Test locally first
4. Check community forums

**Platform Documentation:**
- Streamlit: [docs.streamlit.io](https://docs.streamlit.io)
- Hugging Face: [huggingface.co/docs](https://huggingface.co/docs)

Good luck with your deployment! 🚀