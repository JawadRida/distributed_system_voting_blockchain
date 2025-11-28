from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_cors import CORS
import hashlib
import json
import time
import requests
import secrets
from functools import wraps

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
CORS(app)

# Configuration
BLOCKCHAIN_NODE_URL = "http://localhost:5001"
CANDIDATES = [
    {"id": "candidate_a", "name": "Candidate A", "party": "Party Alpha", "description": "Focus on education and healthcare"},
    {"id": "candidate_b", "name": "Candidate B", "party": "Party Beta", "description": "Focus on economy and jobs"},
    {"id": "candidate_c", "name": "Candidate C", "party": "Party Gamma", "description": "Focus on environment and technology"}
]

# Simple in-memory user database (in production, use a real database)
users_db = {
    "admin@vote.com": {
        "password": hashlib.sha256("admin123".encode()).hexdigest(),
        "name": "Admin User"
    }
}

# Utility Functions
def hash_password(password):
    """Hash password for storage"""
    return hashlib.sha256(password.encode()).hexdigest()

def hash_voter_id(email):
    """Hash email for blockchain anonymity"""
    return hashlib.sha256(email.encode()).hexdigest()

def sign_vote(vote_data):
    """Create digital signature for vote"""
    vote_string = json.dumps(vote_data, sort_keys=True)
    return hashlib.sha256(vote_string.encode()).hexdigest()

def check_if_voted(email):
    """Check if user has already voted by querying blockchain"""
    try:
        response = requests.get(f"{BLOCKCHAIN_NODE_URL}/chain", timeout=5)
        chain_data = response.json()
        
        hashed_email = hash_voter_id(email)
        
        # Check all blocks for this voter ID
        for block in chain_data['chain']:
            for vote in block.get('votes', []):
                if vote.get('voter_id') == hashed_email:
                    return True
        return False
    except:
        return False

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    """Landing page"""
    if 'user_email' in session:
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not all([name, email, password, confirm_password]):
            flash('All fields are required', 'danger')
            return redirect(url_for('signup'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('signup'))
        
        if email in users_db:
            flash('Email already registered', 'danger')
            return redirect(url_for('signup'))
        
        # Create user
        users_db[email] = {
            "password": hash_password(password),
            "name": name
        }
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email in users_db:
            if users_db[email]['password'] == hash_password(password):
                session['user_email'] = email
                session['user_name'] = users_db[email]['name']
                flash(f'Welcome back, {users_db[email]["name"]}!', 'success')
                return redirect(url_for('home'))
        
        flash('Invalid email or password', 'danger')
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/home')
@login_required
def home():
    """Main voting page"""
    user_email = session.get('user_email')
    has_voted = check_if_voted(user_email)
    
    return render_template('home.html', 
                         candidates=CANDIDATES,
                         has_voted=has_voted,
                         user_name=session.get('user_name'))

@app.route('/vote', methods=['POST'])
@login_required
def vote():
    """Submit vote"""
    user_email = session.get('user_email')
    
    # Check if already voted
    if check_if_voted(user_email):
        return jsonify({
            'success': False,
            'message': 'You have already voted!'
        }), 400
    
    candidate_id = request.json.get('candidate_id')
    
    if not candidate_id:
        return jsonify({
            'success': False,
            'message': 'Please select a candidate'
        }), 400
    
    # Find candidate name
    candidate_name = None
    for candidate in CANDIDATES:
        if candidate['id'] == candidate_id:
            candidate_name = candidate['name']
            break
    
    if not candidate_name:
        return jsonify({
            'success': False,
            'message': 'Invalid candidate'
        }), 400
    
    # Create vote data
    vote_data = {
        "voter_id": hash_voter_id(user_email),
        "candidate": candidate_name,
        "timestamp": time.time()
    }
    
    # Sign vote
    vote_data["signature"] = sign_vote(vote_data)
    
    # Submit to blockchain
    try:
        response = requests.post(
            f"{BLOCKCHAIN_NODE_URL}/vote",
            json=vote_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                return jsonify({
                    'success': True,
                    'message': f'Your vote for {candidate_name} has been recorded!'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': result.get('message', 'Vote failed')
                }), 400
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to submit vote to blockchain'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/results')
@login_required
def results():
    """View voting results"""
    try:
        response = requests.get(f"{BLOCKCHAIN_NODE_URL}/results", timeout=5)
        data = response.json()
        
        # Map results to candidates
        results_data = []
        total_votes = sum(data['results'].values())
        
        for candidate in CANDIDATES:
            vote_count = data['results'].get(candidate['name'], 0)
            percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
            
            results_data.append({
                'name': candidate['name'],
                'party': candidate['party'],
                'votes': vote_count,
                'percentage': round(percentage, 1)
            })
        
        # Sort by votes
        results_data.sort(key=lambda x: x['votes'], reverse=True)
        
        return render_template('results.html',
                             results=results_data,
                             total_votes=total_votes,
                             blockchain_valid=data.get('is_valid', False))
    except:
        flash('Could not fetch results from blockchain', 'danger')
        return redirect(url_for('home'))

@app.route('/verify')
@login_required
def verify():
    """Verify vote was recorded"""
    user_email = session.get('user_email')
    has_voted = check_if_voted(user_email)
    
    return render_template('verify.html', has_voted=has_voted)

if __name__ == '__main__':
    print("Starting Web Application on http://localhost:5000")
    print("Make sure blockchain node is running on http://localhost:5001")
    app.run(host='0.0.0.0', port=5000, debug=True)