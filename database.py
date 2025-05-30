from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()

def init_db():
    """Initialize database and create tables with sample data"""
    from models import Job
    
    # Create all tables
    db.create_all()
    
    # Add sample data if database is empty
    if Job.query.count() == 0:
        add_sample_data()

def add_sample_data():
    """Add sample job data to the database"""
    from models import Job
    
    sample_jobs = [
        {
            'title': 'Senior Software Engineer',
            'company': 'TechCorp Inc.',
            'location': 'San Francisco, CA',
            'description': 'Looking for an experienced software engineer to join our team.',
            'salary': '$120,000 - $160,000',
            'job_type': 'Full-time',
            'experience_level': 'Senior',
            'application_url': 'https://example.com/apply/1'
        },
        {
            'title': 'Data Scientist',
            'company': 'DataFlow Solutions',
            'location': 'New York, NY',
            'description': 'Seeking a data scientist with machine learning experience.',
            'salary': '$100,000 - $140,000',
            'job_type': 'Full-time',
            'experience_level': 'Mid',
            'application_url': 'https://example.com/apply/2'
        },
        {
            'title': 'Frontend Developer',
            'company': 'WebDesign Pro',
            'location': 'Remote',
            'description': 'React and JavaScript developer needed for exciting projects.',
            'salary': '$80,000 - $110,000',
            'job_type': 'Contract',
            'experience_level': 'Mid',
            'application_url': 'https://example.com/apply/3'
        },
        {
            'title': 'DevOps Engineer',
            'company': 'CloudTech Systems',
            'location': 'Seattle, WA',
            'description': 'DevOps engineer needed for AWS infrastructure management.',
            'salary': '$100,000 - $140,000',
            'job_type': 'Full-time',
            'experience_level': 'Senior',
            'application_url': 'https://example.com/jobs/devops'
        },
        {
            'title': 'Python Developer',
            'company': 'DataCorp Solutions',
            'location': 'Austin, TX',
            'description': 'Looking for a Python developer with experience in Django and Flask.',
            'salary': '$85,000 - $120,000',
            'job_type': 'Full-time',
            'experience_level': 'Senior',
            'application_url': 'https://example.com/jobs/python'
        }
    ]
    
    for job_data in sample_jobs:
        job = Job(**job_data)
        db.session.add(job)
    
    db.session.commit()
    print("Sample data added to database!")