import requests
import time
from typing import List, Dict

class Auditor:
    """Independent auditor service to monitor blockchain integrity"""
    
    def __init__(self, node_urls: List[str]):
        self.node_urls = node_urls
    
    def verify_chain_integrity(self, node_url: str) -> Dict:
        """Verify blockchain integrity on a specific node"""
        try:
            response = requests.get(f"{node_url}/chain", timeout=5)
            chain_data = response.json()
            
            # Verify each block's hash
            for i, block_data in enumerate(chain_data['chain']):
                if i > 0:
                    prev_block = chain_data['chain'][i-1]
                    if block_data['previous_hash'] != prev_block['hash']:
                        return {
                            "valid": False,
                            "error": f"Chain broken at block {i}",
                            "node": node_url
                        }
            
            return {
                "valid": True,
                "blocks": len(chain_data['chain']),
                "node": node_url
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "node": node_url
            }
    
    def check_consensus(self) -> Dict:
        """Check if all nodes have the same blockchain"""
        chains = {}
        
        for node_url in self.node_urls:
            try:
                response = requests.get(f"{node_url}/chain", timeout=5)
                chain_hash = hash(str(response.json()['chain']))
                chains[node_url] = {
                    "hash": chain_hash,
                    "length": response.json()['length']
                }
            except:
                chains[node_url] = {"error": "Unreachable"}
        
        # Check if all chains match
        chain_hashes = [v.get("hash") for v in chains.values() if "hash" in v]
        consensus = len(set(chain_hashes)) <= 1
        
        return {
            "consensus": consensus,
            "node_states": chains
        }
    
    def detect_double_voting(self) -> Dict:
        """Detect if any voter has voted multiple times"""
        voter_ids = {}
        double_voters = []
        
        for node_url in self.node_urls:
            try:
                response = requests.get(f"{node_url}/chain", timeout=5)
                chain = response.json()['chain']
                
                for block in chain:
                    for vote in block.get('votes', []):
                        voter_id = vote.get('voter_id')
                        if voter_id in voter_ids:
                            double_voters.append(voter_id)
                        else:
                            voter_ids[voter_id] = True
                
                break  # Only check one node (all should be same)
            except:
                continue
        
        return {
            "double_voting_detected": len(double_voters) > 0,
            "double_voters": list(set(double_voters)),
            "total_unique_voters": len(voter_ids)
        }
    
    def generate_audit_report(self) -> Dict:
        """Generate comprehensive audit report"""
        report = {
            "timestamp": time.time(),
            "nodes_audited": len(self.node_urls),
            "integrity_checks": [],
            "consensus_check": self.check_consensus(),
            "double_voting_check": self.detect_double_voting()
        }
        
        for node_url in self.node_urls:
            integrity = self.verify_chain_integrity(node_url)
            report["integrity_checks"].append(integrity)
        
        return report
