import argparse
import arxiv
import os
import csv
from datetime import datetime, timedelta
from configparser import ConfigParser
from typing import List, Dict, Any
from utils import read_lines_from_file

def compute_relevance_score(title: str, abstract: str, include_terms: List[str]) -> int:
    """Compute relevance score based on term occurrences in title and abstract."""
    return sum(2 if term.lower() in title.lower() else 1 if term.lower() in abstract.lower() else 0 for term in include_terms)

def search_papers(input_dir: str, output_dir: str, config: ConfigParser) -> None:
    """
    Search for papers on arXiv based on given configuration.
    
    Args:
    input_dir (str): Directory containing input files.
    output_dir (str): Directory to save output files.
    config (ConfigParser): Configuration object with search parameters.
    """
    # Load configuration
    restrict_to_most_recent: bool = config.getboolean('restrict_to_most_recent')
    max_results: int = config.getint('max_results')
    categories: str = config.get('categories')
    date_range: int = config.getint('date_range')
    include_terms: List[str] = read_lines_from_file(config.get('tags_file'))

    # Prepare search query
    start_date: datetime = datetime.now() - timedelta(days=date_range)
    query: str = f"({categories}) AND submittedDate:[{start_date.strftime('%Y%m%d')} TO {datetime.now().strftime('%Y%m%d')}]"

    # Set up arXiv client and search
    client: arxiv.Client = arxiv.Client(page_size=max_results, delay_seconds=5.0, num_retries=3)
    search: arxiv.Search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )

    # Perform search and process results
    papers: List[Dict[str, Any]] = []
    for result in client.results(search):
        if restrict_to_most_recent and (result.published.date() <= start_date.date()):
            with open(os.path.join(output_dir, 'most_recent_day_searched.txt'), 'w') as file:
                file.write(result.published.date().strftime('%Y-%m-%d'))
            break
        
        score: int = compute_relevance_score(result.title, result.summary, include_terms)
        papers.append({
            "id": result.get_short_id(),
            "title": result.title,
            "arxiv_url": result.entry_id,
            "pdf_url": result.pdf_url,
            "published_date": result.published.date(),
            "score": score
        })

    # Sort papers by relevance score
    papers.sort(key=lambda x: x['score'], reverse=True)

    # Write results to CSV
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, 'papers_found.csv'), mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Title", "ArXiv URL", "PDF URL", "Published Date", "Score"])
        for paper in papers:
            writer.writerow([paper[key] for key in ["id", "title", "arxiv_url", "pdf_url", "published_date", "score"]])

    print(f"Found {len(papers)} papers.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search arXiv papers.")
    parser.add_argument('--input', required=True, help='Input directory')
    parser.add_argument('--output', required=True, help='Output directory')
    args = parser.parse_args()

    config = ConfigParser()
    config.read('config/config.ini')

    search_papers(args.input, args.output, config['Configurations'])