"""
Image Preprocessing Pipeline (MediaPipe version - Python 3.13 Compatible)
Handles cropping and alignment
"""
import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from typing import Tuple, Optional
import logging
import mediapipe as mp
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
        
        # Initialize MediaPipe Face Detection and Face Mesh
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_face_mesh = mp.solutions.face_mesh
        
        # Face Detection for cropping (model_selection=1 for better accuracy)
        self.face_detection = self.mp_face_detection.FaceDetection(
            min_detection_confidence=0.5,
            model_selection=1  # 1=full range detector, 0=short range
        )
        
        # Face Mesh for alignment (landmark detection)
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
        
    def crop_with_retinaface(self, img1: Image.Image, img2: Image.Image) -> Tuple[Optional[Image.Image], Optional[Image.Image], bool]:
        """
        Crop faces using MediaPipe detector
        
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
            
            logger.info("✓ Successfully cropped both images with MediaPipe")
            return cropped1, cropped2, True
            
        except Exception as e:
            logger.error(f"Cropping error: {e}")
            return None, None, False
    
    def _crop_single_image(self, img: Image.Image) -> Optional[Image.Image]:
        """Crop single image using MediaPipe Face Detection"""
        try:
            # Convert PIL to numpy array (RGB format)
            img_array = np.array(img)
            
            # Ensure RGB format (MediaPipe requires RGB)
            if len(img_array.shape) == 2:  # Grayscale
                img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
            elif img_array.shape[2] == 4:  # RGBA
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
            
            # Detect faces
            results = self.face_detection.process(img_array)
            
            if not results.detections:
                logger.warning("No face detected in image")
                return None
            
            # Get the first/largest detection
            detection = results.detections[0]
            bboxC = detection.location_data.relative_bounding_box
            
            h, w, _ = img_array.shape
            
            # Convert relative coordinates to absolute pixels
            x = int(bboxC.xmin * w)
            y = int(bboxC.ymin * h)
            bbox_w = int(bboxC.width * w)
            bbox_h = int(bboxC.height * h)
            
            # Add margin around face
            margin = self.crop_config['margin']
            margin_x = int(bbox_w * margin)
            margin_y = int(bbox_h * margin)
            
            # Calculate crop coordinates with margin (ensure within bounds)
            x1 = max(0, x - margin_x)
            y1 = max(0, y - margin_y)
            x2 = min(w, x + bbox_w + margin_x)
            y2 = min(h, y + bbox_h + margin_y)
            
            # Crop face with margin
            face_with_margin = img_array[y1:y2, x1:x2]
            
            # Convert back to PIL Image
            cropped_img = Image.fromarray(face_with_margin)
            
            # Resize if image is too large
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
        Align faces using MediaPipe Face Mesh landmarks
        
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
            
            logger.info("✓ Successfully aligned both images with MediaPipe")
            return aligned1, aligned2, True
            
        except Exception as e:
            logger.error(f"Alignment error: {e}")
            return None, None, False
    
    def _align_single_image(self, img: Image.Image) -> Optional[Image.Image]:
        """Align single image by rotating to horizontal eyes using MediaPipe Face Mesh"""
        try:
            # Convert PIL to numpy
            img_array = np.array(img)
            
            # Ensure RGB format
            if len(img_array.shape) == 2:  # Grayscale
                img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
            elif img_array.shape[2] == 4:  # RGBA
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
            
            # Get face landmarks using MediaPipe Face Mesh
            results = self.face_mesh.process(img_array)
            
            if not results.multi_face_landmarks:
                logger.warning("No face landmarks detected for alignment")
                return None
            
            # Get first face's landmarks
            face_landmarks = results.multi_face_landmarks[0]
            
            h, w, _ = img_array.shape
            
            # MediaPipe Face Mesh landmark indices for eyes
            # Left eye: outer corner (33) and inner corner (133)
            # Right eye: inner corner (362) and outer corner (263)
            LEFT_EYE_INDICES = [33, 133, 160, 159, 158, 157, 173]
            RIGHT_EYE_INDICES = [362, 263, 387, 386, 385, 384, 398]
            
            # Extract eye landmark coordinates
            left_eye_pts = [
                (int(face_landmarks.landmark[i].x * w), 
                 int(face_landmarks.landmark[i].y * h)) 
                for i in LEFT_EYE_INDICES
            ]
            right_eye_pts = [
                (int(face_landmarks.landmark[i].x * w), 
                 int(face_landmarks.landmark[i].y * h)) 
                for i in RIGHT_EYE_INDICES
            ]
            
            # Calculate eye centers (average of all eye points)
            left_eye_center = np.mean(left_eye_pts, axis=0).astype(int)
            right_eye_center = np.mean(right_eye_pts, axis=0).astype(int)
            
            # Calculate rotation angle to make eyes horizontal
            dY = right_eye_center[1] - left_eye_center[1]
            dX = right_eye_center[0] - left_eye_center[0]
            angle = np.degrees(np.arctan2(dY, dX))
            
            # Calculate rotation center (midpoint between eyes)
            center_x = (left_eye_center[0] + right_eye_center[0]) / 2
            center_y = (left_eye_center[1] + right_eye_center[1]) / 2
            
            # Get rotation matrix
            M = cv2.getRotationMatrix2D((center_x, center_y), angle, 1.0)
            
            # Apply rotation
            aligned_array = cv2.warpAffine(
                img_array, M, (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
            
            # Convert back to PIL Image
            return Image.fromarray(aligned_array)
            
        except Exception as e:
            logger.error(f"Single alignment error: {e}")
            return None
    
    def validate_image(self, img: Image.Image) -> Tuple[bool, str]:
        """
        Validate image format and dimensions
        
        Returns:
            (is_valid, error_message)
        """
        try:
            # Check format
            if img.format and img.format.lower() not in ['jpeg', 'jpg', 'png']:
                return False, f"Invalid format: {img.format}. Only JPG/PNG allowed."
            
            # Check dimensions
            width, height = img.size
            if width < 100 or height < 100:
                return False, "Image too small. Minimum 100x100 pixels."
            
            if width > 5000 or height > 5000:
                return False, "Image too large. Maximum 5000x5000 pixels."
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def __del__(self):
        """Cleanup MediaPipe resources"""
        try:
            if hasattr(self, 'face_detection'):
                self.face_detection.close()
            if hasattr(self, 'face_mesh'):
                self.face_mesh.close()
        except:
            pass

# Global processor instance
processor = ImageProcessor()

if __name__ == "__main__":
    print("Testing Image Processor (MediaPipe)...")
    
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
