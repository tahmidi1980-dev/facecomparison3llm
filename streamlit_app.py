import streamlit as st
import time
import json
from pathlib import Path
from PIL import Image
import sys

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from backend.orchestrator import orchestrator
from backend.logger import logger as comparison_logger
from backend.image_processor import processor
import backend.config as config

# Page Configuration
st.set_page_config(
    page_title="Face Comparison System",
    page_icon="🎭",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS with Enhanced Interactivity
st.markdown("""
<style>
    /* Main container */
    .main {
        padding-top: 2rem;
    }
    
    /* Header styling with gradient animation */
    .header-container {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 1rem;
        margin-bottom: 2rem;
        color: white;
        animation: fadeIn 0.8s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .header-icon {
        font-size: 3rem;
        margin-bottom: 0.5rem;
        animation: bounce 2s infinite;
    }
    
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    
    .header-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .header-subtitle {
        font-size: 1rem;
        opacity: 0.9;
    }
    
    /* Result cards with hover effect */
    .result-card {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(16, 185, 129, 0.05) 100%);
        padding: 2rem;
        border-radius: 1rem;
        text-align: center;
        margin: 2rem 0;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .result-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
    }
    
    .result-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
        animation: scaleIn 0.5s ease;
    }
    
    @keyframes scaleIn {
        from { transform: scale(0); }
        to { transform: scale(1); }
    }
    
    .result-title {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    /* Stage indicators with smooth transitions */
    .stage-container {
        display: flex;
        justify-content: space-around;
        margin: 2rem 0;
        gap: 1rem;
    }
    
    .stage {
        text-align: center;
        padding: 1rem;
        border-radius: 0.5rem;
        transition: all 0.3s ease;
    }
    
    .stage:hover {
        background: rgba(99, 102, 241, 0.05);
    }
    
    .stage-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    
    .stage-label {
        font-size: 0.875rem;
        color: #6b7280;
        font-weight: 500;
    }
    
    /* Info box with hover effect */
    .info-box {
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #6366f1;
        transition: all 0.3s ease;
    }
    
    .info-box:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
    }
    
    /* Enhanced button styling */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        color: white;
        font-weight: 600;
        padding: 0.75rem 2rem;
        border-radius: 0.75rem;
        border: none;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .stButton>button:hover {
        box-shadow: 0 10px 20px rgba(99, 102, 241, 0.4);
        transform: translateY(-2px);
    }
    
    .stButton>button:active {
        transform: translateY(0);
    }
    
    /* Download button special styling */
    .stDownloadButton>button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    }
    
    .stDownloadButton>button:hover {
        box-shadow: 0 10px 20px rgba(16, 185, 129, 0.4);
    }
    
    /* Progress bar animation */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #6366f1, #8b5cf6, #6366f1);
        background-size: 200% 100%;
        animation: shimmer 2s infinite;
    }
    
    @keyframes shimmer {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    
    /* Metric cards enhancement */
    .stMetric {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }
    
    .stMetric:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(16, 185, 129, 0.05) 100%);
        border-radius: 0.5rem;
        font-weight: 600;
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(16, 185, 129, 0.1) 100%);
    }
    
    /* Sidebar enhancement */
    .css-1d391kg {
        background: linear-gradient(180deg, #f9fafb 0%, #ffffff 100%);
    }
    
    /* Image upload area */
    .stFileUploader {
        border: 2px dashed #6366f1;
        border-radius: 0.5rem;
        padding: 1rem;
        transition: all 0.3s ease;
    }
    
    .stFileUploader:hover {
        border-color: #4f46e5;
        background: rgba(99, 102, 241, 0.02);
    }
</style>

<script>
// Enhanced interactivity with JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Smooth scroll behavior
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
    
    // Add ripple effect to buttons
    document.querySelectorAll('.stButton>button').forEach(button => {
        button.addEventListener('click', function(e) {
            let ripple = document.createElement('span');
            ripple.classList.add('ripple');
            this.appendChild(ripple);
            
            let x = e.clientX - e.target.offsetLeft;
            let y = e.clientY - e.target.offsetTop;
            
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            
            setTimeout(() => ripple.remove(), 600);
        });
    });
    
    // Add loading spinner to buttons when clicked
    document.querySelectorAll('.stButton>button').forEach(button => {
        button.addEventListener('click', function() {
            if (!this.disabled) {
                this.innerHTML = '<span class="spinner"></span> ' + this.innerHTML;
            }
        });
    });
});
</script>
""", unsafe_allow_html=True)

# Session State Initialization
if 'stage' not in st.session_state:
    st.session_state.stage = 'upload'

if 'result' not in st.session_state:
    st.session_state.result = None

if 'uploaded_images' not in st.session_state:
    st.session_state.uploaded_images = {'img1': None, 'img2': None}

if 'progress_data' not in st.session_state:
    st.session_state.progress_data = {
        'percentage': 0,
        'message': '',
        'current_stage': None
    }

# Helper Functions

def reset_app():
    """Reset application to initial state"""
    st.session_state.stage = 'upload'
    st.session_state.result = None
    st.session_state.uploaded_images = {'img1': None, 'img2': None}
    st.session_state.progress_data = {
        'percentage': 0,
        'message': '',
        'current_stage': None
    }
    st.rerun()

def validate_image(uploaded_file):
    """Validate uploaded image"""
    if uploaded_file is None:
        return False, "No file uploaded"
    
    if uploaded_file.size > 5 * 1024 * 1024:
        return False, f"File too large ({uploaded_file.size / 1024 / 1024:.1f}MB). Maximum 5MB."
    
    if uploaded_file.type not in ['image/jpeg', 'image/jpg', 'image/png']:
        return False, "Invalid file type. Only JPG and PNG allowed."
    
    return True, ""

def progress_callback(message: str, percentage: float):
    """Callback for progress updates"""
    st.session_state.progress_data['percentage'] = percentage
    st.session_state.progress_data['message'] = message
    
    message_lower = message.lower()
    if 'original' in message_lower:
        st.session_state.progress_data['current_stage'] = 'original'
    elif 'crop' in message_lower:
        st.session_state.progress_data['current_stage'] = 'cropped'
    elif 'align' in message_lower:
        st.session_state.progress_data['current_stage'] = 'aligned'
    elif 'calculat' in message_lower or 'complete' in message_lower:
        st.session_state.progress_data['current_stage'] = 'completed'

def display_confidence_metric(confidence: float, is_same: bool):
    """Display confidence score with color coding"""
    if confidence >= 80:
        color = "🟢"
        level = "High"
    elif confidence >= 60:
        color = "🟡"
        level = "Medium"
    else:
        color = "🔴"
        level = "Low"
    
    return f'{color} <strong>{confidence:.1f}%</strong> ({level} Confidence)'

# Main Application

def main():
    # Header Section
    st.markdown("""
    <div class="header-container">
        <div class="header-icon">🎭</div>
        <div class="header-title">Face Comparison System</div>
        <div class="header-subtitle">Advanced AI-powered face verification with multi-model voting</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Upload Stage
    if st.session_state.stage == 'upload':
        st.markdown("### 📸 Upload Two Face Images")
        st.markdown("Upload two face images to verify if they show the same person")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Image 1**")
            uploaded_file1 = st.file_uploader(
                "Choose first image",
                type=['jpg', 'jpeg', 'png'],
                key='uploader1',
                label_visibility='collapsed'
            )
            
            if uploaded_file1:
                valid, error = validate_image(uploaded_file1)
                if valid:
                    image1 = Image.open(uploaded_file1)
                    st.image(image1, use_column_width=True)
                    st.session_state.uploaded_images['img1'] = image1
                else:
                    st.error(error)
                    st.session_state.uploaded_images['img1'] = None
        
        with col2:
            st.markdown("**Image 2**")
            uploaded_file2 = st.file_uploader(
                "Choose second image",
                type=['jpg', 'jpeg', 'png'],
                key='uploader2',
                label_visibility='collapsed'
            )
            
            if uploaded_file2:
                valid, error = validate_image(uploaded_file2)
                if valid:
                    image2 = Image.open(uploaded_file2)
                    st.image(image2, use_column_width=True)
                    st.session_state.uploaded_images['img2'] = image2
                else:
                    st.error(error)
                    st.session_state.uploaded_images['img2'] = None
        
        # Info Box
        st.markdown("""
        <div class="info-box">
            📌 <strong>Tips for best results:</strong>
            <ul>
                <li>Max 5MB per image</li>
                <li>JPG or PNG format only</li>
                <li>Clear, well-lit face photos</li>
                <li>Front-facing images work best</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Analyze Button
        can_analyze = (
            st.session_state.uploaded_images['img1'] is not None and
            st.session_state.uploaded_images['img2'] is not None
        )
        
        if st.button("🔍 Analyze Faces", disabled=not can_analyze):
            st.session_state.stage = 'processing'
            st.rerun()
    
    # Processing Stage
    elif st.session_state.stage == 'processing':
        st.markdown("### ⏳ Analyzing Faces...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        stage_cols = st.columns(3)
        stage_placeholders = {
            'original': stage_cols[0].empty(),
            'cropped': stage_cols[1].empty(),
            'aligned': stage_cols[2].empty()
        }
        
        for key, placeholder in stage_placeholders.items():
            placeholder.markdown("⏹ Pending")
        
        # Run Comparison
        try:
            img1 = st.session_state.uploaded_images['img1']
            img2 = st.session_state.uploaded_images['img2']
            
            def streamlit_progress_callback(message: str, percentage: float):
                progress_callback(message, percentage)
                progress_bar.progress(percentage)
                status_text.text(message)
                
                current = st.session_state.progress_data['current_stage']
                if current == 'original':
                    stage_placeholders['original'].markdown("⏳ **Processing...**")
                elif current == 'cropped':
                    stage_placeholders['original'].markdown("✅ Completed")
                    stage_placeholders['cropped'].markdown("⏳ **Processing...**")
                elif current == 'aligned':
                    stage_placeholders['original'].markdown("✅ Completed")
                    stage_placeholders['cropped'].markdown("✅ Completed")
                    stage_placeholders['aligned'].markdown("⏳ **Processing...**")
                elif current == 'completed':
                    stage_placeholders['original'].markdown("✅ Completed")
                    stage_placeholders['cropped'].markdown("✅ Completed")
                    stage_placeholders['aligned'].markdown("✅ Completed")
            
            result = orchestrator.run_comparison(
                img1, img2, 
                progress_callback=streamlit_progress_callback
            )
            
            st.session_state.result = result
            comparison_logger.log_comparison(result)
            
            time.sleep(0.5)
            st.session_state.stage = 'result'
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error during processing: {str(e)}")
            st.warning("Please try again with different images.")
            
            if st.button("🔄 Try Again"):
                reset_app()
    
    # Result Stage
    elif st.session_state.stage == 'result':
        result = st.session_state.result
        
        if result is None:
            st.error("No result available")
            if st.button("Start Over"):
                reset_app()
            return
        
        is_same = result['final_decision'] == 'same'
        confidence = result['confidence']
        
        # Result Card
        icon = "✅" if is_same else "❌"
        title = "Same Person" if is_same else "Different Person"
        subtitle = "The images show the same person" if is_same else "The images show different people"
        
        st.markdown(f"""
        <div class="result-card">
            <div class="result-icon">{icon}</div>
            <div class="result-title">{title}</div>
            <div style="color: #6b7280; margin-bottom: 2rem;">{subtitle}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Confidence Score Display
        st.markdown("### 🎯 Confidence Score")
        confidence_display = display_confidence_metric(confidence, is_same)
        st.markdown(f"<div style='text-align: center; font-size: 2rem; margin: 2rem 0;'>{confidence_display}</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Statistics Section
        st.markdown("### 📊 Analysis Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="🗳️ Total Votes",
                value=result['total_votes'],
                help="Number of AI models that voted"
            )
        
        with col2:
            st.metric(
                label="⚡ Processing Time",
                value=f"{result['processing_time']:.1f}s",
                help="Total time taken for analysis"
            )
        
        with col3:
            st.metric(
                label="🎯 API Calls",
                value=result['total_api_calls'],
                help="Number of API calls made"
            )
        
        # Detailed Information Expander
        with st.expander("📋 Detailed Information"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Processing Details:**")
                st.write(f"- Early Stopped: {'Yes ✅' if result.get('stopped_early', False) else 'No'}")
                st.write(f"- Cropping: {'Success ✅' if result.get('cropping_success', False) else 'Failed ❌'}")
                st.write(f"- Alignment: {'Success ✅' if result.get('alignment_success', False) else 'Failed ❌'}")
            
            with col2:
                st.markdown("**Vote Breakdown:**")
                
                breakdown = result.get('breakdown', {})
                
                if breakdown and (breakdown.get('votes_same', 0) > 0 or breakdown.get('votes_different', 0) > 0):
                    votes_same = breakdown.get('votes_same', 0)
                    votes_diff = breakdown.get('votes_different', 0)
                elif result.get('vote_details'):
                    vote_details = result.get('vote_details', [])
                    votes_same = sum(1 for v in vote_details if v.get('result') == 'same')
                    votes_diff = sum(1 for v in vote_details if v.get('result') == 'different')
                else:
                    total_votes = result.get('total_votes', 0)
                    final_decision = result.get('final_decision', '')
                    
                    if total_votes > 0:
                        if final_decision == 'same':
                            votes_same = max(1, int(total_votes * result.get('confidence', 50) / 100))
                            votes_diff = total_votes - votes_same
                        else:
                            votes_diff = max(1, int(total_votes * result.get('confidence', 50) / 100))
                            votes_same = total_votes - votes_diff
                    else:
                        votes_same = 0
                        votes_diff = 0
                
                st.write(f"- Same Person: {votes_same} votes")
                st.write(f"- Different Person: {votes_diff} votes")
                
                total = votes_same + votes_diff
                if total > 0:
                    st.write(f"- **Total:** {total} votes")
        
        # Action Buttons
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 New Comparison"):
                reset_app()
        
        with col2:
            result_json = json.dumps({
                'final_decision': result['final_decision'],
                'confidence': result['confidence'],
                'total_votes': result['total_votes'],
                'processing_time': result.get('processing_time', 0),
                'stopped_early': result.get('stopped_early', False),
                'cropping_success': result.get('cropping_success', False),
                'alignment_success': result.get('alignment_success', False)
            }, indent=2)
            
            st.download_button(
                label="📥 Download Result",
                data=result_json,
                file_name="comparison_result.json",
                mime="application/json"
            )

# Sidebar Section

with st.sidebar:
    st.markdown("### ℹ️ About")
    st.markdown("""
    This system uses advanced AI models to compare faces:
    
    - **Qwen VL** - Vision language model
    - **ChatGPT-4o** - OpenAI's vision model
    - **Gemini** - Google's AI model
    - **MediaPipe** - Face detection & landmarks
    
    **Features:**
    - Multi-model voting (10 votes)
    - Intelligent preprocessing
    - Weighted voting system
    - Early stopping optimization
    """)
    
    st.markdown("---")
    
    # System Statistics
    try:
        stats = comparison_logger.get_statistics()
        if stats.get('total_comparisons', 0) > 0:
            st.markdown("### 📈 System Stats")
            st.metric("Total Comparisons", stats['total_comparisons'])
            st.metric("Avg Confidence", f"{stats.get('avg_confidence', 0):.1f}%")
            st.metric("Avg Time", f"{stats.get('avg_processing_time', 0):.1f}s")
    except:
        pass
    
    st.markdown("---")
    st.markdown("**Made with ❤️ using Streamlit**")

# Run Application

if __name__ == "__main__":
    main()
