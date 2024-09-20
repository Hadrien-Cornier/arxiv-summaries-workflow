import configparser
import sys

from scripts.arxiv_search import search_papers
from scripts.select_papers import select_top_papers
from scripts.arxiv_link_downloader import main as downloader_main
from scripts.summarize_papers import summarize_papers
from scripts.podcast import generate_podcast
from scripts.cleanup import cleanup

def main():
    # Initialize configuration
    config = configparser.ConfigParser()
    config.read('config/config.ini')
    
    # Retrieve pipeline steps
    pipeline_steps = [step.strip() for step in config.get('pipeline', 'steps').split(',')]
    
    for step in pipeline_steps:
        print(f"Executing step: {step}")
        if step == 'arxiv_search':
            search_papers(
                input_dir=config.get('arxiv_search', 'input_dir', fallback='data/input'),
                output_dir=config.get('arxiv_search', 'output_dir', fallback='data/output'),
                config=config['arxiv_search']
            )
        elif step == 'select_papers':
            select_top_papers(
                input_file=config.get('select_papers', 'input_file', fallback='data/papers_found.csv'),
                output_dir=config.get('select_papers', 'output_dir', fallback='data/pdfs-to-summarize'),
                config=config['select_papers']
            )
        elif step == 'arxiv_link_downloader':
            downloader_main(
                input_csv=config.get('arxiv_link_downloader', 'input_csv', fallback='data/papers_to_summarize.csv'),
                output_dir=config.get('arxiv_link_downloader', 'output_dir', fallback='data/pdfs'),
                config=config['arxiv_link_downloader']
            )
        elif step == 'summarize_papers':
            summarize_papers(
                input_folder=config.get('summarize_papers', 'input_folder', fallback='data/pdfs-to-summarize'),
                output_folder=config.get('summarize_papers', 'output_folder', fallback='data/txt-summaries')
            )
        elif step == 'podcast':
            generate_podcast(
                newsletter_text_location=config.get('podcast', 'newsletter_text_location', fallback='data/txt-summaries/newsletter.txt'),
                audio_files_path=config.get('podcast', 'audio_files_directory_path', fallback='audio_files')
            )
        elif step == 'cleanup':
            if config.getboolean('cleanup', 'send_to_obsidian', fallback=False):
                cleanup()
        else:
            print(f"Warning: Unknown pipeline step '{step}'")
    
    print("Pipeline execution completed.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred during pipeline execution: {e}")
        sys.exit(1)