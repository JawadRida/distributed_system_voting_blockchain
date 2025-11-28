import requests
import time
from typing import Dict
from crypto_utils import CryptoUtils

class VoterClient:
    """Client for voters to submit votes (Producer)"""
    
    def __init__(self, node_url: str = "http://localhost:5001"):
        self.node_url = node_url
    
    def cast_vote(self, voter_id: str, candidate: str) -> Dict:
        """Cast a vote"""
        # Create vote data
        vote_data = {
            "voter_id": CryptoUtils.hash_voter_id(voter_id),
            "candidate": candidate,
            "timestamp": time.time()
        }
        
        # Sign vote
        vote_data["signature"] = CryptoUtils.sign_vote(vote_data)
        
        # Submit to blockchain node
        try:
            response = requests.post(f"{self.node_url}/vote", json=vote_data, timeout=10)
            return response.json()
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to submit vote: {str(e)}"
            }
    
    def get_results(self) -> Dict:
        """Get current voting results"""
        try:
            response = requests.get(f"{self.node_url}/results", timeout=5)
            return response.json()
        except Exception as e:
            return {
                "error": f"Failed to get results: {str(e)}"
            }
    
    def verify_vote_recorded(self, voter_id: str) -> bool:
        """Verify that vote was recorded in blockchain"""
        try:
            response = requests.get(f"{self.node_url}/chain", timeout=5)
            chain_data = response.json()
            
            hashed_voter_id = CryptoUtils.hash_voter_id(voter_id)
            
            for block in chain_data['chain']:
                for vote in block.get('votes', []):
                    if vote.get('voter_id') == hashed_voter_id:
                        return True
            return False
        except:
            return False

