"""
Voting System Module
Implements weighted voting with conditional rules
"""
import logging
from typing import Dict, List, Tuple, Any
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VotingSystem:
    """Handles weighted voting and decision making"""
    
    def __init__(self):
        self.weights = config.VOTING_WEIGHTS
        self.early_stop_threshold = config.EARLY_STOP_THRESHOLD
        self.enable_early_stop = config.ENABLE_EARLY_STOP
    
    def apply_conditional_rules(self, 
                               qwen_result: str, 
                               gemini_result: str, 
                               retinaface_result: str) -> List[Dict[str, Any]]:
        """
        Apply conditional voting rules for cropped images
        
        For Qwen and Gemini:
        - If LLM result differs from RetinaFace: 
          Split vote: 0.7 weight to RetinaFace, 0.3 weight to LLM
        - If LLM result agrees with RetinaFace:
          Single vote with full weight 1.0
        
        Args:
            qwen_result: Qwen's comparison result ('same'/'different')
            gemini_result: Gemini's comparison result
            retinaface_result: RetinaFace's comparison result
        
        Returns:
            List of vote dictionaries
        """
        votes = []
        
        # Process Qwen
        if qwen_result and retinaface_result:
            if qwen_result == retinaface_result:
                # Agreement: single vote with weight 1.0
                votes.append({
                    'model': 'qwen',
                    'vote': qwen_result,
                    'weight': 1.0,
                    'conditional': 'agree'
                })
            else:
                # Disagreement: split vote 0.7/0.3
                votes.append({
                    'model': 'retinaface_qwen',
                    'vote': retinaface_result,
                    'weight': self.weights['cropped']['retinaface_weight'],
                    'conditional': 'split'
                })
                votes.append({
                    'model': 'qwen',
                    'vote': qwen_result,
                    'weight': self.weights['cropped']['llm_weight'],
                    'conditional': 'split'
                })
        
        # Process Gemini
        if gemini_result and retinaface_result:
            if gemini_result == retinaface_result:
                # Agreement: single vote with weight 1.0
                votes.append({
                    'model': 'gemini',
                    'vote': gemini_result,
                    'weight': 1.0,
                    'conditional': 'agree'
                })
            else:
                # Disagreement: split vote 0.7/0.3
                votes.append({
                    'model': 'retinaface_gemini',
                    'vote': retinaface_result,
                    'weight': self.weights['cropped']['retinaface_weight'],
                    'conditional': 'split'
                })
                votes.append({
                    'model': 'gemini',
                    'vote': gemini_result,
                    'weight': self.weights['cropped']['llm_weight'],
                    'conditional': 'split'
                })
        
        return votes
    
    def calculate_weighted_vote(self, all_votes: List[Dict[str, Any]]) -> Tuple[str, float, Dict[str, Any]]:
        """
        Calculate final decision using weighted voting
        
        Args:
            all_votes: List of all vote dictionaries
        
        Returns:
            (final_decision, confidence, breakdown)
        """
        # Calculate total weights for each outcome
        weight_same = 0.0
        weight_different = 0.0
        total_weight = 0.0
        
        for vote in all_votes:
            if vote.get('vote') is None:
                continue
            
            weight = vote.get('weight', 1.0)
            total_weight += weight
            
            if vote['vote'] == 'same':
                weight_same += weight
            elif vote['vote'] == 'different':
                weight_different += weight
        
        # Determine final decision
        if weight_same > weight_different:
            final_decision = 'same'
            confidence = (weight_same / total_weight * 100) if total_weight > 0 else 0
        else:
            final_decision = 'different'
            confidence = (weight_different / total_weight * 100) if total_weight > 0 else 0
        
        # Create breakdown
        breakdown = {
            'total_weight': total_weight,
            'weight_same': weight_same,
            'weight_different': weight_different,
            'percentage_same': (weight_same / total_weight * 100) if total_weight > 0 else 0,
            'percentage_different': (weight_different / total_weight * 100) if total_weight > 0 else 0,
            'total_votes': len([v for v in all_votes if v.get('vote') is not None])
        }
        
        logger.info(f"Weighted voting result: {final_decision} ({confidence:.1f}%)")
        logger.info(f"  Same: {weight_same:.2f}, Different: {weight_different:.2f}, Total: {total_weight:.2f}")
        
        return final_decision, confidence, breakdown
    
    def check_early_stopping(self, all_votes: List[Dict[str, Any]]) -> Tuple[bool, str, float]:
        """
        Check if early stopping criteria is met
        
        Args:
            all_votes: Current list of votes
        
        Returns:
            (should_stop, decision, confidence)
        """
        if not self.enable_early_stop:
            return False, "", 0.0
        
        # Count valid votes
        valid_votes = [v for v in all_votes if v.get('vote') is not None]
        
        if len(valid_votes) < self.early_stop_threshold:
            return False, "", 0.0
        
        # Calculate current decision
        decision, confidence, _ = self.calculate_weighted_vote(all_votes)
        
        # Count votes for winning decision
        votes_for_decision = sum(1 for v in valid_votes if v['vote'] == decision)
        
        # Check if threshold met
        if votes_for_decision >= self.early_stop_threshold:
            logger.info(f"✓ Early stopping triggered: {votes_for_decision}/{len(valid_votes)} votes for '{decision}'")
            return True, decision, confidence
        
        return False, "", 0.0
    
    def create_vote_breakdown(self, all_votes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create detailed breakdown of votes by stage
        
        Returns:
            Dictionary with vote breakdown by stage
        """
        breakdown = {
            'original': [],
            'cropped': [],
            'aligned': [],
            'summary': {
                'total_votes': 0,
                'votes_same': 0,
                'votes_different': 0,
                'votes_skipped': 0
            }
        }
        
        for vote in all_votes:
            stage = vote.get('stage', 'unknown')
            
            if stage in breakdown:
                breakdown[stage].append({
                    'model': vote.get('model', 'unknown'),
                    'vote': vote.get('vote', 'skipped'),
                    'weight': vote.get('weight', 0.0),
                    'method': vote.get('method', ''),
                    'conditional': vote.get('conditional', 'none')
                })
            
            # Update summary
            if vote.get('vote') == 'same':
                breakdown['summary']['votes_same'] += 1
            elif vote.get('vote') == 'different':
                breakdown['summary']['votes_different'] += 1
            elif vote.get('vote') is None:
                breakdown['summary']['votes_skipped'] += 1
            
            breakdown['summary']['total_votes'] += 1
        
        return breakdown
    
    def generate_report(self, final_decision: str, confidence: float, 
                       all_votes: List[Dict[str, Any]], 
                       stopped_early: bool) -> str:
        """Generate human-readable report"""
        
        report_lines = [
            "=" * 60,
            "VOTING REPORT",
            "=" * 60,
            f"Final Decision: {final_decision.upper()}",
            f"Confidence: {confidence:.2f}%",
            f"Early Stopped: {'Yes' if stopped_early else 'No'}",
            "",
            "Vote Breakdown:",
            "-" * 60
        ]
        
        # Group by stage
        stages = {}
        for vote in all_votes:
            stage = vote.get('stage', 'unknown')
            if stage not in stages:
                stages[stage] = []
            stages[stage].append(vote)
        
        # Print each stage
        for stage_name, votes in stages.items():
            report_lines.append(f"\n{stage_name.upper()}:")
            for vote in votes:
                model = vote.get('model', 'unknown')
                result = vote.get('vote', 'skipped')
                weight = vote.get('weight', 0.0)
                conditional = vote.get('conditional', '')
                
                line = f"  • {model:20s}: {result:10s} (weight: {weight:.2f})"
                if conditional:
                    line += f" [{conditional}]"
                report_lines.append(line)
        
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)

# Global voting system instance
voting_system = VotingSystem()

if __name__ == "__main__":
    print("Testing Voting System...")
    
    # Test conditional rules
    print("\n1. Testing Conditional Rules:")
    print("   Scenario: Qwen=same, Gemini=different, RetinaFace=same")
    
    votes = voting_system.apply_conditional_rules(
        qwen_result='same',
        gemini_result='different',
        retinaface_result='same'
    )
    
    for vote in votes:
        print(f"   - {vote['model']:20s}: {vote['vote']:10s} (weight: {vote['weight']:.2f})")
    
    # Test weighted voting
    print("\n2. Testing Weighted Voting:")
    
    test_votes = [
        {'model': 'qwen', 'vote': 'same', 'weight': 1.0, 'stage': 'original'},
        {'model': 'chatgpt', 'vote': 'same', 'weight': 1.0, 'stage': 'original'},
        {'model': 'gemini', 'vote': 'different', 'weight': 1.0, 'stage': 'original'},
        {'model': 'deepface', 'vote': 'same', 'weight': 1.0, 'stage': 'original'},
        {'model': 'chatgpt', 'vote': 'same', 'weight': 1.2, 'stage': 'cropped'},
        {'model': 'qwen', 'vote': 'different', 'weight': 0.3, 'stage': 'cropped'},
        {'model': 'retinaface', 'vote': 'same', 'weight': 0.7, 'stage': 'cropped'},
    ]
    
    decision, confidence, breakdown = voting_system.calculate_weighted_vote(test_votes)
    print(f"   Final Decision: {decision}")
    print(f"   Confidence: {confidence:.2f}%")
    print(f"   Breakdown: {breakdown}")
    
    # Test early stopping
    print("\n3. Testing Early Stopping:")
    should_stop, dec, conf = voting_system.check_early_stopping(test_votes)
    print(f"   Should Stop: {should_stop}")
    print(f"   Decision: {dec}, Confidence: {conf:.2f}%")
    
    # Test report generation
    print("\n4. Generating Report:")
    report = voting_system.generate_report(decision, confidence, test_votes, should_stop)
    print(report)
