"""
LLM Comparator Module
Handles face comparison using Qwen, ChatGPT, Gemini, and DeepFace
"""
import base64
import time
import logging
from io import BytesIO
from typing import Tuple, Optional
from PIL import Image
import numpy as np
from openai import OpenAI
from deepface import DeepFace
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMComparator:
    """Handles LLM API calls for face comparison"""
    
    def __init__(self):
        self.rate_delay = config.RATE_DELAY
        self.max_retries = config.MAX_RETRIES
        self.prompt = config.COMPARISON_PROMPT
        
        # Initialize OpenAI clients for each LLM
        self.clients = {}
        for llm_name, llm_config in config.LLM_CONFIGS.items():
            if config.API_KEYS.get(llm_name):
                self.clients[llm_name] = OpenAI(
                    base_url=llm_config['base_url'],
                    api_key=config.API_KEYS[llm_name]
                )
    
    def _image_to_base64(self, img: Image.Image) -> str:
        """Convert PIL Image to base64 string"""
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=config.IMAGE_SETTINGS['jpeg_quality'])
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def _call_llm_api(self, llm_name: str, img1: Image.Image, img2: Image.Image) -> Tuple[Optional[str], str]:
        """
        Call LLM API with retry logic
        
        Returns:
            (result: 'same'/'different'/None, method: str)
        """
        if llm_name not in self.clients:
            logger.error(f"LLM {llm_name} not configured")
            return None, f"{llm_name}_not_configured"
        
        try:
            # Convert images to base64
            img1_b64 = self._image_to_base64(img1)
            img2_b64 = self._image_to_base64(img2)
        except Exception as e:
            logger.error(f"Image encoding error: {e}")
            return None, "encoding_error"
        
        # Get model config
        llm_config = config.LLM_CONFIGS[llm_name]
        models_to_try = [llm_config['model']]
        
        # Add fallbacks if available
        if 'fallbacks' in llm_config:
            models_to_try.extend(llm_config['fallbacks'])
        
        # Try each model
        for model_idx, model in enumerate(models_to_try):
            for attempt in range(self.max_retries):
                try:
                    response = self.clients[llm_name].chat.completions.create(
                        model=model,
                        messages=[{
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{img1_b64}"}
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{img2_b64}"}
                                },
                                {
                                    "type": "text",
                                    "text": self.prompt
                                }
                            ]
                        }],
                        max_tokens=50,
                        temperature=0.0,
                        timeout=config.REQUEST_TIMEOUT
                    )
                    
                    # Parse response
                    text = response.choices[0].message.content.strip().upper()
                    
                    # Determine result
                    if "YES" in text and "NO" not in text:
                        result = "same"
                    elif "NO" in text:
                        result = "different"
                    else:
                        result = "different"  # Default to different if unclear
                    
                    method = f"{llm_name}_{text[:20]}"
                    if model_idx > 0:
                        method += f"_fallback{model_idx}"
                    
                    return result, method
                    
                except Exception as e:
                    error = str(e)
                    
                    # Handle rate limit
                    if "429" in error or "rate limit" in error.lower():
                        wait_time = self.rate_delay * (attempt + 2)
                        logger.warning(f"{llm_name} rate limit, waiting {wait_time}s")
                        time.sleep(wait_time)
                        continue
                    
                    # Handle model not found
                    if "404" in error:
                        logger.warning(f"Model {model} not found, trying next")
                        break
                    
                    # Last attempt failed
                    if attempt == self.max_retries - 1:
                        logger.error(f"{llm_name} failed after {self.max_retries} attempts: {error[:100]}")
                        if model_idx < len(models_to_try) - 1:
                            break
                    
                    time.sleep(self.rate_delay)
        
        return None, f"{llm_name}_failed"
    
    def compare_with_qwen(self, img1: Image.Image, img2: Image.Image) -> Tuple[Optional[str], str]:
        """Compare faces using Qwen VL"""
        logger.info("Calling Qwen VL...")
        return self._call_llm_api("qwen", img1, img2)
    
    def compare_with_chatgpt(self, img1: Image.Image, img2: Image.Image) -> Tuple[Optional[str], str]:
        """Compare faces using ChatGPT-4o"""
        logger.info("Calling ChatGPT-4o...")
        return self._call_llm_api("chatgpt", img1, img2)
    
    def compare_with_gemini(self, img1: Image.Image, img2: Image.Image) -> Tuple[Optional[str], str]:
        """Compare faces using Gemini"""
        logger.info("Calling Gemini...")
        return self._call_llm_api("gemini", img1, img2)
    
    def compare_with_deepface(self, img1: Image.Image, img2: Image.Image) -> Tuple[Optional[str], str]:
        """
        Compare faces using DeepFace
        
        Returns:
            (result: 'same'/'different'/None, method: str)
        """
        logger.info("Comparing with DeepFace...")
        
        try:
            # Convert PIL to numpy arrays
            img1_array = np.array(img1)
            img2_array = np.array(img2)
            
            # Verify faces using DeepFace
            result = DeepFace.verify(
                img1_path=img1_array,
                img2_path=img2_array,
                model_name=config.DEEPFACE_CONFIG['model_name'],
                detector_backend=config.DEEPFACE_CONFIG['detector_backend'],
                distance_metric=config.DEEPFACE_CONFIG['distance_metric'],
                enforce_detection=False,
                align=config.DEEPFACE_CONFIG['align']
            )
            
            # Check if same person based on distance and threshold
            is_same = result.get('verified', False)
            distance = result.get('distance', 1.0)
            threshold = result.get('threshold', config.DEEPFACE_CONFIG['threshold'])
            
            comparison_result = "same" if is_same else "different"
            method = f"deepface_{distance:.3f}"
            
            logger.info(f"DeepFace result: {comparison_result} (distance: {distance:.3f}, threshold: {threshold:.3f})")
            
            return comparison_result, method
            
        except Exception as e:
            logger.error(f"DeepFace error: {e}")
            return None, "deepface_error"
    
    def compare_with_retinaface(self, img1: Image.Image, img2: Image.Image) -> Tuple[Optional[str], str]:
        """
        Compare faces using RetinaFace + DeepFace embeddings
        (Used for conditional voting in cropped stage)
        """
        logger.info("Comparing with RetinaFace...")
        
        try:
            # Convert PIL to numpy
            img1_array = np.array(img1)
            img2_array = np.array(img2)
            
            # Get embeddings using RetinaFace detector
            result = DeepFace.verify(
                img1_path=img1_array,
                img2_path=img2_array,
                model_name=config.DEEPFACE_CONFIG['model_name'],
                detector_backend='retinaface',
                distance_metric=config.DEEPFACE_CONFIG['distance_metric'],
                enforce_detection=False,
                align=True
            )
            
            is_same = result.get('verified', False)
            distance = result.get('distance', 1.0)
            
            comparison_result = "same" if is_same else "different"
            method = f"retinaface_{distance:.3f}"
            
            return comparison_result, method
            
        except Exception as e:
            logger.error(f"RetinaFace comparison error: {e}")
            return None, "retinaface_error"

# Global comparator instance
comparator = LLMComparator()

if __name__ == "__main__":
    print("Testing LLM Comparator...")
    
    from pathlib import Path
    
    # Test with sample images
    dataset = Path("dataset")
    if dataset.exists():
        test_imgs = list(dataset.glob("*_1.jpg"))[:2]
        
        if len(test_imgs) >= 2:
            img1 = Image.open(test_imgs[0])
            img2 = Image.open(test_imgs[1])
            
            print("\n1. Testing DeepFace...")
            result, method = comparator.compare_with_deepface(img1, img2)
            print(f"   Result: {result}, Method: {method}")
            
            print("\n2. Testing Qwen (if API key available)...")
            if config.API_KEYS.get('qwen'):
                result, method = comparator.compare_with_qwen(img1, img2)
                print(f"   Result: {result}, Method: {method}")
            else:
                print("   Skipped (no API key)")
            
            print("\n3. Testing ChatGPT (if API key available)...")
            if config.API_KEYS.get('chatgpt'):
                result, method = comparator.compare_with_chatgpt(img1, img2)
                print(f"   Result: {result}, Method: {method}")
            else:
                print("   Skipped (no API key)")
            
            print("\n4. Testing Gemini (if API key available)...")
            if config.API_KEYS.get('gemini'):
                result, method = comparator.compare_with_gemini(img1, img2)
                print(f"   Result: {result}, Method: {method}")
            else:
                print("   Skipped (no API key)")
        else:
            print("Not enough test images")
    else:
        print("Dataset folder not found")
