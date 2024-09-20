import argparse
import os
import re
import requests
import arxiv
import csv
from datetime import datetime
from configparser import ConfigParser
from typing import List, Dict, Any, Optional
from utils import read_lines_from_file

def download_pdf(url: str, filepath: str) -> None:
    """Download a PDF from a given URL and save it to the specified filepath."""
    response = requests.get(url)
    with open(filepath, "wb") as f:
        f.write(response.content)

def add_to_links_file(title: str, arxiv_url: str, config: ConfigParser) -> None:
    """Add a paper's title and arXiv URL to the links file if it doesn't already exist."""
    links_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                              'data', 
                              config.get('arvix_link_downloader', 'links_file_location'))
    
    line = f'{title} | {arxiv_url}'
    existing_lines = set(read_lines_from_file(links_file))
    
    if line.strip() not in existing_lines:
        with open(links_file, 'a') as file:
            file.write(line + '\n')
        print(f"Added to links file: {line}")
    else:
        print(f'Line already exists in links file - Skipping')

def add_to_csv_file(title: str, arxiv_url: str, published_date: datetime, output_dir: str) -> None:
    """Add paper information to both 'papers_seen.csv' and 'papers_downloaded.csv'."""
    csv_files = [os.path.join(output_dir, filename) for filename in ["papers_seen.csv", "papers_downloaded.csv"]]
    today_date = datetime.now().strftime('%Y-%m-%d')
    row = [title, arxiv_url, published_date, today_date]

    for csv_file in csv_files:
        file_exists = os.path.isfile(csv_file)
        with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["Title", "ArXiv Link", "Paper Date", "Date Added"])
            writer.writerow(row)
        print(f"Added to {os.path.basename(csv_file)}: {title}")

def process_arxiv_url(arxiv_url: str, output_dir: str, config: ConfigParser) -> None:
    """Process an arXiv URL: download the PDF, update links file, and CSV files."""
    arxiv_id = re.sub(r'v\d+$', '', arxiv_url.split('/')[-1])
    paper = next(arxiv.Client().results(arxiv.Search(id_list=[arxiv_id])))

    safe_title = re.sub(r'[<>:"/\\|?*]', ' -', paper.title)
    filepath = os.path.join(output_dir, f"{safe_title}.pdf")

    download_pdf(paper.pdf_url, filepath)
    print(f"Downloaded: {filepath}")

    add_to_links_file(safe_title, arxiv_url, config)
    add_to_csv_file(safe_title, arxiv_url, paper.published.date(), output_dir)

def main(input_csv: str, output_dir: str, config: ConfigParser) -> None:
    """Main function to process arXiv URLs from an input CSV file."""
    os.makedirs(output_dir, exist_ok=True)

    with open(input_csv, mode='r', newline='', encoding='utf-8') as file:
        for row in csv.DictReader(file):
            process_arxiv_url(row['ArXiv URL'], output_dir, config)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download arXiv PDFs and update records.")
    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--output', required=True, help='Output directory')
    args = parser.parse_args()

    config = ConfigParser()
    config.read('config/config.ini')

    main(args.input, args.output, config)