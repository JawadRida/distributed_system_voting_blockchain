# 🗳️ Distributed Voting System with Blockchain

A secure, transparent, and tamper-proof voting system powered by blockchain technology and distributed systems architecture.

## 🌟 Features

- **Blockchain-Based**: All votes stored in an immutable blockchain
- **Distributed Architecture**: Three independent components (Producer, Consumer, Auditor)
- **Secure Authentication**: User login/signup system
- **Double-Voting Prevention**: Blockchain ensures one vote per user
- **Real-Time Results**: Live vote tallying from blockchain
- **Beautiful Web UI**: Modern, responsive interface
- **Cryptographic Security**: SHA-256 hashing and digital signatures
- **Proof-of-Work Consensus**: Decentralized validation

## 🏗️ Architecture

### Three Independent Components:

1. **Producer (Voter Client)**: Web interface for users to cast votes
2. **Consumer (Blockchain Nodes)**: Validates, mines, and stores votes in blocks
3. **Auditor**: Monitors blockchain integrity and detects fraud
```
┌─────────────┐
│  Web UI     │ (Producer - Port 5000)
│  Flask App  │
└──────┬──────┘
       │ REST API
       ↓
┌─────────────┐
│ Blockchain  │ (Consumer - Port 5001)
│   Nodes     │
└──────┬──────┘
       │ P2P
       ↓
┌─────────────┐
│  Auditor    │ (Monitor & Verify)
└─────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/voting-blockchain.git
cd voting-blockchain
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the System

**Terminal 1 - Start Blockchain Node:**
```bash
python main.py node 5001 node_1
```

**Terminal 2 - Start Web Application:**
```bash
python web_app.py
```

**Browser:**
```
http://localhost:5000
```

### Demo Account

- **Email**: admin@vote.com
- **Password**: admin123

## 📁 Project Structure
```
voting-blockchain/
├── block.py                  # Block structure
├── blockchain.py             # Blockchain logic
├── crypto_utils.py           # Cryptographic utilities
├── blockchain_node.py        # Blockchain node (Consumer)
├── voter_client.py           # Voter client (Producer)
├── auditor.py                # Auditor service
├── main.py                   # Entry point
├── web_app.py                # Web application
├── templates/                # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── signup.html
│   ├── login.html
│   ├── home.html
│   ├── results.html
│   └── verify.html
└── requirements.txt
```

## 🔒 Security Features

- **Voter Anonymity**: Email addresses hashed before blockchain storage
- **Digital Signatures**: Each vote cryptographically signed
- **Immutability**: Votes cannot be altered once in blockchain
- **Double-Voting Prevention**: Blockchain validates vote uniqueness
- **Password Encryption**: SHA-256 hashing

## 🎯 Distributed System Concepts

### Demonstrated Principles:

- ✅ **Scalability**: Horizontal scaling by adding nodes
- ✅ **Fault Tolerance**: System continues with node failures
- ✅ **Consensus**: Proof-of-Work algorithm
- ✅ **Concurrency**: Multiple simultaneous votes
- ✅ **Communication**: REST API + P2P networking
- ✅ **Consistency**: Blockchain synchronization

## 📊 Technologies Used

- **Backend**: Python, Flask
- **Blockchain**: Custom implementation with PoW
- **Frontend**: Bootstrap 5, JavaScript
- **Cryptography**: SHA-256, Digital Signatures
- **Communication**: REST API, HTTP

## 🧪 Testing

### Test Double-Voting Prevention:
```python
from voter_client import VoterClient

client = VoterClient("http://localhost:5001")
client.cast_vote("test@example.com", "Candidate A")  # ✓ Success
client.cast_vote("test@example.com", "Candidate B")  # ✗ Rejected
```

### Test Blockchain Integrity:
```python
from auditor import Auditor

auditor = Auditor(["http://localhost:5001"])
report = auditor.generate_audit_report()
print(report)
```

## 📸 Screenshots

### Landing Page
![Landing Page](screenshots/landing.png)

### Voting Interface
![Voting](screenshots/voting.png)

### Results Dashboard
![Results](screenshots/results.png)

## 🎓 Academic Project

This project was developed for a Distributed Systems course to demonstrate:
- Blockchain integration in distributed applications
- Three-component distributed architecture
- Consensus mechanisms
- Fault tolerance and scalability

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License.

## 👨‍💻 Author

[Your Name]
- GitHub: [@yourusername](https://github.com/yourusername)

## 🙏 Acknowledgments

- Course: Distributed Systems
- University: [Your University]
- Year: 2024-2025

---

**⭐ If you found this project helpful, please give it a star!**