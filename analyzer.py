import pandas as pd
import json
import ast
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
from collections import Counter
import numpy as np
from datetime import datetime
import logging
import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class YCAnalyzer:
    def __init__(self, data_file="yc_companies.csv", shared_output_dir=None):
        """Initialize analyzer with company data"""
        self.data_file = data_file
        self.df = None
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Use shared output directory if provided, otherwise create new one
        if shared_output_dir:
            self.output_dir = shared_output_dir
            logger.info(f"Using shared output directory: {self.output_dir}")
        else:
            self.output_dir = f"output_{self.timestamp}"
            logger.info(f"Creating new output directory: {self.output_dir}")
            
        self.analyzer_dir = os.path.join(self.output_dir, "analyzer")
        self.data_dir = os.path.join(self.analyzer_dir, "data")
        self.html_dir = os.path.join(self.analyzer_dir, "html")
        self.charts_dir = os.path.join(self.analyzer_dir, "charts")
        self.load_data()
        
    def load_data(self):
        """Load company data from CSV or JSON file"""
        try:
            if self.data_file.endswith('.csv'):
                # Load raw CSV; parse complex columns in clean_data()
                self.df = pd.read_csv(self.data_file)
            elif self.data_file.endswith('.json'):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                self.df = pd.DataFrame(data)
            else:
                raise ValueError("Unsupported file format. Use CSV or JSON.")
                
            logger.info(f"Loaded {len(self.df)} companies from {self.data_file}")
            
        except FileNotFoundError:
            logger.error(f"Data file {self.data_file} not found. Please run the scraper first.")
            self.df = pd.DataFrame()
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            # Try alternative loading method
            try:
                if self.data_file.endswith('.csv'):
                    self.df = pd.read_csv(self.data_file, on_bad_lines='skip')
                    logger.info("Loaded CSV with basic parsing, will handle complex data in clean_data()")
            except Exception as e2:
                logger.error(f"Alternative loading also failed: {e2}")
                self.df = pd.DataFrame()
    
    def clean_data(self):
        """Clean and preprocess the data"""
        if self.df.empty:
            logger.warning("No data to clean")
            return
            
        # Helper to parse list-like strings safely
        def _parse_list(value):
            if isinstance(value, list):
                return value
            if not isinstance(value, str) or value.strip() == '' or value.strip().lower() == 'nan':
                return []
            # Try JSON first
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else []
            except Exception:
                pass
            # Try Python literal eval
            try:
                parsed = ast.literal_eval(value)
                return parsed if isinstance(parsed, list) else []
            except Exception:
                pass
            # Fallback: comma-separated
            return [item.strip() for item in value.split(',') if item.strip()]

        # Convert categories from string to list if needed
        if 'categories' in self.df.columns:
            self.df['categories'] = self.df['categories'].apply(_parse_list)
        
        # Convert founders from string to list if needed
        if 'founders' in self.df.columns:
            self.df['founders'] = self.df['founders'].apply(_parse_list)
        
        # Clean descriptions
        if 'description' in self.df.columns:
            self.df['description'] = self.df['description'].fillna('N/A')
            self.df['description_length'] = self.df['description'].str.len()
        
        # Extract batch year
        if 'batch' in self.df.columns:
            self.df['batch_year'] = self.df['batch'].str.extract(r'(\d{4})')
        
        logger.info("Data cleaning completed")
    
    def analyze_categories(self):
        """Analyze company categories/sectors"""
        if self.df.empty or 'categories' not in self.df.columns:
            logger.warning("No category data available")
            return {}
        
        # Flatten categories
        all_categories = []
        for categories in self.df['categories']:
            if isinstance(categories, list):
                all_categories.extend(categories)
        
        # Count categories
        category_counts = Counter(all_categories)
        
        # Create category analysis
        category_analysis = {
            'total_categories': len(category_counts),
            'most_common_categories': category_counts.most_common(10),
            'category_distribution': dict(category_counts)
        }
        
        logger.info(f"Found {len(category_counts)} unique categories")
        return category_analysis
    
    def analyze_descriptions(self):
        """Analyze company descriptions"""
        if self.df.empty or 'description' not in self.df.columns:
            logger.warning("No description data available")
            return {}
        
        # Description length statistics
        desc_lengths = self.df['description_length'].dropna()
        
        description_analysis = {
            'avg_description_length': desc_lengths.mean(),
            'median_description_length': desc_lengths.median(),
            'min_description_length': desc_lengths.min(),
            'max_description_length': desc_lengths.max(),
            'description_length_distribution': desc_lengths.value_counts().to_dict()
        }
        
        # Extract common keywords
        all_descriptions = ' '.join(self.df['description'].dropna().astype(str))
        words = re.findall(r'\b\w+\b', all_descriptions.lower())
        
        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their', 'mine', 'yours', 'his', 'hers', 'ours', 'theirs'}
        filtered_words = [word for word in words if word not in stop_words and len(word) > 3]
        
        word_counts = Counter(filtered_words)
        description_analysis['common_keywords'] = word_counts.most_common(20)
        
        logger.info("Description analysis completed")
        return description_analysis
    
    def analyze_founders(self):
        """Analyze founders information"""
        if self.df.empty or 'founders' not in self.df.columns:
            logger.warning("No founders data available")
            return {}
        
        # Flatten founders data
        all_founders = []
        profile_types = []
        linkedin_profiles = []
        
        for founders_list in self.df['founders']:
            # Normalize founders_list to list of dicts
            parsed_list = founders_list
            if isinstance(parsed_list, str):
                try:
                    parsed_list = json.loads(parsed_list)
                except Exception:
                    parsed_list = []
            if isinstance(parsed_list, list):
                for founder in parsed_list:
                    if isinstance(founder, dict):
                        all_founders.append(founder)
                        # Track LinkedIn profiles based on 'linkedin_url'
                        linkedin_url = founder.get('linkedin_url') or ''
                        if isinstance(linkedin_url, str) and linkedin_url.strip():
                            linkedin_profiles.append(founder)
        
        founders_analysis = {
            'total_founders': len(all_founders),
            'companies_with_founders': len([f for f in self.df['founders'] if f and len(f) > 0]),
            'profile_type_distribution': Counter(profile_types) if profile_types else {},
            'linkedin_profiles_count': len(linkedin_profiles),
            'linkedin_profiles': linkedin_profiles,
            'founders_per_company': {
                'avg': len(all_founders) / len(self.df) if len(self.df) > 0 else 0,
                'max': max([len(f) if isinstance(f, list) else 0 for f in self.df['founders']]) if 'founders' in self.df.columns else 0,
                'min': min([len(f) if isinstance(f, list) else 0 for f in self.df['founders']]) if 'founders' in self.df.columns else 0
            }
        }
        
        logger.info(f"Found {len(all_founders)} founders across {founders_analysis['companies_with_founders']} companies")
        return founders_analysis
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report"""
        if self.df.empty:
            logger.warning("No data available for analysis")
            return {}
        
        self.clean_data()
        
        report = {
            'total_companies': len(self.df),
            'batch_info': self.df['batch'].value_counts().to_dict() if 'batch' in self.df.columns else {},
            'categories': self.analyze_categories(),
            'descriptions': self.analyze_descriptions(),
            'founders': self.analyze_founders(),
            'data_quality': {
                'missing_names': self.df['name'].isna().sum() if 'name' in self.df.columns else 0,
                'missing_descriptions': self.df['description'].isna().sum() if 'description' in self.df.columns else 0,
                'missing_urls': self.df['url'].isna().sum() if 'url' in self.df.columns else 0,
                'missing_founders': len([f for f in self.df['founders'] if not f or len(f) == 0]) if 'founders' in self.df.columns else 0
            }
        }
        
        logger.info("Summary report generated")
        return report
    
    def create_visualizations(self, output_dir="charts"):
        """Create interactive visualizations - Only Category Distribution"""
        if self.df.empty:
            logger.warning("No data available for visualizations")
            return
        
        # Create unified output directory structure
        os.makedirs(self.analyzer_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.html_dir, exist_ok=True)
        os.makedirs(self.charts_dir, exist_ok=True)
        
        # Only Category Distribution
        if 'categories' in self.df.columns:
            category_analysis = self.analyze_categories()
            if category_analysis['most_common_categories']:
                categories, counts = zip(*category_analysis['most_common_categories'][:10])
                
                fig = px.bar(
                    x=categories, 
                    y=counts,
                    title="Top 10 Company Categories",
                    labels={'x': 'Category', 'y': 'Number of Companies'}
                )
                fig.write_html(f"{self.charts_dir}/category_distribution.html")
                logger.info(f"Category distribution chart saved to {self.charts_dir}/category_distribution.html")
        
        logger.info(f"Visualizations saved to {self.charts_dir}/")
    
    def export_analysis(self, filename="analysis_report.json"):
        """Export analysis results to JSON"""
        report = self.generate_summary_report()
        
        # Convert numpy types to native Python types for JSON serialization
        def convert_numpy_types(obj):
            if isinstance(obj, dict):
                return {key: convert_numpy_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            elif hasattr(obj, 'item'):  # numpy types
                return obj.item()
            else:
                return obj
        
        report = convert_numpy_types(report)
        
        # Create unified output directory structure
        os.makedirs(self.analyzer_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.html_dir, exist_ok=True)
        
        # Add timestamp to filename and save in data subfolder
        name, ext = os.path.splitext(filename)
        timestamped_filename = os.path.join(self.data_dir, f"{name}_{self.timestamp}{ext}")
        
        with open(timestamped_filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Analysis report exported to {timestamped_filename}")
        
        # Generate HTML table for the analysis report
        try:
            from simple_html_generator import csv_to_html_simple
            # Create a temporary CSV from the JSON data for HTML generation
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_csv:
                # Convert JSON to CSV format
                if isinstance(report, dict) and 'companies' in report:
                    import pandas as pd
                    df = pd.DataFrame(report['companies'])
                    df.to_csv(temp_csv.name, index=False)
                    html_filename = csv_to_html_simple(temp_csv.name, "YC Companies Analysis Report")
                    if html_filename:
                        # Move HTML file to html subfolder
                        html_basename = os.path.basename(html_filename)
                        html_dest = os.path.join(self.html_dir, html_basename)
                        os.rename(html_filename, html_dest)
                        logger.info(f"HTML table generated: {html_dest}")
                    os.unlink(temp_csv.name)  # Clean up temp file
        except Exception as e:
            logger.warning(f"Could not generate HTML table for analysis report: {e}")
    
    def print_summary(self):
        """Print a summary of the analysis to console"""
        report = self.generate_summary_report()
        
        print("\n" + "="*50)
        print("YC COMPANIES ANALYSIS SUMMARY")
        print("="*50)
        
        print(f"\nTotal Companies: {report['total_companies']}")
        
        if report['batch_info']:
            print(f"\nBatch Distribution:")
            for batch, count in report['batch_info'].items():
                print(f"  {batch}: {count} companies")
        
        if report['categories']['most_common_categories']:
            print(f"\nTop 5 Categories:")
            for category, count in report['categories']['most_common_categories'][:5]:
                print(f"  {category}: {count} companies")
        
        if report['descriptions']:
            print(f"\nDescription Statistics:")
            print(f"  Average length: {report['descriptions']['avg_description_length']:.1f} characters")
            print(f"  Median length: {report['descriptions']['median_description_length']:.1f} characters")
        
        if report['founders']:
            print(f"\nFounders Statistics:")
            print(f"  Total founders: {report['founders']['total_founders']}")
            print(f"  Companies with founders: {report['founders']['companies_with_founders']}")
            print(f"  LinkedIn profiles: {report['founders']['linkedin_profiles_count']}")
            print(f"  Average founders per company: {report['founders']['founders_per_company']['avg']:.1f}")
        
        print(f"\nData Quality:")
        for metric, count in report['data_quality'].items():
            print(f"  {metric.replace('_', ' ').title()}: {count}")
        
        print("\n" + "="*50)
    
    def parse_html_companies(self, html_file_path):
        """Parse company names from an HTML file"""
        if not os.path.exists(html_file_path):
            # Try treating it as a file:// URL
            if html_file_path.startswith('file://'):
                html_file_path = html_file_path[7:]  # Remove 'file://' prefix
                if not os.path.exists(html_file_path):
                    logger.error(f"HTML file not found: {html_file_path}")
                    return set()
            else:
                logger.error(f"HTML file not found: {html_file_path}")
                return set()
        
        try:
            with open(html_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            company_names = set()
            
            logger.info(f"Attempting to parse HTML file: {html_file_path}")
            
            # Method 1: Try to find table structure and Company column
            tables = soup.find_all('table')
            logger.info(f"Found {len(tables)} table(s) in HTML")
            
            for table_idx, table in enumerate(tables):
                logger.info(f"Processing table {table_idx + 1}")
                rows = table.find_all('tr')
                
                if not rows:
                    continue
                
                # Try to find header row
                header_row = None
                header_cells = []
                
                # Check first few rows for headers
                for row in rows[:3]:
                    cells = row.find_all(['th', 'td'])
                    if cells:
                        cell_texts = [cell.get_text(strip=True) for cell in cells]
                        # Look for typical header words
                        if any(text.lower() in ['company', 'name', 'startup'] for text in cell_texts):
                            header_row = row
                            header_cells = cell_texts
                            logger.info(f"Found header row: {header_cells}")
                            break
                
                if header_row and header_cells:
                    # Find Company column index
                    company_col_idx = None
                    for idx, header in enumerate(header_cells):
                        if header.lower() in ['company', 'company name', 'name', 'startup', 'startup name']:
                            company_col_idx = idx
                            logger.info(f"Found Company column at index {idx}: '{header}'")
                            break
                    
                    if company_col_idx is not None:
                        # Extract company names from this column
                        data_rows = rows[1:] if header_row == rows[0] else rows
                        for row in data_rows:
                            cells = row.find_all(['td', 'th'])
                            if len(cells) > company_col_idx:
                                company_text = cells[company_col_idx].get_text(strip=True)
                                if company_text and company_text.lower() not in ['company', 'name', 'startup', '']:
                                    # Clean the company name
                                    clean_name = self._clean_company_name(company_text)
                                    if clean_name:
                                        company_names.add(clean_name)
                                        logger.debug(f"Found company: {clean_name}")
                        
                        if company_names:
                            logger.info(f"Successfully extracted {len(company_names)} companies from table structure")
                            return company_names
            
            # Method 2: Fallback to the original parsing logic
            logger.info("No table structure found, falling back to original parsing method")
            
            # Look for companies in table cells with class "company-name"
            company_cells = soup.find_all('td', class_='company-name')
            for cell in company_cells:
                text = cell.get_text(strip=True)
                # Extract company name from the beginning of the text
                # Pattern observed: CompanyNameLocation...Description...BatchType
                # We need to extract just the company name
                if text:
                    import re
                    
                    # Method 1: Split by known location patterns first
                    # Common patterns: "San Francisco, CA, USA", "London, England, United Kingdom", "São Paulo, SP, Brazil"
                    location_patterns = [
                        r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2,}(?:,\s*[A-Z]{2,})?',  # City, State/Province, Country
                        r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*',  # Full location
                        r'São\s+Paulo,\s*SP,\s*Brazil',  # Special case for São Paulo
                        r'London,\s*England,\s*United\s*Kingdom'  # Special case for London
                    ]
                    
                    company_name = text
                    for pattern in location_patterns:
                        match = re.search(pattern, text)
                        if match:
                            # Take everything before the location
                            company_name = text[:match.start()].strip()
                            break
                    
                    # Method 2: If no location found, try splitting by other patterns
                    if company_name == text:
                        # Look for description patterns that start with common words
                        desc_start_patterns = [
                            r'\s+(The\s+[A-Z])',  # "The simulation...", "The AI..."
                            r'\s+(AI-powered)',   # "AI-powered..."
                            r'\s+(Voice\s+AI)',   # "Voice AI..."
                            r'\s+(Autonomous)',   # "Autonomous..."
                            r'\s+(We\s+[a-z])',   # "We help...", "We audit..."
                            r'\s+(Build)',        # "Build AI..."
                            r'\s+(Helping)',      # "Helping..."
                            r'\s+(Database)',     # "Database of..."
                            r'\s+(Converting)',   # "Converting..."
                            r'\s+(Replacing)'     # "Replacing..."
                        ]
                        
                        for pattern in desc_start_patterns:
                            match = re.search(pattern, text)
                            if match:
                                company_name = text[:match.start()].strip()
                                break
                    
                    # Method 3: Remove batch and category info that might be at the end
                    clean_name = re.sub(r'(Summer\s+\d+|Winter\s+\d+|Spring\s+\d+|Fall\s+\d+).*$', '', company_name)
                    
                    # Remove category patterns at the end
                    category_patterns = [
                        r'B2B.*$', r'B2C.*$', r'Consumer.*$', r'Healthcare.*$', r'Fintech.*$',
                        r'Government.*$', r'Infrastructure.*$', r'Sales.*$', r'Security.*$',
                        r'Engineering.*$', r'Product.*$', r'Design.*$', r'Real\s+Estate.*$',
                        r'Manufacturing.*$', r'Robotics.*$', r'Industrials.*$', r'Education.*$'
                    ]
                    
                    for pattern in category_patterns:
                        clean_name = re.sub(pattern, '', clean_name, flags=re.IGNORECASE)
                    
                    clean_name = clean_name.strip()
                    
                    # Final cleanup: remove trailing dots, commas, and extra whitespace
                    clean_name = re.sub(r'[.,\s]+$', '', clean_name)
                    
                    # Only add if it looks like a valid company name (not too short, contains letters)
                    if clean_name and len(clean_name) > 1 and re.search(r'[A-Za-z]', clean_name):
                        company_names.add(clean_name)
            
            logger.info(f"Parsed {len(company_names)} companies from HTML file: {html_file_path}")
            return company_names
            
        except Exception as e:
            logger.error(f"Error parsing HTML file {html_file_path}: {e}")
            return set()
    
    def _clean_company_name(self, text):
        """Clean and extract company name from raw text"""
        if not text:
            return None
        
        import re
        
        # Method 1: Split by known location patterns first
        # Common patterns: "San Francisco, CA, USA", "London, England, United Kingdom"
        location_patterns = [
            r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2,}(?:,\s*[A-Z]{2,})?',  # City, State/Province, Country
            r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*',  # Full location
            r'São\s+Paulo,\s*SP,\s*Brazil',  # Special case for São Paulo
            r'London,\s*England,\s*United\s*Kingdom'  # Special case for London
        ]
        
        company_name = text
        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                # Take everything before the location
                company_name = text[:match.start()].strip()
                break
        
        # Method 2: If no location found, try splitting by description patterns
        if company_name == text:
            # Look for description patterns that start with common words
            desc_start_patterns = [
                r'\s+(The\s+[A-Z])',  # "The simulation...", "The AI..."
                r'\s+(AI-powered)',   # "AI-powered..."
                r'\s+(Voice\s+AI)',   # "Voice AI..."
                r'\s+(Autonomous)',   # "Autonomous..."
                r'\s+(We\s+[a-z])',   # "We help...", "We audit..."
                r'\s+(Build)',        # "Build AI..."
                r'\s+(Helping)',      # "Helping..."
                r'\s+(Database)',     # "Database of..."
                r'\s+(Converting)',   # "Converting..."
                r'\s+(Replacing)'     # "Replacing..."
            ]
            
            for pattern in desc_start_patterns:
                match = re.search(pattern, text)
                if match:
                    company_name = text[:match.start()].strip()
                    break
        
        # Method 3: Remove batch and category info that might be at the end
        clean_name = re.sub(r'(Summer\s+\d+|Winter\s+\d+|Spring\s+\d+|Fall\s+\d+).*$', '', company_name)
        
        # Remove category patterns at the end
        category_patterns = [
            r'B2B.*$', r'B2C.*$', r'Consumer.*$', r'Healthcare.*$', r'Fintech.*$',
            r'Government.*$', r'Infrastructure.*$', r'Sales.*$', r'Security.*$',
            r'Engineering.*$', r'Product.*$', r'Design.*$', r'Real\s+Estate.*$',
            r'Manufacturing.*$', r'Robotics.*$', r'Industrials.*$', r'Education.*$'
        ]
        
        for pattern in category_patterns:
            clean_name = re.sub(pattern, '', clean_name, flags=re.IGNORECASE)
        
        clean_name = clean_name.strip()
        
        # Final cleanup: remove trailing dots, commas, and extra whitespace
        clean_name = re.sub(r'[.,\s]+$', '', clean_name)
        
        # Remove parenthetical information
        clean_name = re.sub(r'\s*\([^)]*\).*', '', clean_name)
        
        # Remove dashes and everything after
        clean_name = re.sub(r'\s*-.*', '', clean_name)
        
        # Only return if it looks like a valid company name (not too short, contains letters)
        if clean_name and len(clean_name) > 1 and re.search(r'[A-Za-z]', clean_name):
            return clean_name
        
        return None
    
    def diff_companies(self, html_file_path, output_file=None):
        """Compare YC S2025 batch companies with companies in HTML file"""
        if self.df.empty:
            logger.error("No company data loaded. Please load data first.")
            return {}
        
        # Get companies from current dataset and clean them for comparison
        current_companies_raw = set()
        if 'name' in self.df.columns:
            current_companies_raw = set(self.df['name'].dropna().str.strip())
        
        # Clean the scraped company names to extract just the company name
        current_companies = set()
        for company_raw in current_companies_raw:
            clean_name = self._clean_company_name(company_raw)
            if clean_name:
                current_companies.add(clean_name)
        
        logger.info(f"Cleaned {len(current_companies_raw)} raw companies to {len(current_companies)} clean names")
        
        # Get companies from HTML file
        html_companies = self.parse_html_companies(html_file_path)
        
        # Find companies in S2025 batch but not in HTML file
        missing_in_html = current_companies - html_companies
        
        # Find companies in HTML but not in current S2025 batch
        missing_in_s2025 = html_companies - current_companies
        
        # Find common companies
        common_companies = current_companies & html_companies
        
        diff_report = {
            'total_s2025_companies': len(current_companies),
            'total_html_companies': len(html_companies),
            'common_companies': sorted(list(common_companies)),
            'missing_in_html': sorted(list(missing_in_html)),
            'missing_in_s2025': sorted(list(missing_in_s2025)),
            'common_count': len(common_companies),
            'missing_in_html_count': len(missing_in_html),
            'missing_in_s2025_count': len(missing_in_s2025),
            'html_file_path': html_file_path,
            'timestamp': datetime.now().isoformat()
        }
        
        # Print summary
        print("\n" + "="*60)
        print("YC S2025 COMPANIES NOT IN HTML FILE")
        print("="*60)
        print(f"HTML File: {html_file_path}")
        print(f"YC S2025 Companies: {len(current_companies)}")
        print(f"HTML File Companies: {len(html_companies)}")
        print(f"Common Companies: {len(common_companies)}")
        print(f"Companies in S2025 but NOT in HTML: {len(missing_in_html)}")
        
        if missing_in_html:
            print(f"\n📋 Companies in YC S2025 batch but NOT listed in HTML file:")
            for i, company in enumerate(sorted(missing_in_html), 1):
                print(f"  {i:3d}. {company}")
        else:
            print(f"\n✅ All YC S2025 companies are present in the HTML file!")
        
        print("="*60)
        
        # Save detailed report if output file specified
        if output_file:
            # Create output directory structure
            os.makedirs(self.data_dir, exist_ok=True)
            
            # Add timestamp to filename
            name, ext = os.path.splitext(output_file)
            timestamped_filename = os.path.join(self.data_dir, f"{name}_diff_{self.timestamp}{ext}")
            
            with open(timestamped_filename, 'w', encoding='utf-8') as f:
                json.dump(diff_report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Diff report saved to: {timestamped_filename}")
            
            # Also create an HTML report for better visualization
            html_report = self.generate_diff_html_report(diff_report)
            html_path = os.path.join(self.html_dir, f"{name}_diff_{self.timestamp}.html")
            os.makedirs(self.html_dir, exist_ok=True)
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_report)
            
            logger.info(f"Diff HTML report saved to: {html_path}")
        
        return diff_report
    
    def generate_diff_html_report(self, diff_report):
        """Generate HTML report for the diff analysis"""
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YC S2025 Companies Not in HTML File</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f8f9fa;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.2em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: 600;
            color: #667eea;
            margin-bottom: 10px;
        }}
        .stat-label {{
            color: #6c757d;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .companies-section {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .companies-section h2 {{
            color: #667eea;
            margin-top: 0;
            border-bottom: 2px solid #f1f3f4;
            padding-bottom: 10px;
        }}
        .companies-list {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 10px;
            margin-top: 20px;
        }}
        .company-item {{
            background: #f8f9fa;
            padding: 10px 15px;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }}
        .missing-in-html {{
            border-left-color: #dc3545;
        }}
        .missing-in-s2025 {{
            border-left-color: #ffc107;
        }}
        .common {{
            border-left-color: #28a745;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #6c757d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📋 YC S2025 Companies Not in HTML File</h1>
        <p><strong>Missing Companies Analysis</strong></p>
        <p>Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">{diff_report['total_s2025_companies']}</div>
            <div class="stat-label">S2025 Companies</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{diff_report['total_html_companies']}</div>
            <div class="stat-label">HTML Companies</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{diff_report['common_count']}</div>
            <div class="stat-label">Common</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{diff_report['missing_in_html_count']}</div>
            <div class="stat-label">Missing from HTML</div>
        </div>
    </div>
    
    {self._format_companies_section('Companies in YC S2025 but NOT in HTML File', diff_report['missing_in_html'], 'missing-in-html')}
    
    <div class="footer">
        <p>HTML File: {diff_report['html_file_path']}</p>
        <p>Report generated by YC Company Analyzer</p>
    </div>
</body>
</html>
        """
        return html_content
    
    def _format_companies_section(self, title, companies, css_class):
        """Format a section of companies for HTML report"""
        if not companies:
            return f"""
    <div class="companies-section">
        <h2>{title}</h2>
        <p><em>No companies found in this category.</em></p>
    </div>
            """
        
        companies_html = ""
        for company in companies:
            companies_html += f'<div class="company-item {css_class}">{company}</div>'
        
        return f"""
    <div class="companies-section">
        <h2>{title} ({len(companies)})</h2>
        <div class="companies-list">
            {companies_html}
        </div>
    </div>
        """

def main():
    """Main function to run the analyzer"""
    analyzer = YCAnalyzer()
    
    if not analyzer.df.empty:
        analyzer.print_summary()
        analyzer.create_visualizations()
        analyzer.export_analysis()
    else:
        print("No data found. Please run the scraper first to collect company data.")

if __name__ == "__main__":
    main() 