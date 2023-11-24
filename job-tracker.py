from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import json
from datetime import datetime
from sqlalchemy import func, case, distinct


app = Flask(__name__)

# Function to load job boards from a JSON file
def load_job_boards(filename):
    try:
        with open(filename, 'r') as file:
            job_boards = json.load(file)
            return job_boards
    except FileNotFoundError:
        return [{"name": "No job boards found", "link": "#"}]

# Load job boards
job_boards = load_job_boards("boards.json")

# Load database configuration from a JSON file
with open('db_config.json') as config_file:
    config_data = json.load(config_file)

# Configure the SQLAlchemy connection string
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{config_data['MYSQL_USER']}:{config_data['MYSQL_PASSWORD']}@"
    f"{config_data['MYSQL_HOST']}:{config_data['MYSQL_PORT']}/{config_data['MYSQL_DB']}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Define the Job model
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.utcnow)
    time = db.Column(db.Time, default=datetime.utcnow)
    company_name = db.Column(db.String(100), nullable=False)
    job_portal = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    job_post_date = db.Column(db.Date, nullable=False)
    number_applicants = db.Column(db.Integer, nullable=False)
    link = db.Column(db.String(255), nullable=False, unique=True)
    applied_date = db.Column(db.Date)
    rejected_date = db.Column(db.Date)
    job_expired_date = db.Column(db.Date)
    interview = db.Column(db.String(50))

# Create the database tables if they don't exist already
with app.app_context():
    db.create_all()

# Utility function to get job board metrics
def get_job_board_metrics():
    return db.session.query(
        Job.job_portal.label('job_board'),
        func.count(Job.id).label('total_added'),
        func.sum(case((Job.applied_date != None, 1), else_=0)).label('total_applied')  # Further fixed case statement
    ).group_by(Job.job_portal).all()


@app.route("/", methods=["GET", "POST"])
def form():
    message = ""
    if request.method == "POST":
        # Extract form data
        job_portal = request.form.get("jobPortal")
        company_name = request.form.get("companyName")
        position = request.form.get("position")
        job_post_date = request.form.get("jobPostDate")
        number_applicants = request.form.get("numberApplicants")
        link = request.form.get("link")

        # Check for duplicate link
        duplicate_entry = Job.query.filter_by(link=link).first()
        if duplicate_entry:
            message = f"This job was already saved on {duplicate_entry.date} at {duplicate_entry.time}"
        else:
            # If no duplicate, add new job entry
            new_job = Job(
                date=datetime.utcnow().date(),
                time=datetime.utcnow().time(),
                company_name=company_name,
                job_portal=job_portal,
                position=position,
                job_post_date=datetime.strptime(job_post_date, '%Y-%m-%d').date() if job_post_date else None,
                number_applicants=number_applicants,
                link=link
            )
            db.session.add(new_job)
            db.session.commit()
            message = "Form submitted successfully!"

    # Fetch job board metrics and convert them into a list of dictionaries
    job_board_metrics_tuples = db.session.query(
        Job.job_portal.label('job_board'),
        func.count(Job.id).label('total_added'),
        func.count(Job.applied_date).label('total_applied')
    ).group_by(Job.job_portal).all()

    job_board_metrics = [
        {'job_board': metric[0], 'total_added': metric[1], 'total_applied': metric[2]}
        for metric in job_board_metrics_tuples
    ]

    # Create a dictionary that maps job board names to their links
    job_board_links = {board['name']: board['link'] for board in job_boards}

    # Add the 'link' to each metric dictionary
    for metric in job_board_metrics:
        metric['link'] = job_board_links.get(metric['job_board'], '#')

    # Pass the job board metrics to the form template, including the links
    return render_template('form.html', job_boards=job_boards, message=message, job_board_metrics=job_board_metrics)

@app.route("/data", methods=["GET"])
def show_data():
    # Order the jobs by date and time in descending order
    jobs = Job.query.order_by(Job.date.desc(), Job.time.desc()).all()
    return render_template('data.html', jobs=jobs)


@app.route("/edit/<int:job_id>", methods=["GET", "POST"])
def edit_entry(job_id):
    job = Job.query.get_or_404(job_id)
    if request.method == "POST":
        # Update job data
        job.number_applicants = request.form.get('numberApplicants', job.number_applicants)
        job.applied_date = request.form.get('appliedDate', job.applied_date) if request.form.get('appliedDate') else None
        job.rejected_date = request.form.get('rejectedDate', job.rejected_date) if request.form.get('rejectedDate') else None
        job.job_expired_date = request.form.get('jobExpiredDate', job.job_expired_date) if request.form.get('jobExpiredDate') else None
        job.interview = request.form.get('interview', job.interview)
        
        db.session.commit()
        return redirect(url_for('show_data'))

    return render_template('edit.html', job=job)

@app.route("/job_board_metrics", methods=["GET"])
def job_board_metrics():
    selected_job_board = request.args.get('job_board', default=None, type=str)
    query = db.session.query(
        Job.date.label('date'), 
        func.count(Job.id).label('total_jobs_saved'),
        func.sum(case((Job.applied_date != None, 1), else_=0)).label('total_jobs_applied')
    )
    
    if selected_job_board:
        query = query.filter_by(job_portal=selected_job_board)
    
    job_board_data = query.group_by(
        Job.date
    ).order_by(
        Job.date
    ).all()
    
    metrics_data = [
        {
            'date': job.date.strftime('%d %b %Y %A'),
            'total_jobs_saved': job.total_jobs_saved,
            'total_jobs_applied': job.total_jobs_applied
        }
        for job in job_board_data
    ]

    # Pass the job boards to the template with their names and links
    return render_template('job_board_metrics.html', metrics_data=metrics_data, job_boards=job_boards, selected_job_board=selected_job_board)




if __name__ == "__main__":
    app.run(port=8080, debug=True)