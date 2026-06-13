import argparse
import re
import os

def replace_numbers_with_words(input_file, output_file, confidence_threshold):
    # Definindo o mapeamento de números para palavras com seus níveis de confiança
    mapping = {
        "0": ("destroy", 3),
        "1": ("I", 4),
        "5": ("a", 4),
    "7": ("and", 5),
    "8": ("an", 4),
    "30": ("now", 4),
    "36": ("are", 4),
    "54": ("see", 4),
    "67": ("to", 5),
    "81": ("and", 5),
    "1288": ("do", 4),
    "14636": ("have", 4),
    "2435": ("power", 3),
    "3046": ("with", 4),
    "345": ("of", 5),
    "467": ("the", 5),
    "60036": ("in", 3),
    "653": ("look", 5),
    "659": ("let", 4),
    "764": ("you", 4),
    "768": ("at", 4),
    "978": ("me", 4),
    "29639": ("we", 4),
    "3478": ("beholder", 3),
}

    # Filtrar o mapeamento com base no nível de confiança
    filtered_mapping = {k: v[0] for k, v in mapping.items() if v[1] >= confidence_threshold}

    # Ordenar o mapeamento por comprimento do número (decrescente) para evitar substituições parciais
    sorted_mapping = sorted(filtered_mapping.items(), key=lambda x: len(x[0]), reverse=True)

    # Ler o conteúdo do arquivo de entrada
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Erro: O arquivo '{input_file}' não foi encontrado.")
        return
    except Exception as e:
        print(f"Erro ao ler o arquivo '{input_file}': {e}")
        return

    # Realizar as substituições
    for number, word in sorted_mapping:
        # Substituição exata utilizando delimitadores de palavra
        pattern = r'\b' + re.escape(number) + r'\b'
        content = re.sub(pattern, word, content)

    # Escrever o conteúdo traduzido no arquivo de saída
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Substituição concluída. Arquivo traduzido salvo em '{output_file}'.")
    except Exception as e:
        print(f"Erro ao escrever no arquivo '{output_file}': {e}")

def main():
    parser = argparse.ArgumentParser(description='Substitua números por palavras em um arquivo com base no mapeamento e nível de confiança.')
    parser.add_argument('--input', type=str, default='./hellsgate_processed.md',
                        help='Caminho para o arquivo de entrada (default: ./hellsgate_processed.md)')
    parser.add_argument('--output', type=str, default='./hellsgate_translated.md',
                        help='Caminho para o arquivo de saída (default: ./hellsgate_translated.md)')
    parser.add_argument('--confidence', type=int, default=2,
                        help='Nível mínimo de confiança para substituir (1-5)')

    args = parser.parse_args()

    # Verificar se o nível de confiança está dentro do intervalo permitido
    if not (1 <= args.confidence <= 5):
        print("Erro: O nível de confiança deve estar entre 1 e 5.")
        return

    # Verificar se o arquivo de entrada existe
    if not os.path.isfile(args.input):
        print(f"Erro: O arquivo de entrada '{args.input}' não existe.")
        return

    # Executar a substituição
    replace_numbers_with_words(args.input, args.output, args.confidence)

if __name__ == "__main__":
    main()