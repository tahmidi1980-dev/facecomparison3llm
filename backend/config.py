"""
Configuration and Constants for Face Comparison System
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# API KEYS (Load from .env file)
# ============================================================================
API_KEYS = {
    "qwen": os.getenv("QWEN_API_KEY", ""),
    "chatgpt": os.getenv("CHATGPT_API_KEY", ""),
    "gemini": os.getenv("GEMINI_API_KEY", ""),
}

# ============================================================================
# LLM CONFIGURATIONS
# ============================================================================
LLM_CONFIGS = {
    "qwen": {
        "model": "qwen/qwen-vl-max",
        "name": "Qwen VL",
        "base_url": "https://openrouter.ai/api/v1"
    },
    "chatgpt": {
        "model": "openai/gpt-4o-2024-11-20",
        "name": "ChatGPT-4o",
        "base_url": "https://openrouter.ai/api/v1"
    },
    "gemini": {
        "model": "google/gemini-2.0-flash-exp:free",
        "name": "Gemini 2.0 Flash",
        "base_url": "https://openrouter.ai/api/v1",
        "fallbacks": [
            "google/gemini-exp-1206:free"
        ]
    }
}

# ============================================================================
# VOTING WEIGHTS
# ============================================================================
VOTING_WEIGHTS = {
    # Original image weights (4 votes)
    "original": {
        "qwen": 1.0,
        "chatgpt": 1.0,
        "gemini": 1.0,
        "deepface": 1.0
    },
    
    # Cropped image weights (3 votes)
    "cropped": {
        "chatgpt": 1.2,  # ChatGPT prioritized for cropped
        "retinaface_weight": 0.7,  # RetinaFace weight for Qwen/Gemini
        "llm_weight": 0.3  # LLM weight for Qwen/Gemini when differs
    },
    
    # Aligned image weights (3 votes)
    "aligned": {
        "qwen": 1.1,
        "chatgpt": 1.1,
        "gemini": 1.1
    }
}

# ============================================================================
# EARLY STOPPING
# ============================================================================
EARLY_STOP_THRESHOLD = 6  # Stop if 6 out of 10 votes agree
ENABLE_EARLY_STOP = True

# ============================================================================
# API SETTINGS
# ============================================================================
RATE_DELAY = 1.0  # Seconds between API calls
MAX_RETRIES = 3
REQUEST_TIMEOUT = 30  # Seconds

# ============================================================================
# IMAGE PROCESSING SETTINGS
# ============================================================================
IMAGE_SETTINGS = {
    "max_size_mb": 5,
    "allowed_formats": ["jpg", "jpeg", "png"],
    "target_size": 1024,
    "jpeg_quality": 95
}

# ============================================================================
# DEEPFACE SETTINGS
# ============================================================================
DEEPFACE_CONFIG = {
    "model_name": "Facenet512",
    "detector_backend": "retinaface",
    "distance_metric": "cosine",
    "threshold": 0.4,  # Same person if distance < threshold
    "align": True
}

# ============================================================================
# PREPROCESSING SETTINGS
# ============================================================================
PREPROCESSING = {
    "cropping": {
        "enabled": True,
        "margin": 0.3,
        "max_size": 1024
    },
    "alignment": {
        "enabled": True,
        "method": "haar",  # haar, template, hough, color_segment, hybrid
        "rotate_only": True,
        "fallback": True
    }
}

# ============================================================================
# PATHS
# ============================================================================
BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = BASE_DIR / "logs"
TEMP_DIR = BASE_DIR / "temp"

# Create directories
LOGS_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# ============================================================================
# LOGGING
# ============================================================================
LOG_FILE = LOGS_DIR / "comparisons.csv"
ENABLE_LOGGING = True

# ============================================================================
# PROMPT FOR LLM
# ============================================================================
COMPARISON_PROMPT = "Are these two images showing the same person? Answer only YES or NO."

# ============================================================================
# VALIDATION
# ============================================================================
def validate_config():
    """Validate configuration"""
    errors = []
    
    # Check API keys
    for llm, key in API_KEYS.items():
        if not key:
            errors.append(f"Missing API key for {llm}")
    
    # Check weights sum
    total_weight = (
        sum(VOTING_WEIGHTS["original"].values()) +
        VOTING_WEIGHTS["cropped"]["chatgpt"] +
        VOTING_WEIGHTS["cropped"]["retinaface_weight"] * 2 +
        sum(VOTING_WEIGHTS["aligned"].values())
    )
    
    if errors:
        print("⚠️  Configuration Warnings:")
        for error in errors:
            print(f"   - {error}")
    
    return len(errors) == 0

# Validate on import
if __name__ == "__main__":
    if validate_config():
        print("✅ Configuration validated successfully")
    else:
        print("⚠️  Configuration has warnings")
