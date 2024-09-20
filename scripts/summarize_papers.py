import os
from typing import List, Dict, Any
from config.config import (
    send_to_obsidian, obsidian_vault_location,
    prompts,
    search_terms_include_file
)
from openai import OpenAI
from utils import read_lines_from_file, get_link
from time import sleep

def summarize_papers(input_folder: str, output_folder: str) -> None:
    """Process PDF files, generate summaries, and save them to output folder and optionally Obsidian."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    pdf_files: List[str] = [f for f in os.listdir(input_folder) if f.endswith('.pdf')]
    summaries: str = ''
    for pdf_file in pdf_files:
        base_filename: str = pdf_file.replace('.pdf', '')
        link: str = get_link(base_filename)
        summaries += f"\n\n\n\n# {base_filename}\n{link}"

        filename: str = f'{output_folder}/{base_filename}.txt'
        if os.path.exists(filename):
            continue

        paper: str = extract_text_from_pdf(f'{input_folder}/{pdf_file}')
        if paper:
            summaries += generate_summary(paper)

        with open(filename, 'w', encoding='utf-8') as summary_file:
            summary_file.write(summaries)

        if send_to_obsidian:
            write_to_obsidian(base_filename, paper, summaries)

    with open('data/txt-summaries/newsletter.txt', 'w', encoding='utf-8') as outfile:
        outfile.write(f"{summaries}")


def chatbot(conversation: List[Dict[str, str]], model: str = "gpt-4o-mini", temperature: float = 0.7) -> str:
    """Interact with the OpenAI chatbot to generate responses."""
    max_retry: int = 3
    retry: int = 0
    while True:
        try:
            response: Any = OpenAI.Completion.create(
                model=model,
                prompt=conversation,
                temperature=temperature,
                max_tokens=1500,
                n=1,
                stop=None
            )
            return response.choices[0].text.strip()
        except Exception as e:
            retry += 1
            if retry >= max_retry:
                print(f"Error: {e}")
                return "Error: " + str(e)
            sleep(1)

def determine_tags(abstract: str) -> List[str]:
    """Determine tags for a paper based on its abstract."""
    include_terms: List[str] = read_lines_from_file(search_terms_include_file)
    tags: List[str] = []
    for term in include_terms:
        if term.lower() in abstract.lower() and term not in tags:
            tags.append(term)
        if len(tags) >= 3:
            break
    return tags

def generate_summary(paper: str) -> str:
    """Generate a summary for a paper using the chatbot."""
    all_messages: List[Dict[str, str]] = [{'role': 'system', 'content': paper}]
    summary: str = ''
    for p in prompts:
        all_messages.append({'role': 'user', 'content': p})
        answer: str = chatbot(all_messages)
        all_messages.append({'role': 'assistant', 'content': answer})
        summary += f'\n{answer}'
    return summary

def write_to_obsidian(base_filename: str, paper: str, summaries: str) -> None:
    """Write the summary to an Obsidian vault."""
    tags: List[str] = determine_tags(paper)
    obsidian_content: str = f"---\ntags: {', '.join(tags)}\n---\n\n{summaries}"
    obsidian_filename: str = os.path.join(obsidian_vault_location, f"{base_filename}.md")
    with open(obsidian_filename, 'w', encoding='utf-8') as f:
        f.write(obsidian_content)