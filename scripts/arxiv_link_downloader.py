import argparse
import os
import re
import requests
import arxiv
import csv
from datetime import datetime
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

def download_pdf(url, filepath):
    response = requests.get(url)
    with open(filepath, "wb") as f:
        f.write(response.content)

def add_to_links_file(title, arxiv_url, output_dir):
    line = f'{title} | {arxiv_url}'
    links_file = os.path.join(output_dir, 'links.txt')
    try:
        with open(links_file, 'r') as file:
            existing_lines = file.readlines()
            if any(line.strip() == l.strip() for l in existing_lines):
                print(f'Line already exists in links.txt - Skipping')
                return
    except FileNotFoundError:
        pass

    with open(links_file, 'a') as file:
        file.write(line + '\n')
    print(f"Added to links.txt: {line}")

def add_to_csv_file(title, arxiv_url, published_date, output_dir):
    csv_file_seen = os.path.join(output_dir, "papers_seen.csv")
    csv_file_downloaded = os.path.join(output_dir, "papers_downloaded.csv")
    today_date = datetime.now().strftime('%Y-%m-%d')

    # Initialize CSV files with headers if they don't exist
    for csv_file in [csv_file_seen, csv_file_downloaded]:
        if not os.path.isfile(csv_file):
            with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["Title", "ArXiv Link", "Paper Date", "Date Added"])

    # Write to CSVs
    with open(csv_file_seen, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([title, arxiv_url, published_date, today_date])
    print(f"Added to {csv_file_seen}: {title}")

    with open(csv_file_downloaded, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([title, arxiv_url, published_date, today_date])
    print(f"Added to {csv_file_downloaded}: {title}")

def process_arxiv_url(arxiv_url, output_dir):
    # Extract the arXiv ID from the URL
    arxiv_id = re.sub(r'v\d+$', '', arxiv_url.split('/')[-1])
    search = arxiv.Search(id_list=[arxiv_id])
    paper = next(arxiv.Client().results(search))

    # Create a valid filename from the paper title
    safe_title = re.sub(r'[<>:"/\\|?*]', ' -', paper.title)  # Replace invalid filename characters
    filename = f"{safe_title}.pdf"
    filepath = os.path.join(output_dir, filename)

    # Download the PDF
    download_pdf(paper.pdf_url, filepath)
    print(f"Downloaded: {filepath}")

    # Add to links.txt
    add_to_links_file(safe_title, arxiv_url, output_dir)

    # Add to CSV files
    add_to_csv_file(safe_title, arxiv_url, paper.published.date(), output_dir)

def main(input_csv, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(input_csv, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            process_arxiv_url(row['ID'], row['ArXiv URL'], output_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download arXiv PDFs and update records.")
    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--output', required=True, help='Output directory')
    args = parser.parse_args()

    config = ConfigParser()
    config.read('config/config.ini')

    main(args.input, args.output)