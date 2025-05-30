import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome driver with enhanced anti-detection options"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless=new")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-javascript")
        chrome_options.add_argument("--window-size=1920,1080")
        
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.driver.implicitly_wait(10)
            logger.info("Chrome driver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            raise
    
    def human_like_delay(self, min_delay=1, max_delay=3):
        """Add human-like random delays"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def scroll_page(self):
        """Simulate human-like scrolling"""
        try:
            # Get page height
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Scroll down in chunks
            for i in range(3):
                # Scroll down
                self.driver.execute_script(f"window.scrollTo(0, {(i + 1) * (last_height // 4)});")
                self.human_like_delay(0.5, 1.5)
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            self.human_like_delay(1, 2)
            
        except Exception as e:
            logger.warning(f"Error during scrolling: {e}")
    
    def scrape_indeed_jobs(self, search_term="software engineer", location="", max_pages=2):
        """Scrape jobs from Indeed with updated selectors and better error handling"""
        jobs = []
        
        try:
            base_url = "https://www.indeed.com/jobs"
            search_encoded = search_term.replace(' ', '+')
            location_encoded = location.replace(' ', '+') if location else ""
            
            for page in range(max_pages):
                start = page * 10
                url = f"{base_url}?q={search_encoded}&l={location_encoded}&start={start}"
                
                logger.info(f"Scraping Indeed page {page + 1}: {url}")
                
                try:
                    self.driver.get(url)
                    self.human_like_delay(3, 5)
                    
                    # Scroll to load content
                    self.scroll_page()
                    
                    # Wait for job cards with multiple possible selectors
                    job_cards = None
                    selectors_to_try = [
                        '[data-jk]',
                        '.job_seen_beacon',
                        '.jobsearch-SerpJobCard',
                        '.slider_container .slider_item',
                        '[data-testid="job-card"]'
                    ]
                    
                    for selector in selectors_to_try:
                        try:
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                            )
                            job_cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            if job_cards:
                                logger.info(f"Found {len(job_cards)} job cards using selector: {selector}")
                                break
                        except TimeoutException:
                            continue
                    
                    if not job_cards:
                        logger.warning(f"No job cards found on page {page + 1}")
                        continue
                    
                    # Extract job data
                    for i, card in enumerate(job_cards[:15]):  # Limit to avoid being blocked
                        try:
                            job_data = self.extract_indeed_job_data(card)
                            if job_data and job_data.get('title'):
                                jobs.append(job_data)
                                logger.info(f"Extracted job {i+1}: {job_data['title']}")
                            
                            # Small delay between extractions
                            if i % 5 == 0:
                                self.human_like_delay(0.5, 1)
                                
                        except Exception as e:
                            logger.warning(f"Error extracting job {i+1}: {e}")
                            continue
                    
                    # Longer delay between pages
                    if page < max_pages - 1:
                        self.human_like_delay(5, 8)
                        
                except Exception as e:
                    logger.error(f"Error on Indeed page {page + 1}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error scraping Indeed: {e}")
        
        return jobs
    
    def extract_indeed_job_data(self, job_card):
        """Extract job data from Indeed job card with multiple selector fallbacks"""
        try:
            job_data = {}
            
            # Job title - try multiple selectors
            title_selectors = [
                'h2 a span[title]',
                '.jobTitle a span[title]',
                'h2 span[title]',
                '.jobTitle span',
                'h2 a',
                '.jobTitle a'
            ]
            
            title = None
            for selector in title_selectors:
                try:
                    element = job_card.find_element(By.CSS_SELECTOR, selector)
                    title = element.get_attribute("title") or element.text
                    if title and title.strip():
                        break
                except NoSuchElementException:
                    continue
            
            if not title or not title.strip():
                return None
            
            job_data['title'] = title.strip()
            
            # Company name
            company_selectors = [
                '[data-testid="company-name"]',
                '.companyName',
                'span.companyName',
                'a[data-testid="company-name"]'
            ]
            
            company = "Company Not Listed"
            for selector in company_selectors:
                try:
                    element = job_card.find_element(By.CSS_SELECTOR, selector)
                    company = element.text.strip()
                    if company:
                        break
                except NoSuchElementException:
                    continue
            
            job_data['company'] = company
            
            # Location
            location_selectors = [
                '[data-testid="job-location"]',
                '.companyLocation',
                'div[data-testid="job-location"]'
            ]
            
            location = "Location Not Specified"
            for selector in location_selectors:
                try:
                    element = job_card.find_element(By.CSS_SELECTOR, selector)
                    location = element.text.strip()
                    if location:
                        break
                except NoSuchElementException:
                    continue
            
            job_data['location'] = location
            
            # Salary
            salary_selectors = [
                '.salary-snippet',
                '[data-testid="attribute_snippet_testid"]',
                '.salaryText',
                '.estimated-salary'
            ]
            
            salary = ""
            for selector in salary_selectors:
                try:
                    element = job_card.find_element(By.CSS_SELECTOR, selector)
                    salary_text = element.text.strip()
                    if salary_text and ('$' in salary_text or 'hour' in salary_text.lower()):
                        salary = salary_text
                        break
                except NoSuchElementException:
                    continue
            
            job_data['salary'] = salary
            
            # Job description/snippet
            desc_selectors = [
                '.summary',
                '[data-testid="job-snippet"]',
                '.job-snippet'
            ]
            
            description = ""
            for selector in desc_selectors:
                try:
                    element = job_card.find_element(By.CSS_SELECTOR, selector)
                    description = element.text.strip()
                    if description:
                        break
                except NoSuchElementException:
                    continue
            
            job_data['description'] = description
            
            # Application URL
            url = ""
            try:
                link_element = job_card.find_element(By.CSS_SELECTOR, 'h2 a, .jobTitle a')
                href = link_element.get_attribute("href")
                if href and href.startswith('http'):
                    url = href
            except NoSuchElementException:
                pass
            
            job_data['application_url'] = url
            
            # Default values
            job_data['job_type'] = "Full-time"
            job_data['experience_level'] = "Mid"
            
            return job_data
            
        except Exception as e:
            logger.error(f"Error extracting job data: {e}")
            return None
    
    def scrape_sample_jobs(self):
        """Generate enhanced sample job data for testing"""
        sample_jobs = [
            {
                'title': 'Senior Full Stack Developer',
                'company': 'TechStart Inc.',
                'location': 'San Francisco, CA',
                'description': 'Join our growing team as a senior full stack developer working with React, Node.js, and AWS. We offer competitive salary and great benefits.',
                'salary': '$120,000 - $160,000',
                'job_type': 'Full-time',
                'experience_level': 'Senior',
                'application_url': 'https://example.com/jobs/fullstack-senior'
            },
            {
                'title': 'Python Developer',
                'company': 'DataCorp Solutions',
                'location': 'Austin, TX',
                'description': 'Looking for a Python developer with experience in Django, Flask, and data analysis. Remote work available.',
                'salary': '$95,000 - $130,000',
                'job_type': 'Full-time',
                'experience_level': 'Mid',
                'application_url': 'https://example.com/jobs/python-dev'
            },
            {
                'title': 'DevOps Engineer',
                'company': 'CloudTech Systems',
                'location': 'Seattle, WA',
                'description': 'DevOps engineer needed for AWS infrastructure management, CI/CD pipelines, and container orchestration.',
                'salary': '$110,000 - $150,000',
                'job_type': 'Full-time',
                'experience_level': 'Senior',
                'application_url': 'https://example.com/jobs/devops-engineer'
            },
            {
                'title': 'Frontend React Developer',
                'company': 'WebFlow Agency',
                'location': 'Remote',
                'description': 'Remote React developer position with flexible hours. Experience with TypeScript and modern CSS frameworks required.',
                'salary': '$80,000 - $105,000',
                'job_type': 'Full-time',
                'experience_level': 'Mid',
                'application_url': 'https://example.com/jobs/react-frontend'
            },
            {
                'title': 'Data Analyst',
                'company': 'Analytics Pro',
                'location': 'Chicago, IL',
                'description': 'Data analyst role focusing on business intelligence, reporting, and data visualization using Python and SQL.',
                'salary': '$70,000 - $90,000',
                'job_type': 'Full-time',
                'experience_level': 'Entry',
                'application_url': 'https://example.com/jobs/data-analyst'
            },
            {
                'title': 'Machine Learning Engineer',
                'company': 'AI Innovations',
                'location': 'Boston, MA',
                'description': 'ML engineer to work on cutting-edge AI projects. Experience with TensorFlow, PyTorch, and cloud platforms required.',
                'salary': '$130,000 - $170,000',
                'job_type': 'Full-time',
                'experience_level': 'Senior',
                'application_url': 'https://example.com/jobs/ml-engineer'
            },
            {
                'title': 'Junior Software Developer',
                'company': 'StartupHub',
                'location': 'Denver, CO',
                'description': 'Entry-level position for new graduates. Training provided in modern web technologies and agile development.',
                'salary': '$60,000 - $75,000',
                'job_type': 'Full-time',
                'experience_level': 'Entry',
                'application_url': 'https://example.com/jobs/junior-dev'
            },
            {
                'title': 'Mobile App Developer',
                'company': 'AppMasters',
                'location': 'Los Angeles, CA',
                'description': 'iOS and Android developer needed for consumer-facing mobile applications. React Native or Flutter experience preferred.',
                'salary': '$100,000 - $135,000',
                'job_type': 'Full-time',
                'experience_level': 'Mid',
                'application_url': 'https://example.com/jobs/mobile-dev'
            }
        ]
        
        logger.info(f"Generated {len(sample_jobs)} sample jobs")
        return sample_jobs
    
    def scrape_jobs(self, search_term="software engineer", location="", use_sample=False, max_pages=2):
        """Main method to scrape jobs with improved error handling"""
        all_jobs = []
        
        if use_sample:
            return self.scrape_sample_jobs()
        
        try:
            logger.info("Starting job scraping...")
            logger.info(f"Search term: {search_term}, Location: {location}")
            
            # Try to scrape from Indeed
            logger.info("Attempting to scrape from Indeed...")
            indeed_jobs = self.scrape_indeed_jobs(search_term, location, max_pages)
            
            if indeed_jobs:
                all_jobs.extend(indeed_jobs)
                logger.info(f"Successfully scraped {len(indeed_jobs)} jobs from Indeed")
            else:
                logger.warning("No jobs found from Indeed, using sample data")
                all_jobs = self.scrape_sample_jobs()
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            logger.info("Falling back to sample data due to scraping error")
            all_jobs = self.scrape_sample_jobs()
        
        # Remove duplicates and clean data
        unique_jobs = self.clean_and_deduplicate_jobs(all_jobs)
        
        logger.info(f"Total unique jobs processed: {len(unique_jobs)}")
        return unique_jobs
    
    def clean_and_deduplicate_jobs(self, jobs):
        """Clean job data and remove duplicates"""
        unique_jobs = []
        seen = set()
        
        for job in jobs:
            # Clean and validate job data
            if not job.get('title') or not job.get('company'):
                continue
            
            # Create unique key
            key = (
                job['title'].lower().strip(),
                job['company'].lower().strip(),
                job.get('location', '').lower().strip()
            )
            
            if key not in seen:
                seen.add(key)
                
                # Clean the job data
                cleaned_job = {
                    'title': job['title'].strip(),
                    'company': job['company'].strip(),
                    'location': job.get('location', 'Not Specified').strip(),
                    'description': job.get('description', '').strip(),
                    'salary': job.get('salary', '').strip(),
                    'job_type': job.get('job_type', 'Full-time').strip(),
                    'experience_level': job.get('experience_level', 'Mid').strip(),
                    'application_url': job.get('application_url', '').strip()
                }
                
                unique_jobs.append(cleaned_job)
        
        return unique_jobs
    
    def close(self):
        """Close the browser driver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser driver closed successfully")
            except Exception as e:
                logger.warning(f"Error closing driver: {e}")
    
    def __del__(self):
        """Destructor to ensure driver is closed"""
        self.close()

# Test the scraper
if __name__ == "__main__":
    scraper = JobScraper(headless=True)  # Set to False for debugging
    
    try:
        # Test with sample data first
        print("Testing with sample data...")
        jobs = scraper.scrape_jobs(use_sample=True)
        print(f"Sample data test: {len(jobs)} jobs")
        
        # Test actual scraping
        print("\nTesting actual scraping...")
        jobs = scraper.scrape_jobs("python developer", "california", use_sample=False, max_pages=1)
        
        print(f"\nScraped {len(jobs)} jobs:")
        for i, job in enumerate(jobs[:5], 1):  # Show first 5 jobs
            print(f"\n{i}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   Salary: {job['salary']}")
            print(f"   Type: {job['job_type']}")
            print(f"   Level: {job['experience_level']}")
            if job['application_url']:
                print(f"   URL: {job['application_url'][:50]}...")
    
    finally:
        scraper.close()