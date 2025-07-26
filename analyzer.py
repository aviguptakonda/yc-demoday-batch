import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
from collections import Counter
import numpy as np
from datetime import datetime
import logging
import os

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
        else:
            self.output_dir = f"output_{self.timestamp}"
            
        self.analyzer_dir = os.path.join(self.output_dir, "analyzer")
        self.data_dir = os.path.join(self.analyzer_dir, "data")
        self.html_dir = os.path.join(self.analyzer_dir, "html")
        self.charts_dir = os.path.join(self.analyzer_dir, "charts")
        self.load_data()
        
    def load_data(self):
        """Load company data from CSV or JSON file"""
        try:
            if self.data_file.endswith('.csv'):
                # For CSV files with complex data structures, try to parse them properly
                self.df = pd.read_csv(self.data_file, converters={
                    'categories': lambda x: eval(x) if pd.notna(x) else [],
                    'founders': lambda x: eval(x) if pd.notna(x) else []
                })
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
                    self.df = pd.read_csv(self.data_file)
                    logger.info("Loaded CSV with basic parsing, will handle complex data in clean_data()")
            except Exception as e2:
                logger.error(f"Alternative loading also failed: {e2}")
                self.df = pd.DataFrame()
    
    def clean_data(self):
        """Clean and preprocess the data"""
        if self.df.empty:
            logger.warning("No data to clean")
            return
            
        # Convert categories from string to list if needed
        if 'categories' in self.df.columns:
            self.df['categories'] = self.df['categories'].apply(
                lambda x: x if isinstance(x, list) else 
                (json.loads(x) if isinstance(x, str) and x.startswith('[') else [])
            )
        
        # Convert founders from string to list if needed
        if 'founders' in self.df.columns:
            self.df['founders'] = self.df['founders'].apply(
                lambda x: x if isinstance(x, list) else 
                (json.loads(x) if isinstance(x, str) and x.startswith('[') else [])
            )
        
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
            if isinstance(founders_list, list):
                for founder in founders_list:
                    if isinstance(founder, dict):
                        all_founders.append(founder)
                        
                        # Track profile types
                        if 'profile_type' in founder:
                            profile_types.append(founder['profile_type'])
                        
                        # Track LinkedIn profiles specifically
                        if founder.get('profile_type') == 'linkedin' and founder.get('profile_url') != 'N/A':
                            linkedin_profiles.append(founder)
        
        founders_analysis = {
            'total_founders': len(all_founders),
            'companies_with_founders': len([f for f in self.df['founders'] if f and len(f) > 0]),
            'profile_type_distribution': Counter(profile_types),
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