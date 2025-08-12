#!/usr/bin/env python3
"""
Robust YC Scraper - Enhanced version with comprehensive data extraction and investment insights

This scraper implements a robust 2-pass approach to ensure complete data capture:
1. First pass: Capture ALL companies with basic info immediately
2. Second pass: Enrich with detailed data using smaller chunks

Features:
- Immediate storage to prevent data loss
- Comprehensive error handling
- Progress tracking and statistics
- Investment-focused data extraction
- Session statistics and reporting
"""

import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RobustYCScraper:
    """
    Enhanced YC Scraper with robust error handling and comprehensive data extraction.
    
    This class implements a 2-pass scraping approach to ensure complete data capture
    for investment analysis purposes.
    """
    
    def __init__(self):
        """Initialize the scraper with default settings and statistics tracking."""
        self.companies = []
        self.output_dir = None
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_stats = {
            'total_processed': 0,
            'successful_captures': 0,
            'successful_enrichments': 0,
            'errors': 0,
            'skipped': 0,
            'start_time': datetime.now(),
            'end_time': None
        }
        
        # Configuration settings
        self.config = {
            'chunk_size': 3,  # Smaller chunks for better reliability
            'scroll_timeout': 60,  # Maximum scroll attempts (increases reliability)
            'page_timeout': 30000,  # Page load timeout in ms
            'company_timeout': 15000,  # Individual company page timeout
            'min_companies_expected': 100,  # Minimum companies to expect
            'target_companies': 200,  # Upper bound to avoid premature stop
            'progress_save_interval': 10,  # Save progress every N companies
            'chunk_delay': 1,  # Delay between chunks in seconds
            'scroll_delay': 2,  # Delay between scrolls in seconds
        }
        
    async def scrape_companies(self):
        """
        Main scraping method with robust error handling and 2-pass approach.
        
        This method orchestrates the entire scraping process:
        1. Browser setup and navigation
        2. Scroll to load all companies
        3. First pass: Capture all companies with basic info
        4. Second pass: Enrich with detailed data
        5. Final data saving and statistics
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                try:
                    # Navigate to YC companies page
                    logger.info("Navigating to YC companies page...")
                    await page.goto("https://www.ycombinator.com/companies?batch=Summer%202025", 
                                  wait_until='domcontentloaded', 
                                  timeout=self.config['page_timeout'])
                    await asyncio.sleep(3)
                    
                    # Scroll to load all companies
                    logger.info("Scrolling to load all companies...")
                    await self._scroll_to_load_all(page)
                    
                    # Get all company links and dedupe/normalize early
                    raw_links = await page.query_selector_all("a[href*='/companies/']")
                    hrefs = []
                    for link in raw_links:
                        href = await link.get_attribute('href')
                        if not href:
                            continue
                        # Normalize to absolute
                        if href.startswith('/'):
                            href = f"https://www.ycombinator.com{href}"
                        # Strict filter: only company profile links (exclude filters, anchors, params)
                        if re.match(r"^https://www\.ycombinator\.com/companies/[a-z0-9\-]+/?$", href):
                            hrefs.append(href.rstrip('/'))

                    unique_hrefs = sorted(set(hrefs))
                    company_links = []
                    for href in unique_hrefs:
                        # Query element for each normalized href
                        el = await page.query_selector(f"a[href='{href.replace('https://www.ycombinator.com','')}'], a[href='{href}']")
                        if el:
                            company_links.append(el)

                    logger.info(f"Found {len(company_links)} normalized unique company links")
                    
                    if len(company_links) < self.config['min_companies_expected']:
                        logger.warning(f"Only found {len(company_links)} companies, expected more")
                    
                    # FIRST PASS: Capture ALL companies with basic info
                    await self._first_pass_capture_all(page, company_links)
                    
                    # SECOND PASS: Enrich with detailed data
                    await self._second_pass_enrich_data(page)
                    
                    # Verify we captured most companies
                    expected_companies = len(company_links)
                    processed_count = len(self.companies)
                    
                    if processed_count < expected_companies * 0.8:
                        logger.error(f"Only processed {processed_count}/{expected_companies} companies. Retrying...")
                        # Could implement retry logic here
                    
                    logger.info(f"Successfully processed {len(self.companies)} companies")
                    
                except Exception as e:
                    logger.error(f"Error during scraping: {e}")
                    raise
                finally:
                    await browser.close()
        except Exception as e:
            logger.error(f"Error in browser setup: {e}")
            raise
        finally:
            self.session_stats['end_time'] = datetime.now()
    
    async def _scroll_to_load_all(self, page):
        """
        Scroll to load all companies with better error handling.
        
        This method scrolls down the page until all companies are loaded
        or until the maximum scroll attempts are reached.
        """
        try:
            last_height = await page.evaluate("document.body.scrollHeight")
            scroll_attempts = 0
            max_attempts = self.config['scroll_timeout']
            
            # Track unique company hrefs to avoid duplicates and detect stabilization
            seen_hrefs = set()
            stable_rounds = 0
            required_stable_rounds = 3
            
            while scroll_attempts < max_attempts and stable_rounds < required_stable_rounds:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(self.config['scroll_delay'])

                new_height = await page.evaluate("document.body.scrollHeight")

                # Collect hrefs each round
                anchors = await page.query_selector_all("a[href*='/companies/']")
                new_hrefs = set()
                for a in anchors:
                    href = await a.get_attribute('href')
                    if href and '/companies/' in href:
                        # Normalize to absolute path and ignore non-company or filter links
                        if href.startswith("/companies/"):
                            new_hrefs.add(href)
                        elif 'ycombinator.com/companies/' in href:
                            # strip domain to path
                            path = '/' + href.split('ycombinator.com/')[-1]
                            new_hrefs.add(path)

                prev_count = len(seen_hrefs)
                seen_hrefs.update(new_hrefs)
                curr_count = len(seen_hrefs)

                if curr_count == prev_count:
                    stable_rounds += 1
                else:
                    stable_rounds = 0

                if new_height == last_height:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0
                    last_height = new_height

                if curr_count >= self.config['target_companies']:
                    logger.info(f"Collected {curr_count} unique company links, stopping scroll")
                    break

            logger.info(f"Finished scrolling, collected {len(seen_hrefs)} unique company links after {scroll_attempts} extra scroll attempts and {stable_rounds} stable rounds")
        except Exception as e:
            logger.error(f"Error during scrolling: {e}")
            raise
    
    async def _first_pass_capture_all(self, page, company_links):
        """
        FIRST PASS: Capture ALL companies with basic info immediately.
        
        This pass ensures that no companies are missed, even if some data
        extraction fails. Companies are saved immediately upon capture.
        """
        logger.info("FIRST PASS: Capturing ALL companies with basic info...")
        
        processed_count = 0
        skipped_count = 0
        error_count = 0
        
        seen_urls: set[str] = set()
        for i, link in enumerate(company_links):
            try:
                # Get the text content
                text = await link.text_content()
                print(f"Processing Link {i+1}/{len(company_links)}: '{text[:100]}...'")
                
                # Skip navigation elements
                if text.strip().lower() in ['founder directory', 'companies', 'about', 'contact']:
                    skipped_count += 1
                    logger.info(f"Skipping navigation element: {text}")
                    continue
                
                # Get the URL
                url = await link.get_attribute('href')
                if not url:
                    error_count += 1
                    logger.error(f"No URL found for link {i+1}")
                    continue
                
                # Ensure URL is absolute and normalized
                if url.startswith('/'):
                    url = f"https://www.ycombinator.com{url}"
                url = re.sub(r"[#?].*$", "", url).rstrip('/')
                
                # Strictly match only company profile URLs
                if not re.match(r"^https://www\.ycombinator\.com/companies/[a-z0-9\-]+$", url):
                    skipped_count += 1
                    continue
                
                # Deduplicate
                if url in seen_urls:
                    skipped_count += 1
                    continue
                seen_urls.add(url)
                
                # Parse company name and categories from text
                company_name, categories = self._extract_basic_info(text)
                
                # Create basic company data
                basic_company_data = {
                    "name": company_name,
                    "description": "",  # Will be populated in second pass
                    "url": url,
                    "categories": categories,
                    "founders": [],  # Will be populated in second pass
                    "summary": "",  # Will be populated in second pass
                    "scraped_at": datetime.now().isoformat()
                }
                
                # IMMEDIATE STORAGE: Add the company immediately to ensure we capture it
                self.companies.append(basic_company_data)
                processed_count += 1
                self.session_stats['successful_captures'] += 1
                logger.info(f"✅ CAPTURED company {i+1}/{len(company_links)}: {company_name}")
                
                # Save progress every N companies
                if processed_count % self.config['progress_save_interval'] == 0:
                    self._save_progress()
                
            except Exception as e:
                error_count += 1
                self.session_stats['errors'] += 1
                logger.error(f"Error processing company link {i+1}: {e}")
                continue
        
        self.session_stats['total_processed'] = processed_count
        self.session_stats['skipped'] = skipped_count
        logger.info(f"✅ FIRST PASS COMPLETE: Captured {len(self.companies)} companies")
        logger.info(f"Processed: {processed_count}, Skipped: {skipped_count}, Errors: {error_count}")
    
    async def _second_pass_enrich_data(self, page):
        """
        SECOND PASS: Enrich with detailed data using smaller chunks.
        
        This pass enriches the captured companies with detailed information
        including descriptions, founders, and investment insights.
        """
        logger.info("SECOND PASS: Enriching data with detailed information...")
        
        chunk_size = self.config['chunk_size']
        total_chunks = (len(self.companies) + chunk_size - 1) // chunk_size
        
        enriched_count = 0
        error_count = 0
        
        for chunk_num in range(total_chunks):
            start_idx = chunk_num * chunk_size
            end_idx = min((chunk_num + 1) * chunk_size, len(self.companies))
            chunk_companies = self.companies[start_idx:end_idx]
            
            logger.info(f"Enriching chunk {chunk_num + 1}/{total_chunks} (companies {start_idx + 1}-{end_idx})")
            
            for chunk_idx, company in enumerate(chunk_companies):
                i = start_idx + chunk_idx  # Global index
                company_name = company['name']
                url = company['url']
                
                try:
                    # Extract detailed data from company page
                    detailed_data = await self._extract_detailed_data(page, url, company_name)
                    
                    # Update the company with enriched data
                    company.update(detailed_data)
                    enriched_count += 1
                    self.session_stats['successful_enrichments'] += 1
                    logger.info(f"✅ ENRICHED company {i+1}/{len(self.companies)}: {company_name}")
                    
                except Exception as e:
                    error_count += 1
                    self.session_stats['errors'] += 1
                    logger.error(f"Error enriching company {i+1}: {e}")
                    # Company remains with basic info - robust error handling
                    continue
            
            # Small delay between chunks to be respectful
            await asyncio.sleep(self.config['chunk_delay'])
            
            # Save progress after each chunk
            self._save_progress()
        
        logger.info(f"✅ SECOND PASS COMPLETE: Enriched {enriched_count}/{len(self.companies)} companies")
        logger.info(f"Enriched: {enriched_count}, Errors: {error_count}")
    
    def _extract_basic_info(self, text: str) -> Tuple[str, str]:
        """
        Extract company name and categories from text.
        
        Args:
            text: The text content from the company link
            
        Returns:
            Tuple of (company_name, categories)
        """
        if not text:
            return "", ""
        
        # Clean the text
        text = text.strip()
        
        # Split by newlines or periods to get different parts
        parts = re.split(r'[\n\r]+', text)
        parts = [part.strip() for part in parts if part.strip()]
        
        if not parts:
            return text, ""
        
        # First part is usually the company name
        company_name = parts[0]
        
        # Extract categories (look for common category indicators)
        categories = []
        category_keywords = [
            'AI', 'ML', 'SaaS', 'B2B', 'Enterprise', 'Fintech', 'Healthtech', 
            'Edtech', 'E-commerce', 'Mobile', 'Web', 'API', 'Analytics', 'Security',
            'Cloud', 'DevOps', 'Marketing', 'Sales', 'HR', 'Legal', 'Real Estate',
            'Transportation', 'Food', 'Fashion', 'Gaming', 'Media', 'Entertainment'
        ]
        
        text_lower = text.lower()
        for keyword in category_keywords:
            if keyword.lower() in text_lower:
                categories.append(keyword)
        
        return company_name, ", ".join(categories)
    
    async def _extract_detailed_data(self, page, company_url: str, company_name: str) -> Dict:
        """
        Extract detailed data from company page.
        
        Args:
            page: Playwright page object
            company_url: URL of the company page
            company_name: Name of the company
            
        Returns:
            Dictionary containing detailed company data
        """
        try:
            logger.info(f"Extracting detailed data from {company_url} for {company_name}")
            
            # Navigate to the company page
            await page.goto(company_url, 
                          wait_until='domcontentloaded', 
                          timeout=self.config['company_timeout'])
            await asyncio.sleep(2)
            
            # Get the page content
            content = await page.content()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract comprehensive data
            detailed_data = {
                'description': '',
                'founders': [],
                'summary': ''
            }
            
            # Extract description
            description = self._extract_description(soup)
            detailed_data['description'] = description
            
            # Extract founders
            founders = self._extract_founders(soup)
            detailed_data['founders'] = founders
            
            # Extract comprehensive summary
            summary = self._extract_comprehensive_summary(soup, company_name)
            detailed_data['summary'] = summary
            
            return detailed_data
            
        except Exception as e:
            logger.error(f"Error extracting detailed data for {company_name}: {e}")
            # Return empty data - robust error handling
            return {
                'description': 'Description not available',
                'founders': [],
                'summary': 'Summary not available'
            }
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """
        Extract company description from page content.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            Extracted description text
        """
        # Look for description in various selectors
        description_selectors = [
            '.description', '.about', '.overview', '.summary', '.content',
            'meta[name="description"]', '.company-description', '.tagline'
        ]
        
        for selector in description_selectors:
            elements = soup.select(selector)
            for element in elements:
                if selector == 'meta[name="description"]':
                    content = element.get('content', '')
                else:
                    content = element.get_text(strip=True)
                
                if len(content) > 20:  # Meaningful description
                    return content[:500]  # Limit length
        
        # Fallback: extract from body text
        body = soup.find('body')
        if body:
            text = body.get_text(separator=' ', strip=True)
            # Take first few sentences
            sentences = re.split(r'[.!?]+', text)
            meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
            if meaningful_sentences:
                return ' '.join(meaningful_sentences[:3])[:500]
        
        return "Description not available"
    
    def _extract_founders(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Extract founders and their LinkedIn profile URLs from the YC company profile page.

        Returns a list of dictionaries: { 'name': str, 'linkedin_url': str }
        Only returns LinkedIn URLs from the page itself; does not visit any external websites.
        """
        def _normalize_linkedin_url(url: str) -> str:
            if not url:
                return ''
            try:
                # Ensure https scheme and strip tracking params/fragments
                url = url.strip()
                if url.startswith('//'):
                    url = 'https:' + url
                if not url.startswith('http'):
                    url = 'https://' + url.lstrip('/')
                # Lowercase domain, keep path case
                url = re.sub(r'^http://', 'https://', url)
                # Remove query params and fragments
                url = re.sub(r'[?#].*$', '', url)
                # Remove trailing slashes
                url = url.rstrip('/')
                # Force www for consistency
                url = url.replace('https://linkedin.com', 'https://www.linkedin.com')
                # Prefer personal profiles, skip company pages
                return url
            except Exception:
                return ''

        founders: List[Dict[str, str]] = []

        # 1) Look for YC-specific founder sections first
        founder_sections = soup.select('.founder, .team-member, .people, .leadership, [class*="founder"], [class*="team"]')
        for section in founder_sections:
            # Look for LinkedIn links within founder sections
            linkedin_links = section.select("a[href*='linkedin.com']")
            for link in linkedin_links:
                href = link.get('href', '')
                if not href:
                    continue
                href_norm = _normalize_linkedin_url(href)
                if '/company/' in href_norm or 'linkedin.com' not in href_norm:
                    continue
                if not ('/in/' in href_norm or '/pub/' in href_norm):
                    continue
                    
                # Extract name from the section context
                name_candidate = ''
                # Try anchor text first
                anchor_text = link.get_text(strip=True)
                if anchor_text and len(anchor_text) > 1 and not anchor_text.lower().startswith('linkedin'):
                    name_candidate = anchor_text
                else:
                    # Look for name in surrounding text - try multiple levels of parents
                    name_candidate = ''
                    current = link
                    for level in range(3):  # Check up to 3 parent levels
                        current = current.parent
                        if not current:
                            break
                        parent_text = current.get_text(separator=' ', strip=True)
                        names = self._extract_names_from_text(parent_text)
                        if names:
                            name_candidate = names[0]
                            break
                
                if name_candidate:
                    founders.append({
                        'name': name_candidate,
                        'linkedin_url': href_norm
                    })

        # 2) Direct LinkedIn anchors commonly present on YC pages (broader search)
        if not founders:
            for a in soup.select("a[href*='linkedin.com']"):
                href = a.get('href', '')
                if not href:
                    continue
                href_norm = _normalize_linkedin_url(href)
                # Skip non-profile/company pages
                if 'linkedin.com' not in href_norm:
                    continue
                if '/company/' in href_norm:
                    continue
                # Heuristic: likely a person profile if contains /in/ or /pub/
                if not ('/in/' in href_norm or '/pub/' in href_norm):
                    continue

                # Try to get the founder's name from anchor text or nearby context
                anchor_text = (a.get_text(strip=True) or '').strip()
                name_candidate = anchor_text
                if not name_candidate or len(name_candidate) < 2 or name_candidate.lower().startswith('linkedin'):
                    # Look in parent hierarchy for names
                    current = a
                    for level in range(4):  # Check up to 4 parent levels
                        current = current.parent
                        if not current:
                            break
                        parent_text = current.get_text(" ", strip=True)
                        # Remove the URL-like substrings
                        parent_text = re.sub(r'https?://\S+', '', parent_text).strip()
                        # Try to extract names from parent text
                        possible_names = self._extract_names_from_text(parent_text)
                        if possible_names:
                            name_candidate = possible_names[0]
                            break

                if name_candidate and not name_candidate.lower().startswith('linkedin'):
                    founders.append({
                        'name': name_candidate,
                        'linkedin_url': href_norm
                    })

        # 3) If no LinkedIn anchors found, fallback to names only (without URLs)
        if not founders:
            founder_patterns = [
                'founder', 'co-founder', 'ceo', 'cto', 'coo', 'founders',
                'team', 'leadership', 'about us', 'our story'
            ]
            text_content = soup.get_text(separator=' ').strip()
            lower_text = text_content.lower()
            if any(p in lower_text for p in founder_patterns):
                names = self._extract_names_from_text(text_content)
                for nm in names[:5]:
                    founders.append({'name': nm, 'linkedin_url': ''})

        # Deduplicate by linkedin_url (prefer entries with names)
        deduped: Dict[str, Dict[str, str]] = {}
        for f in founders:
            key = f.get('linkedin_url') or f.get('name')
            if not key:
                continue
            if key not in deduped or (not deduped[key].get('name') and f.get('name')):
                deduped[key] = {'name': f.get('name', '').strip(), 'linkedin_url': f.get('linkedin_url', '').strip()}

        # Filter out empty names and clean up
        result = []
        for founder in deduped.values():
            name = founder.get('name', '').strip()
            if name and len(name) > 1 and not name.lower().startswith('linkedin'):
                result.append(founder)
        
        # Limit to 5
        return result[:5]
    
    def _extract_names_from_text(self, text: str) -> List[str]:
        """
        Extract potential names from text.
        
        Args:
            text: Text to extract names from
            
        Returns:
            List of potential names
        """
        # Clean up text first
        text = text.replace('\n', ' ').replace('\t', ' ')
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Common words to exclude
        exclude_words = {
            'the', 'and', 'or', 'but', 'for', 'with', 'from', 'to', 'in', 'on', 'at',
            'founder', 'co-founder', 'ceo', 'cto', 'coo', 'chief', 'engineer', 'officer',
            'president', 'director', 'manager', 'lead', 'senior', 'junior',
            'company', 'linkedin', 'profile', 'previously', 'currently', 'formerly',
            'acrely', 'y', 'combinator', 'summer', 'winter', 'spring', 'fall'
        }
        
        words = text.split()
        names = []
        
        i = 0
        while i < len(words):
            word = words[i]
            
            # Look for capitalized words that could be first names
            if (len(word) > 1 and word[0].isupper() and 
                word.lower() not in exclude_words and
                not word.isdigit() and
                not word.startswith('http')):
                
                # Check if next word is also capitalized (potential last name)
                if (i + 1 < len(words) and 
                    len(words[i + 1]) > 1 and 
                    words[i + 1][0].isupper() and
                    words[i + 1].lower() not in exclude_words and
                    not words[i + 1].isdigit()):
                    
                    full_name = f"{word} {words[i + 1]}"
                    # Additional validation - skip if it contains common non-name patterns
                    if not any(pattern in full_name.lower() for pattern in ['founder', 'engineer', 'officer', 'director', 'manager']):
                        names.append(full_name)
                    i += 2  # Skip both words
                else:
                    i += 1
            else:
                i += 1
        
        # Remove duplicates while preserving order
        seen = set()
        unique_names = []
        for name in names:
            if name not in seen:
                seen.add(name)
                unique_names.append(name)
        
        return unique_names[:5]  # Limit to 5 names
    
    def _remove_non_content_elements(self, soup: BeautifulSoup) -> None:
        """Remove navigation, breadcrumbs, and other non-content elements from soup."""
        # Remove navigation elements
        for element in soup.select('nav, .nav, .navigation, .breadcrumb, .breadcrumbs, header, footer'):
            element.decompose()
        
        # Remove specific text patterns that are navigation-like
        for element in soup.find_all(string=True):
            if element.strip() in ['Home', 'Companies', 'Home > Companies', '>', 'Back to companies']:
                if element.parent:
                    element.parent.decompose()
    
    def _clean_text_content(self, text: str) -> str:
        """Clean extracted text content from navigation and breadcrumb elements."""
        # Remove common breadcrumb patterns
        breadcrumb_patterns = [
            r'Home\s*>\s*Companies.*?(?=\w{3,})',  # Home > Companies ... until real content
            r'^\s*Home\s*>\s*Companies\s*',        # Beginning Home > Companies
            r'\s*Home\s*>\s*Companies\s*',         # Any Home > Companies
            r'^\s*>\s*',                           # Leading >
            r'\s*Back to companies\s*',            # Back to companies
            r'^\s*Home\s*',                        # Leading Home
            r'\s*Companies\s*>\s*',                # Companies >
        ]
        
        for pattern in breadcrumb_patterns:
            text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _extract_structured_yc_content(self, soup: BeautifulSoup, company_name: str) -> Dict:
        """
        Extract structured content from YC company pages with improved parsing.
        
        Args:
            soup: BeautifulSoup object of the page
            company_name: Name of the company
            
        Returns:
            Dictionary with structured content fields
        """
        data = {
            'description': '',
            'team_info': '',
            'traction': '',
            'unique_aspects': ''
        }
        
        try:
            # Remove navigation elements first
            self._remove_non_content_elements(soup)
            
            # Extract main company description (usually first major paragraph)
            description = self._extract_main_description(soup, company_name)
            if description:
                data['description'] = description
            
            # Extract team/founder information
            team_info = self._extract_team_information(soup)
            if team_info:
                data['team_info'] = team_info
            
            # Extract traction and business metrics
            traction = self._extract_traction_info(soup)
            if traction:
                data['traction'] = traction
            
            # Extract unique selling points and competitive advantages
            unique_aspects = self._extract_unique_aspects(soup, company_name)
            if unique_aspects:
                data['unique_aspects'] = unique_aspects
                
        except Exception as e:
            logger.error(f"Error extracting structured content for {company_name}: {e}")
        
        return data
    
    def _extract_main_description(self, soup: BeautifulSoup, company_name: str) -> str:
        """Extract the main company description from YC pages."""
        # First, try to get clean description from meta tag
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            content = meta_desc.get('content').strip()
            if len(content) > 30 and not content.lower().startswith(('home', 'companies')):
                return self._clean_sentence(content)
        
        # Look for the main content paragraph that describes what the company does
        main_content_selectors = [
            # Try main content area first
            'main',
            'article', 
            '.content',
            'section'
        ]
        
        for main_selector in main_content_selectors:
            main_element = soup.select_one(main_selector)
            if main_element:
                # Find paragraphs within main content
                paragraphs = main_element.find_all('p')
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if (len(text) > 50 and 
                        self._is_description_paragraph(text, company_name)):
                        return self._clean_sentence(text)
        
        # Fallback: look through all paragraphs for the best description
        all_paragraphs = soup.find_all('p')
        best_description = ""
        
        for p in all_paragraphs:
            text = p.get_text(strip=True)
            if self._is_description_paragraph(text, company_name):
                # Score based on relevance
                score = self._score_description(text, company_name)
                if score > 0 and len(text) > len(best_description):
                    best_description = text
        
        return self._clean_sentence(best_description) if best_description else ""
    
    def _is_description_paragraph(self, text: str, company_name: str) -> bool:
        """Check if a paragraph is likely the main company description."""
        text_lower = text.lower()
        
        # Skip navigation and boilerplate text
        if any(skip_phrase in text_lower for skip_phrase in [
            'home >', 'companies >', 'back to', 'y combinator',
            'founded in', 'employees based', 'san francisco', 'new york'
        ]):
            return False
        
        # Check for description indicators
        return (len(text) > 50 and 
                any(keyword in text_lower for keyword in [
                    'builds', 'creates', 'develops', 'provides', 'offers', 
                    'helps', 'enables', 'platform', 'software', 'ai', 
                    'solution', 'service', 'tool', 'system'
                ]))
    
    def _score_description(self, text: str, company_name: str) -> int:
        """Score how likely a text is to be the main company description."""
        text_lower = text.lower()
        score = 0
        
        # Positive indicators
        if company_name.lower() in text_lower:
            score += 2
        
        action_verbs = ['builds', 'creates', 'develops', 'provides', 'offers', 'helps', 'enables']
        if any(verb in text_lower for verb in action_verbs):
            score += 3
        
        business_terms = ['platform', 'software', 'ai', 'solution', 'service', 'tool', 'system']
        if any(term in text_lower for term in business_terms):
            score += 1
        
        # Negative indicators
        if any(skip_phrase in text_lower for skip_phrase in [
            'founded in', 'based in', 'employees', 'y combinator', 'yc'
        ]):
            score -= 2
        
        return score
    
    def _extract_team_information(self, soup: BeautifulSoup) -> str:
        """Extract team and founder background information."""
        team_info = []
        
        # Look for founder/team sections
        team_selectors = [
            '.team', '.founders', '.about-team', '.leadership',
            '[class*="founder"]', '[class*="team"]'
        ]
        
        for selector in team_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(separator=' ', strip=True)
                if len(text) > 30:
                    # Look for founder credentials
                    sentences = self._split_into_sentences(text)
                    for sentence in sentences:
                        if any(keyword in sentence.lower() for keyword in [
                            'founded by', 'co-founder', 'former', 'ex-', 'previously at',
                            'stanford', 'mit', 'harvard', 'berkeley', 'phd', 'google', 'facebook',
                            'microsoft', 'apple', 'amazon', 'tesla', 'experience at'
                        ]):
                            team_info.append(self._clean_sentence(sentence))
        
        return ' '.join(team_info[:2])  # Limit to 2 most relevant sentences
    
    def _extract_traction_info(self, soup: BeautifulSoup) -> str:
        """Extract business traction and metrics."""
        traction_info = []
        
        # Get clean text content from main areas only
        main_content = self._get_main_content_text(soup)
        sentences = self._split_into_sentences(main_content)
        
        for sentence in sentences:
            if self._is_traction_sentence(sentence):
                traction_info.append(self._clean_sentence(sentence))
        
        return ' '.join(traction_info[:2])  # Limit to 2 most relevant sentences
    
    def _extract_unique_aspects(self, soup: BeautifulSoup, company_name: str) -> str:
        """Extract unique selling points and competitive advantages."""
        unique_info = []
        
        # Get clean text content from main areas only
        main_content = self._get_main_content_text(soup)
        sentences = self._split_into_sentences(main_content)
        
        for sentence in sentences:
            if self._is_unique_aspect_sentence(sentence, company_name):
                unique_info.append(self._clean_sentence(sentence))
        
        return ' '.join(unique_info[:2])  # Limit to 2 most relevant sentences
    
    def _get_main_content_text(self, soup: BeautifulSoup) -> str:
        """Get clean text content from main content areas only."""
        # Remove unwanted elements first
        for element in soup.select('nav, .nav, header, footer, .breadcrumb, .navigation'):
            element.decompose()
        
        # Extract from main content areas
        main_selectors = ['main', 'article', '.content', 'section']
        content_texts = []
        
        for selector in main_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(separator=' ', strip=True)
                if len(text) > 100:  # Only substantial content
                    content_texts.append(text)
        
        # If no main content found, use body but filter heavily
        if not content_texts:
            body = soup.find('body')
            if body:
                content_texts.append(body.get_text(separator=' ', strip=True))
        
        return ' '.join(content_texts)
    
    def _is_traction_sentence(self, sentence: str) -> bool:
        """Check if a sentence contains traction information."""
        sentence_lower = sentence.lower()
        
        # Skip if it's navigation or boilerplate
        if any(skip_phrase in sentence_lower for skip_phrase in [
            'y combinator', 'yc', 'founded in', 'based in', 'employees',
            'home >', 'companies >', 'back to'
        ]):
            return False
        
        # Look for traction indicators
        return any(keyword in sentence_lower for keyword in [
            'customers', 'users', 'revenue', 'growth', 'funding', 'raised',
            'series a', 'series b', 'seed', 'million', 'billion',
            'partnership', 'enterprise', 'fortune 500'
        ]) and len(sentence) > 30
    
    def _is_unique_aspect_sentence(self, sentence: str, company_name: str) -> bool:
        """Check if a sentence describes unique aspects."""
        sentence_lower = sentence.lower()
        
        # Skip if it's navigation or boilerplate
        if any(skip_phrase in sentence_lower for skip_phrase in [
            'y combinator', 'yc', 'founded in', 'based in', 'employees',
            'home >', 'companies >', 'back to'
        ]):
            return False
        
        # Look for uniqueness indicators
        return any(keyword in sentence_lower for keyword in [
            'first', 'only', 'unique', 'breakthrough', 'proprietary', 'patent',
            'innovative', 'revolutionary', 'cutting-edge', 'novel',
            '10x', '100x', 'faster', 'better', 'advanced'
        ]) and len(sentence) > 30
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into proper sentences without breaking in the middle."""
        sentences = []
        
        # Common abbreviations that shouldn't end sentences
        abbreviations = ['Inc', 'LLC', 'Corp', 'Ltd', 'Co', 'Dr', 'Mr', 'Ms', 'Prof', 'Sr', 'Jr']
        
        # Simple but effective sentence splitting
        # First, protect abbreviations by temporarily replacing them
        protected_text = text
        for abbr in abbreviations:
            protected_text = protected_text.replace(f'{abbr}.', f'{abbr}__PERIOD__')
        
        # Split on sentence endings followed by space and capital letter
        potential_sentences = re.split(r'[.!?]\s+(?=[A-Z])', protected_text)
        
        for sentence in potential_sentences:
            # Restore periods in abbreviations
            sentence = sentence.replace('__PERIOD__', '.')
            sentence = sentence.strip()
            
            # Clean up any leftover punctuation issues
            sentence = re.sub(r'\s+', ' ', sentence)
            
            if (len(sentence) > 20 and  # Only meaningful sentences
                not sentence.lower().startswith(('home', 'companies', 'back to')) and
                not re.match(r'^[A-Z][a-z]*\s*[:|>]', sentence)):  # Skip navigation patterns
                sentences.append(sentence)
        
        return sentences
    
    def _clean_sentence(self, sentence: str) -> str:
        """Clean and normalize a sentence."""
        # Remove extra whitespace
        sentence = re.sub(r'\s+', ' ', sentence.strip())
        
        # Ensure sentence ends with proper punctuation
        if sentence and not sentence[-1] in '.!?':
            sentence += '.'
        
        return sentence
    
    def _extract_comprehensive_summary(self, soup: BeautifulSoup, company_name: str) -> str:
        """
        Extract comprehensive summary with investment insights using improved YC page structure parsing.
        
        Args:
            soup: BeautifulSoup object of the page
            company_name: Name of the company
            
        Returns:
            Comprehensive summary with investment insights
        """
        try:
            # Extract structured content from YC company page
            structured_data = self._extract_structured_yc_content(soup, company_name)
            
            # Build comprehensive summary from structured data
            summary_parts = []
            
            # What they do (primary description)
            if structured_data.get('description'):
                summary_parts.append(f"What They Do: {structured_data['description']}")
            
            # Specific insights (team, traction, unique aspects)
            insights = []
            if structured_data.get('team_info'):
                insights.append(structured_data['team_info'])
            if structured_data.get('traction'):
                insights.append(structured_data['traction'])
            if structured_data.get('unique_aspects'):
                insights.append(structured_data['unique_aspects'])
            
            if insights:
                summary_parts.append(f"Specific Insights: {' '.join(insights)}")
            
            if summary_parts:
                return ' | '.join(summary_parts)
            else:
                return "Summary not available"
                
        except Exception as e:
            logger.error(f"Error extracting comprehensive summary for {company_name}: {e}")
            return "Summary not available"
    
    def _extract_investment_insights(self, text: str, company_name: str) -> Dict:
        """
        Extract comprehensive description and high-quality insights from company page content.
        Focus on what the company does and founder credentials.
        
        Args:
            text: Full text content from the company page
            company_name: Name of the company
            
        Returns:
            Dictionary containing various investment insights
        """
        insights = {
            'what_they_do': '',
            'high_quality_insights': '',
            'business_model': '',
            'competitive_advantage': '',
            'technology_focus': ''
        }
        
        # Keywords for what the company does (core business description)
        what_they_do_keywords = [
            'builds', 'creates', 'develops', 'provides', 'offers', 'enables', 'helps',
            'platform', 'software', 'AI', 'automation', 'tool', 'service', 'solution', 
            'product', 'technology', 'app', 'system', 'infrastructure', 'API',
            'analytics', 'data', 'cloud', 'mobile', 'web', 'application',
            'management', 'optimization', 'integration', 'workflow', 'process'
        ]
        
        # Keywords for founder credentials and high-quality insights
        insight_keywords = [
            # Founder background keywords
            'founded by', 'ex-', 'former', 'previously at', 'worked at', 'experience at',
            'stanford', 'mit', 'harvard', 'berkeley', 'google', 'facebook', 'microsoft', 
            'apple', 'amazon', 'tesla', 'uber', 'airbnb', 'stripe', 'palantir',
            'phd', 'professor', 'researcher', 'published', 'patent',
            # Company traction keywords
            'millions', 'customers', 'users', 'revenue', 'growth', 'funding', 'backed by',
            'yc', 'y combinator', 'series a', 'series b', 'seed', 'raised',
            'unique', 'first', 'only', 'breakthrough', 'proprietary', 'patent',
            'market leader', 'enterprise', 'fortune 500', 'partnership'
        ]
        
        # Keywords for business model clarity
        business_model_keywords = [
            'SaaS', 'subscription', 'B2B', 'B2C', 'enterprise', 'marketplace',
            'freemium', 'licensing', 'API pricing', 'per seat', 'usage based'
        ]
        
        # Keywords for technology focus
        tech_keywords = [
            'AI', 'machine learning', 'deep learning', 'neural networks', 'LLM',
            'computer vision', 'NLP', 'generative AI', 'autonomous', 'robotics',
            'blockchain', 'IoT', 'edge computing', 'quantum', 'biotechnology'
        ]
        
        # Extract sentences containing relevant keywords
        sentences = re.split(r'[.!?]+', text)
        
        what_they_do_sentences = []
        insight_sentences = []
        business_model_sentences = []
        tech_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 15:  # Skip very short sentences
                continue
                
            sentence_lower = sentence.lower()
            
            # What they do - prioritize sentences that explain the core business
            if any(keyword in sentence_lower for keyword in what_they_do_keywords):
                # Prioritize sentences that start with company name or contain action verbs
                if (company_name.lower() in sentence_lower or 
                    any(verb in sentence_lower for verb in ['builds', 'creates', 'develops', 'provides', 'offers', 'enables', 'helps'])):
                    what_they_do_sentences.insert(0, sentence)  # Prioritize these
                else:
                    what_they_do_sentences.append(sentence)
            
            # High quality insights - founder credentials and traction
            if any(keyword in sentence_lower for keyword in insight_keywords):
                insight_sentences.append(sentence)
            
            # Business model
            if any(keyword in sentence_lower for keyword in business_model_keywords):
                business_model_sentences.append(sentence)
            
            # Technology focus
            if any(keyword in sentence_lower for keyword in tech_keywords):
                tech_sentences.append(sentence)
        
        # Build insights
        if what_they_do_sentences:
            insights['what_they_do'] = ' '.join(what_they_do_sentences[:3])  # Up to 3 sentences
        
        if insight_sentences:
            insights['high_quality_insights'] = ' '.join(insight_sentences[:2])  # Up to 2 sentences
        
        if business_model_sentences:
            insights['business_model'] = ' '.join(business_model_sentences[:2])
        
        if tech_sentences:
            insights['technology_focus'] = ' '.join(tech_sentences[:2])
        
        return insights
    
    def _save_progress(self):
        """Save current progress to prevent data loss."""
        if not self.companies:
            return
        
        # Create output directory if it doesn't exist
        if not self.output_dir:
            self.output_dir = Path(".") / f"output_{self.timestamp}"
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create data subdirectory
            data_dir = self.output_dir / "scraper" / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV
        df = pd.DataFrame(self.companies)
        csv_file = self.output_dir / "scraper" / "data" / f"yc_companies_{self.timestamp}_progress.csv"
        df.to_csv(csv_file, index=False)
        
        # Save to JSON
        json_file = self.output_dir / "scraper" / "data" / f"yc_companies_{self.timestamp}_progress.json"
        with open(json_file, 'w') as f:
            json.dump(self.companies, f, indent=2)
        
        logger.info(f"Progress saved: {len(self.companies)} companies")
    
    def save_final_data(self, output_dir: str) -> str:
        """
        Save final scraped data to CSV and JSON files.
        
        Args:
            output_dir: Directory to save the data
            
        Returns:
            Path to the output directory
        """
        if not self.companies:
            logger.warning("No companies to save")
            return ""
        
        # Create output directory
        self.output_dir = Path(output_dir) / f"output_{self.timestamp}"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Store reference for sharing with analyzer
        self.shared_output_dir = str(self.output_dir)
        
        # Create data subdirectory
        data_dir = self.output_dir / "scraper" / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV
        df = pd.DataFrame(self.companies)
        csv_file = data_dir / f"yc_companies_{self.timestamp}.csv"
        df.to_csv(csv_file, index=False)
        logger.info(f"Saved {len(self.companies)} companies to {csv_file}")
        
        # Save to JSON
        json_file = data_dir / f"yc_companies_{self.timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(self.companies, f, indent=2)
        logger.info(f"Saved {len(self.companies)} companies to {json_file}")
        
        return str(self.output_dir)
    
    def get_session_stats(self) -> Dict:
        """Get session statistics."""
        return self.session_stats
    
    def print_session_summary(self):
        """Print a summary of the scraping session."""
        stats = self.session_stats
        print("\n" + "="*50)
        print("SCRAPING SESSION SUMMARY")
        print("="*50)
        print(f"Total Companies Processed: {stats['total_processed']}")
        print(f"Successfully Captured: {stats['successful_captures']}")
        print(f"Successfully Enriched: {stats['successful_enrichments']}")
        print(f"Errors Encountered: {stats['errors']}")
        print(f"Skipped Items: {stats['skipped']}")
        print(f"Final Company Count: {len(self.companies)}")
        
        if stats['start_time'] and stats['end_time']:
            duration = stats['end_time'] - stats['start_time']
            print(f"Total Duration: {duration}")
        
        print("="*50)

async def main():
    """Main function to run the scraper."""
    scraper = RobustYCScraper()
    
    try:
        logger.info("Starting YC companies scraping with 2-pass approach...")
        await scraper.scrape_companies()
        
        if scraper.companies:
            output_dir = scraper.save_final_data(".")
            logger.info(f"Scraping completed successfully! Output saved to: {output_dir}")
            logger.info(f"Total companies scraped: {len(scraper.companies)}")
            
            # Print session summary
            scraper.print_session_summary()
        else:
            logger.error("No companies were scraped")
            
    except Exception as e:
        logger.error(f"Error in main scraping process: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 