import json
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import markdown
from tqdm import tqdm
from pubmed_mapper import Article

# Configuration
MAX_WORKERS = 5
BATCH_SIZE = 1
BASE_DIR = Path(__file__).parent
BASE_DIR.mkdir(exist_ok=True)

def fetch_article_data(pmid, retries=3):
    """Fetch article data for a single PMID with retry logic"""
    for attempt in range(retries):
        try:
            article = Article.parse_pmid(pmid)
            authors = [str([author, author.affiliation]) for author in article.authors]
            doi = next((id_obj.id_value for id_obj in article.ids if id_obj.id_type == 'doi'), None)
            pmc_id = next((id_obj.id_value for id_obj in article.ids if id_obj.id_type == 'pmc'), None)
            
            return {
                "pub_id": pmid,
                "doi": doi,
                "pmc_id": pmc_id,
                "abstract": article.abstract or "",
                "title": article.title or "",
                "keyword": article.keywords if hasattr(article, 'keywords') else [],
                "first_author_affiliation": authors[0] if authors else None,
                "communicate_author_affiliation": authors[-1] if authors else None,
                "journal": article.journal.title if article.journal else None,
                "pub_date": str(article.pubdate) if article.pubdate else None
            }
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(3 ** attempt)
            else:
                print(f"Failed to process {pmid}: {str(e)}")
                return None
    return None

def process_batch(batch):
    """Process a batch of PMIDs"""
    results = []
    for pmid in batch:
        article_data = fetch_article_data(pmid)
        if article_data and article_data["abstract"] and article_data["doi"]:
            results.append(article_data)
    return results, batch

def format_article_markdown(data):
    """Format article data as markdown"""
    lines = [
        f"#### {data['title']}\n",
        f"- **Article ID**: {data['pub_id']}\n",
        f"- **DOI**: {data['doi']}\n",
        f"- **Keywords**: {', '.join(data['keyword'])}\n",
        f"- **First Author Affiliation**: {data['first_author_affiliation']}\n",
        f"- **Corresponding Author Affiliation**: {data['communicate_author_affiliation']}\n",
        f"- **Journal**: {data['journal']}\n",
        f"- **Publication Date**: {data['pub_date']}\n",
        f"**Abstract**: {data['abstract']}\n\n"
    ]
    return ''.join(lines)

def has_github_link(abstract):
    """Check if abstract contains GitHub link"""
    return "ithub" in abstract or "avaliable" in abstract

def md_to_html(md_content):
    """Convert markdown to HTML with styling"""
    html_content = markdown.markdown(md_content)
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
body {{ font-family: "Microsoft YaHei", "SimSun", sans-serif; margin: 2cm; line-height: 1.6; }}
h1, h2, h3 {{ color: #333; }}
code {{ background-color: #f5f5f5; padding: 2px 4px; }}
pre {{ background-color: #f5f5f5; padding: 10px; }}
</style>
</head><body>{html_content}</body></html>"""

def save_json_lines(filepath, data_list):
    """Save list of dicts as JSON lines"""
    with open(filepath, 'w', encoding='utf-8') as f:
        for item in data_list:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

def generate_outputs(prefix, select_link=True):
    """Generate all output files from JSON data"""
    json_file = f"{prefix}id_information.json"
    
    # Read all data
    with open(json_file, 'r', encoding='utf-8') as f:
        articles = [json.loads(line) for line in f if line.strip()]
    
    # Separate data
    pmcids = []
    no_pmcids = []
    all_md = []
    link_articles = []
    no_link_articles = []
    
    for article in articles:
        # Extract PMC IDs
        if article['pmc_id']:
            pmcids.append(article['pmc_id'])
        else:
            no_pmcids.append(article)
        
        # Format markdown
        md_text = format_article_markdown(article)
        all_md.append(md_text)
        
        # Separate by GitHub link
        if select_link:
            if has_github_link(article['abstract']):
                link_articles.append(article)
            else:
                no_link_articles.append(article)
    
    # Save outputs
    with open("pmcids.txt", 'w', encoding='utf-8') as f:
        f.write('\n'.join(pmcids))
    
    save_json_lines("no_pmcids.json", no_pmcids)
    
    # Save markdown and HTML
    md_content = ''.join(all_md)
    with open(f"{prefix}id_information.md", 'w', encoding='utf-8') as f:
        f.write(md_content)
    with open(f"{prefix}id_information.html", 'w', encoding='utf-8') as f:
        f.write(md_to_html(md_content))
    
    if select_link:
        # Link articles
        save_json_lines(f"{prefix}link_id_information.json", link_articles)
        link_md = ''.join([format_article_markdown(a) for a in link_articles])
        with open(f"{prefix}link_id_information.md", 'w', encoding='utf-8') as f:
            f.write(link_md)
        with open(f"{prefix}link_id_information.html", 'w', encoding='utf-8') as f:
            f.write(md_to_html(link_md))
        
        # No link articles
        save_json_lines(f"{prefix}no_link_id_information.json", no_link_articles)
        no_link_md = ''.join([format_article_markdown(a) for a in no_link_articles])
        with open(f"{prefix}no_link_id_information.md", 'w', encoding='utf-8') as f:
            f.write(no_link_md)
        with open(f"{prefix}no_link_id_information.html", 'w', encoding='utf-8') as f:
            f.write(md_to_html(no_link_md))
    
    print(f"Generated output files with {len(articles)} articles")

def process_all_ids(pm_ids, prefix="", select_link=True):
    """Process all PMIDs with multithreading"""
    batches = [pm_ids[i:i+BATCH_SIZE] for i in range(0, len(pm_ids), BATCH_SIZE)]
    failed_ids = []
    
    # Initialize output file
    json_file = f"{prefix}id_information.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        f.write("")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_batch, batch) for batch in batches]
        
        with tqdm(total=len(batches), desc="Processing") as pbar:
            for future in as_completed(futures):
                results, current_batch = future.result()
                if results:
                    # Write successful results
                    with open(json_file, "a", encoding="utf-8") as f:
                        for result in results:
                            f.write(json.dumps(result, ensure_ascii=False) + '\n')
                else:
                    failed_ids.extend(current_batch)
                pbar.update(1)
    
    # Generate all output files
    try:
        generate_outputs(prefix, select_link)
    except Exception as e:
        print(f"Error generating output files: {e}")
        return
    
    # Save failed IDs
    if failed_ids:
        with open("failed_ids.txt", "w") as f:
            f.write("\n".join(failed_ids))
        print(f"Saved {len(failed_ids)} failed IDs to failed_ids.txt")

if __name__ == "__main__":
    input_file = BASE_DIR / "pubmed_ids.txt"
    
    with open(input_file) as f:
        pm_ids = [line.strip() for line in f if line.strip()]
    
    print(f"Processing {len(pm_ids)} articles...")
    process_all_ids(pm_ids, prefix="", select_link=True)
    print("Done!")
