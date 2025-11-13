"""
LLM Comparator Module (MediaPipe version - Streamlit Cloud Compatible)
"""
import base64
import time
import logging
from io import BytesIO
from typing import Tuple, Optional
from PIL import Image
import numpy as np
from openai import OpenAI
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from . import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lazy import MediaPipe
mp_face_mesh = None
FaceMesh = None

def _init_mediapipe():
    """Initialize MediaPipe"""
    global mp_face_mesh, FaceMesh
    
    if mp_face_mesh is None:
        try:
            import mediapipe as mp
            mp_face_mesh = mp.solutions.face_mesh
            FaceMesh = mp_face_mesh.FaceMesh
            logger.info("MediaPipe initialized")
        except ImportError as e:
            logger.error(f"MediaPipe not available: {e}")
            raise

class LLMComparator:
    """Handles LLM API calls for face comparison"""
    
    def __init__(self):
        self.rate_delay = config.RATE_DELAY
        self.max_retries = config.MAX_RETRIES
        self.prompt = config.COMPARISON_PROMPT
        
        # Initialize OpenAI clients (with error handling)
        self.clients = {}
        for llm_name, llm_config in config.LLM_CONFIGS.items():
            api_key = config.API_KEYS.get(llm_name)
            if api_key and api_key.startswith('sk-'):  # Valid key format
                try:
                    self.clients[llm_name] = OpenAI(
                        base_url=llm_config['base_url'],
                        api_key=api_key,
                        timeout=30.0
                    )
                    logger.info(f"✓ {llm_name} client initialized")
                except Exception as e:
                    logger.warning(f"✗ Failed to init {llm_name}: {str(e)[:100]}")
            else:
                logger.warning(f"⚠️  No valid API key for {llm_name}")
        
        # MediaPipe (lazy init)
        self.face_mesh = None
    
    def _ensure_mediapipe(self):
        """Ensure MediaPipe is initialized"""
        if self.face_mesh is None:
            _init_mediapipe()
            self.face_mesh = FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5
            )
    
    def _image_to_base64(self, img: Image.Image) -> str:
        """Convert PIL Image to base64"""
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=config.IMAGE_SETTINGS['jpeg_quality'])
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def _call_llm_api(self, llm_name: str, img1: Image.Image, img2: Image.Image) -> Tuple[Optional[str], str]:
        """Call LLM API"""
        if llm_name not in self.clients:
            logger.error(f"{llm_name} not configured")
            return None, f"{llm_name}_not_configured"
        
        try:
            img1_b64 = self._image_to_base64(img1)
            img2_b64 = self._image_to_base64(img2)
        except Exception as e:
            logger.error(f"Encoding error: {e}")
            return None, "encoding_error"
        
        llm_config = config.LLM_CONFIGS[llm_name]
        models_to_try = [llm_config['model']]
        
        if 'fallbacks' in llm_config:
            models_to_try.extend(llm_config['fallbacks'])
        
        for model_idx, model in enumerate(models_to_try):
            for attempt in range(self.max_retries):
                try:
                    response = self.clients[llm_name].chat.completions.create(
                        model=model,
                        messages=[{
                            "role": "user",
                            "content": [
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img1_b64}"}},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img2_b64}"}},
                                {"type": "text", "text": self.prompt}
                            ]
                        }],
                        max_tokens=50,
                        temperature=0.0,
                        timeout=config.REQUEST_TIMEOUT
                    )
                    
                    text = response.choices[0].message.content.strip().upper()
                    
                    if "YES" in text and "NO" not in text:
                        result = "same"
                    elif "NO" in text:
                        result = "different"
                    else:
                        result = "different"
                    
                    method = f"{llm_name}_{text[:20]}"
                    if model_idx > 0:
                        method += f"_fallback{model_idx}"
                    
                    return result, method
                    
                except Exception as e:
                    error = str(e)
                    
                    if "429" in error or "rate limit" in error.lower():
                        wait_time = self.rate_delay * (attempt + 2)
                        logger.warning(f"{llm_name} rate limit, waiting {wait_time}s")
                        time.sleep(wait_time)
                        continue
                    
                    if "404" in error:
                        logger.warning(f"Model {model} not found")
                        break
                    
                    if attempt == self.max_retries - 1:
                        logger.error(f"{llm_name} failed: {error[:100]}")
                        if model_idx < len(models_to_try) - 1:
                            break
                    
                    time.sleep(self.rate_delay)
        
        return None, f"{llm_name}_failed"
    
    def compare_with_qwen(self, img1: Image.Image, img2: Image.Image) -> Tuple[Optional[str], str]:
        """Compare using Qwen VL"""
        logger.info("Calling Qwen VL...")
        return self._call_llm_api("qwen", img1, img2)
    
    def compare_with_chatgpt(self, img1: Image.Image, img2: Image.Image) -> Tuple[Optional[str], str]:
        """Compare using ChatGPT-4o"""
        logger.info("Calling ChatGPT-4o...")
        return self._call_llm_api("chatgpt", img1, img2)
    
    def compare_with_gemini(self, img1: Image.Image, img2: Image.Image) -> Tuple[Optional[str], str]:
        """Compare using Gemini"""
        logger.info("Calling Gemini...")
        return self._call_llm_api("gemini", img1, img2)
    
    def compare_with_deepface(self, img1: Image.Image, img2: Image.Image) -> Tuple[Optional[str], str]:
        """Compare using MediaPipe"""
        logger.info("Comparing with MediaPipe...")
        
        try:
            self._ensure_mediapipe()
            
            img1_array = np.array(img1)
            img2_array = np.array(img2)
            
            results1 = self.face_mesh.process(img1_array)
            results2 = self.face_mesh.process(img2_array)
            
            if not results1.multi_face_landmarks or not results2.multi_face_landmarks:
                logger.warning("No face detected")
                return None, "mediapipe_no_face"
            
            landmarks1 = results1.multi_face_landmarks[0].landmark
            landmarks2 = results2.multi_face_landmarks[0].landmark
            
            # Key facial points
            key_indices = [1, 33, 61, 199, 263, 291]
            
            points1 = np.array([[lm.x, lm.y, lm.z] for i, lm in enumerate(landmarks1) if i in key_indices])
            points2 = np.array([[lm.x, lm.y, lm.z] for i, lm in enumerate(landmarks2) if i in key_indices])
            
            distance = np.linalg.norm(points1 - points2)
            threshold = 0.15
            is_same = distance < threshold
            
            result = "same" if is_same else "different"
            method = f"mediapipe_{distance:.3f}"
            
            logger.info(f"MediaPipe: {result} (dist: {distance:.3f})")
            
            return result, method
            
        except Exception as e:
            logger.error(f"MediaPipe error: {e}")
            return None, "mediapipe_error"
    
    def compare_with_retinaface(self, img1: Image.Image, img2: Image.Image) -> Tuple[Optional[str], str]:
        """Alias for compatibility"""
        return self.compare_with_deepface(img1, img2)
    
    def __del__(self):
        """Cleanup"""
        try:
            if hasattr(self, 'face_mesh') and self.face_mesh:
                self.face_mesh.close()
        except:
            pass

# Global instance
comparator = LLMComparator()
