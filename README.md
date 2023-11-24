# Job Tracker Application

## Description
The Job Tracker is a Flask-based web application designed to track job applications and their statuses. It allows users to add, edit, and view job application data.

## Features
- Add new job applications.
- Edit existing job applications.
- View all job applications in a tabulated format.
- Track job board metrics.

## Installation

### Prerequisites
- Python 3
- Flask
- Flask-SQLAlchemy
- MySQL

### Setup
1. **Clone the Repository**: `git clone https://github.com/am3y/job-tracker.git`
2. **Navigate to the Project Directory**: `cd job-tracker`

### Configuration
1. **Database Setup**:
   - Create a MySQL database for the application.
   - Update the `db_config.json` file with your MySQL configuration.

2. **Environment Setup**:
   - Install required packages: `pip install -r requirements.txt`

### Running the Application
**Start the Flask Server**:
   - Run `python3 job-tracker.py`
   - Access the application at `http://localhost:8080`

## Usage
- **Home Page**: Add new job applications.
- **Data Page**: View/Edit all job applications.
- **Job Board Metrics Page**: View metrics related to different job boards.

#### Note
    To make changes or add any job board, you can edit the `boards.json` file.