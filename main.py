#!/usr/bin/env python3
"""
YC Demo Day Batch Monitor
A tool to analyze YC companies data and generate reports
"""

import argparse
import sys
from analyzer import YCAnalyzer
from sample_data import create_sample_data
import asyncio
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='YC Demo Day Batch Monitor')
    parser.add_argument('--action', choices=['scrape', 'analyze', 'sample', 'all'], default='all',
                       help='Action to perform: scrape data, analyze data, generate sample data, or all')
    parser.add_argument('--input', default='yc_companies.csv',
                       help='Input file for analysis (default: yc_companies.csv)')
    parser.add_argument('--report', default='analysis_report.json',
                       help='Output file for analysis report (default: analysis_report.json)')
    parser.add_argument('--charts-dir', default='charts',
                       help='Output directory for charts (default: charts)')
    
    args = parser.parse_args()
    
    try:
        if args.action in ['scrape', 'all']:
            logger.info("Starting data scraping...")
            from yc_scraper import FinalYCScraper
            scraper = FinalYCScraper()
            companies = asyncio.run(scraper.scrape_companies())
            if companies:
                scraper.save_data()
                logger.info(f"Successfully scraped {len(companies)} companies")
                
                # Store the shared output directory for analyzer
                shared_output_dir = getattr(scraper, 'shared_output_dir', None)
                
                # Update input file path to use the latest scraped data
                if args.action == 'all':
                    # Find the latest CSV file in output directories
                    import glob
                    import os
                    output_dirs = glob.glob("output_*")
                    if output_dirs:
                        latest_dir = max(output_dirs, key=os.path.getctime)
                        scraper_data_dir = os.path.join(latest_dir, "scraper", "data")
                        csv_files = glob.glob(os.path.join(scraper_data_dir, "*.csv"))
                        if csv_files:
                            args.input = csv_files[0]
                            logger.info(f"Using latest scraped data: {args.input}")
            else:
                logger.error("No companies were scraped")
                sys.exit(1)

        if args.action in ['sample', 'all']:
            logger.info("Generating sample data...")
            create_sample_data()
            logger.info("Sample data generated successfully")

        if args.action in ['analyze', 'all']:
            logger.info("Starting data analysis...")
            analyzer = YCAnalyzer(args.input, shared_output_dir=shared_output_dir if 'shared_output_dir' in locals() else None)
            
            if not analyzer.df.empty:
                analyzer.print_summary()
                analyzer.create_visualizations(args.charts_dir)
                analyzer.export_analysis(args.report)
                logger.info("Analysis completed successfully")
                logger.info(f"All output files organized in: {analyzer.output_dir}")
                logger.info(f"  📁 Scraper data: {os.path.join(analyzer.output_dir, 'scraper')}")
                logger.info(f"  📊 Analyzer data: {analyzer.analyzer_dir}")
                logger.info(f"    ├── Data files (JSON): {analyzer.data_dir}")
                logger.info(f"    ├── Charts: {analyzer.charts_dir}")
                logger.info(f"    └── HTML files: {analyzer.html_dir}")
            else:
                logger.error("No data available for analysis. Please generate sample data first or provide a data file.")
                sys.exit(1)
        
        logger.info("All operations completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 