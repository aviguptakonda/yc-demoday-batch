#!/usr/bin/env python3
"""
Company List Comparison Tool
Compares a provided list of companies with scraped CSV data
"""

import pandas as pd
import json
import re
from datetime import datetime
import os


class CompanyListComparer:
    def __init__(self, csv_file):
        """Initialize with CSV file path"""
        self.csv_file = csv_file
        self.df = pd.read_csv(csv_file)
        self.scraped_companies_dict = self._extract_company_names()
    
    def _extract_company_names(self):
        """Extract clean company names from the scraped data"""
        companies = {}
        for _, row in self.df.iterrows():
            full_name = row['name'].strip()
            
            # Extract company name before location
            location_pattern = r'(San Francisco|New York|Los Angeles|San Diego|San Mateo|Palo Alto|Atlanta|Boulder|Cambridge|London|Stockholm|Brussels|Bengaluru|Toronto|Sunnyvale)'
            match = re.search(location_pattern, full_name)
            
            if match:
                company_name = full_name[:match.start()].strip()
            else:
                # Look for CamelCase boundary
                matches = list(re.finditer(r'([a-z])([A-Z])', full_name))
                if matches:
                    split_pos = matches[0].end() - 1
                    company_name = full_name[:split_pos].strip()
                else:
                    company_name = full_name.split('Fall')[0].strip() if 'Fall' in full_name else full_name
            
            if len(company_name) >= 2:
                companies[company_name.lower()] = company_name
        
        return companies
    
    def _normalize_name(self, name):
        """Normalize company name for comparison"""
        return name.lower().replace(' ', '').replace('-', '').replace('.', '').replace("'", '')
    
    def _match_companies(self, name1_lower, name2_lower):
        """Check if two company names match using flexible matching"""
        # Exact match
        if name1_lower == name2_lower:
            return True
        
        # One contains the other
        if name1_lower in name2_lower or name2_lower in name1_lower:
            return True
        
        # Normalized match (remove spaces, dashes, dots)
        norm1 = self._normalize_name(name1_lower)
        norm2 = self._normalize_name(name2_lower)
        if norm1 == norm2 or norm1 in norm2 or norm2 in norm1:
            return True
        
        return False
    
    def compare_with_list(self, company_list, output_file=None):
        """
        Compare provided company list with scraped data
        
        Args:
            company_list: List of company names or newline-separated string
            output_file: Optional path to save missing companies
        
        Returns:
            Dictionary with comparison results
        """
        # Parse the provided list
        if isinstance(company_list, str):
            provided_list = [line.strip() for line in company_list.split('\n') if line.strip()]
        else:
            provided_list = [str(c).strip() for c in company_list if str(c).strip()]
        
        provided_dict = {c.lower(): c for c in provided_list}
        
        # Find missing companies (in provided list but not scraped)
        missing_from_scrape = []
        for provided_lower, provided_name in sorted(provided_dict.items()):
            found = False
            for scraped_lower in self.scraped_companies_dict.keys():
                if self._match_companies(provided_lower, scraped_lower):
                    found = True
                    break
            
            if not found:
                missing_from_scrape.append(provided_name)
        
        # Find extra companies (scraped but not in provided list)
        extra_in_scrape = []
        for scraped_lower, scraped_name in sorted(self.scraped_companies_dict.items()):
            found = False
            for provided_lower in provided_dict.keys():
                if self._match_companies(scraped_lower, provided_lower):
                    found = True
                    break
            
            if not found:
                extra_in_scrape.append(scraped_name)
        
        matched_count = len(provided_dict) - len(missing_from_scrape)
        match_percentage = round(matched_count * 100 / len(provided_dict), 1) if provided_dict else 0
        
        results = {
            "summary": {
                "provided_count": len(provided_dict),
                "scraped_count": len(self.scraped_companies_dict),
                "matched_count": matched_count,
                "missing_count": len(missing_from_scrape),
                "extra_count": len(extra_in_scrape),
                "match_percentage": match_percentage,
                "comparison_date": datetime.now().isoformat()
            },
            "missing_from_scrape": sorted(missing_from_scrape),
            "extra_in_scrape": sorted(extra_in_scrape),
            "provided_list": sorted(provided_dict.values()),
            "scraped_list": sorted(self.scraped_companies_dict.values())
        }
        
        # Save results to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
        
        # Also save missing companies to a separate text file
        if missing_from_scrape:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            missing_file = f'missing_companies_{timestamp}.txt'
            with open(missing_file, 'w') as f:
                f.write(f"Missing Companies Report\n")
                f.write(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n")
                f.write(f"CSV Source: {self.csv_file}\n")
                f.write(f"={'='*70}\n\n")
                f.write(f"Companies in your list but NOT found in scraped data:\n")
                f.write(f"Total: {len(missing_from_scrape)}\n\n")
                for i, company in enumerate(sorted(missing_from_scrape), 1):
                    f.write(f"{i}. {company}\n")
            results['missing_companies_file'] = missing_file
        
        return results
    
    def print_results(self, results):
        """Print comparison results in a formatted way"""
        summary = results['summary']
        missing = results['missing_from_scrape']
        extra = results['extra_in_scrape']
        
        print(f"\n{'='*70}")
        print(f"📊 COMPANY LIST COMPARISON RESULTS")
        print(f"{'='*70}")
        print(f"  Provided list:           {summary['provided_count']} companies")
        print(f"  Scraped data:            {summary['scraped_count']} companies")
        print(f"  Successfully matched:    {summary['matched_count']} companies ({summary['match_percentage']}%)")
        print(f"  Missing from scrape:     {summary['missing_count']} companies")
        print(f"  Extra in scrape:         {summary['extra_count']} companies")
        
        if missing:
            print(f"\n{'='*70}")
            print(f"🔴 MISSING: Companies in your list but NOT in scraped data")
            print(f"{'='*70}")
            for i, company in enumerate(sorted(missing), 1):
                print(f"  {i}. {company}")
            
            if 'missing_companies_file' in results:
                print(f"\n📄 Missing companies saved to: {results['missing_companies_file']}")
        else:
            print(f"\n✅ All companies from your list were successfully scraped!")
        
        if extra:
            print(f"\n{'='*70}")
            print(f"🟢 EXTRA: Companies scraped but NOT in your provided list")
            print(f"{'='*70}")
            for i, company in enumerate(sorted(extra), 1):
                print(f"  {i}. {company}")
        
        print(f"{'='*70}\n")


def compare_from_file(csv_file, company_list_file, output_file=None):
    """
    Compare companies from a text file with scraped CSV data
    
    Args:
        csv_file: Path to scraped CSV file
        company_list_file: Path to text file with company names (one per line)
        output_file: Optional path to save comparison results JSON
    """
    comparer = CompanyListComparer(csv_file)
    
    # Read company list from file
    with open(company_list_file, 'r') as f:
        company_list = f.read()
    
    results = comparer.compare_with_list(company_list, output_file)
    comparer.print_results(results)
    
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python company_list_comparer.py <csv_file> <company_list_file> [output_json]")
        print("\nExample:")
        print("  python company_list_comparer.py yc_companies.csv companies_to_check.txt")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    company_list_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    compare_from_file(csv_file, company_list_file, output_file)

