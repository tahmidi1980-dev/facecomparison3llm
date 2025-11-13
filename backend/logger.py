"""
CSV Logger for Face Comparison System
Logs all comparisons to CSV file for analysis
"""
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import config

class ComparisonLogger:
    """Logs comparison results to CSV file"""
    
    def __init__(self, log_file: Path = None):
        self.log_file = log_file or config.LOG_FILE
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create header if file doesn't exist
        if not self.log_file.exists():
            self._create_header()
    
    def _create_header(self):
        """Create CSV header"""
        with open(self.log_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp',
                'final_result',
                'confidence',
                'total_votes',
                'votes_for_same',
                'votes_for_different',
                'api_calls',
                'processing_time_seconds',
                'early_stopped',
                'cropping_success',
                'alignment_success',
                'original_votes_json',
                'cropped_votes_json',
                'aligned_votes_json',
                'ip_address',
                'user_agent'
            ])
    
    def log_comparison(self, result: Dict[str, Any], 
                      ip_address: str = "", 
                      user_agent: str = ""):
        """
        Log a comparison result
        
        Args:
            result: Result dictionary from orchestrator
            ip_address: Client IP address
            user_agent: Client user agent
        """
        if not config.ENABLE_LOGGING:
            return
        
        try:
            with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Calculate votes
                votes_same = sum(1 for v in result.get('all_votes', []) if v['vote'] == 'same')
                votes_different = result['total_votes'] - votes_same
                
                writer.writerow([
                    datetime.now().isoformat(),
                    result['final_decision'],
                    f"{result['confidence']:.2f}",
                    result['total_votes'],
                    votes_same,
                    votes_different,
                    result['total_api_calls'],
                    f"{result['processing_time']:.2f}",
                    result['stopped_early'],
                    result.get('cropping_success', False),
                    result.get('alignment_success', False),
                    json.dumps(result.get('original', {})),
                    json.dumps(result.get('cropped', {})),
                    json.dumps(result.get('aligned', {})),
                    ip_address,
                    user_agent
                ])
        except Exception as e:
            print(f"⚠️  Logging error: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics from log file"""
        if not self.log_file.exists():
            return {
                'total_comparisons': 0,
                'same_person': 0,
                'different_person': 0,
                'avg_confidence': 0.0,
                'avg_processing_time': 0.0,
                'total_api_calls': 0,
                'early_stops': 0
            }
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            if not rows:
                return {'total_comparisons': 0}
            
            total = len(rows)
            same = sum(1 for r in rows if r['final_result'] == 'same')
            different = total - same
            
            confidences = [float(r['confidence']) for r in rows if r['confidence']]
            times = [float(r['processing_time_seconds']) for r in rows if r['processing_time_seconds']]
            api_calls = [int(r['api_calls']) for r in rows if r['api_calls']]
            early_stops = sum(1 for r in rows if r['early_stopped'] == 'True')
            
            return {
                'total_comparisons': total,
                'same_person': same,
                'different_person': different,
                'avg_confidence': sum(confidences) / len(confidences) if confidences else 0,
                'avg_processing_time': sum(times) / len(times) if times else 0,
                'total_api_calls': sum(api_calls),
                'early_stops': early_stops,
                'early_stop_rate': (early_stops / total * 100) if total > 0 else 0
            }
        except Exception as e:
            print(f"⚠️  Statistics error: {e}")
            return {'total_comparisons': 0, 'error': str(e)}

# Global logger instance
logger = ComparisonLogger()

if __name__ == "__main__":
    # Test logger
    print("Testing Logger...")
    
    # Test log entry
    test_result = {
        'final_decision': 'same',
        'confidence': 87.5,
        'total_votes': 10,
        'total_api_calls': 11,
        'processing_time': 12.3,
        'stopped_early': False,
        'cropping_success': True,
        'alignment_success': True,
        'all_votes': [
            {'model': 'qwen', 'stage': 'original', 'vote': 'same'},
            {'model': 'chatgpt', 'stage': 'original', 'vote': 'same'},
        ],
        'original': {},
        'cropped': {},
        'aligned': {}
    }
    
    logger.log_comparison(test_result, ip_address="127.0.0.1", user_agent="test")
    print("✅ Test log created")
    
    # Get statistics
    stats = logger.get_statistics()
    print("\n📊 Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
