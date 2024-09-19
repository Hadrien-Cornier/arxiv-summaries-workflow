import os
import PyPDF2
import csv
from config.config import (
    send_to_obsidian, obsidian_vault_location,
    obsidian_vault_attachments_location, tags_file, prompts,
    search_terms_include_file
)
from openai import OpenAI
from datetime import datetime

def read_lines_from_file(filename):
    """
    Read lines from a text file and store them as strings in a list.
    """
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

def summarize_papers(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    pdf_files = [f for f in os.listdir(input_folder) if f.endswith('.pdf')]
    summaries = ''
    for pdf_file in pdf_files:
        base_filename = pdf_file.replace('.pdf', '')
        link = get_link(base_filename)
        summaries += f"\n\n\n\n# {base_filename}\n{link}"

        filename = f'{output_folder}/{base_filename}.txt'
        if os.path.exists(filename):
            continue

        try:
            with open(f'{input_folder}/{pdf_file}', 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                paper = ''
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    try:
                        paper += page.extract_text()
                    except Exception as e:
                        print(f"Skipping page due to error: {e}")
                        continue
        except PyPDF2.errors.PdfReadError as e:
            print(f"Error reading file {pdf_file}: {e}")
            continue

        if len(paper) > 176000:
            paper = paper[:176000]

        all_messages = [{'role': 'system', 'content': paper}]
        for p in prompts:
            all_messages.append({'role': 'user', 'content': p})
            answer = chatbot(all_messages)
            all_messages.append({'role': 'assistant', 'content': answer})
            summaries += f'\n{answer}'

        # Save the summary to a text file
        with open(filename, 'w', encoding='utf-8') as summary_file:
            summary_file.write(summaries)

        # Write summary to Obsidian if configured
        if send_to_obsidian:
            tags = determine_tags(paper)
            obsidian_content = f"---\ntags: {', '.join(tags)}\n---\n\n{summaries}"
            obsidian_filename = os.path.join(obsidian_vault_location, f"{base_filename}.md")
            with open(obsidian_filename, 'w', encoding='utf-8') as f:
                f.write(obsidian_content)

    # Write the combined summaries to 'newsletter.txt'
    with open('data/txt-summaries/newsletter.txt', 'w', encoding='utf-8') as outfile:
        outfile.write(f"{summaries}")

def chatbot(conversation, model="gpt-4o-mini", temperature=0.7):
    max_retry = 3
    retry = 0
    while True:
        try:
            response = OpenAI.Completion.create(
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

def get_link(base_filename):
    with open('data/papers_to_summarize.csv', mode='r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['ID'] == base_filename:
                return row['ArXiv URL']
    return ''

def determine_tags(abstract):
    include_terms = read_lines_from_file(search_terms_include_file)
    tags = []
    for term in include_terms:
        if term.lower() in abstract.lower() and term not in tags:
            tags.append(term)
        if len(tags) >= 3:
            break
    return tags