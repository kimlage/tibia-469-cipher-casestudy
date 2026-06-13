import os
import re
from collections import defaultdict
from tqdm import tqdm  # Para barras de progresso

# Função para extrair conteúdo entre três crases (``` ```
def extract_code_blocks(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    # Usa regex para encontrar todo conteúdo entre ``` ```
    # Suporta blocos de código com ou sem especificação de linguagem
    code_blocks = re.findall(r'```(?:\w+)?\n?([\s\S]*?)```', content)
    return code_blocks

# Função para calcular a frequência das substrings usando ocorrências exatas
def calculate_frequencies(blocks, min_length=2, max_length=100):
    substring_frequencies = defaultdict(int)
    
    print("Calculando frequências das substrings...")
    
    for block in tqdm(blocks, desc="Processando blocos"):
        # Limpa o bloco removendo espaços e quebras de linha
        block = block.replace('\n', '').replace(' ', '')
        block_length = len(block)
        
        # Limita o comprimento máximo para evitar computação excessiva
        current_max = min(max_length, block_length)
        
        for length in range(min_length, current_max + 1):
            for i in range(block_length - length + 1):
                substring = block[i:i+length]
                substring_frequencies[substring] += 1
                
    return substring_frequencies

# Função para filtrar substrings com base na comparação de frequências
def filter_substrings(frequencies):
    print("Filtrando substrings...")
    # Ordena as substrings por comprimento decrescente e frequência decrescente
    sorted_substrings = sorted(frequencies.items(), key=lambda item: (-len(item[0]), -item[1]))
    
    filtered_frequencies = frequencies.copy()
    substrings_sorted = [item[0] for item in sorted_substrings]
    
    # Usaremos um conjunto para armazenar substrings já processadas
    processed_substrings = set()
    
    for substr in tqdm(substrings_sorted, desc="Filtrando substrings"):
        freq = frequencies[substr]
        
        # Itera através de substrings mais longas que já foram processadas
        for longer_substr in processed_substrings:
            if substr in longer_substr and frequencies[longer_substr] == freq:
                if substr in filtered_frequencies:
                    del filtered_frequencies[substr]
                break  # Não precisa verificar mais substrings longas
                
        # Adiciona a substring atual ao conjunto de substrings processadas
        processed_substrings.add(substr)
                
    return filtered_frequencies

# Função para escrever as frequências em um arquivo Markdown com ordenação solicitada
def write_frequencies_to_file(frequencies, output_filepath):
    with open(output_filepath, 'w') as f:
        f.write("# Frequência de Substrings Comuns\n\n")
        f.write("| Substring | Comprimento | Frequência |\n")
        f.write("|-----------|-------------|------------|\n")
        # Ordena por comprimento decrescente, depois por frequência decrescente e, por fim, por ordem alfabética crescente
        sorted_freq = sorted(frequencies.items(), key=lambda item: (-len(item[0]), -item[1], item[0]))
        for substring, frequency in sorted_freq:
            if len(substring) >= 2 and frequency > 1:  # Garantindo comprimento mínimo e frequência >1
                f.write(f"| `{substring}` | {len(substring)} | {frequency} |\n")

# Função principal
def main():
    # Define os caminhos dos arquivos
    input_filepath = './01-books.md'
    output_filepath = 'books_frequency.md'
    
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
    
    # Passo 2: Calcular as frequências
    frequencies = calculate_frequencies(code_blocks, min_length=2, max_length=100)
    
    # Depuração: Verificar a contagem de substrings específicas antes da filtragem
    test_substrings = ['51595646114145190', '85611451']
    for test_substring in test_substrings:
        if test_substring in frequencies:
            print(f"Frequência de '{test_substring}' antes da filtragem: {frequencies[test_substring]}")
        else:
            print(f"Substring '{test_substring}' não encontrada antes da filtragem.")
    
    # Passo 3: Filtrar substrings com base na comparação de frequências
    filtered_frequencies = filter_substrings(frequencies)
    
    # Depuração: Verificar a contagem das substrings específicas após a filtragem
    for test_substring in test_substrings:
        if test_substring in filtered_frequencies:
            print(f"Frequência de '{test_substring}' após a filtragem: {filtered_frequencies[test_substring]}")
        else:
            print(f"Substring '{test_substring}' foi removida durante a filtragem.")
    
    # Passo 4: Escrever as frequências no arquivo de saída
    write_frequencies_to_file(filtered_frequencies, output_filepath)
    print(f"\nAnálise de frequência escrita em {output_filepath}")

if __name__ == '__main__':
    main()