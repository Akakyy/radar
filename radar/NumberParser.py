# Dictionary to map words to numeric values
NUM_WORDS = {
    "ноль": 0,
    "один": 1, "одна": 1,
    "два": 2, "две": 2,
    "три": 3,
    "четыре": 4,
    "пять": 5,
    "шесть": 6,
    "семь": 7,
    "восемь": 8,
    "девять": 9,
    "десять": 10,
    "одиннадцать": 11,
    "двенадцать": 12,
    "тринадцать": 13,
    "четырнадцать": 14,
    "пятнадцать": 15,
    "шестнадцать": 16,
    "семнадцать": 17,
    "восемнадцать": 18,
    "девятнадцать": 19,
    "двадцать": 20,
    "тридцать": 30,
    "сорок": 40,
    "пятьдесят": 50,
    "шестьдесят": 60,
    "семьдесят": 70,
    "восемьдесят": 80,
    "девяносто": 90,
    "сто": 100,
    "двести": 200,
    "триста": 300,
    "четыреста": 400,
    "пятьсот": 500,
    "шестьсот": 600,
    "семьсот": 700,
    "восемьсот": 800,
    "девятьсот": 900,
    "тысяча": 1000,
    "миллион": 1_000_000,
    "миллиард": 1_000_000_000
}

# Function to convert words to a numeric value
def words_to_number(words, morph):
    total = 0  # Final result
    current = 0  # Current number being processed
    for word in words:
        word = morph.parse(word)[0].normal_form  # Normalize word to its base form
        if word in NUM_WORDS:
            value = NUM_WORDS[word]
            if value >= 1000:  # Multiplier for large numbers (e.g., "тысяча")
                current *= value
            elif value >= 100:  # Add hundreds (e.g., "сто")
                current += value
            else:  # Add smaller values (e.g., "два", "три")
                current += value
        elif word == "и":  # Ignore conjunctions
            continue
        else:  # Reset and add the current value to total
            total += current
            current = 0
    return total + current  # Include the last processed number

# Main function to replace numbers in words with digits
def convert_numbers_in_text(text, segmenter, syntax_parser, morph):
    # Parse the text with Natasha
    doc = Doc(text)
    doc.segment(segmenter)  # Split into sentences and tokens
    doc.parse_syntax(syntax_parser)  # Parse syntax tree to understand structure

    tokens = [_.text for _ in doc.tokens]  # Extract tokens from the document
    result_text = text  # Final text to return
    current_chunk = []  # Current numeric chunk being processed
    chunks = []  # All numeric chunks found

    # Split text into potential numeric chunks
    for token in tokens:
        word_normal = morph.parse(token)[0].normal_form  # Normalize each token
        if word_normal in NUM_WORDS or token.lower() == "и":  # Check if it's part of a number
            current_chunk.append(token)  # Add token to the current numeric chunk
        else:
            if current_chunk:  # If a numeric chunk is completed
                chunks.append(" ".join(current_chunk))  # Save the chunk
                current_chunk = []  # Reset the chunk
    if current_chunk:  # Add the last chunk if not empty
        chunks.append(" ".join(current_chunk))

    # Replace numeric chunks in the original text
    for chunk in chunks:
        number = words_to_number(chunk.split())  # Convert chunk to a number
        result_text = result_text.replace(chunk, str(number))  # Replace words with digits

    return result_text  # Return the final processed text

