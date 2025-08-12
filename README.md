# YC Demo Day Batch Monitor

A comprehensive, investment-ready tool for scraping and analyzing YC (Y Combinator) companies data from the [Summer 2025 batch](https://www.ycombinator.com/companies?batch=Summer%202025) with enhanced AI-powered summary extraction, founder LinkedIn integration, and interactive visualizations.

## 🔥 Latest Enhancements (December 2024)

- **🧠 AI-Powered Summary Extraction**: Complete business descriptions with "What They Do" + "Specific Insights" format
- **👥 Founder LinkedIn Integration**: Automatic extraction of founder profiles with clickable links
- **📝 Complete Sentence Integrity**: Advanced parsing prevents sentence breaking mid-way
- **🎯 Investment-Ready Format**: Structured data optimized for angel investors and VCs
- **📊 Enhanced HTML Tables**: Beautiful, interactive tables with founder links and comprehensive summaries
- **🏗️ Unified Output Structure**: Scraper and analyzer outputs organized in single timestamped directories
- **📈 Expanded Coverage**: Now captures 143+ companies (vs. previous 86) with complete data

## 🚀 Features

### Web Scraping
- **ENHANCED ROBUST SCROLLING**: Advanced headless browser scraping with 5 different scrolling techniques
- **MAXIMUM RELIABILITY**: Priority on capturing ALL available companies with multiple retry attempts
- **Complete Coverage**: Captures all companies from YC Summer 2025 batch with enhanced accuracy
- **Dynamic Content Handling**: Handles JavaScript-loaded content and lazy loading with verification
- **Robust Parsing**: Intelligent text parsing for company names, descriptions, and categories
- **URL Extraction**: Captures company profile URLs for further research
- **Fallback Mechanisms**: Multiple safety checks and error recovery throughout the process

### 🔥 Enhanced Summary Extraction (NEW!)
- **AI-Powered Content Analysis**: Structured extraction of company descriptions with complete sentence preservation
- **Investment-Ready Summaries**: "What They Do" + "Specific Insights" format optimized for investors
- **Intelligent Content Filtering**: Removes navigation breadcrumbs and focuses on business-critical information
- **Complete Sentence Integrity**: Advanced parsing prevents sentence breaking mid-way
- **Founder Credentials**: Extracts founder backgrounds, education, and previous experience
- **Traction Metrics**: Captures business metrics, funding, partnerships, and growth indicators
- **Unique Selling Points**: Identifies competitive advantages and innovative aspects

### 👥 Founder Integration
- **LinkedIn Profile Extraction**: Automatically captures founder LinkedIn URLs from YC pages
- **Enhanced Name Parsing**: Intelligent extraction of founder names with role information
- **Profile Validation**: Supports multiple profile URL formats and validates data integrity
- **Team Background Analysis**: Identifies founder credentials and previous company experience

### Data Analysis
- **Company Analysis**: Comprehensive analysis of company data including categories, descriptions, and batch information
- **Category Distribution**: Identifies and analyzes company categories and sectors
- **Description Analysis**: Analyzes company descriptions for keywords and themes
- **Data Quality Metrics**: Tracks missing data and data completeness
- **Investment Insights**: Provides analysis for angel investment decision-making

### Visualization
- **Interactive Charts**: 4 different types of interactive HTML visualizations
- **Category Distribution**: Top company categories visualization
- **Description Length Analysis**: Distribution of company description lengths
- **Batch Distribution**: Companies by batch pie chart
- **Founders Analysis**: Distribution of founder information (when available)

### Report Generation
- **Timestamped Reports**: All reports and charts are timestamped to prevent overwrites
- **JSON Reports**: Comprehensive analysis reports in JSON format
- **CSV Support**: Works with CSV data files
- **HTML Tables**: Beautiful, interactive HTML tables automatically generated for all data
- **Professional Output**: Clean, organized file structure

## 📁 Project Structure

```
yc-demoday-batch/
├── yc_scraper_robust.py     # Enhanced Playwright-based web scraper with AI summaries
├── analyzer.py              # Main analysis engine with founder statistics
├── simple_html_generator.py # Beautiful HTML table generator with founder links
├── sample_data.py           # Sample data generator with enhanced summaries
├── main.py                  # Command-line interface with unified output structure
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── activate_env.sh         # Virtual environment activation script
├── run_in_venv.sh          # Script to run commands in virtual environment
└── yc_env/                 # Virtual environment directory
```

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd yc-demoday-batch
   ```

2. **Activate the virtual environment**:
   ```bash
   source activate_env.sh
   ```
   Or manually:
   ```bash
   source yc_env/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers** (for web scraping):
   ```bash
   playwright install chromium
   ```

## 📊 Usage

### Complete Pipeline (Scrape + Analyze)
```bash
./run_in_venv.sh python main.py --action all
```

### Scrape Only (Get Latest Data with Enhanced Summaries)
```bash
./run_in_venv.sh python main.py --action scrape
```

### Analyze Only (Use Existing Data)
```bash
./run_in_venv.sh python main.py --action analyze --input yc_companies_YYYYMMDD_HHMMSS.csv
```

### Generate Sample Data (For Testing)
```bash
./run_in_venv.sh python main.py --action sample
```

### Custom Analysis
```bash
./run_in_venv.sh python main.py --action analyze --input your_data.csv --report custom_report.json --charts-dir custom_charts
```

### Test Enhanced Scrolling
```bash
./run_in_venv.sh python test_scrolling.py
```

## 🔍 Scraping Approach

### Technology Stack
- **Playwright**: Modern headless browser automation
- **Python Async**: Efficient handling of dynamic content
- **Infinite Scroll**: Automatically loads all content by scrolling
- **Smart Parsing**: Intelligent text extraction and categorization

### Enhanced Scraping Process
1. **Page Navigation**: Loads the YC Summer 2025 companies page
2. **ENHANCED CONTENT LOADING**: Performs 5 different scrolling techniques to ensure ALL content is loaded:
   - Scroll to bottom with multiple passes
   - Scroll by viewport height (granular)
   - Scroll to specific company elements
   - Force load more content with JavaScript
   - Extended wait and verification techniques
3. **Progress Tracking**: Monitors company count to detect when all content is loaded
4. **Element Detection**: Finds company links using CSS selectors
5. **Basic Data Extraction**: Extracts company names, descriptions, URLs, and categories
6. **🔥 ENHANCED DETAIL EXTRACTION**: Two-pass approach for comprehensive data:
   - **Pass 1**: Quick capture of all companies with basic information
   - **Pass 2**: Deep dive into each company page for detailed summaries and founder info
7. **AI-Powered Summary Generation**: Structured content extraction with:
   - Business description analysis
   - Founder background extraction
   - Traction and metrics identification
   - Unique selling point detection
8. **Data Cleaning**: Removes duplicates, validates data quality, and ensures sentence integrity
9. **Output Generation**: Saves enhanced data in CSV and JSON formats with timestamps

### Key Features
- **MAXIMUM RELIABILITY**: Enhanced scrolling with 5 techniques ensures capture of ALL available companies
- **Multiple Retry Attempts**: Up to 5 attempts with progressive backoff for maximum success rate
- **Progress Tracking**: Real-time monitoring of company count to detect completion
- **Timeout Protection**: Prevents infinite loops with configurable timeouts
- **Verification Methods**: Additional verification techniques to ensure completeness
- **Best Result Tracking**: Keeps the best result across multiple attempts
- **Error Handling**: Comprehensive error handling and recovery throughout
- **Duplicate Prevention**: Case-insensitive duplicate detection
- **Data Validation**: Ensures data quality and completeness

## 📈 Output Files

### Output Structure
All generated files are organized in a single timestamped output directory with separate scraper and analyzer sections:

```
output_YYYYMMDD_HHMMSS/
├── scraper/                  # Scraped data and HTML tables
│   ├── data/                 # Raw scraped data
│   │   ├── yc_companies_YYYYMMDD_HHMMSS.csv
│   │   └── yc_companies_YYYYMMDD_HHMMSS.json
│   └── html/                 # Scraped data HTML tables
│       └── yc_companies_YYYYMMDD_HHMMSS_table.html
└── analyzer/                 # Analysis results and visualizations
    ├── data/                 # Analysis reports
    │   └── analysis_report_YYYYMMDD_HHMMSS.json
    ├── html/                 # Analysis HTML tables
    │   └── analysis_report_YYYYMMDD_HHMMSS_table.html
    └── charts/               # Interactive Plotly visualizations
        ├── category_distribution.html
        ├── description_length_distribution.html
        ├── batch_distribution.html
        ├── founder_profile_types.html
        └── founders_per_company.html
```

### Data Files
- `scraper/data/yc_companies_YYYYMMDD_HHMMSS.csv`: Scraped company data in CSV format
- `scraper/data/yc_companies_YYYYMMDD_HHMMSS.json`: Scraped company data in JSON format
- `analyzer/data/analysis_report_YYYYMMDD_HHMMSS.json`: Comprehensive analysis report

### HTML Files
- `scraper/html/yc_companies_YYYYMMDD_HHMMSS_table.html`: Interactive HTML table of company data
- `analyzer/html/analysis_report_YYYYMMDD_HHMMSS_table.html`: Interactive HTML table of analysis results

### Chart Files
- `analyzer/charts/category_distribution.html`: Top company categories visualization
- `analyzer/charts/description_length_distribution.html`: Description length analysis
- `analyzer/charts/batch_distribution.html`: Companies by batch visualization
- `analyzer/charts/founder_profile_types.html`: Founder profile types distribution
- `analyzer/charts/founders_per_company.html`: Founders per company distribution

## 📋 Data Structure

The scraper generates company data with the following structure:

### Enhanced Company Record
- `name`: Company name
- `description`: Company description
- `url`: Company profile URL on YC website
- `batch`: YC batch information (Summer 2025)
- `categories`: List of company categories/tags
- `founders`: **Enhanced founder information** with:
  - `name`: Founder's full name
  - `linkedin_url` / `profile_url`: Direct link to LinkedIn profile
  - `profile_type`: Type of profile (linkedin, twitter, github)
  - `title`: Role/position (CEO, CTO, Co-founder, etc.)
- `summary`: **🔥 NEW Enhanced AI-generated summary** with:
  - **"What They Do"**: Clear business description and value proposition
  - **"Specific Insights"**: Founder credentials, traction metrics, and unique aspects
- `scraped_at`: Timestamp when data was collected

## 🔍 Analysis Features

### Category Analysis
- Identifies all unique categories
- Calculates category distribution
- Finds most common categories
- Tracks category trends

### Description Analysis
- Analyzes description lengths
- Extracts common keywords
- Identifies popular themes and technologies

### Data Quality Metrics
- Missing data detection
- Data completeness statistics
- Quality scoring

## 🎯 Investment Insights

### Current YC Summer 2025 Batch Analysis
- **Total Companies**: 143+ (Enhanced capture with improved scraping)
- **B2B Dominance**: 93 companies (~65%) - B2B remains the dominant model
- **AI/ML Revolution**: 90 companies (~63%) leverage AI/ML technology
- **Diverse Sectors**: Healthcare, Fintech, Security, Robotics, Education, Real Estate
- **Global Reach**: Companies from US, UK, Germany, Brazil, and more
- **Founder Network**: 300+ founders with LinkedIn profiles captured
- **Investment Ready**: Complete summaries with traction metrics and founder credentials

### Investment Themes
- **AI/ML Infrastructure & Tools** (Dominant trend with 90 companies)
- **B2B SaaS Solutions** (93 companies focusing on enterprise)
- **Healthcare Technology** (Digital health, AI diagnostics, clinical tools)
- **Financial Technology** (Fintech solutions, payments, lending)
- **Robotics & Manufacturing** (Autonomous systems, industrial automation)
- **Voice AI & Conversational AI** (Emerging trend across multiple sectors)
- **Developer Tools** (Infrastructure, coding agents, MLOps platforms)
- **Real Estate Technology** (PropTech, AI assistants, automation)

## 🔧 Customization

### Adding New Analysis Types
1. Add new methods to the `YCAnalyzer` class in `analyzer.py`
2. Update the `generate_summary_report()` method
3. Add corresponding visualizations in `create_visualizations()`

### Custom Data Sources
1. Format your data according to the expected structure
2. Use the `--input` parameter to specify your data file
3. The analyzer will automatically detect CSV or JSON formats

### Extending the Enhanced Scraper
1. Modify `yc_scraper_robust.py` to add new data extraction methods
2. Update the parsing logic in structured content extraction methods:
   - `_extract_main_description()` for business descriptions
   - `_extract_team_information()` for founder data
   - `_extract_traction_info()` for business metrics
   - `_extract_unique_aspects()` for competitive advantages
3. Add new selectors for different page elements
4. Enhance the `_extract_structured_yc_content()` method for new data types

## 🐛 Troubleshooting

### Common Issues

1. **No data found error**:
   - Ensure your data file exists and is properly formatted
   - Check that the file path is correct
   - Verify the data structure matches the expected format

2. **Missing dependencies**:
   - Activate the virtual environment: `source activate_env.sh`
   - Reinstall dependencies: `pip install -r requirements.txt`
   - Install Playwright browsers: `playwright install chromium`

3. **Scraping issues**:
   - Check internet connection
   - Verify YC website is accessible
   - Ensure Playwright is properly installed
   - Check for rate limiting or anti-bot measures

4. **Browser issues**:
   - Ensure Chromium is installed via Playwright
   - Check system resources (memory, CPU)
   - Verify no firewall blocking browser automation

## 📝 Notes

- **🔥 Enhanced Coverage**: The scraper now captures 143+ companies from the YC Summer 2025 batch with complete summaries
- **Investment-Ready Data**: Each company includes founder LinkedIn profiles, traction metrics, and detailed business descriptions
- **Complete Sentence Integrity**: Advanced parsing ensures no sentences are broken mid-way
- **Timestamped Output**: All reports and charts include timestamps to prevent overwrites
- **Unified Output Structure**: Scraper and analyzer outputs are organized in single timestamped directories
- **Virtual Environment**: All dependencies are isolated in a virtual environment
- **Production Ready**: The tool is designed for regular monitoring and investment analysis
- **Respectful Scraping**: Includes proper delays and follows website terms of service
- **Beautiful HTML Tables**: Enhanced HTML generator creates investor-ready presentations with clickable founder links

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is for educational and research purposes. Please respect YC's terms of service and data usage policies.

## 🎯 Use Cases

1. **Angel Investment Research**: Analyze YC companies for investment opportunities
2. **Market Analysis**: Understand startup ecosystem trends and sector distribution
3. **Competitive Intelligence**: Track emerging companies in specific sectors
4. **Data Collection**: Build comprehensive datasets of YC companies
5. **Academic Research**: Study startup ecosystem patterns and trends
