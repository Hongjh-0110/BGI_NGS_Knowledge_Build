import json
import xml.etree.ElementTree as ET

import requests

def load_config(config_file='search_config.json'):
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Config file '{config_file}' not found")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format - {e}")
        return None
    except Exception as e:
        print(f"Error: Failed to read config file - {e}")
        return None

def search_pubmed(keyword, email, api_key=None, mindate=None, maxdate=None):
    """Search PubMed for articles matching keyword and date range
    
    Args:
        keyword: Search term
        email: Email address (required by NCBI)
        api_key: Optional NCBI API key for higher rate limits
        mindate: Start date (YYYY/MM/DD or YYYY/MM or YYYY)
        maxdate: End date (YYYY/MM/DD or YYYY/MM or YYYY)
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        'db': 'pubmed',
        'term': keyword,
        'email': email,
        'retmax': 10000
    }
    
    # Add API key if provided (enables higher rate limits)
    if api_key:
        params['api_key'] = api_key
    
    if mindate and maxdate:
        params['mindate'] = mindate
        params['maxdate'] = maxdate
        print(f"Date range: {mindate} to {maxdate}")
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        root = ET.fromstring(response.text)
        id_list = root.find('IdList')
        
        if id_list is not None:
            ids = [id_elem.text for id_elem in id_list.findall('Id')]
            print(f"Keyword '{keyword}': Found {len(ids)} PubMed IDs")
            return ids
        else:
            print(f"Keyword '{keyword}': No results found")
            return []
            
    except ET.ParseError as e:
        print(f"XML parse error: {e}")
        return []
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return []
    except Exception as e:
        print(f"Error processing keyword '{keyword}': {e}")
        return []

def main():
    """Main execution function"""
    config = load_config()
    if not config:
        return
    
    keywords = config.get('search_keywords', [])
    email = config.get('email', '')
    api_key = config.get('NCBI_api', '').strip()
    mindate = config.get('mindate')
    maxdate = config.get('maxdate')
    
    # Validate configuration
    if not keywords:
        print("Error: 'search_keywords' not found in config")
        return
    
    if not email:
        print("Error: 'email' not found in config")
        return
    
    if not mindate or not maxdate:
        print("Error: Both 'mindate' and 'maxdate' are required")
        print("Format: YYYY/MM/DD or YYYY/MM or YYYY")
        return
    
    # Check if API key is provided
    if api_key and api_key.lower() not in ['', 'your_api_key_here_optional', 'optional']:
        print(f"Using API key (enables higher rate limits)")
        max_keywords = 10
    else:
        print("No API key detected (rate limited to 3 requests/second)")
        api_key = None
        max_keywords = 3
    
    # Warn if too many keywords
    if len(keywords) > max_keywords:
        print(f"Warning: You have {len(keywords)} keywords, but limit is {max_keywords}")
        print(f"Consider {'adding an API key' if not api_key else 'reducing keywords'}")
    
    # Search for all keywords
    all_ids = []
    for keyword in keywords:
        print(f"\nProcessing keyword: {keyword}")
        ids = search_pubmed(keyword, email, api_key, mindate, maxdate)
        all_ids.extend(ids)
    
    # Remove duplicates and save
    unique_ids = list(set(all_ids))
    
    with open('pubmed_ids.txt', 'w') as f:
        f.write('\n'.join(unique_ids))
    
    print(f"\nTotal IDs found: {len(all_ids)}")
    print(f"Unique IDs: {len(unique_ids)}")
    print("Results saved to pubmed_ids.txt")

if __name__ == "__main__":
    main()