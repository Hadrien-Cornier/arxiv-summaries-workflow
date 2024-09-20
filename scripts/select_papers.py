import argparse
import csv
import os
import requests
from configparser import ConfigParser
from typing import List, Dict, Any
from utils import read_papers_from_csv

def select_top_papers(input_file: str, output_dir: str, config: ConfigParser) -> None:
    """Select top papers, download PDFs, and save info to CSV."""
    number_of_papers = config.getint('number_of_papers_to_summarize')
    papers = read_papers_from_csv(input_file)
    top_papers = sorted(papers, key=lambda x: int(x['Score']), reverse=True)[:number_of_papers]
    
    os.makedirs(output_dir, exist_ok=True)
    
    for paper in top_papers:
        pdf_path = os.path.join(output_dir, f"{paper['ID']}.pdf")
        with open(pdf_path, "wb") as f:
            f.write(requests.get(paper['PDF URL']).content)
        print(f"Downloaded {paper['ID']}.pdf")
    
    with open(os.path.join(output_dir, 'papers_to_summarize.csv'), 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Title", "ArXiv URL", "PDF URL", "Published Date", "Score"])
        writer.writerows([paper.values() for paper in top_papers])
    
    print(f"Selected top {len(top_papers)} papers.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Select top arXiv papers.")
    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--output', required=True, help='Output directory')
    args = parser.parse_args()

    config = ConfigParser()
    config.read('config/config.ini')

    select_top_papers(args.input, args.output, config['Configurations'])