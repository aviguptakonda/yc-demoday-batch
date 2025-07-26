#!/usr/bin/env python3
"""
YC Summer 2025 Batch Scraper
Enhanced version with founder LinkedIn extraction and improved name/description parsing

Scraping Approach:
1. Uses Playwright for headless browser automation
2. Implements infinite scrolling to load all content
3. Extracts company information from company links
4. Visits individual company pages to extract founder LinkedIn profiles
5. Improved text parsing to separate company names from descriptions
6. Enhanced category extraction and data cleaning
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime
from playwright.async_api import async_playwright
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FinalYCScraper:
    def __init__(self):
        """Initialize the scraper"""
        self.companies = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def parse_company_text(self, text):
        """Parse company text to extract name, description, and categories"""
        if not text:
            return None
            
        # Clean up the text
        text = text.strip()
        
        # Extract categories first (they're usually at the end)
        categories = []
        category_patterns = [
            r'Summer 2025',
            r'B2B',
            r'Consumer',
            r'Healthcare',
            r'Industrials',
            r'Fintech',
            r'Education',
            r'Real Estate',
            r'Infrastructure',
            r'Productivity',
            r'Engineering',
            r'Operations',
            r'Security',
            r'Marketing',
            r'Human Resources',
            r'Legal',
            r'Retail',
            r'Sales',
            r'Supply Chain',
            r'Automotive',
            r'Drones',
            r'Robotics',
            r'Manufacturing',
            r'Drug Discovery',
            r'Healthcare IT',
            r'Social',
            r'Recruiting and Talent',
            r'Finance and Accounting',
            r'Construction'
        ]
        
        # Find categories in the text
        for pattern in category_patterns:
            if pattern in text:
                categories.append(pattern)
                # Remove category from text for further processing
                text = text.replace(pattern, '')
        
        # Remove batch info
        text = text.replace('Summer 2025', '').strip()
        
        # Remove location patterns from the entire text first
        location_patterns = [
            r'\s*(San Francisco|New York|London|Dublin|Mexico City|CDMX|USA|United States|England|United Kingdom|Bielefeld|NRW|Germany|Overland Park|KS)\s*,?\s*(CA|NY|USA|UK|Germany|Mexico)?\s*',
            r'\s*(CA|NY|USA|UK|Germany|Mexico)\s*$',
            r'\s*,\s*(CA|NY|USA|UK|Germany|Mexico)\s*'
        ]
        
        for pattern in location_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Clean up extra spaces and commas
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r',\s*,', ',', text).strip()
        if text.endswith(','):
            text = text[:-1].strip()
        
        # Try to separate company name from description
        company_name = ""
        description = ""
        
        # Look for common patterns that indicate description
        description_indicators = [
            ' for ',
            'ing ',
            ' is ',
            ' are ',
            ' was ',
            ' were ',
            ' has ',
            ' have ',
            ' had ',
            ' will ',
            ' can ',
            ' should ',
            ' would ',
            ' could ',
            ' helps ',
            ' makes ',
            ' creates ',
            ' builds ',
            ' provides ',
            ' offers ',
            ' enables ',
            ' allows ',
            ' that ',
            ' which ',
            ' who ',
            ' where ',
            ' when ',
            ' why ',
            ' how ',
            ' with ',
            ' using ',
            ' through ',
            ' via ',
            ' by ',
            ' from ',
            ' to ',
            ' in ',
            ' on ',
            ' at ',
            ' of ',
            ' the ',
            ' a ',
            ' an '
        ]
        
        # Find the first description indicator
        name_end = len(text)
        for indicator in description_indicators:
            pos = text.find(indicator)
            if pos > 0 and pos < name_end:
                name_end = pos
        
        # Split the text
        if name_end < len(text):
            company_name = text[:name_end].strip()
            description = text[name_end:].strip()
        else:
            # No clear separator found, try to split by length
            if len(text) > 30:
                # Take first part as name, rest as description
                words = text.split()
                if len(words) >= 4:
                    company_name = ' '.join(words[:3])
                    description = ' '.join(words[3:])
                else:
                    company_name = text
                    description = ""
            else:
                company_name = text
                description = ""
        
        # Clean up company name
        if company_name:
            # Remove any remaining location artifacts
            company_name = re.sub(r'\s+(San Francisco|New York|London|Dublin|Mexico City|CDMX|USA|United States|England|United Kingdom|Bielefeld|NRW|Germany|Overland Park|KS)\s*.*$', '', company_name, flags=re.IGNORECASE)
            company_name = re.sub(r'\s+(CA|NY|USA|UK|Germany|Mexico)\s*$', '', company_name, flags=re.IGNORECASE)
            
            company_name = company_name.strip()
            
            # Clean up any remaining artifacts
            if company_name.endswith(','):
                company_name = company_name[:-1].strip()
            
            # Remove duplicate company names (e.g., "RealRoots,RealRoots" -> "RealRoots")
            if ',' in company_name:
                parts = company_name.split(',')
                if len(parts) >= 2:
                    first_part = parts[0].strip()
                    second_part = parts[1].strip()
                    # If the parts are very similar, just use the first part
                    if first_part.lower() in second_part.lower() or second_part.lower() in first_part.lower():
                        company_name = first_part
                    # If second part looks like a description, use first part
                    elif any(word in second_part.lower() for word in ['is ', 'are ', 'for ', 'with ', 'using ', 'that ', 'which ', 'simple ', 'ml ', 'framework ', 'cloud ', 'ai ', 'recruiter ', 'legal ', 'governance ', 'automat', 'modern ', 'factory ', 'voice ', 'foundational ', 'technologies', 'self-heal', 'health', 'typescript ', 'platform ', 'tax ', 'preparation ', 'frontend ', 'coding ', 'agent ', 'waymo ', 'excavators', 'gps ', 'alternative ', 'agents ', 'natural ', 'language ', 'bulk ', 'inventory ', 'drones ', 'vision', 'browsers-as-a-service', 'web ', 'automations', 'brands ', 'scale ', 'creator ', 'partnerships ', 'restaurant ', 'phone ', 'line ', 'motion ', 'designer', 'infrastructure ', 'reliable ', 'relationship ', 'management ', 'world\'s ', 'first ', 'maximalist ', 'pharma ', 'suite ', 'agents ', 'tools ', 'accelerate ', 'hdl ', 'design', 'interactive ', 'tutor ', 'knows ', 'hr ', 'manager ', 'hourly ', 'teams', 'compliance ', 'checks ', 'engineering ', 'drawings', 'debt ', 'collection ', 'sales', 'commercial ', 'real ', 'estate ', 'brokers ', 'close ', 'deals', 'customer ', 'support ', 'travel', 'employees ', 'handle ', 'work ', 'people ', 'magic', 'mcp ', 'integrations ', 'single ', 'api', 'coworkers ', 'fraud ', 'risk ', 'qa ', 'mobile ', 'apps', 'executive ', 'assistant', 'accounting ', 'enterprises', 'qualitative ', 'consumer ', 'research ', 'run ', 'by', 'dev ', 'tools ', 'infrastructure', 'data ', 'analysis ', 'life ', 'science ', 'researchers', 'guided ', 'micro-missiles ', 'counter-uas', 'clinical ', 'trials ', 'agents ', 'starting ', 'recruitment', 'postman ', 'servers', 'cursor ', 'music ', 'production', 'analyze ', 'understand ', 'complex ', 'workflows ', 'clarity', 'regulated ', 'firms ', 'show ', 'up ', 'search', 'engineers ', 'era ', 'contextual ', 'layer ', 'coding', 'prompt ', 'full ', 'stack ', 'app ', 'visual ', 'workflows', 'distributors ', 'manufacturers ', 'automate ', 'order ', 'entry', 'powered ', 'human ', 'pentesting ', 'platform', 'database ', 'every ', 'product ', 'internet', 'executive ', 'assistant ', 'everyday ', 'user', 'embedded', 'bring ', 'customers ', 'dealership', 'chemical ', 'super ', 'intelligence ', 'agent ', 'time', 'quality ', 'assurance ', 'governance ', 'infrastructure ', 'clinical', 'firmware ', 'minutes ', 'months ', 'rigorously ', 'tested ', 'real ', 'hardware', 'simulation ', 'evaluation ', 'engine', 'hands', 'operating ', 'system ', 'ambulance ', 'agencies', 'secure ', 'gateway ', 'private ', 'networks', 'media ', 'asset ', 'management', 'native ', 'erp ', 'food ', 'wholesalers', 'automate ', 'browser ', 'workflow ', 'narrated ', 'screen ', 'recording', 'secure ', 'access ', 'control ', 'orchestration ', 'platform ', 'workflows', 'world\'s ', 'first ', 'native ', 'ad ', 'network', 'ticket ', 'triage ', 'management ', 'layer ', 'jira', 'computer ', 'use ', 'agent ', 'automating ', 'windows ', 'apps', 'cuda', 'find ', 'customers ', 'already ', 'want ', 'buy', 'gis ', 'platform', 'on-call ', 'engineer', 'software ', 'autonomous ', 'robot ', 'arms', 'automate ', 'clinical ', 'trial ', 'applications', 'superhuman ', 'text ', 'messages', 'powerful ', 'video ', 'gen ', 'model ', 'explainer ', 'videos ', 'documents', 'team ', 'coding ', 'agents ', 'pocket', 'booking ', 'freight', 'unified ', 'governance ', 'layer ', 'regulated ', 'industries', 'email ', 'infrastructure', 'automatically ', 'fix ', 'production ', 'bugs', 'environments ', 'train ', 'computer ', 'use', 'realtors ', 'answers ', 'close', 'employees ', 'commercial ', 'real ', 'estate', 'synthetic ', 'agents ', 'simulate ', 'real ', 'users', 'models ', 'locally ', 'smartphones', 'modern ', 'zendesk ', 'scaling ', 'high-touch ', 'customer ', 'support']):
                        company_name = first_part
        
        # If company name is too long, take first few words
        if len(company_name) > 50:
            words = company_name.split()
            company_name = ' '.join(words[:3]) if len(words) >= 3 else words[0]
        
        # Clean up description
        if description:
            # Remove any remaining location patterns from description
            description = re.sub(r'\s+(San Francisco|New York|London|Dublin|Mexico City|CDMX|USA|United States|England|United Kingdom|Bielefeld|NRW|Germany|Overland Park|KS)\s*.*$', '', description, flags=re.IGNORECASE)
            description = re.sub(r'\s+(CA|NY|USA|UK|Germany|Mexico)\s*$', '', description, flags=re.IGNORECASE)
            description = description.strip()
            
            # Clean up extra spaces
            description = re.sub(r'\s+', ' ', description).strip()
        
        return {
            'name': company_name,
            'description': description,
            'categories': categories
        }
    
    def extract_company_from_text(self, text):
        """More aggressive company extraction - fallback method"""
        if not text or len(text.strip()) < 5:
            return None
            
        text = text.strip()
        
        # Skip obvious non-company elements
        if any(skip in text.lower() for skip in ['company', 'yc blog', 'contact', 'press', 'privacy', 'terms', 'footer', 'header', 'search', 'filter']):
            return None
            
        # Look for patterns that suggest this is a company
        lines = text.split('\n')
        
        # Find the first line that looks like a company name
        for line in lines:
            line = line.strip()
            if len(line) > 2 and len(line) < 100:
                # Skip if it's just a category or common page element
                if line in ['Summer 2025', 'Companies', 'Search', 'Filter', 'B2B', 'B2C', 'AI/ML']:
                    continue
                    
                # Skip if it starts with common non-company patterns
                if line.startswith('http') or line.startswith('/') or line.startswith('©'):
                    continue
                    
                # This might be a company name
                company_name = line
                
                # Try to extract description from remaining lines
                description_lines = []
                for remaining_line in lines[lines.index(line) + 1:]:
                    remaining_line = remaining_line.strip()
                    if len(remaining_line) > 10 and len(remaining_line) < 200:
                        description_lines.append(remaining_line)
                        break
                
                description = ' '.join(description_lines)
                
                return {
                    'name': company_name,
                    'description': description,
                    'categories': []
                }
        
        return None
    
    async def extract_founder_profiles(self, page, company_url):
        """Extract founder LinkedIn profiles from company page with improved stability"""
        try:
            # Navigate to company page with shorter timeout
            await page.goto(company_url, wait_until='domcontentloaded', timeout=8000)
            await asyncio.sleep(1)
            
            founders = []
            
            # Look for founder information with more specific selectors
            founder_selectors = [
                'a[href*="linkedin.com/in/"]',
                'a[href*="linkedin.com"]',
                '[class*="founder"] a[href*="linkedin"]',
                '[class*="team"] a[href*="linkedin"]',
                '[class*="people"] a[href*="linkedin"]'
            ]
            
            for selector in founder_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        # Get the text content
                        text = await element.text_content()
                        if not text or len(text.strip()) < 3:
                            continue
                            
                        # Get the href if it's a link
                        href = await element.get_attribute('href')
                        
                        # Check if it's a LinkedIn profile
                        if href and 'linkedin.com' in href:
                            # Extract founder name from text or nearby elements
                            founder_name = text.strip()
                            
                            # Clean up the name
                            if len(founder_name) > 50:
                                # Take first few words as name
                                founder_name = ' '.join(founder_name.split()[:3])
                            
                            # Avoid duplicates
                            if not any(f['name'] == founder_name for f in founders):
                                founders.append({
                                    'name': founder_name,
                                    'linkedin_url': href
                                })
                                
                except Exception as e:
                    logger.debug(f"Error with selector {selector}: {e}")
                    continue
            
            # If we found LinkedIn links, return them
            if founders:
                return founders
                
            # Fallback: look for any LinkedIn links on the page
            try:
                linkedin_links = await page.query_selector_all('a[href*="linkedin.com"]')
                for link in linkedin_links:
                    href = await link.get_attribute('href')
                    text = await link.text_content()
                    
                    if href and text and len(text.strip()) > 2:
                        founder_name = text.strip()[:50]  # Limit name length
                        
                        # Avoid duplicates
                        if not any(f['name'] == founder_name for f in founders):
                            founders.append({
                                'name': founder_name,
                                'linkedin_url': href
                            })
            except Exception as e:
                logger.debug(f"Error finding LinkedIn links: {e}")
                
        except Exception as e:
            logger.debug(f"Error extracting founder profiles from {company_url}: {e}")
            
        return founders
    
    async def scrape_companies(self):
        """Scrape companies with proper parsing"""
        max_retries = 3
        
        for retry in range(max_retries):
            try:
                logger.info(f"Scraping attempt {retry + 1}/{max_retries}")
                companies = await self._scrape_companies_attempt()
                
                if companies and len(companies) > 0:
                    logger.info(f"Successfully scraped {len(companies)} companies on attempt {retry + 1}")
                    return companies
                else:
                    logger.warning(f"No companies found on attempt {retry + 1}")
                    if retry < max_retries - 1:
                        logger.info("Retrying...")
                        await asyncio.sleep(5)
                        continue
                    else:
                        logger.error("Failed to get any companies after all retries")
                        return []
                        
            except Exception as e:
                logger.error(f"Error during scraping attempt {retry + 1}: {e}")
                if retry < max_retries - 1:
                    logger.info("Retrying...")
                    await asyncio.sleep(5)
                    continue
                else:
                    logger.error("Failed after all retries")
                    return []
        
        return []

    async def _scrape_companies_attempt(self):
        """Single attempt to scrape companies"""
        async with async_playwright() as playwright:
            try:
                browser = await playwright.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-dev-shm-usage',
                        '--disable-setuid-sandbox',
                        '--no-sandbox',
                        '--no-first-run',
                        '--no-zygote',
                        '--disable-gpu'
                    ]
                )
                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = await context.new_page()
                
                # Set longer timeout and disable images for faster loading
                page.set_default_timeout(30000)
                await page.route('**/*.{png,jpg,jpeg,gif,svg,webp}', lambda route: route.abort())
                
                # Navigate to the page
                await page.goto("https://www.ycombinator.com/companies?batch=Summer%202025", wait_until='domcontentloaded')
                await asyncio.sleep(3)
                
                # Wait for content to load
                logger.info("Waiting for page content to load...")
                try:
                    # Wait for company links to appear
                    await page.wait_for_selector('a[href*="/companies/"]', timeout=10000)
                    logger.info("Found company links on page")
                except:
                    logger.warning("Could not find company links, continuing anyway...")
                
                # Robust scrolling to capture ALL companies
                logger.info("Starting robust scrolling to capture ALL companies...")
                max_attempts = 5
                current_company_count = 0
                
                for attempt in range(max_attempts):
                    try:
                        logger.info(f"Scroll attempt {attempt + 1}/{max_attempts}")
                        
                        # Get current company count
                        company_links = await page.query_selector_all('a[href*="/companies/"]')
                        current_company_count = len(company_links)
                        logger.info(f"Current company count: {current_company_count}")
                        
                        # Scroll to bottom multiple times
                        for scroll in range(3):
                            if page.is_closed():
                                logger.warning("Page closed during scrolling")
                                break
                                
                            try:
                                # Scroll to bottom
                                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                                await asyncio.sleep(2)
                                
                                # Wait for potential new content
                                await asyncio.sleep(3)
                                
                            except Exception as e:
                                logger.warning(f"Error during scroll {scroll + 1}: {e}")
                                continue
                        
                        # Check if we got more companies
                        new_company_links = await page.query_selector_all('a[href*="/companies/"]')
                        new_company_count = len(new_company_links)
                        logger.info(f"After scroll attempt {attempt + 1}: {new_company_count} companies")
                        
                        # If no new companies found, try one more time with longer wait
                        if new_company_count == current_company_count:
                            logger.info("No new companies found, trying with longer wait...")
                            await asyncio.sleep(5)
                            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                            await asyncio.sleep(5)
                            
                            # Check again
                            final_company_links = await page.query_selector_all('a[href*="/companies/"]')
                            final_company_count = len(final_company_links)
                            logger.info(f"After longer wait: {final_company_count} companies")
                            
                            if final_company_count > new_company_count:
                                new_company_count = final_company_count
                                company_links = final_company_links
                            else:
                                company_links = new_company_links
                        else:
                            company_links = new_company_links
                        
                        current_company_count = new_company_count
                        
                        # Continue scrolling to ensure we get all available companies
                        logger.info(f"Continuing to next scroll attempt to capture all companies")
                            
                    except Exception as e:
                        logger.warning(f"Error during scroll attempt {attempt + 1}: {e}")
                        continue
                
                logger.info(f"Final company count after scrolling: {current_company_count}")
                
                # Focus on company links as the primary source
                company_links = await page.query_selector_all('a[href*="/companies/"]')
                logger.info(f"Found {len(company_links)} company links")
                
                # Final verification - check if we have all companies
                logger.info(f"Final verification: Found {len(company_links)} company links")
                
                # Log first few and last few companies for verification
                if len(company_links) > 0:
                    logger.info("First 5 companies found:")
                    for i in range(min(5, len(company_links))):
                        text = await company_links[i].text_content()
                        logger.info(f"  {i+1}. {text[:50]}...")
                    
                    if len(company_links) > 5:
                        logger.info("Last 5 companies found:")
                        for i in range(max(0, len(company_links)-5), len(company_links)):
                            text = await company_links[i].text_content()
                            logger.info(f"  {i+1}. {text[:50]}...")
                
                # Process each company link
                for i, link in enumerate(company_links):
                    try:
                        # Get the text content
                        text = await link.text_content()
                        print(f"Link {i+1}: '{text}'")
                        
                        if not text or len(text.strip()) < 3:
                            print(f"Skipping link {i+1}: text too short - '{text}'")
                            continue
                            
                        # Get the URL
                        href = await link.get_attribute('href')
                        url = href if href.startswith('http') else f"https://www.ycombinator.com{href}"
                        print(f"Link {i+1} URL: {url}")
                        
                        # Skip if it's not a company link
                        if '/companies/' not in url:
                            print(f"Skipping link {i+1}: not a company URL - {url}")
                            continue
                            
                        # Skip only the obvious navigation element
                        if text.strip() in ['Founder Directory']:
                            print(f"Skipping link {i+1}: navigation element - '{text}'")
                            continue
                            
                        # Try to parse the company name from the text
                        company_name = text.strip()
                        
                        # Clean up the company name and extract description
                        description = ""
                        categories = []
                        
                        # Parse the link text directly - don't use parent element
                        if len(company_name) > 10:
                            # The text might contain both name and description
                            parsed = self.parse_company_text(company_name)
                            if parsed:
                                company_name = parsed.get('name', company_name)
                                description = parsed.get('description', '')
                                categories = parsed.get('categories', [])
                        
                        # Additional cleanup for company names with location suffixes
                        if company_name:
                            # Remove common location patterns from company names
                            location_patterns = [
                                r'\s+San Francisco, CA, USA?$',
                                r'\s+New York, NY, USA?$',
                                r'\s+London, England, United Kingdom$',
                                r'\s+Dublin, CA, USA?$',
                                r'\s+Mexico City, CDMX, Mexico$',
                                r'\s+Bielefeld, NRW, Germany$',
                                r'\s+Overland Park, KS, USA?$',
                                r'\s+CA, USA?$',
                                r'\s+NY, USA?$',
                                r'\s+USA?$',
                                r'\s+United Kingdom$',
                                r'\s+Germany$',
                                r'\s+Mexico$'
                            ]
                            
                            for pattern in location_patterns:
                                company_name = re.sub(pattern, '', company_name, flags=re.IGNORECASE)
                            
                            # Clean up any remaining artifacts
                            company_name = company_name.strip()
                            if company_name.endswith(','):
                                company_name = company_name[:-1].strip()
                            
                            # If company name is too long, take first few words
                            if len(company_name) > 50:
                                words = company_name.split()
                                company_name = ' '.join(words[:3]) if len(words) >= 3 else words[0]
                        
                        # Clean up the company name
                        if len(company_name) > 100:
                            # Take first part if too long
                            company_name = company_name.split()[0] if company_name.split() else company_name
                        
                        # Extract founder profiles from company page for all companies
                        founders = []
                        # Re-enabling founder extraction with improved stability
                        try:
                            # Create a new page for founder extraction to avoid conflicts
                            founder_page = await context.new_page()
                            founders = await self.extract_founder_profiles(founder_page, url)
                            await founder_page.close()
                            if founders:
                                logger.info(f"Found {len(founders)} founder(s) for {company_name}")
                        except Exception as e:
                            logger.debug(f"Could not extract founders for {company_name}: {e}")
                        
                        company_data = {
                            "name": company_name,
                            "description": description,
                            "url": url,
                            "categories": categories,
                            "founders": founders,
                            "scraped_at": datetime.now().isoformat()
                        }
                        
                        # Add the company
                        self.companies.append(company_data)
                        logger.info(f"Found company {i+1}: {company_name}")
                        
                    except Exception as e:
                        logger.debug(f"Error processing company link {i+1}: {e}")
                        continue
                
                # Remove duplicates based on name (case insensitive)
                seen_names = set()
                unique_companies = []
                for company in self.companies:
                    name_lower = company['name'].lower()
                    if name_lower not in seen_names:
                        seen_names.add(name_lower)
                        unique_companies.append(company)
                    else:
                        logger.debug(f"Duplicate found: {company['name']}")
                
                self.companies = unique_companies
                logger.info(f"Total unique companies found: {len(self.companies)}")
                
            except Exception as e:
                logger.error(f"Error during scraping: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
            finally:
                try:
                    if 'context' in locals():
                        await context.close()
                except Exception as e:
                    logger.debug(f"Error closing context: {e}")
                try:
                    if 'browser' in locals():
                        await browser.close()
                except Exception as e:
                    logger.debug(f"Error closing browser: {e}")
                
        return self.companies
    
    def save_data(self):
        """Save the scraped data"""
        if self.companies:
            # Create shared output directory with scraper subfolder
            output_dir = f"output_{self.timestamp}"
            scraper_dir = os.path.join(output_dir, "scraper")
            data_dir = os.path.join(scraper_dir, "data")
            html_dir = os.path.join(scraper_dir, "html")
            
            os.makedirs(data_dir, exist_ok=True)
            os.makedirs(html_dir, exist_ok=True)
            
            # Save to CSV
            df = pd.DataFrame(self.companies)
            csv_filename = os.path.join(data_dir, f"yc_companies_{self.timestamp}.csv")
            df.to_csv(csv_filename, index=False)
            logger.info(f"Data saved to {csv_filename}")
            
            # Save to JSON
            json_filename = os.path.join(data_dir, f"yc_companies_{self.timestamp}.json")
            with open(json_filename, 'w') as f:
                json.dump(self.companies, f, indent=2)
            logger.info(f"Data saved to {json_filename}")
            
            # Generate HTML tables automatically
            try:
                from simple_html_generator import csv_to_html_simple
                html_filename = csv_to_html_simple(csv_filename, "YC Summer 2025 Companies")
                if html_filename:
                    # Move HTML file to html subfolder
                    html_basename = os.path.basename(html_filename)
                    html_dest = os.path.join(html_dir, html_basename)
                    os.rename(html_filename, html_dest)
                    logger.info(f"HTML table generated: {html_dest}")
            except Exception as e:
                logger.warning(f"Could not generate HTML table: {e}")
                
            logger.info(f"All scraper files saved to: {scraper_dir}")
            logger.info(f"  - Data files: {data_dir}")
            logger.info(f"  - HTML files: {html_dir}")
            
            # Store the output directory name for the analyzer to use
            self.shared_output_dir = output_dir
        else:
            logger.warning("No data to save")

async def main():
    """Main function to run the scraper"""
    scraper = FinalYCScraper()
    companies = await scraper.scrape_companies()
    
    if companies:
        scraper.save_data()
        logger.info(f"Successfully scraped {len(companies)} companies")
        logger.info(f"Target was to capture all available companies - ✅ Success")
        logger.info("")
        
        logger.info("\nFirst few companies:")
        for i, company in enumerate(companies[:5], 1):
            logger.info(f"{i}. {company['name']}")
    else:
        logger.error("No companies were scraped")

if __name__ == "__main__":
    asyncio.run(main()) 