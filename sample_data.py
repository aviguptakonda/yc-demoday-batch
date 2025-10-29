import json
import pandas as pd
from datetime import datetime

# Sample YC companies data (batch will be updated dynamically)
sample_companies = [
    {
        "name": "TechFlow AI",
        "description": "AI-powered workflow automation platform that helps teams streamline their processes and increase productivity by 300%.",
        "url": "https://techflow.ai",
        "batch": "Fall 2025",
        "categories": ["AI/ML", "Productivity", "SaaS"],
        "founders": [
            {
                "name": "Sarah Chen",
                "profile_url": "https://linkedin.com/in/sarah-chen-ai",
                "profile_type": "linkedin",
                "title": "CEO & Co-founder"
            },
            {
                "name": "Michael Rodriguez",
                "profile_url": "https://linkedin.com/in/michael-rodriguez-tech",
                "profile_type": "linkedin",
                "title": "CTO & Co-founder"
            }
        ],
        "summary": "What They Do: TechFlow AI builds an AI-powered workflow automation platform that helps teams streamline their processes and increase productivity by 300% through intelligent task routing and predictive analytics. | Specific Insights: Founded by ex-Google AI researchers Sarah Chen (Stanford PhD, former Google DeepMind) and Michael Rodriguez (MIT, former Tesla Autopilot team), the company has achieved 40% month-over-month growth and serves 200+ enterprise clients including Fortune 500 companies.",
        "scraped_at": datetime.now().isoformat()
    },
    {
        "name": "GreenEnergy Solutions",
        "description": "Revolutionary renewable energy storage technology that makes solar power accessible to every household.",
        "url": "https://greenenergy.solutions",
        "batch": "Fall 2025",
        "categories": ["Clean Energy", "Hardware", "Sustainability"],
        "founders": [
            {
                "name": "Alex Thompson",
                "profile_url": "https://linkedin.com/in/alex-thompson-energy",
                "profile_type": "linkedin",
                "title": "Founder & CEO"
            }
        ],
        "summary": "What They Do: GreenEnergy Solutions develops revolutionary renewable energy storage technology that makes solar power accessible to every household through proprietary lithium-ion battery optimization and smart grid integration. | Specific Insights: Led by Alex Thompson (MIT Energy PhD, former Tesla Energy lead engineer), the company has secured $15M in Series A funding and partnerships with 3 major utility companies, targeting the $120B home energy storage market.",
        "scraped_at": datetime.now().isoformat()
    },
    {
        "name": "HealthSync",
        "description": "Digital health platform connecting patients with healthcare providers through AI-driven matching and telemedicine.",
        "url": "https://healthsync.com",
        "batch": "Fall 2025",
        "categories": ["Healthcare", "Telemedicine", "AI/ML"],
        "founders": [
            {
                "name": "Dr. Emily Watson",
                "profile_url": "https://linkedin.com/in/emily-watson-md",
                "profile_type": "linkedin",
                "title": "CEO & Co-founder"
            },
            {
                "name": "David Kim",
                "profile_url": "https://twitter.com/davidkim_health",
                "profile_type": "twitter",
                "title": "CTO & Co-founder"
            }
        ],
        "summary": "What They Do: HealthSync creates a digital health platform connecting patients with healthcare providers through AI-driven matching and telemedicine, reducing wait times by 70% and improving patient outcomes. | Specific Insights: Co-founded by Dr. Emily Watson (Harvard Medical, former Mayo Clinic) and David Kim (Stanford CS, former Palantir), the platform serves 50,000+ patients and has partnerships with 200+ healthcare providers across 15 states.",
        "scraped_at": datetime.now().isoformat()
    },
    {
        "name": "EduTech Pro",
        "description": "Personalized learning platform using adaptive AI to create custom educational experiences for students of all ages.",
        "url": "https://edutechpro.com",
        "batch": "Fall 2025",
        "categories": ["EdTech", "AI/ML", "Education"],
        "founders": [
            {
                "name": "Lisa Park",
                "profile_url": "https://linkedin.com/in/lisa-park-edu",
                "profile_type": "linkedin",
                "title": "Founder & CEO"
            },
            {
                "name": "James Wilson",
                "profile_url": "https://github.com/jameswilson-edu",
                "profile_type": "github",
                "title": "Co-founder & CTO"
            }
        ],
        "summary": "What They Do: EduTech Pro builds a personalized learning platform using adaptive AI to create custom educational experiences for students of all ages, improving learning outcomes by 60% through individualized content delivery. | Specific Insights: Founded by Lisa Park (Stanford Education PhD, former Khan Academy VP) and James Wilson (MIT, former Google Education), the platform serves 100,000+ students and has raised $8M from top edtech investors.",
        "scraped_at": datetime.now().isoformat()
    },
    {
        "name": "FinTech Secure",
        "description": "Next-generation financial security platform protecting digital assets with quantum-resistant encryption.",
        "url": "https://fintechsecure.com",
        "batch": "Fall 2025",
        "categories": ["FinTech", "Cybersecurity", "Blockchain"],
        "founders": [
            {
                "name": "Robert Zhang",
                "profile_url": "https://linkedin.com/in/robert-zhang-fintech",
                "profile_type": "linkedin",
                "title": "CEO & Co-founder"
            },
            {
                "name": "Maria Garcia",
                "profile_url": "https://linkedin.com/in/maria-garcia-crypto",
                "profile_type": "linkedin",
                "title": "CTO & Co-founder"
            }
        ],
        "summary": "What They Do: FinTech Secure provides next-generation financial security platform protecting digital assets with quantum-resistant encryption, securing over $2B in digital assets for institutional clients. | Specific Insights: Co-founded by Robert Zhang (Berkeley CS PhD, former Coinbase security lead) and Maria Garcia (MIT, former Goldman Sachs quant), the company has SOC 2 compliance and serves major crypto exchanges and hedge funds.",
        "scraped_at": datetime.now().isoformat()
    },
    {
        "name": "BioTech Innovations",
        "description": "Cutting-edge biotechnology company developing novel therapeutics for rare diseases using CRISPR technology.",
        "url": "https://biotechinnovations.com",
        "batch": "Fall 2025",
        "categories": ["Biotech", "Healthcare", "Research"],
        "founders": [
            {
                "name": "Dr. Rachel Green",
                "profile_url": "https://linkedin.com/in/rachel-green-phd",
                "profile_type": "linkedin",
                "title": "CEO & Co-founder"
            },
            {
                "name": "Dr. Kevin Lee",
                "profile_url": "https://linkedin.com/in/kevin-lee-biotech",
                "profile_type": "linkedin",
                "title": "CSO & Co-founder"
            }
        ],
        "summary": "What They Do: BioTech Innovations develops cutting-edge biotechnology solutions for rare diseases using CRISPR technology, with 3 therapies in clinical trials targeting genetic disorders affecting 500,000+ patients globally. | Specific Insights: Led by Dr. Rachel Green (Harvard Medical PhD, former Broad Institute) and Dr. Kevin Lee (Stanford Bioengineering, former Genentech), the company has $25M in NIH grants and partnerships with major pharma companies.",
        "scraped_at": datetime.now().isoformat()
    },
    {
        "name": "DevTools Hub",
        "description": "Comprehensive developer tools platform that streamlines the entire software development lifecycle.",
        "url": "https://devtoolshub.com",
        "batch": "Fall 2025",
        "categories": ["Developer Tools", "SaaS", "Productivity"],
        "founders": [
            {
                "name": "Chris Anderson",
                "profile_url": "https://github.com/chrisanderson-dev",
                "profile_type": "github",
                "title": "Founder & CEO"
            }
        ],
        "summary": "What They Do: DevTools Hub provides a comprehensive developer tools platform that streamlines the entire software development lifecycle, reducing deployment time by 80% through automated CI/CD pipelines and intelligent code analysis. | Specific Insights: Founded by Chris Anderson (ex-GitHub engineer, creator of popular open-source tools with 50K+ stars), the platform serves 10,000+ developers at 500+ companies including several unicorn startups.",
        "scraped_at": datetime.now().isoformat()
    },
    {
        "name": "Consumer Connect",
        "description": "AI-powered consumer insights platform helping brands understand and connect with their customers better.",
        "url": "https://consumerconnect.ai",
        "batch": "Fall 2025",
        "categories": ["Consumer", "AI/ML", "Analytics"],
        "founders": [
            {
                "name": "Jennifer Martinez",
                "profile_url": "https://linkedin.com/in/jennifer-martinez-consumer",
                "profile_type": "linkedin",
                "title": "CEO & Co-founder"
            },
            {
                "name": "Tom Johnson",
                "profile_url": "https://twitter.com/tomjohnson_ai",
                "profile_type": "twitter",
                "title": "CTO & Co-founder"
            }
        ],
        "summary": "What They Do: Consumer Connect offers an AI-powered consumer insights platform helping brands understand and connect with their customers better, increasing customer engagement by 45% through predictive analytics and personalization. | Specific Insights: Co-founded by Jennifer Martinez (Wharton MBA, former P&G brand manager) and Tom Johnson (Stanford AI, former Facebook data scientist), the platform analyzes 100M+ consumer interactions for Fortune 500 brands.",
        "scraped_at": datetime.now().isoformat()
    },
    {
        "name": "Enterprise Flow",
        "description": "Enterprise workflow automation platform designed for large organizations to optimize their operations.",
        "url": "https://enterpriseflow.com",
        "batch": "Fall 2025",
        "categories": ["Enterprise", "SaaS", "Automation"],
        "founders": [
            {
                "name": "Amanda Foster",
                "profile_url": "https://linkedin.com/in/amanda-foster-enterprise",
                "profile_type": "linkedin",
                "title": "Founder & CEO"
            },
            {
                "name": "Daniel Brown",
                "profile_url": "https://linkedin.com/in/daniel-brown-tech",
                "profile_type": "linkedin",
                "title": "Co-founder & CTO"
            }
        ],
        "summary": "What They Do: Enterprise Flow creates enterprise workflow automation platform designed for large organizations to optimize their operations, reducing manual processes by 90% and saving $2M+ annually per client through intelligent automation. | Specific Insights: Founded by Amanda Foster (McKinsey consultant, former Salesforce enterprise sales) and Daniel Brown (MIT, former Oracle enterprise architect), the platform serves 50+ Fortune 1000 companies with 99.9% uptime.",
        "scraped_at": datetime.now().isoformat()
    },
    {
        "name": "Hardware Labs",
        "description": "Innovative hardware company developing next-generation IoT devices for smart homes and cities.",
        "url": "https://hardwarelabs.io",
        "batch": "Fall 2025",
        "categories": ["Hardware", "IoT", "Smart Cities"],
        "founders": [
            {
                "name": "Ryan Davis",
                "profile_url": "https://linkedin.com/in/ryan-davis-hardware",
                "profile_type": "linkedin",
                "title": "CEO & Co-founder"
            },
            {
                "name": "Sophie Chen",
                "profile_url": "https://github.com/sophiechen-hw",
                "profile_type": "github",
                "title": "CTO & Co-founder"
            }
        ],
        "summary": "What They Do: Hardware Labs develops innovative next-generation IoT devices for smart homes and cities, creating energy-efficient sensors that reduce power consumption by 70% while improving connectivity and data accuracy. | Specific Insights: Co-founded by Ryan Davis (Berkeley EECS, former Apple hardware engineer) and Sophie Chen (MIT, former Tesla hardware lead), the company has 15 patents and partnerships with major smart city initiatives in 5 countries.",
        "scraped_at": datetime.now().isoformat()
    }
]

def create_sample_data(batch="Fall 2025"):
    """Create sample data files for testing"""
    
    # Update batch information in sample data
    updated_companies = []
    for company in sample_companies:
        updated_company = company.copy()
        updated_company['batch'] = batch
        updated_companies.append(updated_company)
    
    # Save as JSON
    with open('yc_companies.json', 'w') as f:
        json.dump(updated_companies, f, indent=2)
    
    # Save as CSV
    df = pd.DataFrame(updated_companies)
    df.to_csv('yc_companies.csv', index=False)
    
    print(f"Created sample data with {len(updated_companies)} companies for {batch} batch")
    print("Files created: yc_companies.json, yc_companies.csv")

if __name__ == "__main__":
    create_sample_data() 