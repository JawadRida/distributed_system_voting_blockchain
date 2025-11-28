import json
from typing import List, Dict, Optional
from block import Block

class Blockchain:
    """Manages the blockchain of votes"""
    
    def __init__(self):
        self.chain: List[Block] = []
        self.pending_votes: List[Dict] = []
        self.difficulty = 4
        self.mining_reward = 1
        self.voter_ids = set()  # Track voters to prevent double voting
        self.create_genesis_block()
    
    def create_genesis_block(self):
        """Create the first block in the chain"""
        genesis_block = Block(0, [], "0")
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)
    
    def get_latest_block(self) -> Block:
        """Get the most recent block"""
        return self.chain[-1]
    
    def add_vote(self, vote: Dict) -> Dict:
        """Add a vote to pending votes (Producer action)"""
        voter_id = vote.get("voter_id")
        
        # Check for double voting
        if voter_id in self.voter_ids:
            return {
                "success": False,
                "message": "Voter has already cast a vote",
                "voter_id": voter_id
            }
        
        # Validate vote structure
        required_fields = ["voter_id", "candidate", "timestamp", "signature"]
        if not all(field in vote for field in required_fields):
            return {
                "success": False,
                "message": "Invalid vote structure"
            }
        
        self.pending_votes.append(vote)
        self.voter_ids.add(voter_id)
        
        return {
            "success": True,
            "message": "Vote added to pending pool",
            "vote_id": vote.get("voter_id")
        }
    
    def mine_pending_votes(self, miner_address: str) -> bool:
        """Mine pending votes into a new block (Consumer action)"""
        if not self.pending_votes:
            return False
        
        # Create new block with pending votes
        new_block = Block(
            index=len(self.chain),
            votes=self.pending_votes.copy(),
            previous_hash=self.get_latest_block().hash
        )
        
        # Mine the block
        new_block.mine_block(self.difficulty)
        
        # Add to chain
        self.chain.append(new_block)
        
        # Clear pending votes
        self.pending_votes = []
        
        print(f"Block {new_block.index} mined by {miner_address}")
        return True
    
    def is_chain_valid(self) -> bool:
        """Verify blockchain integrity (Auditor action)"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Verify hash
            if current_block.hash != current_block.calculate_hash():
                print(f"Invalid hash at block {i}")
                return False
            
            # Verify chain linkage
            if current_block.previous_hash != previous_block.hash:
                print(f"Invalid previous hash at block {i}")
                return False
            
            # Verify proof of work
            if not current_block.hash.startswith("0" * self.difficulty):
                print(f"Invalid proof of work at block {i}")
                return False
        
        return True
    
    def get_vote_count(self) -> Dict[str, int]:
        """Count votes for each candidate"""
        vote_count = {}
        
        for block in self.chain[1:]:  # Skip genesis block
            for vote in block.votes:
                candidate = vote.get("candidate")
                if candidate:
                    vote_count[candidate] = vote_count.get(candidate, 0) + 1
        
        return vote_count
    
    def to_dict(self) -> List[Dict]:
        """Export blockchain to dictionary"""
        return [block.to_dict() for block in self.chain]