"""
Orchestrator Module
Coordinates the entire face comparison pipeline
"""
import time
import logging
from typing import Dict, Any, Callable, Optional
from PIL import Image
from backend.image_processor import processor
from backend.llm_comparator import comparator
from backend.voting_system import voting_system
from backend import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComparisonOrchestrator:
    """Orchestrates the complete face comparison pipeline"""
    
    def __init__(self):
        self.processor = processor
        self.comparator = comparator
        self.voting = voting_system
    
    def run_comparison(self, 
                      img1: Image.Image, 
                      img2: Image.Image,
                      progress_callback: Optional[Callable[[str, float], None]] = None) -> Dict[str, Any]:
        """
        Run complete face comparison pipeline
        
        Args:
            img1: First image (PIL Image)
            img2: Second image (PIL Image)
            progress_callback: Optional callback for progress updates (message, percentage)
        
        Returns:
            Complete results dictionary
        """
        start_time = time.time()
        
        results = {
            'final_decision': 'different',
            'confidence': 0.0,
            'total_votes': 0,
            'total_api_calls': 0,
            'processing_time': 0.0,
            'stopped_early': False,
            'cropping_success': False,
            'alignment_success': False,
            'all_votes': [],
            'original': {},
            'cropped': {},
            'aligned': {},
            'breakdown': {}
        }
        
        all_votes = []
        api_call_count = 0
        
        # =================================================================
        # STAGE 1: ORIGINAL IMAGES (4 votes)
        # =================================================================
        if progress_callback:
            progress_callback("Analyzing original images...", 0.1)
        
        logger.info("\n" + "="*60)
        logger.info("STAGE 1: ORIGINAL IMAGES")
        logger.info("="*60)
        
        # 1. Qwen
        qwen_result, qwen_method = self.comparator.compare_with_qwen(img1, img2)
        if qwen_result:
            all_votes.append({
                'model': 'qwen',
                'vote': qwen_result,
                'weight': config.VOTING_WEIGHTS['original']['qwen'],
                'stage': 'original',
                'method': qwen_method
            })
            api_call_count += 1
            time.sleep(config.RATE_DELAY)
        
        # 2. ChatGPT
        chatgpt_result, chatgpt_method = self.comparator.compare_with_chatgpt(img1, img2)
        if chatgpt_result:
            all_votes.append({
                'model': 'chatgpt',
                'vote': chatgpt_result,
                'weight': config.VOTING_WEIGHTS['original']['chatgpt'],
                'stage': 'original',
                'method': chatgpt_method
            })
            api_call_count += 1
            time.sleep(config.RATE_DELAY)
        
        # 3. Gemini
        gemini_result, gemini_method = self.comparator.compare_with_gemini(img1, img2)
        if gemini_result:
            all_votes.append({
                'model': 'gemini',
                'vote': gemini_result,
                'weight': config.VOTING_WEIGHTS['original']['gemini'],
                'stage': 'original',
                'method': gemini_method
            })
            api_call_count += 1
            time.sleep(config.RATE_DELAY)
        
        # 4. DeepFace
        deepface_result, deepface_method = self.comparator.compare_with_deepface(img1, img2)
        if deepface_result:
            all_votes.append({
                'model': 'deepface',
                'vote': deepface_result,
                'weight': config.VOTING_WEIGHTS['original']['deepface'],
                'stage': 'original',
                'method': deepface_method
            })
        
        # Store original results
        results['original'] = {
            'qwen': qwen_result,
            'chatgpt': chatgpt_result,
            'gemini': gemini_result,
            'deepface': deepface_result
        }
        
        logger.info(f"Original stage completed: {len(all_votes)} votes")
        
        # Check early stopping after original (unlikely to trigger at 4 votes)
        if progress_callback:
            progress_callback("Checking consensus...", 0.3)
        
        should_stop, decision, confidence = self.voting.check_early_stopping(all_votes)
        if should_stop:
            logger.info("✓ Early stopping after original images")
            results['stopped_early'] = True
            results['final_decision'] = decision
            results['confidence'] = confidence
            results['all_votes'] = all_votes
            results['total_votes'] = len(all_votes)
            results['total_api_calls'] = api_call_count
            results['processing_time'] = time.time() - start_time
            results['breakdown'] = self.voting.create_vote_breakdown(all_votes)
            return results
        
        # =================================================================
        # STAGE 2: CROPPED IMAGES (up to 4 votes)
        # =================================================================
        if progress_callback:
            progress_callback("Cropping faces with RetinaFace...", 0.4)
        
        logger.info("\n" + "="*60)
        logger.info("STAGE 2: CROPPED IMAGES")
        logger.info("="*60)
        
        cropped1, cropped2, crop_success = self.processor.crop_with_retinaface(img1, img2)
        results['cropping_success'] = crop_success
        
        if crop_success and cropped1 and cropped2:
            # Cropping successful - get new comparisons
            
            # 1. Qwen (cropped)
            qwen_cropped, qwen_crop_method = self.comparator.compare_with_qwen(cropped1, cropped2)
            api_call_count += 1
            time.sleep(config.RATE_DELAY)
            
            # 2. ChatGPT (cropped) - prioritized with higher weight
            chatgpt_cropped, chatgpt_crop_method = self.comparator.compare_with_chatgpt(cropped1, cropped2)
            if chatgpt_cropped:
                all_votes.append({
                    'model': 'chatgpt',
                    'vote': chatgpt_cropped,
                    'weight': config.VOTING_WEIGHTS['cropped']['chatgpt'],
                    'stage': 'cropped',
                    'method': chatgpt_crop_method
                })
            api_call_count += 1
            time.sleep(config.RATE_DELAY)
            
            # 3. Gemini (cropped)
            gemini_cropped, gemini_crop_method = self.comparator.compare_with_gemini(cropped1, cropped2)
            api_call_count += 1
            time.sleep(config.RATE_DELAY)
            
            # 4. RetinaFace comparison (for conditional voting)
            retinaface_result, retinaface_method = self.comparator.compare_with_retinaface(cropped1, cropped2)
            
            # Apply conditional rules for Qwen and Gemini
            if qwen_cropped and retinaface_result:
                conditional_votes = self.voting.apply_conditional_rules(
                    qwen_result=qwen_cropped,
                    gemini_result=gemini_cropped,
                    retinaface_result=retinaface_result
                )
                
                # Add conditional votes with stage information
                for vote in conditional_votes:
                    vote['stage'] = 'cropped'
                    vote['method'] = vote.get('method', '')
                    all_votes.append(vote)
            
            results['cropped'] = {
                'qwen': qwen_cropped,
                'chatgpt': chatgpt_cropped,
                'gemini': gemini_cropped,
                'retinaface': retinaface_result
            }
            
            logger.info(f"Cropped stage completed: {api_call_count} API calls so far")
        else:
            # Cropping failed - use original results as fallback
            logger.info("Cropping failed, using original results as fallback")
            
            # Copy original results to cropped (NO additional API calls)
            if qwen_result:
                all_votes.append({
                    'model': 'qwen',
                    'vote': qwen_result,
                    'weight': config.VOTING_WEIGHTS['cropped']['chatgpt'],  # Use cropped weight
                    'stage': 'cropped',
                    'method': qwen_method + '_fallback_original'
                })
            
            if chatgpt_result:
                all_votes.append({
                    'model': 'chatgpt',
                    'vote': chatgpt_result,
                    'weight': config.VOTING_WEIGHTS['cropped']['chatgpt'],
                    'stage': 'cropped',
                    'method': chatgpt_method + '_fallback_original'
                })
            
            if gemini_result:
                all_votes.append({
                    'model': 'gemini',
                    'vote': gemini_result,
                    'weight': 1.0,
                    'stage': 'cropped',
                    'method': gemini_method + '_fallback_original'
                })
            
            results['cropped'] = {'skipped': True, 'reason': 'cropping_failed'}
        
        # Check early stopping after cropped
        if progress_callback:
            progress_callback("Checking consensus...", 0.6)
        
        should_stop, decision, confidence = self.voting.check_early_stopping(all_votes)
        if should_stop:
            logger.info("✓ Early stopping after cropped images")
            results['stopped_early'] = True
            results['final_decision'] = decision
            results['confidence'] = confidence
            results['all_votes'] = all_votes
            results['total_votes'] = len(all_votes)
            results['total_api_calls'] = api_call_count
            results['processing_time'] = time.time() - start_time
            results['breakdown'] = self.voting.create_vote_breakdown(all_votes)
            return results
        
        # =================================================================
        # STAGE 3: ALIGNED IMAGES (up to 3 votes)
        # =================================================================
        if progress_callback:
            progress_callback("Aligning faces...", 0.7)
        
        logger.info("\n" + "="*60)
        logger.info("STAGE 3: ALIGNED IMAGES")
        logger.info("="*60)
        
        aligned1, aligned2, align_success = self.processor.align_faces(img1, img2)
        results['alignment_success'] = align_success
        
        if align_success and aligned1 and aligned2:
            # Alignment successful - get new comparisons
            
            # 1. Qwen (aligned)
            qwen_aligned, qwen_align_method = self.comparator.compare_with_qwen(aligned1, aligned2)
            if qwen_aligned:
                all_votes.append({
                    'model': 'qwen',
                    'vote': qwen_aligned,
                    'weight': config.VOTING_WEIGHTS['aligned']['qwen'],
                    'stage': 'aligned',
                    'method': qwen_align_method
                })
            api_call_count += 1
            time.sleep(config.RATE_DELAY)
            
            # 2. ChatGPT (aligned)
            chatgpt_aligned, chatgpt_align_method = self.comparator.compare_with_chatgpt(aligned1, aligned2)
            if chatgpt_aligned:
                all_votes.append({
                    'model': 'chatgpt',
                    'vote': chatgpt_aligned,
                    'weight': config.VOTING_WEIGHTS['aligned']['chatgpt'],
                    'stage': 'aligned',
                    'method': chatgpt_align_method
                })
            api_call_count += 1
            time.sleep(config.RATE_DELAY)
            
            # 3. Gemini (aligned)
            gemini_aligned, gemini_align_method = self.comparator.compare_with_gemini(aligned1, aligned2)
            if gemini_aligned:
                all_votes.append({
                    'model': 'gemini',
                    'vote': gemini_aligned,
                    'weight': config.VOTING_WEIGHTS['aligned']['gemini'],
                    'stage': 'aligned',
                    'method': gemini_align_method
                })
            api_call_count += 1
            
            results['aligned'] = {
                'qwen': qwen_aligned,
                'chatgpt': chatgpt_aligned,
                'gemini': gemini_aligned
            }
            
            logger.info(f"Aligned stage completed: {api_call_count} API calls total")
        else:
            # Alignment failed - use original results as fallback
            logger.info("Alignment failed, using original results as fallback")
            
            # Copy original results to aligned (NO additional API calls)
            if qwen_result:
                all_votes.append({
                    'model': 'qwen',
                    'vote': qwen_result,
                    'weight': config.VOTING_WEIGHTS['aligned']['qwen'],
                    'stage': 'aligned',
                    'method': qwen_method + '_fallback_original'
                })
            
            if chatgpt_result:
                all_votes.append({
                    'model': 'chatgpt',
                    'vote': chatgpt_result,
                    'weight': config.VOTING_WEIGHTS['aligned']['chatgpt'],
                    'stage': 'aligned',
                    'method': chatgpt_method + '_fallback_original'
                })
            
            if gemini_result:
                all_votes.append({
                    'model': 'gemini',
                    'vote': gemini_result,
                    'weight': config.VOTING_WEIGHTS['aligned']['gemini'],
                    'stage': 'aligned',
                    'method': gemini_method + '_fallback_original'
                })
            
            results['aligned'] = {'skipped': True, 'reason': 'alignment_failed'}
        
        # =================================================================
        # FINAL DECISION
        # =================================================================
        if progress_callback:
            progress_callback("Calculating final result...", 0.9)
        
        logger.info("\n" + "="*60)
        logger.info("FINAL DECISION")
        logger.info("="*60)
        
        final_decision, confidence, breakdown = self.voting.calculate_weighted_vote(all_votes)
        
        results['final_decision'] = final_decision
        results['confidence'] = confidence
        results['all_votes'] = all_votes
        results['total_votes'] = len(all_votes)
        results['total_api_calls'] = api_call_count
        results['processing_time'] = time.time() - start_time
        results['breakdown'] = self.voting.create_vote_breakdown(all_votes)
        
        # Generate report
        report = self.voting.generate_report(
            final_decision, confidence, all_votes, results['stopped_early']
        )
        logger.info("\n" + report)
        
        if progress_callback:
            progress_callback("Complete!", 1.0)
        
        return results

# Global orchestrator instance
orchestrator = ComparisonOrchestrator()

if __name__ == "__main__":
    print("Testing Orchestrator...")
    
    from pathlib import Path
    
    # Progress callback for testing
    def progress(message, percentage):
        print(f"[{percentage*100:.0f}%] {message}")
    
    # Test with sample images
    dataset = Path("dataset")
    if dataset.exists():
        test_imgs = list(dataset.glob("*_1.jpg"))[:2]
        
        if len(test_imgs) >= 2:
            print(f"\nComparing: {test_imgs[0].name} vs {test_imgs[1].name}")
            
            img1 = Image.open(test_imgs[0])
            img2 = Image.open(test_imgs[1])
            
            results = orchestrator.run_comparison(img1, img2, progress_callback=progress)
            
            print("\n" + "="*60)
            print("RESULTS SUMMARY")
            print("="*60)
            print(f"Final Decision: {results['final_decision'].upper()}")
            print(f"Confidence: {results['confidence']:.2f}%")
            print(f"Total Votes: {results['total_votes']}")
            print(f"API Calls: {results['total_api_calls']}")
            print(f"Processing Time: {results['processing_time']:.2f}s")
            print(f"Early Stopped: {results['stopped_early']}")
            print(f"Cropping Success: {results['cropping_success']}")
            print(f"Alignment Success: {results['alignment_success']}")
            print("="*60)
        else:
            print("Not enough test images")
    else:
        print("Dataset folder not found")
