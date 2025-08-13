#!/usr/bin/env python3
"""
Company Research Tool
Comprehensive research module for deep company analysis using multiple data sources
"""

import asyncio
import json
import logging
import os
import re
import requests
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
import aiohttp
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompanyResearcher:
    """Comprehensive company research tool using multiple data sources"""
    
    def __init__(self):
        self.research_data = {}
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = None  # Will be set when we know the company name
        
    async def research_company(self, company_name: str, company_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Conduct comprehensive research on a company using multiple sources
        
        Args:
            company_name: Name of the company to research
            company_url: Optional company website URL
            
        Returns:
            Dict containing all research findings
        """
        logger.info(f"🔍 Starting comprehensive research for: {company_name}")
        
        # Create output directory with format: research_companyName_date
        company_name_clean = company_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        date_str = datetime.now().strftime("%Y%m%d")
        self.output_dir = f"research_{company_name_clean}_{date_str}"
        os.makedirs(self.output_dir, exist_ok=True)
        
        research_results = {
            "company_name": company_name,
            "company_url": company_url,
            "research_timestamp": self.timestamp,
            "sources": {}
        }
        
        # Initialize all research tasks
        tasks = [
            self._research_linkedin(company_name),
            self._research_techcrunch(company_name),
            self._research_crunchbase(company_name),
            self._research_github(company_name),
            self._research_npm(company_name),
            self._research_web_presence(company_name, company_url),
            self._research_social_media(company_name),
            self._research_news_coverage(company_name)
        ]
        
        # Execute all research tasks in parallel
        logger.info("🚀 Executing parallel research across all sources...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        source_names = ["linkedin", "techcrunch", "crunchbase", "github", "npm", "web_presence", "social_media", "news"]
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ Error in {source_names[i]} research: {result}")
                research_results["sources"][source_names[i]] = {"error": str(result)}
            else:
                research_results["sources"][source_names[i]] = result
        
        # Generate comprehensive insights
        research_results["insights"] = self._generate_insights(research_results)
        
        # Save research report
        report_path = os.path.join(self.output_dir, f"{company_name.replace(' ', '_')}_research_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(research_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Research completed! Report saved to: {report_path}")
        return research_results
    
    async def _research_linkedin(self, company_name: str) -> Dict[str, Any]:
        """Research company LinkedIn presence using direct URL checking"""
        logger.info(f"🔗 Researching LinkedIn for {company_name}")
        
        try:
            # Generate potential LinkedIn company URLs
            potential_handles = [
                company_name.lower().replace(' ', ''),
                company_name.lower().replace(' ', '-'),
                company_name.lower().replace(' ', '_'),
                ''.join(word[0] for word in company_name.split()).lower(),  # Acronym
                company_name.split()[0].lower() if ' ' in company_name else company_name.lower(),  # First word
            ]
            
            linkedin_data = {
                "company_url": None,
                "found": False,
                "clickable_link": None,
                "employee_count": None,
                "industry": None,
                "headquarters": None,
                "founded": None,
                "description": None,
                "top_posts": [],
                "recent_activity": None
            }
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
                
                for handle in potential_handles:
                    try:
                        linkedin_url = f"https://linkedin.com/company/{handle}"
                        
                        # Check if LinkedIn profile exists
                        async with session.head(linkedin_url, headers=headers, allow_redirects=True) as response:
                            if response.status in [200, 301, 302]:
                                # Profile likely exists, verify with GET request
                                async with session.get(linkedin_url, headers=headers, timeout=10) as get_response:
                                    if get_response.status == 200:
                                        content = await get_response.text()
                                        
                                        # Check if this is actually a company page (not a personal profile)
                                        if (company_name.lower() in content.lower() or 
                                            handle in content.lower() or
                                            'company' in content.lower()):
                                            
                                            linkedin_data["company_url"] = linkedin_url
                                            linkedin_data["clickable_link"] = linkedin_url
                                            linkedin_data["found"] = True
                                            
                                            # Try to extract additional info from page content
                                            soup = BeautifulSoup(content, 'html.parser')
                                            
                                            # Look for employee count
                                            employee_match = re.search(r'(\d+[\d,]*)\s+employees?', content, re.IGNORECASE)
                                            if employee_match:
                                                linkedin_data["employee_count"] = employee_match.group(1)
                                            
                                            # Look for description in meta tags
                                            description_meta = soup.find('meta', {'name': 'description'})
                                            if description_meta:
                                                linkedin_data["description"] = description_meta.get('content', '')[:200]
                                            
                                            # Try to extract recent posts/updates
                                            try:
                                                await self._extract_linkedin_posts(session, linkedin_url, linkedin_data)
                                            except Exception as e:
                                                logger.warning(f"Could not extract LinkedIn posts: {e}")
                                            
                                            break  # Found a working profile
                                            
                    except Exception as e:
                        continue  # Try next handle
                
                # If direct URL checking didn't work, try a simple search approach
                if not linkedin_data["found"]:
                    try:
                        search_url = f"https://www.linkedin.com/company/{company_name.lower().replace(' ', '-')}"
                        async with session.head(search_url, headers=headers, allow_redirects=True) as response:
                            if response.status in [200, 301, 302]:
                                linkedin_data["company_url"] = search_url
                                linkedin_data["clickable_link"] = search_url
                                linkedin_data["found"] = True
                    except:
                        pass
                
                return linkedin_data
                
        except Exception as e:
            logger.error(f"LinkedIn research failed: {e}")
            return {"error": str(e), "found": False}
    
    async def _extract_linkedin_posts(self, session, linkedin_url: str, linkedin_data: Dict[str, Any]):
        """Extract recent LinkedIn posts from company page"""
        try:
            # Try to access the company posts/updates page
            posts_url = f"{linkedin_url}/posts/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            async with session.get(posts_url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Look for post content - LinkedIn has dynamic content, so we'll extract what we can
                    posts = []
                    
                    # Try to find post containers
                    post_containers = soup.find_all(['div', 'article'], class_=lambda x: x and any(
                        keyword in x.lower() for keyword in ['post', 'update', 'feed', 'activity']
                    ))
                    
                    for container in post_containers[:5]:  # Limit to 5 posts
                        post_text = container.get_text(strip=True)
                        
                        # Filter for substantial content that looks like a post
                        if (len(post_text) > 50 and len(post_text) < 500 and
                            not any(skip in post_text.lower() for skip in ['cookie', 'privacy', 'terms', 'linkedin corporation'])):
                            
                            # Try to extract post date
                            date_text = None
                            date_elements = container.find_all(['time', 'span'], string=re.compile(r'\d+[dwmy]|\d{4}'))
                            if date_elements:
                                date_text = date_elements[0].get_text(strip=True)
                            
                            posts.append({
                                "content": post_text[:200] + "..." if len(post_text) > 200 else post_text,
                                "date": date_text,
                                "url": posts_url
                            })
                    
                    if posts:
                        linkedin_data["top_posts"] = posts
                        linkedin_data["recent_activity"] = f"Found {len(posts)} recent posts"
                    
                    # Alternative: Look for company updates in meta tags or structured data
                    if not posts:
                        # Look for recent news or updates mentioned in the page
                        text_content = soup.get_text()
                        
                        # Look for sentences that might be recent updates
                        sentences = re.split(r'[.!?]\s+', text_content)
                        potential_updates = []
                        
                        for sentence in sentences:
                            sentence = sentence.strip()
                            if (len(sentence) > 30 and len(sentence) < 200 and
                                any(keyword in sentence.lower() for keyword in [
                                    'announce', 'launch', 'release', 'new', 'today', 'recently',
                                    'partnership', 'funding', 'expansion', 'hiring'
                                ]) and
                                not any(skip in sentence.lower() for skip in [
                                    'linkedin', 'cookie', 'privacy', 'terms', 'sign in'
                                ])):
                                potential_updates.append({
                                    "content": sentence,
                                    "type": "company_update",
                                    "url": linkedin_url
                                })
                                
                                if len(potential_updates) >= 3:
                                    break
                        
                        if potential_updates:
                            linkedin_data["top_posts"] = potential_updates
                            linkedin_data["recent_activity"] = f"Found {len(potential_updates)} company updates"
                        
        except Exception as e:
            logger.warning(f"Failed to extract LinkedIn posts: {e}")
            # Don't fail the entire research if posts extraction fails
            pass
    
    async def _research_techcrunch(self, company_name: str) -> Dict[str, Any]:
        """Research TechCrunch coverage using direct API and search"""
        logger.info(f"📰 Researching TechCrunch coverage for {company_name}")
        
        try:
            techcrunch_data = {
                "articles_found": 0,
                "articles": [],
                "funding_mentions": [],
                "coverage_summary": None
            }
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
                
                # Try TechCrunch WordPress API first
                try:
                    api_url = f"https://techcrunch.com/wp-json/wp/v2/posts?search={company_name.replace(' ', '+')}&per_page=5"
                    async with session.get(api_url, headers=headers, timeout=10) as response:
                        if response.status == 200:
                            import json
                            articles = await response.json()
                            
                            for article in articles:
                                title = article.get('title', {}).get('rendered', '')
                                link = article.get('link', '')
                                excerpt = article.get('excerpt', {}).get('rendered', '')
                                
                                if title and link and company_name.lower() in title.lower():
                                    # Check for funding keywords
                                    text_content = f"{title} {excerpt}".lower()
                                    funding_keywords = ['raised', 'funding', 'series a', 'series b', 'seed', 'round', 'million', 'billion', 'investment']
                                    funding_found = any(keyword in text_content for keyword in funding_keywords)
                                    
                                    article_info = {
                                        "title": title,
                                        "url": link,
                                        "clickable_link": link,
                                        "funding_related": funding_found,
                                        "source": "techcrunch.com"
                                    }
                                    
                                    if funding_found:
                                        # Extract funding amount if possible
                                        funding_match = re.search(r'\$(\d+(?:\.\d+)?)\s*(million|billion|k)', text_content)
                                        if funding_match:
                                            article_info["funding_amount"] = f"${funding_match.group(1)} {funding_match.group(2)}"
                                            techcrunch_data["funding_mentions"].append(article_info)
                                    
                                    techcrunch_data["articles"].append(article_info)
                                    techcrunch_data["articles_found"] += 1
                                    
                except Exception as e:
                    logger.warning(f"TechCrunch API search failed: {e}")
                
                # If API didn't work or found few results, try direct search
                if techcrunch_data["articles_found"] < 2:
                    try:
                        search_url = f"https://techcrunch.com/?s={company_name.replace(' ', '+')}"
                        async with session.get(search_url, headers=headers, timeout=10) as response:
                            if response.status == 200:
                                content = await response.text()
                                soup = BeautifulSoup(content, 'html.parser')
                                
                                # Look for article links
                                article_links = soup.find_all('a', href=True)
                                
                                for link in article_links[:10]:
                                    href = link.get('href', '')
                                    title = link.get_text().strip()
                                    
                                    if (href.startswith('https://techcrunch.com/') and 
                                        title and len(title) > 10 and len(title) < 200 and
                                        company_name.lower() in title.lower() and
                                        not any(a['url'] == href for a in techcrunch_data['articles'])):  # Avoid duplicates
                                        
                                        # Check for funding keywords
                                        funding_keywords = ['raised', 'funding', 'series a', 'series b', 'seed', 'round', 'million', 'billion', 'investment']
                                        funding_found = any(keyword in title.lower() for keyword in funding_keywords)
                                        
                                        article_info = {
                                            "title": title,
                                            "url": href,
                                            "clickable_link": href,
                                            "funding_related": funding_found,
                                            "source": "techcrunch.com"
                                        }
                                        
                                        if funding_found:
                                            techcrunch_data["funding_mentions"].append(article_info)
                                        
                                        techcrunch_data["articles"].append(article_info)
                                        techcrunch_data["articles_found"] += 1
                                        
                                        if techcrunch_data["articles_found"] >= 5:  # Limit results
                                            break
                                            
                    except Exception as e:
                        logger.warning(f"TechCrunch direct search failed: {e}")
                
                # Generate summary
                if techcrunch_data["articles_found"] > 0:
                    techcrunch_data["coverage_summary"] = f"Found {techcrunch_data['articles_found']} TechCrunch articles"
                    if techcrunch_data["funding_mentions"]:
                        techcrunch_data["coverage_summary"] += f", {len(techcrunch_data['funding_mentions'])} funding-related"
                
                return techcrunch_data
                    
        except Exception as e:
            logger.error(f"TechCrunch research failed: {e}")
            return {"error": str(e)}
    
    async def _research_crunchbase(self, company_name: str) -> Dict[str, Any]:
        """Research Crunchbase data using direct URL checking and public APIs"""
        logger.info(f"💰 Researching funding data for {company_name}")
        
        try:
            # Generate potential Crunchbase organization URLs
            potential_handles = [
                company_name.lower().replace(' ', '-'),
                company_name.lower().replace(' ', ''),
                company_name.lower().replace(' ', '_'),
                ''.join(word[0] for word in company_name.split()).lower(),
                company_name.split()[0].lower() if ' ' in company_name else company_name.lower(),
            ]
            
            crunchbase_data = {
                "profile_found": False,
                "profile_url": None,
                "clickable_link": None,
                "total_funding": None,
                "funding_rounds": [],
                "investors": [],
                "valuation": None,
                "founded_year": None,
                "employees": None
            }
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
                
                # Try direct Crunchbase URLs
                for handle in potential_handles:
                    try:
                        crunchbase_url = f"https://www.crunchbase.com/organization/{handle}"
                        
                        # Check if profile exists
                        async with session.head(crunchbase_url, headers=headers, allow_redirects=True) as response:
                            if response.status in [200, 301, 302]:
                                # Verify with GET request
                                async with session.get(crunchbase_url, headers=headers, timeout=10) as get_response:
                                    if get_response.status == 200:
                                        content = await get_response.text()
                                        
                                        # Check if this is a real company profile
                                        if (company_name.lower() in content.lower() and
                                            'organization' in content.lower() and
                                            not 'page not found' in content.lower()):
                                            
                                            crunchbase_data["profile_found"] = True
                                            crunchbase_data["profile_url"] = crunchbase_url
                                            crunchbase_data["clickable_link"] = crunchbase_url
                                            
                                            # Try to extract basic funding info from page content
                                            # Look for funding patterns in the content
                                            funding_patterns = [
                                                r'Total Funding Amount.*?\$([0-9,.]+[MBK]?)',
                                                r'Funding Rounds.*?\$([0-9,.]+[MBK]?)',
                                                r'raised.*?\$([0-9,.]+[MBK]?)',
                                                r'\$([0-9,.]+[MBK]?).*?total funding',
                                                r'\$([0-9,.]+[MBK]?).*?raised'
                                            ]
                                            
                                            for pattern in funding_patterns:
                                                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                                                if match:
                                                    crunchbase_data["total_funding"] = f"${match.group(1)}"
                                                    break
                                            
                                            # Look for founded year
                                            founded_match = re.search(r'Founded.*?(\d{4})', content, re.IGNORECASE)
                                            if founded_match:
                                                crunchbase_data["founded_year"] = founded_match.group(1)
                                            
                                            # Look for employee count
                                            employee_match = re.search(r'(\d+[\d,]*)\s+employees?', content, re.IGNORECASE)
                                            if employee_match:
                                                crunchbase_data["employees"] = employee_match.group(1)
                                            
                                            break  # Found a working profile
                                            
                    except Exception as e:
                        continue  # Try next handle
                
                # If no direct profile found, try alternative search
                if not crunchbase_data["profile_found"]:
                    try:
                        # Try searching with the exact company name
                        search_url = f"https://www.crunchbase.com/discover/organization.companies/field/organizations/num_funding_rounds/funding-rounds"
                        
                        # For now, just create a potential URL that users can check manually
                        potential_url = f"https://www.crunchbase.com/organization/{company_name.lower().replace(' ', '-')}"
                        
                        # Don't set as found, but provide the potential URL for manual checking
                        crunchbase_data["potential_url"] = potential_url
                        
                    except Exception as e:
                        pass
                
                return crunchbase_data
                    
        except Exception as e:
            logger.error(f"Crunchbase research failed: {e}")
            return {"error": str(e)}
    
    async def _research_github(self, company_name: str) -> Dict[str, Any]:
        """Research GitHub presence and repository statistics"""
        logger.info(f"🐱 Researching GitHub presence for {company_name}")
        
        try:
            github_data = {
                "organization_found": False,
                "organization_url": None,
                "clickable_link": None,
                "public_repos": 0,
                "total_stars": 0,
                "top_repositories": [],
                "primary_languages": [],
                "recent_activity": None
            }
            
            # Search for GitHub organization
            possible_usernames = [
                company_name.lower().replace(' ', ''),
                company_name.lower().replace(' ', '-'),
                company_name.lower().replace(' ', '_'),
                ''.join(word[0] for word in company_name.split()).lower()  # Acronym
            ]
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Accept': 'application/vnd.github.v3+json'
                }
                
                # Try each possible username
                for username in possible_usernames:
                    try:
                        # Check if organization exists
                        org_url = f"https://api.github.com/orgs/{username}"
                        async with session.get(org_url, headers=headers) as response:
                            if response.status == 200:
                                org_data = await response.json()
                                github_data["organization_found"] = True
                                github_data["organization_url"] = f"https://github.com/{username}"
                                github_data["clickable_link"] = f"https://github.com/{username}"
                                github_data["public_repos"] = org_data.get("public_repos", 0)
                                
                                # Get repositories
                                repos_url = f"https://api.github.com/orgs/{username}/repos?sort=stars&direction=desc&per_page=10"
                                async with session.get(repos_url, headers=headers) as repos_response:
                                    if repos_response.status == 200:
                                        repos_data = await repos_response.json()
                                        
                                        total_stars = 0
                                        languages = {}
                                        
                                        for repo in repos_data:
                                            stars = repo.get("stargazers_count", 0)
                                            total_stars += stars
                                            
                                            language = repo.get("language")
                                            if language:
                                                languages[language] = languages.get(language, 0) + 1
                                            
                                            if stars > 5:  # Only include repos with some activity
                                                github_data["top_repositories"].append({
                                                    "name": repo.get("name"),
                                                    "description": repo.get("description", ""),
                                                    "stars": stars,
                                                    "forks": repo.get("forks_count", 0),
                                                    "language": language,
                                                    "url": repo.get("html_url"),
                                                    "clickable_link": repo.get("html_url")
                                                })
                                        
                                        github_data["total_stars"] = total_stars
                                        github_data["primary_languages"] = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]
                                        
                                break  # Found organization, stop searching
                                
                    except Exception as e:
                        continue  # Try next username
                
                # If no organization found, search for repositories
                if not github_data["organization_found"]:
                    search_url = f"https://api.github.com/search/repositories?q={company_name.replace(' ', '+')}&sort=stars&order=desc"
                    async with session.get(search_url, headers=headers) as response:
                        if response.status == 200:
                            search_data = await response.json()
                            items = search_data.get("items", [])[:5]
                            
                            for repo in items:
                                if company_name.lower() in repo.get("full_name", "").lower():
                                    github_data["top_repositories"].append({
                                        "name": repo.get("name"),
                                        "description": repo.get("description", ""),
                                        "stars": repo.get("stargazers_count", 0),
                                        "forks": repo.get("forks_count", 0),
                                        "language": repo.get("language"),
                                        "url": repo.get("html_url"),
                                        "clickable_link": repo.get("html_url"),
                                        "owner": repo.get("owner", {}).get("login")
                                    })
            
            return github_data
            
        except Exception as e:
            logger.error(f"GitHub research failed: {e}")
            return {"error": str(e)}
    
    async def _research_npm(self, company_name: str) -> Dict[str, Any]:
        """Research npm packages and JavaScript ecosystem presence"""
        logger.info(f"📦 Researching npm packages for {company_name}")
        
        try:
            npm_data = {
                "packages_found": 0,
                "packages": [],
                "total_downloads": 0,
                "organization_packages": []
            }
            
            # Search for npm packages
            search_terms = [
                company_name.lower().replace(' ', ''),
                company_name.lower().replace(' ', '-'),
                f"@{company_name.lower().replace(' ', '')}"
            ]
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
                
                for search_term in search_terms:
                    try:
                        search_url = f"https://api.npmjs.org/search?text={search_term}&size=10"
                        async with session.get(search_url, headers=headers) as response:
                            if response.status == 200:
                                search_data = await response.json()
                                packages = search_data.get("objects", [])
                                
                                for pkg_obj in packages:
                                    pkg = pkg_obj.get("package", {})
                                    pkg_name = pkg.get("name", "")
                                    
                                    # Check if package is likely related to the company
                                    if (company_name.lower().replace(' ', '') in pkg_name.lower() or
                                        pkg_name.lower().startswith(company_name.lower().replace(' ', '')[:4])):
                                        
                                        # Get download stats
                                        downloads_url = f"https://api.npmjs.org/downloads/point/last-month/{pkg_name}"
                                        try:
                                            async with session.get(downloads_url, headers=headers) as dl_response:
                                                downloads = 0
                                                if dl_response.status == 200:
                                                    dl_data = await dl_response.json()
                                                    downloads = dl_data.get("downloads", 0)
                                        except:
                                            downloads = 0
                                        
                                        package_info = {
                                            "name": pkg_name,
                                            "description": pkg.get("description", ""),
                                            "version": pkg.get("version", ""),
                                            "author": pkg.get("author", {}).get("name", "") if isinstance(pkg.get("author"), dict) else str(pkg.get("author", "")),
                                            "downloads_last_month": downloads,
                                            "npm_url": f"https://www.npmjs.com/package/{pkg_name}",
                                            "clickable_link": f"https://www.npmjs.com/package/{pkg_name}",
                                            "homepage": pkg.get("links", {}).get("homepage", ""),
                                            "repository": pkg.get("links", {}).get("repository", "")
                                        }
                                        
                                        npm_data["packages"].append(package_info)
                                        npm_data["total_downloads"] += downloads
                                        npm_data["packages_found"] += 1
                                        
                    except Exception as e:
                        logger.warning(f"NPM search for '{search_term}' failed: {e}")
                        continue
            
            return npm_data
            
        except Exception as e:
            logger.error(f"NPM research failed: {e}")
            return {"error": str(e)}
    
    async def _research_web_presence(self, company_name: str, company_url: Optional[str] = None) -> Dict[str, Any]:
        """Research company's web presence and domain information using direct URL checking"""
        logger.info(f"🌐 Researching web presence for {company_name}")
        
        try:
            web_data = {
                "company_website": company_url,
                "clickable_link": company_url,
                "domain_info": {},
                "technology_stack": [],
                "social_links": {},
                "contact_info": {},
                "seo_data": {}
            }
            
            # Generate potential website URLs if not provided
            if not company_url:
                potential_domains = [
                    f"https://{company_name.lower().replace(' ', '')}.com",
                    f"https://{company_name.lower().replace(' ', '')}.ai",
                    f"https://{company_name.lower().replace(' ', '')}.io",
                    f"https://{company_name.lower().replace(' ', '-')}.com",
                    f"https://{company_name.lower().replace(' ', '-')}.ai",
                    f"https://{company_name.lower().replace(' ', '-')}.io",
                    f"https://www.{company_name.lower().replace(' ', '')}.com",
                    f"https://www.{company_name.lower().replace(' ', '-')}.com",
                ]
                
                # For well-known companies, add specific domains
                known_domains = {
                    'openai': 'https://openai.com',
                    'anthropic': 'https://anthropic.com',
                    'stripe': 'https://stripe.com',
                    'airbnb': 'https://airbnb.com',
                    'tesla': 'https://tesla.com',
                    'spacex': 'https://spacex.com',
                    'apple': 'https://apple.com',
                    'microsoft': 'https://microsoft.com',
                    'google': 'https://google.com',
                    'facebook': 'https://facebook.com',
                    'meta': 'https://meta.com',
                    'amazon': 'https://amazon.com',
                    'netflix': 'https://netflix.com',
                    'uber': 'https://uber.com',
                    'twitter': 'https://twitter.com',
                    'linkedin': 'https://linkedin.com'
                }
                
                company_key = company_name.lower().replace(' ', '')
                if company_key in known_domains:
                    potential_domains.insert(0, known_domains[company_key])
                
                async with aiohttp.ClientSession() as session:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                    }
                    
                    # Try each potential domain
                    for domain in potential_domains:
                        try:
                            # Try HEAD request first
                            try:
                                async with session.head(domain, headers=headers, allow_redirects=True, timeout=5) as response:
                                    if response.status in [200, 301, 302]:
                                        # Domain is accessible, store it
                                        company_url = domain
                                        web_data["company_website"] = company_url
                                        web_data["clickable_link"] = company_url
                                        
                                        # Try to get content for analysis
                                        try:
                                            async with session.get(domain, headers=headers, timeout=10) as get_response:
                                                if get_response.status == 200:
                                                    content = await get_response.text()
                                                    # Additional verification that this is the right company
                                                    if (company_name.lower() in content.lower() or 
                                                        len(content) > 5000):
                                                        break  # This is the right website
                                        except:
                                            # Even if we can't get content, the domain exists
                                            pass
                                        break
                                    elif response.status == 403:
                                        # Cloudflare or similar protection, but domain exists
                                        company_url = domain
                                        web_data["company_website"] = company_url
                                        web_data["clickable_link"] = company_url
                                        web_data["seo_data"]["protected"] = True
                                        break
                            except:
                                # HEAD request failed, but domain might still exist
                                # For known companies, assume the website exists
                                company_key = company_name.lower().replace(' ', '')
                                if company_key in ['openai', 'anthropic', 'stripe', 'airbnb', 'tesla']:
                                    company_url = domain
                                    web_data["company_website"] = company_url
                                    web_data["clickable_link"] = company_url
                                    web_data["seo_data"]["access_limited"] = True
                                    break
                        except:
                            continue
            
            # If we found or were provided a company URL, analyze it
            if company_url:
                try:
                    async with aiohttp.ClientSession() as session:
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                        }
                        async with session.get(company_url, headers=headers, timeout=10) as response:
                            if response.status == 200:
                                content = await response.text()
                                soup = BeautifulSoup(content, 'html.parser')
                                
                                # Extract SEO data
                                title = soup.find('title')
                                description = soup.find('meta', {'name': 'description'})
                                
                                web_data["seo_data"] = {
                                    "title": title.get_text() if title else "",
                                    "description": description.get('content') if description else "",
                                    "has_analytics": 'google-analytics' in content.lower() or 'gtag' in content.lower(),
                                    "has_tracking": 'facebook' in content.lower() or 'twitter' in content.lower()
                                }
                                
                                # Extract comprehensive company description
                                company_description = self._extract_company_description(soup, content, company_name)
                                if company_description:
                                    web_data["company_description"] = company_description
                                
                                # Look for social media links
                                social_patterns = {
                                    'twitter': r'twitter\.com/([^/\s"\']+)',
                                    'linkedin': r'linkedin\.com/company/([^/\s"\']+)',
                                    'facebook': r'facebook\.com/([^/\s"\']+)',
                                    'github': r'github\.com/([^/\s"\']+)',
                                    'instagram': r'instagram\.com/([^/\s"\']+)'
                                }
                                
                                for platform, pattern in social_patterns.items():
                                    match = re.search(pattern, content, re.IGNORECASE)
                                    if match:
                                        web_data["social_links"][platform] = f"https://{platform}.com/{match.group(1)}"
                                
                                # Extract contact information
                                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                                emails = re.findall(email_pattern, content)
                                
                                # Filter out example/dummy emails and limit to legitimate company emails
                                filtered_emails = []
                                for email in emails:
                                    email_lower = email.lower()
                                    # Skip example, dummy, or test emails
                                    if not any(skip in email_lower for skip in [
                                        'example.com', 'test.com', 'dummy.com', 'sample.com',
                                        'placeholder.com', 'tempmail.com', 'noreply@',
                                        'donotreply@', 'no-reply@', 'jane.doe', 'john.doe',
                                        'j.appleseed', 'jane.diaz', 'user@domain.com'
                                    ]):
                                        # Prefer emails from the company's domain
                                        parsed_url = urlparse(company_url)
                                        domain = parsed_url.netloc.replace('www.', '')
                                        
                                        if domain in email_lower or len(filtered_emails) < 2:
                                            filtered_emails.append(email)
                                            
                                        if len(filtered_emails) >= 3:
                                            break
                                
                                if filtered_emails:
                                    web_data["contact_info"]["emails"] = filtered_emails
                                
                                # Look for technology indicators with very specific patterns to avoid false positives
                                tech_indicators = {
                                    'React': [
                                        r'react\.js',
                                        r'/_react\.',
                                        r'react-dom',
                                        r'import\s+.*\s+from\s+["\']react["\']',
                                        r'<script[^>]*react[^>]*\.js'
                                    ],
                                    'Vue.js': [
                                        r'vue\.js',
                                        r'/_vue\.',
                                        r'vue-router',
                                        r'import\s+.*\s+from\s+["\']vue["\']',
                                        r'<script[^>]*vue[^>]*\.js'
                                    ],
                                    'Angular': [
                                        r'angular\.js',
                                        r'@angular/',
                                        r'angular-',
                                        r'<script[^>]*angular[^>]*\.js'
                                    ],
                                    'WordPress': [
                                        r'wp-content/',
                                        r'wp-includes/',
                                        r'/wp-admin/',
                                        r'wp-json/',
                                        r'wordpress\.org'
                                    ],
                                    'Shopify': [
                                        r'shopifycdn\.com',
                                        r'shopify-analytics',
                                        r'Shopify\.analytics'
                                    ],
                                    'Next.js': [
                                        r'_next/static/',
                                        r'__next',
                                        r'next\.js'
                                    ],
                                    'Gatsby': [
                                        r'___gatsby',
                                        r'gatsby-',
                                        r'public-path\.js'
                                    ],
                                    'Cloudflare': [
                                        r'cf-ray:',
                                        r'cloudflare',
                                        r'__cf_bm'
                                    ]
                                }
                                
                                # Only check tech indicators if they're not the company's own services
                                company_name_lower = company_name.lower().replace(' ', '')
                                
                                for tech, patterns in tech_indicators.items():
                                    # Skip if this tech name is the company name (e.g., don't detect "Stripe" tech for Stripe company)
                                    if tech.lower().replace('.', '').replace(' ', '') == company_name_lower:
                                        continue
                                        
                                    # Check if any pattern matches
                                    tech_found = False
                                    for pattern in patterns:
                                        if re.search(pattern, content, re.IGNORECASE):
                                            tech_found = True
                                            break
                                    
                                    if tech_found:
                                        web_data["technology_stack"].append(tech)
                                
                                # Domain analysis
                                parsed_url = urlparse(company_url)
                                web_data["domain_info"] = {
                                    "domain": parsed_url.netloc,
                                    "uses_https": parsed_url.scheme == 'https',
                                    "subdomain": parsed_url.netloc.split('.')[0] if len(parsed_url.netloc.split('.')) > 2 else None
                                }
                                
                except Exception as e:
                    logger.warning(f"Could not analyze website {company_url}: {e}")
            
            return web_data
            
        except Exception as e:
            logger.error(f"Web presence research failed: {e}")
            return {"error": str(e)}
    
    async def _research_social_media(self, company_name: str) -> Dict[str, Any]:
        """Research social media presence across platforms using direct URL checking"""
        logger.info(f"📱 Researching social media presence for {company_name}")
        
        try:
            social_data = {
                "twitter_found": False,
                "linkedin_found": False,
                "facebook_found": False,
                "instagram_found": False,
                "youtube_found": False,
                "profiles": {}
            }
            
            # Generate potential usernames/handles for the company
            potential_handles = [
                company_name.lower().replace(' ', ''),
                company_name.lower().replace(' ', '_'),
                company_name.lower().replace(' ', '-'),
                ''.join(word[0] for word in company_name.split()).lower(),  # Acronym
                company_name.split()[0].lower() if ' ' in company_name else company_name.lower(),  # First word
            ]
            
            # Add some common variations
            if len(company_name.split()) > 1:
                potential_handles.append(''.join(company_name.split()).lower())
            
            platforms = {
                'twitter': 'https://twitter.com/{}',
                'linkedin': 'https://linkedin.com/company/{}',
                'facebook': 'https://facebook.com/{}',
                'instagram': 'https://instagram.com/{}',
                'youtube': 'https://youtube.com/c/{}'
            }
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
                
                for platform, url_template in platforms.items():
                    for handle in potential_handles:
                        try:
                            profile_url = url_template.format(handle)
                            
                            # Try to check if the profile exists (HEAD request is faster)
                            async with session.head(profile_url, headers=headers, allow_redirects=True) as response:
                                if response.status in [200, 301, 302]:
                                    # Profile likely exists
                                    social_data[f"{platform}_found"] = True
                                    social_data["profiles"][platform] = {
                                        "url": profile_url,
                                        "clickable_link": profile_url,
                                        "username": handle,
                                        "verified": response.status == 200
                                    }
                                    break  # Found a working profile for this platform
                                    
                        except Exception as e:
                            # If HEAD fails, try GET request for this handle
                            try:
                                async with session.get(profile_url, headers=headers, timeout=5) as response:
                                    if response.status == 200:
                                        # Check if the page content suggests it's a real profile
                                        content = await response.text()
                                        if (company_name.lower() in content.lower() or 
                                            handle in content.lower() or
                                            len(content) > 10000):  # Substantial content suggests real profile
                                            social_data[f"{platform}_found"] = True
                                            social_data["profiles"][platform] = {
                                                "url": profile_url,
                                                "clickable_link": profile_url,
                                                "username": handle,
                                                "verified": True
                                            }
                                            break
                            except:
                                continue
            
            return social_data
            
        except Exception as e:
            logger.error(f"Social media research failed: {e}")
            return {"error": str(e)}
    
    async def _research_news_coverage(self, company_name: str) -> Dict[str, Any]:
        """Research recent news coverage using RSS feeds and news APIs"""
        logger.info(f"📺 Researching news coverage for {company_name}")
        
        try:
            news_data = {
                "recent_articles": [],
                "news_sources": [],
                "coverage_sentiment": "neutral",
                "total_mentions": 0
            }
            
            # List of news sources to check
            news_sources = [
                {
                    "name": "TechCrunch",
                    "search_url": "https://techcrunch.com/wp-json/wp/v2/posts?search={}&per_page=5",
                    "domain": "techcrunch.com"
                },
                {
                    "name": "VentureBeat", 
                    "search_url": "https://venturebeat.com/?s={}",
                    "domain": "venturebeat.com"
                },
                {
                    "name": "The Verge",
                    "search_url": "https://www.theverge.com/search?q={}",
                    "domain": "theverge.com"
                }
            ]
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
                
                for source in news_sources:
                    try:
                        search_url = source["search_url"].format(company_name.replace(' ', '+'))
                        
                        async with session.get(search_url, headers=headers, timeout=10) as response:
                            if response.status == 200:
                                content = await response.text()
                                
                                if source["name"] == "TechCrunch":
                                    # Try to parse JSON response from TechCrunch API
                                    try:
                                        import json
                                        articles = json.loads(content)
                                        for article in articles[:3]:  # Get first 3 articles
                                            title = article.get('title', {}).get('rendered', '')
                                            link = article.get('link', '')
                                            if title and link and company_name.lower() in title.lower():
                                                news_data["recent_articles"].append({
                                                    "title": title[:200],
                                                    "url": link,
                                                    "clickable_link": link,
                                                    "source": source["domain"]
                                                })
                                                news_data["total_mentions"] += 1
                                    except:
                                        pass
                                
                                else:
                                    # Parse HTML content for other sources
                                    soup = BeautifulSoup(content, 'html.parser')
                                    
                                    # Look for article links and titles
                                    articles = soup.find_all('a', href=True)[:20]
                                    for article in articles:
                                        title = article.get_text().strip()
                                        href = article.get('href', '')
                                        
                                        # Make relative URLs absolute
                                        if href.startswith('/'):
                                            href = f"https://{source['domain']}{href}"
                                        
                                        # Filter for relevant articles
                                        if (title and len(title) > 20 and len(title) < 200 and
                                            href.startswith('http') and
                                            company_name.lower() in title.lower() and
                                            source["domain"] in href):
                                            
                                            news_data["recent_articles"].append({
                                                "title": title[:200],
                                                "url": href,
                                                "clickable_link": href,
                                                "source": source["domain"]
                                            })
                                            news_data["total_mentions"] += 1
                                            
                                            if news_data["total_mentions"] >= 10:  # Limit total articles
                                                break
                                
                                if news_data["total_mentions"] > 0:
                                    news_data["news_sources"].append(source["domain"])
                                    
                    except Exception as e:
                        logger.warning(f"Failed to search {source['name']}: {e}")
                        continue
            
            # If we found articles, set a basic sentiment
            if news_data["total_mentions"] > 0:
                news_data["coverage_sentiment"] = "positive" if news_data["total_mentions"] >= 3 else "neutral"
            
            return news_data
            
        except Exception as e:
            logger.error(f"News coverage research failed: {e}")
            return {"error": str(e)}
    
    def _extract_company_description(self, soup: BeautifulSoup, content: str, company_name: str) -> Dict[str, str]:
        """Extract comprehensive company description and what they do"""
        try:
            description_data = {}
            
            # 1. Try hero/banner sections first
            hero_selectors = [
                'section[class*="hero"]',
                'div[class*="hero"]',
                'section[class*="banner"]',
                'div[class*="banner"]',
                '.hero', '.banner', '.intro', '.overview'
            ]
            
            for selector in hero_selectors:
                hero_section = soup.select_one(selector)
                if hero_section:
                    hero_text = hero_section.get_text(strip=True)
                    if len(hero_text) > 50 and len(hero_text) < 300:
                        description_data["hero_description"] = hero_text
                        break
            
            # 2. Look for "About" or "What we do" sections
            about_keywords = ['about', 'what we do', 'our mission', 'company overview', 'who we are']
            for keyword in about_keywords:
                # Look for headings containing these keywords
                headings = soup.find_all(['h1', 'h2', 'h3', 'h4'], string=lambda text: text and keyword.lower() in text.lower())
                for heading in headings:
                    # Get the next paragraph or section
                    next_content = heading.find_next(['p', 'div', 'section'])
                    if next_content:
                        about_text = next_content.get_text(strip=True)
                        if len(about_text) > 50 and len(about_text) < 500:
                            description_data["about_section"] = about_text
                            break
                if "about_section" in description_data:
                    break
            
            # 3. Extract from meta description if comprehensive
            meta_desc = soup.find('meta', {'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                meta_content = meta_desc.get('content').strip()
                if len(meta_content) > 30:
                    description_data["meta_description"] = meta_content
            
            # 4. Look for product/service descriptions
            product_keywords = ['product', 'service', 'solution', 'platform', 'software', 'tool', 'api']
            product_sections = soup.find_all(['section', 'div'], class_=lambda x: x and any(keyword in str(x).lower() for keyword in product_keywords))
            
            for section in product_sections[:2]:  # Check first 2 matching sections
                section_text = section.get_text(strip=True)
                if len(section_text) > 50 and len(section_text) < 400:
                    description_data["product_description"] = section_text
                    break
            
            # 5. Extract mission/vision statements
            mission_keywords = ['mission', 'vision', 'purpose', 'goal', 'believe']
            for keyword in mission_keywords:
                mission_elem = soup.find(string=lambda text: text and keyword.lower() in text.lower() and len(text) > 50)
                if mission_elem:
                    mission_text = mission_elem.strip()
                    if len(mission_text) < 300:
                        description_data["mission_statement"] = mission_text
                        break
            
            # 6. Extract key value propositions from main content
            main_content = soup.find(['main', 'article']) or soup.find('div', class_=lambda x: x and 'content' in str(x).lower())
            if main_content:
                paragraphs = main_content.find_all('p')
                for p in paragraphs[:5]:  # Check first 5 paragraphs
                    p_text = p.get_text(strip=True)
                    # Look for value proposition indicators
                    value_indicators = ['help', 'enable', 'provide', 'deliver', 'solve', 'transform', 'improve', 'optimize']
                    if any(indicator in p_text.lower() for indicator in value_indicators) and len(p_text) > 50 and len(p_text) < 300:
                        description_data["value_proposition"] = p_text
                        break
            
            return description_data
            
        except Exception as e:
            logger.error(f"Error extracting company description: {e}")
            return {}

    def _generate_insights(self, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive insights from all research sources"""
        logger.info("🧠 Generating comprehensive insights...")
        
        insights = {
            "overall_assessment": {},
            "investment_signals": {},
            "risk_factors": {},
            "growth_indicators": {},
            "competitive_analysis": {},
            "recommendation": ""
        }
        
        sources = research_data.get("sources", {})
        
        # Overall Assessment
        online_presence_score = 0
        total_sources = len(sources)
        
        for source, data in sources.items():
            if isinstance(data, dict) and not data.get("error"):
                if source == "linkedin" and data.get("found"):
                    online_presence_score += 2
                elif source == "github" and data.get("organization_found"):
                    online_presence_score += 2
                elif source == "web_presence" and data.get("company_website"):
                    online_presence_score += 2
                elif source in ["techcrunch", "news"] and data.get("articles_found", 0) > 0:
                    online_presence_score += 1
                elif source == "npm" and data.get("packages_found", 0) > 0:
                    online_presence_score += 1
        
        insights["overall_assessment"] = {
            "online_presence_score": f"{online_presence_score}/10",
            "digital_maturity": "High" if online_presence_score >= 7 else "Medium" if online_presence_score >= 4 else "Low",
            "data_completeness": f"{len([s for s in sources.values() if not (isinstance(s, dict) and s.get('error'))])}/{total_sources}"
        }
        
        # Investment Signals
        positive_signals = []
        negative_signals = []
        
        # GitHub signals
        github_data = sources.get("github", {})
        if github_data.get("total_stars", 0) > 100:
            positive_signals.append(f"Strong GitHub presence with {github_data['total_stars']} total stars")
        if github_data.get("public_repos", 0) > 5:
            positive_signals.append(f"Active development with {github_data['public_repos']} public repositories")
        
        # Funding signals
        techcrunch_data = sources.get("techcrunch", {})
        if techcrunch_data.get("funding_mentions"):
            funding_info = techcrunch_data["funding_mentions"][0].get("funding_amount", "")
            if funding_info:
                positive_signals.append(f"Recent funding coverage: {funding_info}")
        
        crunchbase_data = sources.get("crunchbase", {})
        if crunchbase_data.get("total_funding"):
            positive_signals.append(f"Total funding raised: {crunchbase_data['total_funding']}")
        
        # NPM signals (for tech companies)
        npm_data = sources.get("npm", {})
        if npm_data.get("total_downloads", 0) > 1000:
            positive_signals.append(f"Strong NPM ecosystem presence with {npm_data['total_downloads']:,} monthly downloads")
        
        # LinkedIn signals
        linkedin_data = sources.get("linkedin", {})
        if linkedin_data.get("employee_count"):
            try:
                emp_count = int(linkedin_data["employee_count"].replace(",", ""))
                if emp_count > 50:
                    positive_signals.append(f"Substantial team size: {emp_count} employees")
                elif emp_count < 5:
                    negative_signals.append("Very small team size may indicate early stage")
            except:
                pass
        
        # Web presence signals
        web_data = sources.get("web_presence", {})
        if web_data.get("technology_stack"):
            tech_stack = web_data["technology_stack"]
            modern_tech = ["React", "Vue.js", "Angular", "AWS", "Google Cloud", "Vercel"]
            if any(tech in tech_stack for tech in modern_tech):
                positive_signals.append(f"Modern technology stack: {', '.join(tech_stack)}")
        
        insights["investment_signals"] = {
            "positive": positive_signals,
            "negative": negative_signals,
            "signal_strength": "Strong" if len(positive_signals) > len(negative_signals) + 2 else "Moderate" if len(positive_signals) > len(negative_signals) else "Weak"
        }
        
        # Growth Indicators
        growth_indicators = []
        
        if techcrunch_data.get("articles_found", 0) > 0:
            growth_indicators.append(f"Media attention with {techcrunch_data['articles_found']} TechCrunch articles")
        
        news_data = sources.get("news", {})
        if news_data.get("total_mentions", 0) > 3:
            growth_indicators.append(f"High media visibility with {news_data['total_mentions']} recent mentions")
        
        if github_data.get("organization_found"):
            growth_indicators.append("Active technical development and open source presence")
        
        insights["growth_indicators"] = growth_indicators
        
        # Risk Factors
        risk_factors = []
        
        if not sources.get("web_presence", {}).get("company_website"):
            risk_factors.append("No official website found - may indicate very early stage")
        
        if not sources.get("linkedin", {}).get("found"):
            risk_factors.append("No LinkedIn company page - limited professional presence")
        
        if online_presence_score < 4:
            risk_factors.append("Low overall online presence may indicate limited market traction")
        
        insights["risk_factors"] = risk_factors
        
        # Generate recommendation
        if len(positive_signals) >= 3 and len(risk_factors) <= 1:
            recommendation = "STRONG POTENTIAL - Multiple positive signals with minimal risk factors"
        elif len(positive_signals) >= 2 and len(risk_factors) <= 2:
            recommendation = "MODERATE POTENTIAL - Some positive signals, requires further due diligence"
        elif len(positive_signals) >= 1:
            recommendation = "EARLY STAGE - Limited data available, high risk/high reward potential"
        else:
            recommendation = "INSUFFICIENT DATA - Requires direct company research and engagement"
        
        insights["recommendation"] = recommendation
        
        return insights
    
    def generate_html_report(self, research_data: Dict[str, Any]) -> str:
        """Generate a beautiful HTML report from research data"""
        company_name = research_data["company_name"]
        insights = research_data.get("insights", {})
        sources = research_data.get("sources", {})
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Research Report: {company_name}</title>
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
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .insights-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .insight-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }}
        .insight-card h3 {{
            margin-top: 0;
            color: #667eea;
            font-size: 1.3em;
        }}
        .positive {{ border-left-color: #28a745; }}
        .negative {{ border-left-color: #dc3545; }}
        .neutral {{ border-left-color: #ffc107; }}
        .sources-section {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .source-item {{
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 3px solid #667eea;
        }}
        .source-title {{
            font-weight: 600;
            color: #667eea;
            margin-bottom: 10px;
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 0.5px;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            background: #667eea;
            color: white;
            border-radius: 20px;
            font-size: 0.8em;
            margin: 2px;
        }}
        .success {{ background: #28a745; }}
        .warning {{ background: #ffc107; }}
        .danger {{ background: #dc3545; }}
        .list-item {{
            margin: 5px 0;
            padding-left: 15px;
            position: relative;
        }}
        .list-item:before {{
            content: "•";
            color: #667eea;
            font-weight: bold;
            position: absolute;
            left: 0;
        }}
        .recommendation {{
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            font-size: 1.2em;
            font-weight: 500;
            margin-top: 30px;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #6c757d;
            font-size: 0.9em;
        }}
        a {{
            color: #667eea;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Company Research Report</h1>
        <p><strong>{company_name}</strong></p>
        <p>Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
    </div>
    
    <div class="insights-grid">
        <div class="insight-card positive">
            <h3>📈 Investment Signals</h3>
            <p><strong>Signal Strength:</strong> {insights.get('investment_signals', {}).get('signal_strength', 'Unknown')}</p>
            {self._format_list_items(insights.get('investment_signals', {}).get('positive', []))}
        </div>
        
        <div class="insight-card neutral">
            <h3>🎯 Overall Assessment</h3>
            <p><strong>Digital Maturity:</strong> {insights.get('overall_assessment', {}).get('digital_maturity', 'Unknown')}</p>
            <p><strong>Online Presence:</strong> {insights.get('overall_assessment', {}).get('online_presence_score', 'Unknown')}</p>
            <p><strong>Data Coverage:</strong> {insights.get('overall_assessment', {}).get('data_completeness', 'Unknown')}</p>
        </div>
        
        <div class="insight-card {'negative' if insights.get('risk_factors') else 'positive'}">
            <h3>⚠️ Risk Assessment</h3>
            {self._format_list_items(insights.get('risk_factors', []) if insights.get('risk_factors') else ['No significant risk factors identified'])}
        </div>
        
        <div class="insight-card positive">
            <h3>🚀 Growth Indicators</h3>
            {self._format_list_items(insights.get('growth_indicators', []) if insights.get('growth_indicators') else ['Limited growth indicators available'])}
        </div>
    </div>
    
    <div class="sources-section">
        <h2>📊 Research Sources Summary</h2>
        {self._format_sources_html(sources)}
    </div>
    
    <div class="recommendation">
        <strong>🎯 Investment Recommendation:</strong><br>
        {insights.get('recommendation', 'Further research required')}
    </div>
    
    <div class="footer">
        <p>Report generated by YC Company Research Tool</p>
        <p>⚠️ This report is for informational purposes only and should not be considered as investment advice.</p>
    </div>
</body>
</html>
        """
        
        return html_content
    
    def _format_list_items(self, items: List[str]) -> str:
        """Format list items for HTML display"""
        if not items:
            return '<div class="list-item">No items available</div>'
        
        html = ""
        for item in items:
            html += f'<div class="list-item">{item}</div>'
        return html
    
    def _format_sources_html(self, sources: Dict[str, Any]) -> str:
        """Format sources data for HTML display"""
        html = ""
        
        for source_name, source_data in sources.items():
            if isinstance(source_data, dict) and not source_data.get("error"):
                html += f'<div class="source-item">'
                html += f'<div class="source-title">{source_name.replace("_", " ").title()}</div>'
                
                # Format source-specific data
                if source_name == "linkedin":
                    if source_data.get("found"):
                        html += f'<span class="badge success">✓ Profile Found</span>'
                        if source_data.get("clickable_link"):
                            html += f' <a href="{source_data["clickable_link"]}" target="_blank" class="badge success">View Profile</a>'
                        if source_data.get("employee_count"):
                            html += f'<span class="badge">{source_data["employee_count"]} employees</span>'
                        
                        # Add recent posts information
                        posts = source_data.get("top_posts", [])
                        if posts:
                            html += f'<span class="badge">{len(posts)} recent posts</span>'
                            for i, post in enumerate(posts[:2]):  # Show first 2 posts
                                post_content = post.get("content", "")[:100] + "..."
                                html += f'<div style="margin: 5px 0; padding: 5px; background: #f0f0f0; border-radius: 3px; font-size: 0.8em;">'
                                html += f'<strong>Post {i+1}:</strong> {post_content}'
                                if post.get("date"):
                                    html += f' <em>({post["date"]})</em>'
                                html += f'</div>'
                    else:
                        html += f'<span class="badge warning">Profile Not Found</span>'
                
                elif source_name == "github":
                    if source_data.get("organization_found"):
                        html += f'<span class="badge success">✓ Organization Found</span>'
                        if source_data.get("clickable_link"):
                            html += f' <a href="{source_data["clickable_link"]}" target="_blank" class="badge success">View GitHub</a>'
                        html += f'<span class="badge">{source_data.get("total_stars", 0)} stars</span>'
                        html += f'<span class="badge">{source_data.get("public_repos", 0)} repos</span>'
                    else:
                        html += f'<span class="badge warning">Organization Not Found</span>'
                
                elif source_name == "techcrunch":
                    articles = source_data.get("articles_found", 0)
                    if articles > 0:
                        html += f'<span class="badge success">{articles} articles found</span>'
                        # Add links to first few articles with meaningful names
                        articles_list = source_data.get("articles", [])
                        for i, article in enumerate(articles_list[:2]):  # Show first 2 articles
                            if article.get("clickable_link"):
                                # Create meaningful link text from article title
                                title = article.get("title", f"Article {i+1}")
                                # Truncate title if too long and clean it up
                                clean_title = title.replace('"', "'").replace('\n', ' ')
                                if len(clean_title) > 40:
                                    clean_title = clean_title[:37] + "..."
                                html += f' <a href="{article["clickable_link"]}" target="_blank" class="badge" title="{title}">{clean_title}</a>'
                        funding = len(source_data.get("funding_mentions", []))
                        if funding > 0:
                            html += f'<span class="badge">{funding} funding mentions</span>'
                    else:
                        html += f'<span class="badge warning">No articles found</span>'
                
                elif source_name == "npm":
                    packages = source_data.get("packages_found", 0)
                    if packages > 0:
                        html += f'<span class="badge success">{packages} packages found</span>'
                        # Add links to top packages
                        packages_list = source_data.get("packages", [])
                        for i, package in enumerate(packages_list[:2]):  # Show first 2 packages
                            if package.get("clickable_link"):
                                html += f' <a href="{package["clickable_link"]}" target="_blank" class="badge">{package["name"]}</a>'
                        downloads = source_data.get("total_downloads", 0)
                        if downloads > 0:
                            html += f'<span class="badge">{downloads:,} monthly downloads</span>'
                    else:
                        html += f'<span class="badge warning">No packages found</span>'
                
                elif source_name == "web_presence":
                    if source_data.get("company_website"):
                        html += f'<span class="badge success">✓ Website Found</span>'
                        if source_data.get("clickable_link"):
                            html += f' <a href="{source_data["clickable_link"]}" target="_blank" class="badge success">Visit Website</a>'
                        
                        # Show domain info
                        domain_info = source_data.get("domain_info", {})
                        if domain_info.get("domain"):
                            html += f'<span class="badge">{domain_info["domain"]}</span>'
                        if domain_info.get("uses_https"):
                            html += f'<span class="badge success">HTTPS</span>'
                        
                        # Show company description if available
                        company_desc = source_data.get("company_description", {})
                        if company_desc:
                            html += f'<div class="company-description" style="margin-top: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px;">'
                            html += f'<h4 style="margin: 0 0 8px 0; color: #2c3e50;">What They Do:</h4>'
                            
                            # Show different types of descriptions
                            if company_desc.get("meta_description"):
                                html += f'<p style="margin: 0 0 5px 0;"><strong>Meta:</strong> {company_desc["meta_description"]}</p>'
                            if company_desc.get("hero_description"):
                                html += f'<p style="margin: 0 0 5px 0;"><strong>Hero:</strong> {company_desc["hero_description"]}</p>'
                            if company_desc.get("about_section"):
                                html += f'<p style="margin: 0 0 5px 0;"><strong>About:</strong> {company_desc["about_section"]}</p>'
                            if company_desc.get("product_description"):
                                html += f'<p style="margin: 0 0 5px 0;"><strong>Product:</strong> {company_desc["product_description"]}</p>'
                            if company_desc.get("value_proposition"):
                                html += f'<p style="margin: 0 0 5px 0;"><strong>Value:</strong> {company_desc["value_proposition"]}</p>'
                            if company_desc.get("mission_statement"):
                                html += f'<p style="margin: 0 0 5px 0;"><strong>Mission:</strong> {company_desc["mission_statement"]}</p>'
                            
                            html += f'</div>'
                        
                        # Show technology stack
                        tech_stack = source_data.get("technology_stack", [])
                        for tech in tech_stack[:3]:  # Show first 3 technologies
                            html += f'<span class="badge">{tech}</span>'
                        
                        # Show social links found on website
                        social_links = source_data.get("social_links", {})
                        if social_links:
                            html += f'<span class="badge">{len(social_links)} social links</span>'
                            
                        # Show contact info
                        contact_info = source_data.get("contact_info", {})
                        emails = contact_info.get("emails", [])
                        if emails:
                            html += f'<span class="badge">{len(emails)} email(s)</span>'
                    else:
                        html += f'<span class="badge warning">Website Not Found</span>'
                
                elif source_name == "social_media":
                    profiles = source_data.get("profiles", {})
                    if profiles:
                        html += f'<span class="badge success">✓ Social Profiles Found</span>'
                        for platform, profile_data in profiles.items():
                            if isinstance(profile_data, dict) and profile_data.get("clickable_link"):
                                username = profile_data.get("username", platform)
                                html += f' <a href="{profile_data["clickable_link"]}" target="_blank" class="badge">{platform.title()}: @{username}</a>'
                    else:
                        html += f'<span class="badge warning">No Social Profiles Found</span>'
                
                elif source_name == "news":
                    articles = source_data.get("recent_articles", [])
                    if articles:
                        html += f'<span class="badge success">{len(articles)} news articles found</span>'
                        for i, article in enumerate(articles[:2]):  # Show first 2 articles
                            if article.get("clickable_link"):
                                # Create meaningful link text from article title
                                title = article.get("title", f"Article {i+1}")
                                # Truncate title if too long and clean it up
                                clean_title = title.replace('"', "'").replace('\n', ' ')
                                if len(clean_title) > 40:
                                    clean_title = clean_title[:37] + "..."
                                html += f' <a href="{article["clickable_link"]}" target="_blank" class="badge" title="{title}">{clean_title}</a>'
                    else:
                        html += f'<span class="badge warning">No news articles found</span>'
                
                elif source_name == "crunchbase":
                    if source_data.get("profile_found"):
                        html += f'<span class="badge success">✓ Profile Found</span>'
                        if source_data.get("clickable_link"):
                            html += f' <a href="{source_data["clickable_link"]}" target="_blank" class="badge success">View Crunchbase</a>'
                        if source_data.get("total_funding"):
                            html += f'<span class="badge">{source_data["total_funding"]} funding</span>'
                    else:
                        html += f'<span class="badge warning">Profile Not Found</span>'
                
                html += '</div>'
            else:
                html += f'<div class="source-item">'
                html += f'<div class="source-title">{source_name.replace("_", " ").title()}</div>'
                html += f'<span class="badge danger">Error: {source_data.get("error", "Unknown error")}</span>'
                html += '</div>'
        
        return html

async def main():
    """Main function for command-line usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python company_researcher.py <company_name> [company_url]")
        sys.exit(1)
    
    company_name = sys.argv[1]
    company_url = sys.argv[2] if len(sys.argv) > 2 else None
    
    researcher = CompanyResearcher()
    research_data = await researcher.research_company(company_name, company_url)
    
    # Generate HTML report
    html_report = researcher.generate_html_report(research_data)
    html_path = os.path.join(researcher.output_dir, f"{company_name.replace(' ', '_')}_research_report.html")
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_report)
    
    print(f"\n✅ Research completed!")
    json_report_path = os.path.join(researcher.output_dir, f"{company_name.replace(' ', '_')}_research_report.json")
    print(f"📊 JSON Report: {json_report_path}")
    print(f"🌐 HTML Report: {html_path}")
    print(f"\n🎯 Investment Recommendation: {research_data['insights']['recommendation']}")

if __name__ == "__main__":
    asyncio.run(main())
