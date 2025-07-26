import json
import pandas as pd
from datetime import datetime

# Sample YC Summer 2025 companies data
sample_companies = [
    {
        "name": "TechFlow AI",
        "description": "AI-powered workflow automation platform that helps teams streamline their processes and increase productivity by 300%.",
        "url": "https://techflow.ai",
        "batch": "Summer 2025",
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
        "scraped_at": datetime.now().isoformat()
    },
    {
        "name": "GreenEnergy Solutions",
        "description": "Revolutionary renewable energy storage technology that makes solar power accessible to every household.",
        "url": "https://greenenergy.solutions",
        "batch": "Summer 2025",
        "categories": ["Clean Energy", "Hardware", "Sustainability"],
        "founders": [
            {
                "name": "Alex Thompson",
                "profile_url": "https://linkedin.com/in/alex-thompson-energy",
                "profile_type": "linkedin",
                "title": "Founder & CEO"
            }
        ],
        "scraped_at": datetime.now().isoformat()
    },
    {
        "name": "HealthSync",
        "description": "Digital health platform connecting patients with healthcare providers through AI-driven matching and telemedicine.",
        "url": "https://healthsync.com",
        "batch": "Summer 2025",
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
        "scraped_at": datetime.now().isoformat()
    },
    {
        "name": "EduTech Pro",
        "description": "Personalized learning platform using adaptive AI to create custom educational experiences for students of all ages.",
        "url": "https://edutechpro.com",
        "batch": "Summer 2025",
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
        "scraped_at": datetime.now().isoformat()
    },
    {
        "name": "FinTech Secure",
        "description": "Next-generation financial security platform protecting digital assets with quantum-resistant encryption.",
        "url": "https://fintechsecure.com",
        "batch": "Summer 2025",
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
        "scraped_at": datetime.now().isoformat()
    },
    {
        "name": "BioTech Innovations",
        "description": "Cutting-edge biotechnology company developing novel therapeutics for rare diseases using CRISPR technology.",
        "url": "https://biotechinnovations.com",
        "batch": "Summer 2025",
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
        "scraped_at": datetime.now().isoformat()
    },
    {
        "name": "DevTools Hub",
        "description": "Comprehensive developer tools platform that streamlines the entire software development lifecycle.",
        "url": "https://devtoolshub.com",
        "batch": "Summer 2025",
        "categories": ["Developer Tools", "SaaS", "Productivity"],
        "founders": [
            {
                "name": "Chris Anderson",
                "profile_url": "https://github.com/chrisanderson-dev",
                "profile_type": "github",
                "title": "Founder & CEO"
            }
        ],
        "scraped_at": datetime.now().isoformat()
    },
    {
        "name": "Consumer Connect",
        "description": "AI-powered consumer insights platform helping brands understand and connect with their customers better.",
        "url": "https://consumerconnect.ai",
        "batch": "Summer 2025",
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
        "scraped_at": datetime.now().isoformat()
    },
    {
        "name": "Enterprise Flow",
        "description": "Enterprise workflow automation platform designed for large organizations to optimize their operations.",
        "url": "https://enterpriseflow.com",
        "batch": "Summer 2025",
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
        "scraped_at": datetime.now().isoformat()
    },
    {
        "name": "Hardware Labs",
        "description": "Innovative hardware company developing next-generation IoT devices for smart homes and cities.",
        "url": "https://hardwarelabs.io",
        "batch": "Summer 2025",
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
        "scraped_at": datetime.now().isoformat()
    }
]

def create_sample_data():
    """Create sample data files for testing"""
    
    # Save as JSON
    with open('yc_companies.json', 'w') as f:
        json.dump(sample_companies, f, indent=2)
    
    # Save as CSV
    df = pd.DataFrame(sample_companies)
    df.to_csv('yc_companies.csv', index=False)
    
    print(f"Created sample data with {len(sample_companies)} companies")
    print("Files created: yc_companies.json, yc_companies.csv")

if __name__ == "__main__":
    create_sample_data() 