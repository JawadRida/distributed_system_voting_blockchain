import hashlib
import json
import time
from typing import List, Dict, Any

class Block:
    """Represents a single block in the blockchain"""
    
    def __init__(self, index: int, votes: List[Dict], previous_hash: str, timestamp: float = None):
        self.index = index
        self.votes = votes
        self.timestamp = timestamp or time.time()
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """Calculate SHA-256 hash of block contents"""
        block_string = json.dumps({
            "index": self.index,
            "votes": self.votes,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty: int = 4):
        """Mine block using Proof of Work"""
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        print(f"Block mined: {self.hash}")
    
    def to_dict(self) -> Dict:
        """Convert block to dictionary"""
        return {
            "index": self.index,
            "votes": self.votes,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash
        }
