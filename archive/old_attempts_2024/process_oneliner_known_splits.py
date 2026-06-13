import re

# Function to parse known sequences from examples, excluding '0'
def parse_known_sequences(example_text):
    known_sequences = set()
    lines = example_text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            # Find all sequences of digits in the line
            sequences = re.findall(r'\b\d+\b', line)
            for seq in sequences:
                if seq != '0':  # Exclude '0' from known sequences
                    known_sequences.add(seq)
    return known_sequences

# Function to process a sequence by matching known sequences
def process_sequence(seq, known_sequences_sorted):
    seq_len = len(seq)
    matches = []

    # Iterate over the sequence and find matches
    i = 0
    while i < seq_len:
        match_found = False
        for known_seq in known_sequences_sorted:
            known_seq_len = len(known_seq)
            if seq[i:i+known_seq_len] == known_seq:
                matches.append((i, i+known_seq_len))
                i += known_seq_len
                match_found = True
                break
        if not match_found:
            i += 1  # Move to the next character if no match is found

    # Merge overlapping matches and prioritize longer matches
    merged_matches = []
    last_end = -1
    for start, end in sorted(matches, key=lambda x: (x[0], -x[1]+x[0])):
        if start >= last_end:
            merged_matches.append((start, end))
            last_end = end

    # Insert spaces at match boundaries
    result = []
    last_index = 0
    for start, end in merged_matches:
        # Add unmatched part
        if last_index < start:
            result.append(seq[last_index:start])
        # Add matched part
        result.append(seq[start:end])
        last_index = end
    # Add any remaining unmatched part
    if last_index < seq_len:
        result.append(seq[last_index:])

    # Join the result with spaces
    return ' '.join(result)

# Read the example sequences
example_text = """
# Knightmare’s Phrase
3478 67 90871 97664 3466 345  # Removed '0' from this line

# Chayenne’s Interview Response:
114514519485611451908304576512282177 6612527570584

# Phrase from tibia.com poll
663 902073 7223 67538 467 80097

# Frases de criaturas
653 768 764
659 978 54 764
653768764
659978 54764
653768764

# Avar tar’s Poem
29639 467 81 9063376290 3222011 677 80322429 67538 14805394
6880326 677 63378129 337011 72683 149630 4378
453 639 578300 986372 2953639

# Secret Library book
74032 45331

"""

# Parse known sequences, excluding '0'
known_sequences = parse_known_sequences(example_text)
# Sort known sequences from longest to shortest to prioritize longer matches
known_sequences_sorted = sorted(known_sequences, key=lambda x: -len(x))

# Set the input and output filenames
input_filename = './hellsgate_oneliner.md'
output_filename = './hellsgate_processed.md'

# Read the input file and process sequences
with open(input_filename, 'r') as infile, open(output_filename, 'w') as outfile:
    for line in infile:
        stripped_line = line.strip()
        if stripped_line.startswith((
            'FirstBookcase', 'SecondBookcase', 'ThirdBookcase',
            'FourthBookcase', 'FifthBookcase', 'SixthBookcase',
            'SeventhBookcase', 'EighthBookcase', 'Book1:', 'Book2:', 'Book3:')):
            # Write headers as is
            outfile.write(line)
        else:
            # Find all sequences of digits in the line
            sequences = re.findall(r'\d+', line)
            if sequences:
                processed_sequences = []
                for seq in sequences:
                    processed_seq = process_sequence(seq, known_sequences_sorted)
                    processed_sequences.append(processed_seq)
                # Reconstruct the line with processed sequences
                new_line = line
                for original, processed in zip(sequences, processed_sequences):
                    new_line = new_line.replace(original, processed)
                outfile.write(new_line + '\n')
            else:
                # If no sequences, write the line as is
                outfile.write(line)