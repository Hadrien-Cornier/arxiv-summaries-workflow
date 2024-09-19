import argparse
import csv
import os
import requests
from configparser import ConfigParser

def select_top_papers(input_file, output_dir, config):
    number_of_papers = config.getint('number_of_papers_to_summarize')
    papers = []

    with open(input_file, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            papers.append(row)

    # Sort papers by score
    papers.sort(key=lambda x: int(x['Score']), reverse=True)

    # Select top N papers
    top_papers = papers[:number_of_papers]

    os.makedirs(output_dir, exist_ok=True)

    for paper in top_papers:
        pdf_url = paper['PDF URL']
        pdf_filename = f"{paper['ID']}.pdf"
        pdf_path = os.path.join(output_dir, pdf_filename)
        response = requests.get(pdf_url)
        with open(pdf_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded {pdf_filename}")

    # Save selected papers info
    with open(os.path.join(output_dir, 'papers_to_summarize.csv'), mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Title", "ArXiv URL", "PDF URL", "Published Date", "Score"])
        for paper in top_papers:
            writer.writerow([
                paper['ID'], paper['Title'], paper['ArXiv URL'],
                paper['PDF URL'], paper['Published Date'], paper['Score']
            ])

    print(f"Selected top {len(top_papers)} papers.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Select top arXiv papers.")
    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--output', required=True, help='Output directory')
    args = parser.parse_args()

    config = ConfigParser()
    config.read('config/config.ini')

    select_top_papers(args.input, args.output, config['Configurations'])