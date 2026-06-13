import re
import os

def load_separated_words(file_path, min_length=3):
    """
    Load all separated words from the file that meet the minimum length requirement.

    Args:
        file_path (str): Path to the input file.
        min_length (int): Minimum length of words to consider.

    Returns:
        set: A set of unique words.
    """
    separated_words = set()
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            # Split the line into words based on whitespace
            words = line.strip().split()
            # Add words that meet the minimum length
            for word in words:
                if len(word) >= min_length:
                    separated_words.add(word)
    return separated_words

def sort_words_by_length(words):
    """
    Sort words by their length in descending order.

    Args:
        words (set): A set of words.

    Returns:
        list: A list of words sorted by length (longest first).
    """
    return sorted(words, key=lambda x: len(x), reverse=True)

def insert_spaces(line, word):
    """
    Insert spaces around the word in the line if it's concatenated without spaces.

    Args:
        line (str): The original line.
        word (str): The word to insert spaces around.

    Returns:
        str: The modified line with spaces around the word.
    """
    # Use regex to find the word not preceded or followed by a space
    # Negative lookbehind and negative lookahead ensure the word is not already separated
    pattern = rf'(?<!\s){re.escape(word)}(?!\s)'
    # Replace the matched pattern with the word surrounded by spaces
    replaced_line = re.sub(pattern, f' {word} ', line)
    return replaced_line

def process_file(input_path, output_path, min_length=3):
    """
    Process the input file to separate concatenated words based on known separated words.

    Args:
        input_path (str): Path to the input file.
        output_path (str): Path to the output file.
        min_length (int): Minimum length of words to consider for separation.
    """
    if not os.path.exists(input_path):
        print(f"Error: The file '{input_path}' does not exist.")
        return

    # Step 1: Load separated words
    separated_words = load_separated_words(input_path, min_length)
    print(f"Total separated words found (length >= {min_length}): {len(separated_words)}")

    # Step 2: Sort words by length (longest first)
    sorted_words = sort_words_by_length(separated_words)
    print("Words sorted by length (longest first).")

    # Step 3: Read the file and process each line
    processed_lines = []
    with open(input_path, 'r', encoding='utf-8') as file:
        for line_number, line in enumerate(file, 1):
            original_line = line.rstrip('\n')  # Remove only the newline character
            modified_line = original_line
            for word in sorted_words:
                # Only process words with minimum length
                if len(word) < min_length:
                    continue
                # Insert spaces around the word if it's concatenated
                modified_line = insert_spaces(modified_line, word)
            # Remove any multiple spaces introduced and re-add the original newline
            modified_line = re.sub(r'\s+', ' ', modified_line).strip()
            processed_lines.append(modified_line)
            print(f"Processed line {line_number}.")

    # Step 4: Write the processed lines to the output file
    with open(output_path, 'w', encoding='utf-8') as file:
        for line in processed_lines:
            file.write(line + '\n')  # Re-add the newline character
    print(f"Processing complete. Output saved to '{output_path}'.")

def main():
    # Define the paths to the input and output files
    input_file = './hellsgate_processed.md'
    output_file = './hellsgate_processed_separated.md'

    # Define the minimum word length to consider
    minimum_word_length = 2

    # Process the file
    process_file(input_file, output_file, minimum_word_length)

if __name__ == "__main__":
    main()