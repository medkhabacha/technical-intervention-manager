from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps

app = Flask(__name__)
app.secret_key = 'super_secret_key'  # Change this in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///interventions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Database Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'admin' or 'technician'

class Intervention(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='To Do') # To Do, In Progress, Done
    technician_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    technician = db.relationship('User', backref='interventions')

# --- Decorators for Access Control ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash("Admin access required.", "error")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- HTML & CSS Layout Parts ---
HEADER = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Intervention Manager</title>
    <style>
        :root {
            --primary-color: #2563eb;
            --primary-hover: #1d4ed8;
            --bg-color: #f8fafc;
            --text-color: #1e293b;
            --card-bg: #ffffff;
            --border-color: #e2e8f0;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--border-color);
        }
        .card {
            background: var(--card-bg);
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        h2, h3 { margin-top: 0; }
        
        /* Form Styling */
        form.inline-form { display: inline-flex; gap: 10px; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="text"], textarea, select {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            box-sizing: border-box;
            font-family: inherit;
        }
        textarea { resize: vertical; min-height: 80px; }
        button, .btn {
            background-color: var(--primary-color);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            text-decoration: none;
            font-size: 14px;
            transition: background-color 0.2s;
        }
        button:hover, .btn:hover { background-color: var(--primary-hover); }
        .btn-danger { background-color: #ef4444; }
        .btn-danger:hover { background-color: #dc2626; }
        
        /* Table Styling */
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            background: var(--card-bg);
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }
        th { background-color: #f1f5f9; font-weight: 600; }
        tr:last-child td { border-bottom: none; }
        
        /* Badges */
        .status-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: bold;
        }
        .status-todo { background: #fef3c7; color: #92400e; }
        .status-progress { background: #dbeafe; color: #1e40af; }
        .status-done { background: #dcfce3; color: #166534; }
        
        /* Alerts */
        .alert {
            padding: 10px 15px;
            background-color: #fee2e2;
            color: #991b1b;
            border-radius: 4px;
            margin-bottom: 15px;
            list-style-type: none;
        }
    </style>
</head>
<body>
    <div class="container">
'''

FOOTER = '''
    </div>
</body>
</html>
'''

# --- Routes ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('dashboard'))
        else:
            flash("User not found.")
    
    return render_template_string(HEADER + '''
        <div class="card" style="max-width: 400px; margin: 40px auto;">
            <h2>Login</h2>
            {% with messages = get_flashed_messages() %}
              {% if messages %}<ul class="alert">{% for message in messages %}<li>{{ message }}</li>{% endfor %}</ul>{% endif %}
            {% endwith %}
            <form method="post">
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" name="username" required>
                </div>
                <button type="submit" style="width: 100%;">Login</button>
            </form>
            <p style="font-size: 14px; color: #64748b; margin-top: 15px;"><i>Hint: Use 'admin1', 'tech1', or 'tech2'</i></p>
        </div>
    ''' + FOOTER)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    if session['role'] == 'admin':
        interventions = Intervention.query.all()
        technicians = User.query.filter_by(role='technician').all()
        return render_template_string(HEADER + '''
            <div class="header">
                <h2>Admin Dashboard</h2>
                <a href="{{ url_for('logout') }}" class="btn btn-danger">Logout</a>
            </div>
            
            <div class="card">
                <h3>Create New Intervention</h3>
                <form action="{{ url_for('create_intervention') }}" method="post">
                    <div class="form-group">
                        <label>Title</label>
                        <input type="text" name="title" required>
                    </div>
                    <div class="form-group">
                        <label>Description</label>
                        <textarea name="description" required></textarea>
                    </div>
                    <div class="form-group">
                        <label>Assign to Technician</label>
                        <select name="technician_id">
                            <option value="">-- Unassigned --</option>
                            {% for tech in technicians %}
                                <option value="{{ tech.id }}">{{ tech.username }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <button type="submit">Create Task</button>
                </form>
            </div>
            
            <h3>All Interventions</h3>
            <table>
                <tr>
                    <th>ID</th>
                    <th>Title</th>
                    <th>Status</th>
                    <th>Assigned To</th>
                </tr>
                {% for inv in interventions %}
                <tr>
                    <td>#{{ inv.id }}</td>
                    <td><strong>{{ inv.title }}</strong><br><small style="color: #64748b;">{{ inv.description }}</small></td>
                    <td>
                        <span class="status-badge 
                            {% if inv.status == 'To Do' %}status-todo
                            {% elif inv.status == 'In Progress' %}status-progress
                            {% else %}status-done{% endif %}">
                            {{ inv.status }}
                        </span>
                    </td>
                    <td>{{ inv.technician.username if inv.technician else 'Unassigned' }}</td>
                </tr>
                {% endfor %}
            </table>
        ''' + FOOTER, interventions=interventions, technicians=technicians)
    else:
        # Technician Dashboard
        interventions = Intervention.query.filter_by(technician_id=session['user_id']).all()
        return render_template_string(HEADER + '''
            <div class="header">
                <h2>Technician Dashboard ({{ session['username'] }})</h2>
                <a href="{{ url_for('logout') }}" class="btn btn-danger">Logout</a>
            </div>
            
            <h3>My Assigned Interventions</h3>
            <table>
                <tr>
                    <th>ID</th>
                    <th>Task Details</th>
                    <th>Status</th>
                    <th>Action</th>
                </tr>
                {% for inv in interventions %}
                <tr>
                    <td>#{{ inv.id }}</td>
                    <td><strong>{{ inv.title }}</strong><br><small style="color: #64748b;">{{ inv.description }}</small></td>
                    <td>
                        <span class="status-badge 
                            {% if inv.status == 'To Do' %}status-todo
                            {% elif inv.status == 'In Progress' %}status-progress
                            {% else %}status-done{% endif %}">
                            {{ inv.status }}
                        </span>
                    </td>
                    <td>
                        <form action="{{ url_for('update_status', inv_id=inv.id) }}" method="post" class="inline-form">
                            <select name="status" style="width: auto;">
                                <option value="To Do" {% if inv.status == 'To Do' %}selected{% endif %}>To Do</option>
                                <option value="In Progress" {% if inv.status == 'In Progress' %}selected{% endif %}>In Progress</option>
                                <option value="Done" {% if inv.status == 'Done' %}selected{% endif %}>Done</option>
                            </select>
                            <button type="submit">Update</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </table>
        ''' + FOOTER, interventions=interventions)

@app.route('/create_intervention', methods=['POST'])
@login_required
@admin_required
def create_intervention():
    title = request.form.get('title')
    description = request.form.get('description')
    tech_id = request.form.get('technician_id')
    
    new_inv = Intervention(
        title=title, 
        description=description, 
        technician_id=tech_id if tech_id else None
    )
    db.session.add(new_inv)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/update_status/<int:inv_id>', methods=['POST'])
@login_required
def update_status(inv_id):
    intervention = Intervention.query.get_or_404(inv_id)
    
    if session['role'] == 'technician' and intervention.technician_id != session['user_id']:
        flash("Unauthorized.")
        return redirect(url_for('dashboard'))
        
    new_status = request.form.get('status')
    if new_status in ['To Do', 'In Progress', 'Done']:
        intervention.status = new_status
        db.session.commit()
        
    return redirect(url_for('dashboard'))

def setup_database():
    with app.app_context():
        db.create_all()
        if not User.query.first():
            admin = User(username='admin1', role='admin')
            tech1 = User(username='tech1', role='technician')
            tech2 = User(username='tech2', role='technician')
            db.session.add_all([admin, tech1, tech2])
            db.session.commit()

if __name__ == '__main__':
    setup_database()
    app.run(debug=True)