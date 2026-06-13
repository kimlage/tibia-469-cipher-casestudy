import os
import re
import csv
import statistics
from collections import Counter

def extract_statistics_to_csv(md_file_path):
    # Read the markdown file
    try:
        with open(md_file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: The file {md_file_path} was not found.")
        return
    except Exception as e:
        print(f"Error reading the file: {e}")
        return

    # Find all the books between triple backticks
    books = re.findall(r'```(?:markdown:?[^`\n]*)?\n(.*?)```', content, re.DOTALL)

    print(f"Number of code blocks found: {len(books)}")

    if not books:
        print("No code blocks found. Please ensure that the book lines are enclosed within triple backticks (```).\n"
              "For example:\n"
              "```\n"
              "1234567890\n"
              "9876543210\n"
              "```")
        return

    # Prepare the CSV file path
    csv_file_path = os.path.splitext(md_file_path)[0] + '_stats.csv'

    # Define CSV headers
    headers = [
        'Book Line', 'Mean', 'Median', 'Mode', 'Count', 'Min', 'Max', 'Standard Deviation',
        'Distinct Numbers', 'Missing Numbers'
    ]

    with open(csv_file_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()

        # Process each book
        for book_idx, book in enumerate(books, 1):
            lines = book.strip().split('\n')
            if not lines:
                print(f"Warning: No lines found in book {book_idx}.")
                continue

            for line_num, line in enumerate(lines, 1):
                # Consider each character as a separate number
                numbers = [int(char) for char in line if char.isdigit()]
                if numbers:
                    # Compute statistics
                    mean_val = statistics.mean(numbers)
                    median_val = statistics.median(numbers)
                    count_val = len(numbers)
                    min_val = min(numbers)
                    max_val = max(numbers)
                    stdev_val = statistics.stdev(numbers) if count_val > 1 else 0.0

                    # Compute distinct numbers in ascending order
                    distinct_numbers = sorted(set(numbers))
                    distinct_numbers_str = ','.join(map(str, distinct_numbers))

                    # Compute missing numbers
                    all_digits = set(range(0, 10))
                    missing_numbers = sorted(all_digits - set(numbers))
                    missing_numbers_str = ','.join(map(str, missing_numbers))

                    # Compute mode(s)
                    frequency = Counter(numbers)
                    max_freq = max(frequency.values())
                    modes = sorted([num for num, freq in frequency.items() if freq == max_freq])
                    modes_str = ','.join(map(str, modes))

                    # Write to CSV
                    writer.writerow({
                        'Book Line': f'Book {book_idx}, Line {line_num}',
                        'Mean': round(mean_val, 2),
                        'Median': median_val,
                        'Mode': modes_str,
                        'Count': count_val,
                        'Min': min_val,
                        'Max': max_val,
                        'Standard Deviation': round(stdev_val, 2),
                        'Distinct Numbers': distinct_numbers_str,
                        'Missing Numbers': missing_numbers_str
                    })
                else:
                    print(f"Warning: No digits found in Book {book_idx}, Line {line_num}.")

    print(f"Statistics successfully written to {csv_file_path}")

if __name__ == '__main__':
    md_file_path = './01-books.md'
    extract_statistics_to_csv(md_file_path)
