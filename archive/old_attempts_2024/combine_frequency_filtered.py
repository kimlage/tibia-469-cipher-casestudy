import os
import re
import logging
from tqdm import tqdm

def read_frequency_file(filepath, min_length=5):
    """
    Reads the frequency file and extracts all substrings that meet the minimum length.
    
    Returns:
        List[str]: List of filtered substrings.
    """
    substrings = []

    if not os.path.exists(filepath):
        logging.error(f"Frequency file not found at {filepath}")
        return substrings

    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Skip the header lines
    data_lines = lines[4:]  # Adjust index if necessary based on your file's format

    for line in data_lines:
        line = line.strip()
        if not line:
            continue
        # Expected line format:
        # | `substring` | length | frequency |
        match = re.match(r'\| `([\d]+)` \| (\d+) \| (\d+) \|', line)
        if match:
            substring = match.group(1)
            length = int(match.group(2))
            if length >= min_length:
                substrings.append(substring)
            else:
                logging.debug(f"Skipping substring of length {length} (less than {min_length}).")
        else:
            logging.warning(f"Invalid line format: {line}")
    logging.info(f"Total substrings read: {len(substrings)}")
    return substrings

def compute_maximum_overlap(s1, s2):
    """
    Computes the maximum overlap between s1 and s2.

    Returns:
        max_overlap_len (int): The length of the maximum overlap.
        merged_string (str): The merged string after overlapping.
    """
    max_overlap_len = 0
    merged_string = s1 + s2  # Default concatenation if no overlap
    
    # Check for suffix of s1 matching prefix of s2
    max_len = min(len(s1), len(s2))
    for i in range(1, max_len + 1):
        if s1[-i:] == s2[:i]:
            if i > max_overlap_len:
                max_overlap_len = i
                merged_string = s1 + s2[i:]
    # Check for prefix of s1 matching suffix of s2
    for i in range(1, max_len + 1):
        if s1[:i] == s2[-i:]:
            if i > max_overlap_len:
                max_overlap_len = i
                merged_string = s2 + s1[i:]
    return max_overlap_len, merged_string

def shortest_common_superstring(substrings):
    """
    Computes the shortest common superstring by greedily merging substrings with maximum overlaps.
    
    Args:
        substrings (List[str]): List of substrings to merge.
    
    Returns:
        str: The shortest common superstring.
    """
    substrings = substrings.copy()
    pbar = tqdm(total=len(substrings) - 1, desc="Combining substrings")

    while len(substrings) > 1:
        max_overlap_len = -1
        max_i, max_j = -1, -1
        best_merged = ''

        for i in range(len(substrings)):
            for j in range(len(substrings)):
                if i != j:
                    overlap_len, merged_sequence = compute_maximum_overlap(substrings[i], substrings[j])
                    if overlap_len > max_overlap_len:
                        max_overlap_len = overlap_len
                        max_i, max_j = i, j
                        best_merged = merged_sequence

        if max_overlap_len == -1 or max_overlap_len == 0:
            # No overlaps found, append the last substring and proceed
            substrings[0] += substrings.pop()
            pbar.update(1)
            logging.info(f"No overlap found. Concatenating remaining substrings.")
        else:
            logging.info(f"Merging substrings at indices {max_i} and {max_j} with overlap length {max_overlap_len}.")
            substrings[max_i] = best_merged
            substrings.pop(max_j)
            pbar.update(1)
    pbar.close()
    return substrings[0]

def main():
    # Configure logging to write to a file and console
    log_file_path = './sequence_combination.log'
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path, mode='w'),
            logging.StreamHandler()
        ]
    )

    # Define file paths
    frequency_filepath = './books_frequency_filtered.md'
    output_combined_filepath = './books_frequency_filtered_combined.md'

    logging.info("Starting the sequence combination process.")

    # Step 1: Read substrings
    logging.info("Reading substrings from the frequency file...")
    substrings = read_frequency_file(frequency_filepath, min_length=5)
    if not substrings:
        logging.error("No substrings to process.")
        return

    # Step 2: Combine sequences using improved algorithm
    logging.info("Combining sequences using the improved algorithm...")
    combined_sequence = shortest_common_superstring(substrings)

    # Step 3: Save the combined sequence
    logging.info(f"Saving the combined sequence to '{output_combined_filepath}'...")
    with open(output_combined_filepath, 'w') as f:
        f.write("# Combined Sequence\n\n")
        f.write(f"## Length: {len(combined_sequence)} characters\n\n")
        f.write(combined_sequence + "\n")

    logging.info("Combined sequence saved successfully!")
    logging.info("Sequence combination process completed.")

if __name__ == "__main__":
    main()