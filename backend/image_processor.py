"""
Image Preprocessing Pipeline (face-recognition version)
Handles cropping and alignment
"""
import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from typing import Tuple, Optional
import logging
import face_recognition
import sys

sys.path.append(str(Path(__file__).parent))
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageProcessor:
    """Handles image preprocessing (cropping and alignment)"""
    
    def __init__(self):
        self.crop_config = config.PREPROCESSING['cropping']
        self.align_config = config.PREPROCESSING['alignment']
        
    def crop_with_retinaface(self, img1: Image.Image, img2: Image.Image) -> Tuple[Optional[Image.Image], Optional[Image.Image], bool]:
        """
        Crop faces using face_recognition detector (replaces RetinaFace)
        
        Returns:
            (cropped_img1, cropped_img2, success)
        """
        if not self.crop_config['enabled']:
            return None, None, False
        
        try:
            # Crop image 1
            cropped1 = self._crop_single_image(img1)
            if cropped1 is None:
                logger.warning("Failed to crop image 1")
                return None, None, False
            
            # Crop image 2
            cropped2 = self._crop_single_image(img2)
            if cropped2 is None:
                logger.warning("Failed to crop image 2")
                return None, None, False
            
            logger.info("✓ Successfully cropped both images")
            return cropped1, cropped2, True
            
        except Exception as e:
            logger.error(f"Cropping error: {e}")
            return None, None, False
    
    def _crop_single_image(self, img: Image.Image) -> Optional[Image.Image]:
        """Crop single image using face_recognition"""
        try:
            # Convert PIL to numpy
            img_array = np.array(img)
            
            # Detect face locations using face_recognition
            face_locations = face_recognition.face_locations(img_array)
            
            if not face_locations or len(face_locations) == 0:
                logger.warning("No face detected")
                return None
            
            # Get largest face (by area)
            best_face = max(face_locations, key=lambda loc: (loc[2] - loc[0]) * (loc[1] - loc[3]))
            top, right, bottom, left = best_face
            
            # Convert to x, y, w, h format
            x = left
            y = top
            w = right - left
            h = bottom - top
            
            # Add margin
            margin = self.crop_config['margin']
            margin_x = int(w * margin)
            margin_y = int(h * margin)
            
            x1 = max(0, x - margin_x)
            y1 = max(0, y - margin_y)
            x2 = min(img_array.shape[1], x + w + margin_x)
            y2 = min(img_array.shape[0], y + h + margin_y)
            
            # Crop with margin
            face_with_margin = img_array[y1:y2, x1:x2]
            cropped_img = Image.fromarray(face_with_margin)
            
            # Resize if needed
            max_size = self.crop_config.get('max_size')
            if max_size and max(cropped_img.size) > max_size:
                ratio = max_size / max(cropped_img.size)
                new_size = tuple(int(dim * ratio) for dim in cropped_img.size)
                cropped_img = cropped_img.resize(new_size, Image.Resampling.LANCZOS)
            
            return cropped_img
            
        except Exception as e:
            logger.error(f"Single crop error: {e}")
            return None
    
    def align_faces(self, img1: Image.Image, img2: Image.Image) -> Tuple[Optional[Image.Image], Optional[Image.Image], bool]:
        """
        Align faces using face_recognition landmarks
        
        Returns:
            (aligned_img1, aligned_img2, success)
        """
        if not self.align_config['enabled']:
            return None, None, False
        
        try:
            # Align image 1
            aligned1 = self._align_single_image(img1)
            if aligned1 is None:
                logger.warning("Failed to align image 1")
                return None, None, False
            
            # Align image 2
            aligned2 = self._align_single_image(img2)
            if aligned2 is None:
                logger.warning("Failed to align image 2")
                return None, None, False
            
            logger.info("✓ Successfully aligned both images")
            return aligned1, aligned2, True
            
        except Exception as e:
            logger.error(f"Alignment error: {e}")
            return None, None, False
    
    def _align_single_image(self, img: Image.Image) -> Optional[Image.Image]:
        """Align single image by rotating to horizontal eyes using face_recognition"""
        try:
            # Convert to numpy
            img_array = np.array(img)
            
            # Get face landmarks using face_recognition
            face_landmarks_list = face_recognition.face_landmarks(img_array)
            
            if not face_landmarks_list or len(face_landmarks_list) == 0:
                logger.warning("No face landmarks detected")
                return None
            
            # Get first face's landmarks
            face_landmarks = face_landmarks_list[0]
            
            # Get eye positions
            left_eye = face_landmarks.get('left_eye', [])
            right_eye = face_landmarks.get('right_eye', [])
            
            if not left_eye or not right_eye:
                logger.warning("Eye landmarks not found")
                return None
            
            # Calculate average eye positions
            left_eye_center = np.mean(left_eye, axis=0).astype(int)
            right_eye_center = np.mean(right_eye, axis=0).astype(int)
            
            # Calculate angle
            dY = right_eye_center[1] - left_eye_center[1]
            dX = right_eye_center[0] - left_eye_center[0]
            angle = np.degrees(np.arctan2(dY, dX))
            
            # Rotate image
            center_x = (left_eye_center[0] + right_eye_center[0]) / 2
            center_y = (left_eye_center[1] + right_eye_center[1]) / 2
            
            M = cv2.getRotationMatrix2D((center_x, center_y), angle, 1.0)
            h, w = img_array.shape[:2]
            aligned_array = cv2.warpAffine(
                img_array, M, (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
            
            return Image.fromarray(aligned_array)
            
        except Exception as e:
            logger.error(f"Single alignment error: {e}")
            return None
    
    def validate_image(self, img: Image.Image) -> Tuple[bool, str]:
        """
        Validate image
        
        Returns:
            (is_valid, error_message)
        """
        try:
            # Check format
            if img.format and img.format.lower() not in ['jpeg', 'jpg', 'png']:
                return False, f"Invalid format: {img.format}. Only JPG/PNG allowed."
            
            # Check size
            width, height = img.size
            if width < 100 or height < 100:
                return False, "Image too small. Minimum 100x100 pixels."
            
            if width > 5000 or height > 5000:
                return False, "Image too large. Maximum 5000x5000 pixels."
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"

# Global processor instance
processor = ImageProcessor()

if __name__ == "__main__":
    print("Testing Image Processor...")
    
    # Test with sample images if available
    from pathlib import Path
    
    dataset = Path("dataset")
    if dataset.exists():
        test_imgs = list(dataset.glob("*_1.jpg"))[:2]
        
        if len(test_imgs) >= 2:
            img1 = Image.open(test_imgs[0])
            img2 = Image.open(test_imgs[1])
            
            print("\n1. Testing cropping...")
            cropped1, cropped2, success = processor.crop_with_retinaface(img1, img2)
            if success:
                print(f"   ✓ Cropped: {cropped1.size}, {cropped2.size}")
            else:
                print("   ✗ Cropping failed")
            
            print("\n2. Testing alignment...")
            aligned1, aligned2, success = processor.align_faces(img1, img2)
            if success:
                print(f"   ✓ Aligned: {aligned1.size}, {aligned2.size}")
            else:
                print("   ✗ Alignment failed")
            
            print("\n3. Testing validation...")
            valid, msg = processor.validate_image(img1)
            if valid:
                print("   ✓ Image valid")
            else:
                print(f"   ✗ {msg}")
        else:
            print("Not enough test images in dataset folder")
    else:
        print("Dataset folder not found")
