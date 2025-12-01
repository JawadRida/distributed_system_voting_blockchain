from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_cors import CORS
import hashlib
import json
import time
import requests
import secrets
from functools import wraps
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
CORS(app)

# Configuration
BLOCKCHAIN_NODE_URL = "http://localhost:5001"

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"

# Election settings (stored in memory, can be moved to file/database)
election_settings = {
    "is_active": True,
    "start_time": datetime.now(),
    "end_time": datetime.now() + timedelta(days=7),  # 7 days by default
    "title": "General Election 2024",
    "description": "Vote for your preferred candidate"
}

# Candidates database (in memory, can be moved to file/database)
candidates_db = [
    {
        "id": "candidate_a",
        "name": "Candidate A",
        "party": "Party Alpha",
        "description": "Focus on education and healthcare",
        "image_url": "https://via.placeholder.com/150"
    },
    {
        "id": "candidate_b",
        "name": "Candidate B",
        "party": "Party Beta",
        "description": "Focus on economy and jobs",
        "image_url": "https://via.placeholder.com/150"
    },
    {
        "id": "candidate_c",
        "name": "Candidate C",
        "party": "Party Gamma",
        "description": "Focus on environment and technology",
        "image_url": "https://via.placeholder.com/150"
    }
]

# Simple in-memory user database (in production, use a real database)
users_db = {
    "admin@vote.com": {
        "password": hashlib.sha256("admin123".encode()).hexdigest(),
        "name": "Admin User"
    }
}

# Helper functions for data persistence
def save_candidates():
    """Save candidates to file"""
    with open('candidates.json', 'w') as f:
        json.dump(candidates_db, f, indent=2)

def load_candidates():
    """Load candidates from file"""
    global candidates_db
    try:
        with open('candidates.json', 'r') as f:
            candidates_db = json.load(f)
    except FileNotFoundError:
        save_candidates()  # Create file with default candidates

def save_election_settings():
    """Save election settings to file"""
    settings_copy = election_settings.copy()
    settings_copy['start_time'] = settings_copy['start_time'].isoformat()
    settings_copy['end_time'] = settings_copy['end_time'].isoformat()
    with open('election_settings.json', 'w') as f:
        json.dump(settings_copy, f, indent=2)

def load_election_settings():
    """Load election settings from file"""
    global election_settings
    try:
        with open('election_settings.json', 'r') as f:
            settings = json.load(f)
            settings['start_time'] = datetime.fromisoformat(settings['start_time'])
            settings['end_time'] = datetime.fromisoformat(settings['end_time'])
            election_settings = settings
    except FileNotFoundError:
        save_election_settings()

# Load data on startup
load_candidates()
load_election_settings()

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

def is_election_active():
    """Check if election is currently active"""
    now = datetime.now()
    return (election_settings['is_active'] and 
            election_settings['start_time'] <= now <= election_settings['end_time'])

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'is_admin' not in session or not session['is_admin']:
            flash('Admin access required', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# USER ROUTES
# ============================================================================

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
    
    # Check if election is active
    if not is_election_active():
        return render_template('election_closed.html', 
                             settings=election_settings)
    
    return render_template('home.html', 
                         candidates=candidates_db,
                         has_voted=has_voted,
                         user_name=session.get('user_name'))

@app.route('/vote', methods=['POST'])
@login_required
def vote():
    """Submit vote"""
    # Check if election is active
    if not is_election_active():
        return jsonify({
            'success': False,
            'message': 'Voting is currently closed'
        }), 400
    
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
    for candidate in candidates_db:
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
        
        for candidate in candidates_db:
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

# ============================================================================
# ADMIN ROUTES
# ============================================================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['is_admin'] = True
            session['admin_username'] = username
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials', 'danger')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('is_admin', None)
    session.pop('admin_username', None)
    flash('Admin logged out', 'info')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    # Get vote statistics
    try:
        response = requests.get(f"{BLOCKCHAIN_NODE_URL}/results", timeout=5)
        vote_data = response.json()
        total_votes = sum(vote_data['results'].values())
    except:
        total_votes = 0
        vote_data = {'results': {}}
    
    return render_template('admin_dashboard.html',
                         candidates=candidates_db,
                         election_settings=election_settings,
                         total_votes=total_votes,
                         vote_data=vote_data,
                         is_active=is_election_active())

@app.route('/admin/candidates')
@admin_required
def admin_candidates():
    """Manage candidates"""
    return render_template('admin_candidates.html', candidates=candidates_db)

@app.route('/admin/candidates/add', methods=['GET', 'POST'])
@admin_required
def admin_add_candidate():
    """Add new candidate"""
    if request.method == 'POST':
        new_candidate = {
            "id": f"candidate_{int(time.time())}",
            "name": request.form.get('name'),
            "party": request.form.get('party'),
            "description": request.form.get('description'),
            "image_url": request.form.get('image_url', 'https://via.placeholder.com/150')
        }
        candidates_db.append(new_candidate)
        save_candidates()
        flash(f'Candidate {new_candidate["name"]} added successfully!', 'success')
        return redirect(url_for('admin_candidates'))
    
    return render_template('admin_candidate_form.html', candidate=None, action='Add')

@app.route('/admin/candidates/edit/<candidate_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_candidate(candidate_id):
    """Edit existing candidate"""
    candidate = next((c for c in candidates_db if c['id'] == candidate_id), None)
    
    if not candidate:
        flash('Candidate not found', 'danger')
        return redirect(url_for('admin_candidates'))
    
    if request.method == 'POST':
        candidate['name'] = request.form.get('name')
        candidate['party'] = request.form.get('party')
        candidate['description'] = request.form.get('description')
        candidate['image_url'] = request.form.get('image_url')
        save_candidates()
        flash(f'Candidate {candidate["name"]} updated successfully!', 'success')
        return redirect(url_for('admin_candidates'))
    
    return render_template('admin_candidate_form.html', candidate=candidate, action='Edit')

@app.route('/admin/candidates/delete/<candidate_id>', methods=['POST'])
@admin_required
def admin_delete_candidate(candidate_id):
    """Delete candidate"""
    global candidates_db
    candidates_db = [c for c in candidates_db if c['id'] != candidate_id]
    save_candidates()
    flash('Candidate deleted successfully!', 'success')
    return redirect(url_for('admin_candidates'))

@app.route('/admin/election', methods=['GET', 'POST'])
@admin_required
def admin_election_settings():
    """Manage election settings"""
    if request.method == 'POST':
        election_settings['title'] = request.form.get('title')
        election_settings['description'] = request.form.get('description')
        election_settings['is_active'] = request.form.get('is_active') == 'on'
        
        # Parse dates
        start_date = request.form.get('start_date')
        start_time = request.form.get('start_time', '00:00')
        end_date = request.form.get('end_date')
        end_time = request.form.get('end_time', '23:59')
        
        election_settings['start_time'] = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
        election_settings['end_time'] = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")
        
        save_election_settings()
        flash('Election settings updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_election.html', settings=election_settings)

@app.route('/admin/election/end', methods=['POST'])
@admin_required
def admin_end_election():
    """End election immediately"""
    election_settings['is_active'] = False
    election_settings['end_time'] = datetime.now()
    save_election_settings()
    flash('Election ended successfully!', 'warning')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/election/start', methods=['POST'])
@admin_required
def admin_start_election():
    """Start election immediately"""
    election_settings['is_active'] = True
    election_settings['start_time'] = datetime.now()
    save_election_settings()
    flash('Election started successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == '__main__':
    print("Starting Web Application on http://localhost:5000")
    print("Admin Panel: http://localhost:5000/admin/login")
    print("Admin Credentials - Username: admin, Password: admin")
    print("Make sure blockchain node is running on http://localhost:5001")
    app.run(host='0.0.0.0', port=5000, debug=True)