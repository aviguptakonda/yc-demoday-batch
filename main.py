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
    parser.add_argument('--action', choices=['scrape', 'analyze', 'sample', 'research', 'diff', 'all'], default='all',
                       help='Action to perform: scrape data, analyze data, generate sample data, research company, diff companies, or all')
    parser.add_argument('--batch', default='Fall 2025',
                       help='YC batch to target (default: Fall 2025). Examples: "Fall 2025", "Summer 2025", "Winter 2025"')
    parser.add_argument('--input', default='yc_companies.csv',
                       help='Input file for analysis (default: yc_companies.csv)')
    parser.add_argument('--report', default='analysis_report.json',
                       help='Output file for analysis report (default: analysis_report.json)')
    parser.add_argument('--charts-dir', default='charts',
                       help='Output directory for charts (default: charts)')
    
    # Research-specific arguments
    parser.add_argument('--company', type=str,
                       help='Company name to research (required for research action)')
    parser.add_argument('--company-url', type=str,
                       help='Company website URL (optional for research action)')
    
    # Diff-specific arguments
    parser.add_argument('--html-file', type=str,
                       help='HTML file path (file:// URL or local path) to compare against YC batch (required for diff action)')
    parser.add_argument('--diff-output', type=str, default='company_diff_report.json',
                       help='Output file for diff report (default: company_diff_report.json)')
    
    args = parser.parse_args()
    
    try:
        # Handle research action
        if args.action == 'research':
            if not args.company:
                logger.error("Company name is required for research action. Use --company 'Company Name'")
                sys.exit(1)
            
            logger.info(f"Starting comprehensive research for: {args.company}")
            from company_researcher import CompanyResearcher
            
            researcher = CompanyResearcher()
            research_data = asyncio.run(researcher.research_company(args.company, args.company_url))
            
            # Generate HTML report
            html_report = researcher.generate_html_report(research_data)
            html_path = os.path.join(researcher.output_dir, f"{args.company.replace(' ', '_')}_research_report.html")
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_report)
            
            logger.info(f"✅ Research completed for {args.company}!")
            json_report_path = os.path.join(researcher.output_dir, f"{args.company.replace(' ', '_')}_research_report.json")
            logger.info(f"📊 JSON Report: {json_report_path}")
            logger.info(f"🌐 HTML Report: {html_path}")
            logger.info(f"🎯 Investment Recommendation: {research_data['insights']['recommendation']}")
            return
        
        # Handle diff action
        if args.action == 'diff':
            if not args.html_file:
                logger.error("HTML file path is required for diff action. Use --html-file 'path/to/file.html'")
                sys.exit(1)
            
            logger.info(f"Starting company comparison between YC {args.batch} batch and HTML file: {args.html_file}")
            
            # Use existing data if available, otherwise try to find latest data
            input_file = args.input
            if not os.path.exists(input_file):
                # Try to find the latest CSV file from output directories
                import glob
                output_dirs = glob.glob("output_*")
                if output_dirs:
                    latest_dir = max(output_dirs, key=os.path.getctime)
                    scraper_data_dir = os.path.join(latest_dir, "scraper", "data")
                    csv_files = glob.glob(os.path.join(scraper_data_dir, "*.csv"))
                    # Prefer final CSVs over progress CSVs
                    final_csvs = [p for p in csv_files if "_progress" not in p]
                    preferred_list = final_csvs if final_csvs else csv_files
                    if preferred_list:
                        input_file = max(preferred_list, key=os.path.getctime)
                        logger.info(f"Using latest scraped data: {input_file}")
                    else:
                        logger.error("No YC company data found. Please run scraper first or provide data file.")
                        sys.exit(1)
                else:
                    logger.error("No YC company data found. Please run scraper first or provide data file.")
                    sys.exit(1)
            
            analyzer = YCAnalyzer(input_file, batch=args.batch)
            
            if analyzer.df.empty:
                logger.error("No data available for comparison. Please check your data file.")
                sys.exit(1)
            
            # Perform the diff
            diff_report = analyzer.diff_companies(args.html_file, args.diff_output)
            
            logger.info("✅ Company comparison completed!")
            logger.info(f"📊 Detailed report saved with visualizations")
            return
        
        if args.action in ['scrape', 'all']:
            logger.info(f"Starting data scraping for YC {args.batch} batch...")
            from yc_scraper_robust import RobustYCScraper
            scraper = RobustYCScraper(batch=args.batch)
            asyncio.run(scraper.scrape_companies())
            if scraper.companies:
                output_dir = scraper.save_final_data(".")
                logger.info(f"Successfully scraped {len(scraper.companies)} companies")
                
                # Store the shared output directory for analyzer
                shared_output_dir = getattr(scraper, 'shared_output_dir', None)
                
                # Update input file path to use the latest scraped data
                if args.action == 'all':
                    # Find the latest CSV file in output directories
                    import glob
                    output_dirs = glob.glob("output_*")
                    if output_dirs:
                        latest_dir = max(output_dirs, key=os.path.getctime)
                        scraper_data_dir = os.path.join(latest_dir, "scraper", "data")
                        csv_files = glob.glob(os.path.join(scraper_data_dir, "*.csv"))
                        # Prefer final CSVs over progress CSVs
                        final_csvs = [p for p in csv_files if "_progress" not in p]
                        preferred_list = final_csvs if final_csvs else csv_files
                        if preferred_list:
                            # Choose the most recent CSV by ctime
                            args.input = max(preferred_list, key=os.path.getctime)
                            logger.info(f"Using latest scraped data: {args.input}")
            else:
                logger.error("No companies were scraped")
                sys.exit(1)

        if args.action in ['sample', 'all']:
            logger.info(f"Generating sample data for YC {args.batch} batch...")
            create_sample_data(batch=args.batch)
            logger.info("Sample data generated successfully")

        if args.action in ['analyze', 'all']:
            logger.info("Starting data analysis...")
            # Use the scraper's output directory if available, otherwise create new one
            shared_dir = shared_output_dir if 'shared_output_dir' in locals() else None
            analyzer = YCAnalyzer(args.input, shared_output_dir=shared_dir, batch=args.batch)
            
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