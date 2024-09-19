import argparse
import arxiv
import os
import csv
import re
import requests
from datetime import datetime, timedelta
from configparser import ConfigParser

def read_lines_from_file(filename):
    lines = []
    try:
        with open(filename, 'r') as file:
            for line in file:
                lines.append(line.strip())
    except FileNotFoundError:
        print(f"File not found: {filename}.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return lines

def compute_relevance_score(title, abstract, include_terms):
    score = 0
    for term in include_terms:
        if term.lower() in title.lower():
            score += 2  # Higher weight for title matches
        if term.lower() in abstract.lower():
            score += 1
    return score

def search_papers(input_dir, output_dir, config):
    restrict_to_most_recent = config.getboolean('restrict_to_most_recent')
    max_results = config.getint('max_results')
    categories = config.get('categories')
    date_range = config.getint('date_range')
    include_terms = read_lines_from_file(config.get('tags_file'))
    exclude_terms = read_lines_from_file(config.get('search_terms_exclude_file'))

    start_date = datetime.now() - timedelta(days=date_range)
    query = f"({categories}) AND submittedDate:[{start_date.strftime('%Y%m%d')} TO {datetime.now().strftime('%Y%m%d')}]"

    client = arxiv.Client(
        page_size=max_results,
        delay_seconds=5.0,
        num_retries=3
    )

    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )

    papers = []
    for result in client.results(search):
        if restrict_to_most_recent and (result.published.date() <= start_date.date()):
            with open(os.path.join(output_dir, 'most_recent_day_searched.txt'), 'w') as file:
                file.write(result.published.date().strftime('%Y-%m-%d'))
            break
        score = compute_relevance_score(result.title, result.summary, include_terms)
        papers.append({
            "id": result.get_short_id(),
            "title": result.title,
            "arxiv_url": result.entry_id,
            "pdf_url": result.pdf_url,
            "published_date": result.published.date(),
            "abstract": result.summary,
            "score": score
        })

    # Sort papers by relevance score
    papers.sort(key=lambda x: x['score'], reverse=True)

    # Write the papers to a CSV for later processing
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, 'papers_found.csv'), mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Title", "ArXiv URL", "PDF URL", "Published Date", "Score"])
        for paper in papers:
            writer.writerow([
                paper['id'], paper['title'], paper['arxiv_url'],
                paper['pdf_url'], paper['published_date'], paper['score']
            ])

    print(f"Found {len(papers)} papers.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search arXiv papers.")
    parser.add_argument('--input', required=True, help='Input directory')
    parser.add_argument('--output', required=True, help='Output directory')
    args = parser.parse_args()

    config = ConfigParser()
    config.read('config/config.ini')

    search_papers(args.input, args.output, config['Configurations'])