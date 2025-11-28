import hashlib
import json
from typing import Dict

class CryptoUtils:
    """Cryptographic utilities for voting system"""
    
    @staticmethod
    def hash_voter_id(voter_id: str) -> str:
        """Hash voter ID for anonymity"""
        return hashlib.sha256(voter_id.encode()).hexdigest()
    
    @staticmethod
    def sign_vote(vote_data: Dict) -> str:
        """Create digital signature for vote (simplified)"""
        vote_string = json.dumps(vote_data, sort_keys=True)
        return hashlib.sha256(vote_string.encode()).hexdigest()
    
    @staticmethod
    def verify_signature(vote: Dict) -> bool:
        """Verify vote signature"""
        signature = vote.get("signature")
        vote_copy = {k: v for k, v in vote.items() if k != "signature"}
        expected_signature = CryptoUtils.sign_vote(vote_copy)
        return signature == expected_signature
