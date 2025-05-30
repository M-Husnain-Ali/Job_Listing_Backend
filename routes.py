from flask import Blueprint, request, jsonify
from datetime import datetime
from database import db
from models import Job

api_bp = Blueprint('api', __name__)

@api_bp.route('/jobs', methods=['GET'])
def get_jobs():
    """Fetch all job listings with optional filtering and sorting"""
    
    location_filter = request.args.get('location', '')
    company_filter = request.args.get('company', '')
    job_type_filter = request.args.get('job_type', '')
    experience_filter = request.args.get('experience', '')
    sort_by = request.args.get('sort_by', 'posted_date')
    sort_order = request.args.get('sort_order', 'desc')
    query = Job.query
    
    if location_filter:
        query = query.filter(Job.location.ilike(f'%{location_filter}%'))
    if company_filter:
        query = query.filter(Job.company.ilike(f'%{company_filter}%'))
    if job_type_filter:
        query = query.filter(Job.job_type.ilike(f'%{job_type_filter}%'))
    if experience_filter:
        query = query.filter(Job.experience_level.ilike(f'%{experience_filter}%'))
    
    if sort_by == 'title':
        order_col = Job.title
    elif sort_by == 'company':
        order_col = Job.company
    elif sort_by == 'location':
        order_col = Job.location
    else:
        order_col = Job.posted_date
    
    if sort_order == 'asc':
        query = query.order_by(order_col.asc())
    else:
        query = query.order_by(order_col.desc())
    
    jobs = query.all()
    return jsonify([job.to_dict() for job in jobs])

@api_bp.route('/jobs', methods=['POST'])
def add_job():
    """Add a new job listing"""
    try:
        data = request.get_json()
        
        new_job = Job(
            title=data.get('title'),
            company=data.get('company'),
            location=data.get('location'),
            description=data.get('description', ''),
            salary=data.get('salary', ''),
            job_type=data.get('job_type', ''),
            experience_level=data.get('experience_level', ''),
            application_url=data.get('application_url', ''),
            scraped=data.get('scraped', False)
        )
        
        db.session.add(new_job)
        db.session.commit()
        
        return jsonify({
            'message': 'Job added successfully',
            'job': new_job.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/jobs/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Delete a specific job listing"""
    try:
        job = Job.query.get_or_404(job_id)
        db.session.delete(job)
        db.session.commit()
        
        return jsonify({'message': 'Job deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/jobs/<int:job_id>', methods=['PUT'])
def update_job(job_id):
    """Update a specific job listing"""
    try:
        job = Job.query.get_or_404(job_id)
        data = request.get_json()
        
        job.title = data.get('title', job.title)
        job.company = data.get('company', job.company)
        job.location = data.get('location', job.location)
        job.description = data.get('description', job.description)
        job.salary = data.get('salary', job.salary)
        job.job_type = data.get('job_type', job.job_type)
        job.experience_level = data.get('experience_level', job.experience_level)
        job.application_url = data.get('application_url', job.application_url)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Job updated successfully',
            'job': job.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get statistics about job listings"""
    total_jobs = Job.query.count()
    scraped_jobs = Job.query.filter_by(scraped=True).count()
    manual_jobs = total_jobs - scraped_jobs
    
    companies = db.session.query(Job.company, db.func.count(Job.id).label('count'))\
                         .group_by(Job.company)\
                         .order_by(db.func.count(Job.id).desc())\
                         .limit(5).all()
    
    locations = db.session.query(Job.location, db.func.count(Job.id).label('count'))\
                         .group_by(Job.location)\
                         .order_by(db.func.count(Job.id).desc())\
                         .limit(5).all()
    
    return jsonify({
        'total_jobs': total_jobs,
        'scraped_jobs': scraped_jobs,
        'manual_jobs': manual_jobs,
        'top_companies': [{'name': c[0], 'count': c[1]} for c in companies],
        'top_locations': [{'name': l[0], 'count': l[1]} for l in locations]
    })

@api_bp.route('/scrape', methods=['POST'])
def trigger_scraping():
    """Trigger the Selenium scraping bot"""
    try:
        from selenium_scraper import JobScraper
        
        scraper = JobScraper()
        scraped_jobs = scraper.scrape_jobs()
        
        added_count = 0
        for job_data in scraped_jobs:
            existing_job = Job.query.filter_by(
                title=job_data['title'],
                company=job_data['company']
            ).first()
            
            if not existing_job:
                new_job = Job(
                    title=job_data['title'],
                    company=job_data['company'],
                    location=job_data['location'],
                    description=job_data.get('description', ''),
                    salary=job_data.get('salary', ''),
                    job_type=job_data.get('job_type', ''),
                    experience_level=job_data.get('experience_level', ''),
                    application_url=job_data.get('application_url', ''),
                    scraped=True
                )
                db.session.add(new_job)
                added_count += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'Scraping completed. Added {added_count} new jobs.',
            'total_scraped': len(scraped_jobs),
            'added': added_count
        }), 200
        
    except ImportError:
        return jsonify({'error': 'Selenium scraper not available'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})