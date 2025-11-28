import sys
import threading
import time

def run_node(port, node_id):
    """Run a blockchain node"""
    from blockchain_node import BlockchainNode
    node = BlockchainNode(port, node_id)
    node.run()

def simulate_voting():
    """Simulate voting process"""
    time.sleep(3)  # Wait for nodes to start
    
    from voter_client import VoterClient
    
    print("\n=== SIMULATING VOTING PROCESS ===\n")
    
    # Create voter clients
    voter1 = VoterClient("http://localhost:5001")
    voter2 = VoterClient("http://localhost:5002")
    voter3 = VoterClient("http://localhost:5003")
    
    # Cast votes
    voters = [
        ("alice@email.com", "Candidate A", voter1),
        ("bob@email.com", "Candidate B", voter2),
        ("charlie@email.com", "Candidate A", voter3),
        ("diana@email.com", "Candidate C", voter1),
        ("eve@email.com", "Candidate B", voter2),
        ("frank@email.com", "Candidate A", voter3)
    ]
    
    for voter_id, candidate, client in voters:
        result = client.cast_vote(voter_id, candidate)
        print(f"Vote from {voter_id}: {result['message']}")
        time.sleep(1)
    
    # Wait for mining
    print("\nWaiting for blocks to be mined...")
    time.sleep(10)
    
    # Get results
    print("\n=== VOTING RESULTS ===")
    results = voter1.get_results()
    print(f"Results: {results['results']}")
    print(f"Blockchain valid: {results['is_valid']}")
    
    # Run audit
    print("\n=== AUDIT REPORT ===")
    from auditor import Auditor
    auditor = Auditor([
        "http://localhost:5001",
        "http://localhost:5002",
        "http://localhost:5003"
    ])
    
    report = auditor.generate_audit_report()
    print(f"Consensus achieved: {report['consensus_check']['consensus']}")
    print(f"Double voting detected: {report['double_voting_check']['double_voting_detected']}")
    print(f"Total unique voters: {report['double_voting_check']['total_unique_voters']}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "node":
        # Run single node
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 5001
        node_id = sys.argv[3] if len(sys.argv) > 3 else f"node_{port}"
        run_node(port, node_id)
    else:
        # Run full simulation
        print("Starting Distributed Voting System...")
        
        # Start 3 blockchain nodes
        nodes = [
            (5001, "node_1"),
            (5002, "node_2"),
            (5003, "node_3")
        ]
        
        threads = []
        for port, node_id in nodes:
            thread = threading.Thread(target=run_node, args=(port, node_id), daemon=True)
            thread.start()
            threads.append(thread)
            time.sleep(1)
        
        # Connect nodes as peers
        time.sleep(3)
        import requests
        try:
            requests.post("http://localhost:5001/peers/add", 
                         json={"peer_url": "http://localhost:5002"})
            requests.post("http://localhost:5001/peers/add", 
                         json={"peer_url": "http://localhost:5003"})
            requests.post("http://localhost:5002/peers/add", 
                         json={"peer_url": "http://localhost:5001"})
            requests.post("http://localhost:5002/peers/add", 
                         json={"peer_url": "http://localhost:5003"})
            requests.post("http://localhost:5003/peers/add", 
                         json={"peer_url": "http://localhost:5001"})
            requests.post("http://localhost:5003/peers/add", 
                         json={"peer_url": "http://localhost:5002"})
        except:
            pass
        
        # Run voting simulation
        simulate_voting()
        
        print("\nSystem running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")