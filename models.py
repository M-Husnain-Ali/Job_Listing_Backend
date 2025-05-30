from datetime import datetime
from database import db

class Job(db.Model):
    """Job model for storing job listings"""
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    salary = db.Column(db.String(100), nullable=True)
    job_type = db.Column(db.String(50), nullable=True)
    experience_level = db.Column(db.String(50), nullable=True)
    posted_date = db.Column(db.DateTime, default=datetime.utcnow)
    application_url = db.Column(db.String(500), nullable=True)
    scraped = db.Column(db.Boolean, default=False)

    def to_dict(self):
        """Convert job object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'description': self.description,
            'salary': self.salary,
            'job_type': self.job_type,
            'experience_level': self.experience_level,
            'posted_date': self.posted_date.isoformat() if self.posted_date else None,
            'application_url': self.application_url,
            'scraped': self.scraped
        }
    
    def __repr__(self):
        return f'<Job {self.title} at {self.company}>'