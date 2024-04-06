from flask import Flask, request, render_template
from v_plus_seven import process_text, load_dictionary

app = Flask(__name__)

# Load your dictionary data once when the app starts
dictionary_data = load_dictionary('/home/kaizenagility/oulipo/dictionary.json')


@app.route('/', methods=['GET', 'POST'])
def index():
    transformed_text = ""  # Ensure transformed_text is defined outside the if block
    if request.method == 'POST':
        # Extract text from the form submission
        data = request.form.get('data', '')

        # Process and transform the text
        processed_text = process_text(data, dictionary_data)
        transformed_text = processed_text  # Assign the processed text to transformed_text

    # Render the form, passing the transformed text to the template
    return render_template('form.html', transformed_text=transformed_text)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
