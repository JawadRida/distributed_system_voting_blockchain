from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import threading
import time
from typing import Dict, List
from block import Block
from blockchain import Blockchain
from crypto_utils import CryptoUtils

class BlockchainNode:
    """Blockchain node that processes and validates votes (Consumer)"""
    
    def __init__(self, port: int, node_id: str):
        self.app = Flask(__name__)
        CORS(self.app)
        self.blockchain = Blockchain()
        self.port = port
        self.node_id = node_id
        self.peers = set()
        self.setup_routes()
        self.mining_active = True
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/vote', methods=['POST'])
        def submit_vote():
            """Receive vote from producer"""
            vote_data = request.json
            
            # Verify signature
            if not CryptoUtils.verify_signature(vote_data):
                return jsonify({
                    "success": False,
                    "message": "Invalid vote signature"
                }), 400
            
            # Add vote to blockchain
            result = self.blockchain.add_vote(vote_data)
            
            # Broadcast to peers
            if result["success"]:
                self.broadcast_vote(vote_data)
            
            return jsonify(result)
        
        @self.app.route('/chain', methods=['GET'])
        def get_chain():
            """Get full blockchain"""
            return jsonify({
                "chain": self.blockchain.to_dict(),
                "length": len(self.blockchain.chain)
            })
        
        @self.app.route('/pending', methods=['GET'])
        def get_pending():
            """Get pending votes"""
            return jsonify({
                "pending_votes": self.blockchain.pending_votes,
                "count": len(self.blockchain.pending_votes)
            })
        
        @self.app.route('/results', methods=['GET'])
        def get_results():
            """Get voting results"""
            return jsonify({
                "results": self.blockchain.get_vote_count(),
                "total_blocks": len(self.blockchain.chain),
                "is_valid": self.blockchain.is_chain_valid()
            })
        
        @self.app.route('/peers/add', methods=['POST'])
        def add_peer():
            """Add peer node"""
            peer_url = request.json.get('peer_url')
            if peer_url:
                self.peers.add(peer_url)
                return jsonify({"message": f"Peer added: {peer_url}"})
            return jsonify({"error": "Invalid peer URL"}), 400
        
        @self.app.route('/peers', methods=['GET'])
        def get_peers():
            """Get all peers"""
            return jsonify({"peers": list(self.peers)})
        
        @self.app.route('/sync', methods=['POST'])
        def sync_chain():
            """Synchronize blockchain with peers"""
            self.consensus()
            return jsonify({
                "message": "Blockchain synchronized",
                "length": len(self.blockchain.chain)
            })
    
    def broadcast_vote(self, vote: Dict):
        """Broadcast vote to peer nodes (asynchronous)"""
        def send_to_peer(peer_url, vote_data):
            try:
                requests.post(f"{peer_url}/vote", json=vote_data, timeout=2)
            except:
                pass
        
        # Send to peers in separate threads to avoid blocking
        for peer in self.peers:
            thread = threading.Thread(target=send_to_peer, args=(peer, vote), daemon=True)
            thread.start()
    
    def consensus(self):
        """Achieve consensus by adopting longest valid chain"""
        longest_chain = None
        max_length = len(self.blockchain.chain)
        
        for peer in self.peers:
            try:
                response = requests.get(f"{peer}/chain", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    length = data['length']
                    chain_data = data['chain']
                    
                    if length > max_length:
                        # Validate chain before accepting
                        temp_blockchain = Blockchain()
                        temp_blockchain.chain = []
                        for block_data in chain_data:
                            block = Block(
                                index=block_data['index'],
                                votes=block_data['votes'],
                                previous_hash=block_data['previous_hash'],
                                timestamp=block_data['timestamp']
                            )
                            block.nonce = block_data['nonce']
                            block.hash = block_data['hash']
                            temp_blockchain.chain.append(block)
                        
                        if temp_blockchain.is_chain_valid():
                            longest_chain = temp_blockchain
                            max_length = length
            except:
                pass
        
        if longest_chain:
            self.blockchain = longest_chain
            print(f"Chain replaced with length {max_length}")
            return True
        
        return False
    
    def auto_mine(self):
        """Automatically mine blocks when pending votes exist"""
        while self.mining_active:
            time.sleep(5)  # Check every 5 seconds
            
            # Sync with network before mining to avoid forks
            self.consensus()
            
            if len(self.blockchain.pending_votes) >= 1:  # Mine when 1+ votes pending
                self.blockchain.mine_pending_votes(self.node_id)
                time.sleep(1)  # Brief pause to allow propagation
                self.consensus()  # Sync with network after mining
    
    def run(self):
        """Start the node"""
        # Start auto-mining in background thread
        mining_thread = threading.Thread(target=self.auto_mine, daemon=True)
        mining_thread.start()
        
        print(f"Node {self.node_id} running on port {self.port}")
        self.app.run(host='0.0.0.0', port=self.port, debug=False)

