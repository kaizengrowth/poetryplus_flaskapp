import spacy
from music21 import stream, note
from midi2audio import FluidSynth
from datetime import datetime
import os
from flask import Flask, request, render_template, send_from_directory
from v_plus_seven import process_v_plus_7, load_dictionary
from a_plus_seven import process_a_plus_7
import requests
import re
import random

app = Flask(__name__)

# Load your dictionary data once when the app starts
dictionary_data = load_dictionary('/home/kaizenagility/oulipo/dictionary.json')

# Function to fetch a random rhyme using the DataMuse API


def fetch_random_rhyme(word):
    api_url = f"http://api.datamuse.com/words?rel_rhy={word}"
    response = requests.get(api_url)
    if response.status_code == 200 and response.json():
        rhymes = response.json()
        random_rhyme = random.choice(rhymes)['word'].upper()
        return random_rhyme + " "
    else:
        return word.upper() + " "

# Function to replace every seventh word with a random rhyme


def replace_every_seventh_with_random_rhyme(text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    transformed_words = []

    for i, token in enumerate(doc):
        if token.is_alpha:
            if (i + 1) % 7 == 0:
                rhyme = fetch_random_rhyme(token.text)
                transformed_words.append(rhyme)
            else:
                transformed_words.append(token.text_with_ws)
        else:
            transformed_words.append(token.text_with_ws)

    return ''.join(transformed_words)


def get_every_seventh_character(text):
    # Select every seventh character from the text
    return [char for i, char in enumerate(text) if (i + 1) % 7 == 0 and char.isalpha()]


def char_to_pitch(char):
    # Map the character's position in the alphabet to a MIDI pitch
    base_note = 60  # Middle C
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    char_position = alphabet.index(
        char.lower()) if char.lower() in alphabet else 0
    # Keep within an octave for simplicity
    return base_note + (char_position % 12)


def convert_midi_to_wav(midi_path, wav_path):
    # Initialize FluidSynth with a specific SoundFont
    soundfont_path = os.path.join(app.root_path, 'static', 'soundfont.sf2')
    fs = FluidSynth(soundfont_path)
    fs.midi_to_audio(midi_path, wav_path)


def create_music_with_music21(chars, filename="latest_output.midi"):
    # Get every seventh character from the text
    chars = get_every_seventh_character(text)

    # Create a music21 stream to hold the music
    part = stream.Part()

    for char in chars:
        # Use the char_to_pitch function to determine the pitch
        # Convert character position to MIDI pitch
        midi_pitch = char_to_pitch(char)
        new_note = note.Note(midi_pitch)
        new_note.duration.type = 'quarter'  # Set note duration to a quarter note
        part.append(new_note)

    # Define the paths for the MIDI and WAV files
    midi_path = os.path.join(app.root_path, 'static', 'midi', filename)
    wav_filename = filename.replace('.midi', '.wav')
    wav_path = os.path.join(app.root_path, 'static', 'audio', wav_filename)

    # Save the MIDI file
    part.write('midi', fp=midi_path)

    # Convert MIDI to WAV using midi2audio
    convert_midi_to_wav(midi_path, wav_path)

    # Return relative path for the WAV file for web access
    return os.path.join('static', 'audio', wav_filename)


@app.route('/generate_music', methods=['POST'])
def generate_music():
    # Assume 'data' is the form field containing the text input by the user
    text = request.form.get('data', '')
    if text:
        chars = get_every_seventh_character(text)
        wav_file_relative_path = create_music_with_music21(chars)
        # Provide the link to the WAV file for playback in the template
        return render_template('play_music.html', wav_file=wav_file_relative_path)
    else:
        return "No text provided", 400


@app.route('/', methods=['GET', 'POST'])
def index():
    original_text = ""
    transformed_text = ""
    transformation_type = ""

    if request.method == 'POST':
        data = request.form.get('data', '')
        original_text = data
        action = request.form.get('action', '')

        if action == "V+7":
            transformed_text = process_v_plus_7(data, dictionary_data)
            transformation_type = "V+7"
        elif action == "A+7":
            transformed_text = process_a_plus_7(data, dictionary_data)
            transformation_type = "A+7"
        elif action == "Rhyme+7":
            transformed_text = replace_every_seventh_with_random_rhyme(data)
            transformation_type = "Rhyme+7"
        elif action == "Music+7":
            chars = get_every_seventh_character(data)
            create_music_with_music21(chars)
            transformed_text = "Play the poem as MIDI music in the sound player."
            transformation_type = "Music+7"

    # Highlight all-caps words in the transformed_text
    transformed_text = re.sub(
        r'\b([A-Z]{2,})\b', r'<span class="highlight">\1</span>', transformed_text)

    return render_template('form.html', transformed_text=transformed_text, transformation_type=transformation_type, original_text=original_text)


if __name__ == "__main__":
    app.run(debug=True)
