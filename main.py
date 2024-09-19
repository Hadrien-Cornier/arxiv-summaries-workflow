from scripts.arxiv_search import search_papers
from scripts.select_papers import select_top_papers
from scripts.summarize_papers import summarize_papers
from scripts.cleanup import cleanup
from config.config import perform_cleanup
from scripts.newsletter_podcast import generate_podcast  # Updated import

def main():
    # Step 1: Search and download papers
    search_papers()

    # Step 2: Select top papers for summarization
    select_top_papers()

    # Step 3: Summarize selected papers
    summarize_papers(
        input_folder='data/pdfs-to-summarize',
        output_folder='data/txt-summaries'
    )

    # Step 4: Generate podcast from summaries
    generate_podcast()  # Correctly calling the generate_podcast function

    # Step 5: Cleanup (if configured)
    if perform_cleanup:
        cleanup()

if __name__ == "__main__":
    main()