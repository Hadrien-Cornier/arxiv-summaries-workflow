import os
import PyPDF2
from config.config import prompts
from openai import OpenAI

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
                    except KeyError as e:
                        print(f"Skipping page due to missing information: {e}")
                        continue
        except PyPDF2.errors.PdfReadError:
            print(f"Error reading file: {pdf_file}")
            continue

        if len(paper) > 176000:
            paper = paper[:176000]

        all_messages = [{'role': 'system', 'content': paper}]
        for p in prompts:
            all_messages.append({'role': 'user', 'content': p})
            answer = chatbot(all_messages)
            all_messages.append({'role': 'assistant', 'content': answer})
            summaries += f'\n{answer}'

    with open('newsletter.txt', 'a') as outfile:
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
                return "Error: " + str(e)
            sleep(1)

def get_link(base_filename):
    with open('data/papers_downloaded.csv', mode='r', newline='') as file:
        reader = csv.reader(file)
        headers = next(reader)
        for row in reader:
            if row[0] == base_filename:
                return row[1]
    return ''