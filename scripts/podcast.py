from openai import OpenAI
from config.config import prompts
from time import sleep
from datetime import datetime
import os
from halo import Halo
from pathlib import Path
from pydub import AudioSegment

def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)

def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
        return infile.read()

def cut_off_string(input_string, cutoff_string):
    # Find the position of the cutoff string
    cutoff_index = input_string.find(cutoff_string)
    
    # If the cutoff string is found, slice the input string up to that point
    if cutoff_index != -1:
        return input_string[:cutoff_index + len(cutoff_string)], input_string[cutoff_index + len(cutoff_string):]
    else:
        # If the cutoff string is not found, return the original string
        # You can also choose to handle this case differently
        return input_string, ''

def get_link(base_filename):
    with open('data/papers_to_summarize.csv', mode='r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['ID'] == base_filename:
                return row['ArXiv URL']
    return ''
    
def generate_podcast():
    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')

    # Open the combined newsletter text
    newsletter_content = open_file('data/txt-summaries/newsletter.txt').strip()

    # Ensure the audio_files directory exists
    audio_files_path = Path('audio_files')
    audio_files_path.mkdir(exist_ok=True)

    # Initialize variables
    cutoff_str = "\n\n\n\n"
    remaining_text = newsletter_content
    segment_files = []
    first_segment = True

    while remaining_text:
        segment_text, remaining_text = cut_off_string(remaining_text, cutoff_str)
        
        if not segment_text.strip():
            continue

        # Generate audio using OpenAI's API (or another TTS service)
        response = OpenAI.Audio.create(
            model="tts-1",
            text=segment_text[:4096],
            voice="alloy"
        )
        
        segment_file_path = audio_files_path / f"segment_{len(segment_files)}.mp3"

        # Save the audio file
        with open(segment_file_path, 'wb') as audio_file:
            audio_file.write(response.audio_content)

        segment_files.append(segment_file_path)

        if first_segment:
            full_audio = AudioSegment.from_mp3(segment_file_path)
            first_segment = False
        else:
            segment_audio = AudioSegment.from_mp3(segment_file_path)
            full_audio += segment_audio

    # Save the concatenated audio
    date_str = datetime.now().strftime('%Y-%m-%d')
    final_audio_path = audio_files_path / f"{date_str}_newsletter_podcast.mp3"
    full_audio.export(final_audio_path, format="mp3")

    # Clean up the individual segment files
    for segment_file in segment_files:
        os.remove(segment_file)

if __name__ == '__main__':
    generate_podcast()
