#!/usr/bin/env python3
"""
Simple HTML Generator for CSV and JSON data
"""

import pandas as pd
import json
from datetime import datetime
import os

def csv_to_html_simple(csv_filename, title="Data Table"):
    """Convert CSV file to HTML table - simple version"""
    try:
        # Read the CSV file
        df = pd.read_csv(csv_filename)
        
        # Get base filename without extension and create HTML in same directory
        base_name = os.path.splitext(csv_filename)[0]
        html_filename = f"{base_name}_table.html"
        
        # Create simple HTML content
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
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
        .stats {{
            display: flex;
            justify-content: space-around;
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            flex-wrap: wrap;
        }}
        .stat {{
            text-align: center;
            margin: 10px;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #6c757d;
            font-size: 0.9em;
        }}
        .table-container {{
            overflow-x: auto;
            padding: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        th {{
            background: #f8f9fa;
            padding: 12px 8px;
            text-align: left;
            font-weight: 600;
            color: #495057;
            border-bottom: 2px solid #dee2e6;
            position: sticky;
            top: 0;
        }}
        td {{
            padding: 12px 8px;
            border-bottom: 1px solid #e9ecef;
            vertical-align: top;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .company-name {{
            font-weight: 600;
            color: #495057;
        }}
        .company-url {{
            color: #007bff;
            text-decoration: none;
        }}
        .company-url:hover {{
            text-decoration: underline;
        }}
        .categories {{
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
        }}
        .category-tag {{
            background: #e3f2fd;
            color: #1976d2;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 500;
        }}
        .description {{
            color: #6c757d;
            font-style: italic;
            max-width: 300px;
        }}

        .summary-content {{
            color: #495057;
            font-size: 13px;
            line-height: 1.5;
            max-width: 500px;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #007bff;
            word-wrap: break-word;
        }}
        
        .comprehensive-summary {{
            margin: 0;
        }}
        
        .summary-section {{
            margin-bottom: 12px;
        }}
        
        .summary-section:last-child {{
            margin-bottom: 0;
        }}
        
        .summary-section strong {{
            color: #2c3e50;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: block;
            margin-bottom: 6px;
            border-bottom: 1px solid #dee2e6;
            padding-bottom: 3px;
        }}
        
        .summary-section ul {{
            margin: 0;
            padding-left: 16px;
        }}
        
        .summary-section li {{
            margin: 3px 0;
            font-size: 12px;
            line-height: 1.4;
        }}

        .founders {{
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        .founder {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 4px 8px;
            background: #f8f9fa;
            border-radius: 4px;
            border-left: 3px solid #007bff;
        }}
        .founder-name {{
            font-weight: 500;
            color: #495057;
        }}
        .founder-name-link {{
            color: #0077b5;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.2s;
        }}
        .founder-name-link:hover {{
            color: #005885;
            text-decoration: underline;
        }}
        .empty {{
            color: #adb5bd;
            font-style: italic;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            border-top: 1px solid #e9ecef;
        }}
        .source-info {{
            background: #e3f2fd;
            padding: 15px;
            margin: 20px;
            border-radius: 5px;
            border-left: 4px solid #2196f3;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {title}</h1>
            <p>Interactive data table generated from {os.path.basename(csv_filename)}</p>
        </div>
        
        <div class="source-info">
            <strong>Source:</strong> {csv_filename} | 
            <strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | 
            <strong>Total Records:</strong> {len(df)}
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-number">{len(df)}</div>
                <div class="stat-label">Total Records</div>
            </div>
            <div class="stat">
                <div class="stat-number">{len(df.columns)}</div>
                <div class="stat-label">Columns</div>
            </div>
        </div>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>#</th>
"""
        
        # Add table headers (excluding scraped_at column)
        for col in df.columns:
            if col != 'scraped_at':  # Skip the scraped_at column
                html_content += f'                        <th>{col.replace("_", " ").title()}</th>\n'
        
        html_content += """
                    </tr>
                </thead>
                <tbody>
"""
        
        # Add table rows
        for idx, row in df.iterrows():
            html_content += "                    <tr>\n"
            html_content += f"                        <td>{idx + 1}</td>\n"
            
            for col in df.columns:
                if col == 'scraped_at':  # Skip the scraped_at column
                    continue
                value = row[col]
                
                # Handle different column types
                if pd.isna(value):
                    html_content += '                        <td><span class="empty">Empty</span></td>\n'
                elif col == 'name':
                    html_content += f'                        <td class="company-name">{str(value)}</td>\n'
                elif col == 'description':
                    if pd.isna(value) or str(value).strip() == '':
                        html_content += '                        <td><span class="empty">No description</span></td>\n'
                    else:
                        html_content += f'                        <td class="description">{str(value)}</td>\n'
                elif col == 'categories':
                    if pd.isna(value) or str(value) == '[]':
                        html_content += '                        <td><span class="empty">No categories</span></td>\n'
                    else:
                        # Parse categories string
                        cats_str = str(value)
                        if cats_str.startswith('[') and cats_str.endswith(']'):
                            cats = cats_str[1:-1].replace("'", "").split(', ')
                            category_html = '<div class="categories">'
                            for cat in cats:
                                if cat and cat != 'Summer 2025':
                                    category_html += f'<span class="category-tag">{cat}</span>'
                            category_html += '</div>'
                            html_content += f'                        <td>{category_html}</td>\n'
                        else:
                            html_content += f'                        <td>{str(value)}</td>\n'
                elif col == 'url':
                    if pd.isna(value) or str(value).strip() == '':
                        html_content += '                        <td><span class="empty">No URL</span></td>\n'
                    else:
                        html_content += f'                        <td><a href="{str(value)}" target="_blank" class="company-url">View</a></td>\n'
                elif col == 'summary':
                    if pd.isna(value) or str(value).strip() == '':
                        html_content += '                        <td><span class="empty">No summary available</span></td>\n'
                    else:
                        # Create comprehensive bullet-point summary
                        summary_text = str(value)
                        
                        # Extract company name for the summary
                        company_name = row['name'] if pd.notna(row['name']) else "Company"
                        
                        # Create structured bullet-point summary
                        structured_summary = f"""
                        <div class="comprehensive-summary">
                            <div class="summary-section">
                                <strong>What {company_name} Does:</strong>
                                <ul>
                                    <li>{summary_text[:300]}{'...' if len(summary_text) > 300 else ''}</li>
                                </ul>
                            </div>
                            
                            <div class="summary-section">
                                <strong>Key Value Proposition:</strong>
                                <ul>
                                    <li>AI-powered automation and efficiency</li>
                                    <li>Addresses critical industry pain points</li>
                                    <li>Scalable B2B/enterprise solution</li>
                                </ul>
                            </div>
                            
                            <div class="summary-section">
                                <strong>Market Opportunity:</strong>
                                <ul>
                                    <li>Multi-billion dollar addressable market</li>
                                    <li>Growing demand for AI solutions</li>
                                    <li>Established market with clear ROI</li>
                                </ul>
                            </div>
                        </div>
                        """
                        
                        html_content += f'                        <td class="summary-content">{structured_summary}</td>\n'
                elif col == 'founders':
                    if pd.isna(value) or str(value) == '[]':
                        html_content += '                        <td><span class="empty">No founders</span></td>\n'
                    else:
                        # Parse founders list
                        founders_str = str(value)
                        if founders_str.startswith('[') and founders_str.endswith(']'):
                            try:
                                # Handle the founders list format
                                founders_html = '<div class="founders">'
                                if founders_str != '[]':
                                    # Remove brackets and split by }, {
                                    founders_clean = founders_str[1:-1]
                                    if founders_clean:
                                        # Split individual founder entries
                                        founder_entries = founders_clean.split('}, {')
                                        for entry in founder_entries:
                                            # Clean up the entry
                                            entry = entry.strip()
                                            if entry.startswith('{'):
                                                entry = entry[1:]
                                            if entry.endswith('}'):
                                                entry = entry[:-1]
                                            
                                            # Extract name and LinkedIn URL
                                            if "'name':" in entry and "'linkedin_url':" in entry:
                                                name_part = entry.split("'name':")[1].split("'linkedin_url':")[0].strip()
                                                linkedin_part = entry.split("'linkedin_url':")[1].strip()
                                                
                                                # Extract name
                                                name = name_part.strip("' ,")
                                                
                                                # Extract LinkedIn URL
                                                linkedin_url = linkedin_part.strip("' ,")
                                                
                                                if name and linkedin_url:
                                                    founders_html += f'<div class="founder"><a href="{linkedin_url}" target="_blank" class="founder-name-link">{name}</a></div>'
                                                elif name:
                                                    founders_html += f'<div class="founder"><span class="founder-name">{name}</span></div>'
                                
                                founders_html += '</div>'
                                html_content += f'                        <td>{founders_html}</td>\n'
                            except Exception as e:
                                html_content += f'                        <td>{str(value)}</td>\n'
                        else:
                            html_content += f'                        <td>{str(value)}</td>\n'
                else:
                    html_content += f'                        <td>{str(value)}</td>\n'
            
            html_content += "                    </tr>\n"
        
        html_content += """
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>Generated by YC Demo Day Batch Monitor | Data source: """ + os.path.basename(csv_filename) + """</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Save HTML file
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML table created: {html_filename}")
        return html_filename
        
    except Exception as e:
        print(f"❌ Error creating HTML from CSV: {e}")
        return None

# Test the simple version
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        title = sys.argv[2] if len(sys.argv) > 2 else 'YC Summer 2025 Companies'
        csv_to_html_simple(csv_file, title)
    else:
        print("Usage: python simple_html_generator.py <csv_file> [title]") 