import os
import re
from collections import defaultdict
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

def process_block(args):
    block, min_length, max_length = args
    block_frequencies = defaultdict(int)

    # Divide o bloco em linhas
    lines = block.split('\n')

    for line in lines:
        # Remove espaços no início e no fim da linha
        line = line.strip()
        line_length = len(line)

        # Se a linha estiver vazia, pula para a próxima
        if line_length == 0:
            continue

        # Preprocessamento: Contar ocorrências de substrings na linha
        for i in range(line_length):
            for j in range(i + min_length, min(i + max_length + 1, line_length + 1)):
                substring = line[i:j]
                block_frequencies[substring] += 1

    return block_frequencies

def calculate_frequencies_efficient(blocks, min_length=2, max_length=300):
    print("Calculando frequências das substrings de forma eficiente...")

    substring_frequencies = defaultdict(int)
    total_blocks = len(blocks)

    # Prepara os argumentos para a função process_block
    args = [(block, min_length, max_length) for block in blocks]

    with Pool(processes=cpu_count()) as pool:
        # Usa imap_unordered para processar blocos em paralelo com tqdm
        results = []
        for block_freq in tqdm(pool.imap_unordered(process_block, args), total=total_blocks, desc="Processando blocos"):
            results.append(block_freq)

    # Combina as frequências de todos os blocos
    for block_freq in results:
        for substring, freq in block_freq.items():
            substring_frequencies[substring] += freq

    return substring_frequencies

def extract_code_blocks(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Usa regex para encontrar todo conteúdo entre ``` ```
    code_blocks = re.findall(r'```(?:\s*\n)?([\s\S]*?)```', content)
    return code_blocks

def filter_substrings(frequencies):
    print("Filtrando substrings...")
    # Ordena as substrings por comprimento decrescente e frequência decrescente.
    sorted_substrings = sorted(frequencies.items(), key=lambda item: (-len(item[0]), -item[1]))

    filtered_frequencies = {}
    substrings_set = set(frequencies.keys())

    for substr, freq in tqdm(sorted_substrings, desc="Filtrando substrings"):
        # Se a substring já foi removida, pule.
        if substr not in substrings_set:
            continue

        filtered_frequencies[substr] = freq

        # Remover substrings menores que estão contidas em substr e têm a mesma frequência.
        substr_length = len(substr)
        substrings_to_remove = set()
        for s in substrings_set:
            if s != substr and s in substr and frequencies[s] == freq:
                substrings_to_remove.add(s)
        substrings_set -= substrings_to_remove

    return filtered_frequencies

def write_frequencies_to_file(frequencies, output_filepath):
    with open(output_filepath, 'w') as f:
        f.write("# Frequência de Substrings Comuns\n\n")
        f.write("| Substring | Comprimento | Frequência |\n")
        f.write("|-----------|-------------|------------|\n")
        # Ordena por comprimento decrescente, depois por frequência decrescente.
        sorted_freq = sorted(frequencies.items(), key=lambda item: (-len(item[0]), -item[1]))
        for substring, frequency in sorted_freq:
            if len(substring) >= 2:  # Garantindo comprimento mínimo
                f.write(f"| `{substring}` | {len(substring)} | {frequency} |\n")
                    
def main():
    # Define os caminhos dos arquivos
    input_filepath = './01-books.md'
    output_filtered_filepath = './books_frequency_filtered.md'
    output_all_filepath = './books_frequency_all.md'
    
    # Verifica se o arquivo de entrada existe
    if not os.path.exists(input_filepath):
        print(f"Arquivo de entrada não encontrado em {input_filepath}")
        return
    
    # Passo 1: Extrair blocos de código
    code_blocks = extract_code_blocks(input_filepath)
    if not code_blocks:
        print("Nenhum bloco de código encontrado no arquivo de entrada.")
        return
    
    print(f"Foram encontrados {len(code_blocks)} bloco(s) de código.")
    
    # Passo 2: Calcular as frequências de forma eficiente
    frequencies = calculate_frequencies_efficient(code_blocks, min_length=2, max_length=300)
    
    # Escrever todas as frequências no arquivo (sem filtragem)
    print(f"Escrevendo todas as frequências no arquivo '{output_all_filepath}'...")
    write_frequencies_to_file(frequencies, output_all_filepath)
    print("Arquivo com todas as frequências gerado com sucesso!")
    
    # Filtrar substrings com base na comparação de frequências
    filtered_frequencies = filter_substrings(frequencies)
    
    # Escrever as frequências filtradas no arquivo de saída
    print(f"Escrevendo frequências filtradas no arquivo '{output_filtered_filepath}'...")
    write_frequencies_to_file(filtered_frequencies, output_filtered_filepath)
    print("Arquivo com frequências filtradas gerado com sucesso!")
    
if __name__ == '__main__':
    main()