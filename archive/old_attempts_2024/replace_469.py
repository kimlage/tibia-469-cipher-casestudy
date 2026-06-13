import argparse
import re
import os

def replace_numbers_with_words(input_file, output_file, confidence_threshold):
    # Definindo o mapeamento de números para palavras com seus níveis de confiança
    mapping = {
        "0": ("destroy/death", 4),               # Contexto de ação nas frases | Frequência: 37
        "467": ("the", 5),                  # Palavra mais frequente | Frequência: 101
        "81": ("and", 5),                   # Conjunção comum | Frequência: 65
        "60": ("is", 4),                    # Verbo auxiliar comum | Frequência: 73
        "36": ("are", 4),                   # Verbo auxiliar plural | Frequência: 65
        "11800": ("from", 4),               # Preposição comum | Frequência: 59
        "1288": ("do", 4),                  # Verbo auxiliar ou principal | Frequência: 57
        "595": ("he", 4),                   # Pronome pessoal masculino | Frequência: 54
        "857": ("must", 4),                 # Contexto de obrigação | Frequência: 50
        "54": ("see", 4),                   # Verbo comum nas frases das criaturas | Frequência: 49
        "30": ("now", 4),                  # Advérbio de tempo | Frequência: 46
        "2435": ("power", 3),              # Palavra de contexto específico | Frequência: 17
        "9": ("go", 4),                     # Verbo de ação | Frequência: 30
        "5": ("a", 4),                      # Artigo indefinido comum | Frequência: 26
        "8": ("an", 4),                     # Artigo indefinido usado antes de vogais | Frequência: 25
        "1": ("Tibia", 5),                      # Uso frequente como pronome sujeito | Frequência: 22
        "3478": ("beholder", 5),            # Palavra de contexto específico | Frequência: 23
        "3046": ("with", 4),                # Preposição comum | Frequência: 19
        "19": ("it", 4),                    # Uso frequente como pronome objeto | Frequência: 19
        "764": ("you", 4),                  # Pronome pessoal | Frequência: 18
        "65": ("has", 4),                   # Verbo auxiliar de posse | Frequência: 13
        "14636": ("have", 4),               # Verbo auxiliar ou principal | Frequência: 12
        "659": ("let", 4),                 # Verbo nas frases das criaturas | Frequência: 12
        "978": ("me", 4),                   # Pronome objeto | Frequência: 12
        "653": ("look", 5),                # Verbo nas frases das criaturas | Frequência: 10
        "500": ("she", 2),                  # Pronome pessoal feminino | Frequência: 3
        "501": ("her", 2),                  # Pronome objeto feminino | Frequência: 2
        "503": ("them", 2),                 # Pronome objeto plural | Frequência: 2
        "512": ("know", 4),                # Verbo de conhecimento | Frequência: 4
        "38": ("on", 4),                    # Preposição comum | Frequência: 11
        "768": ("at", 4),                   # Preposição comum nas frases das criaturas | Frequência: 8
        "29639": ("we", 4),                 # Pronome coletivo | Frequência: 4
    }

    # Filtrar o mapeamento com base no nível de confiança
    filtered_mapping = {k: v[0] for k, v in mapping.items() if v[1] >= confidence_threshold}

    # Ordenar o mapeamento por comprimento do número (decrescente) para evitar substituições parciais
    sorted_mapping = sorted(filtered_mapping.items(), key=lambda x: len(x[0]), reverse=True)

    def replace_numbers(text):
        for num, word in sorted_mapping:
            text = re.sub(r'\b' + re.escape(num) + r'\b', word, text)
        return text

    def process_content(content):
        lines = content.splitlines()
        for i in range(len(lines)):
            if lines[i].startswith('|'):  # Verifica se é uma linha da tabela
                columns = lines[i].split('|')
                if len(columns) > 1:
                    columns[1] = replace_numbers(columns[1])
                    lines[i] = '|'.join(columns)
            else:
                lines[i] = replace_numbers(lines[i])
        return '\n'.join(lines)

    # Processar o arquivo de entrada
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        processed_content = process_content(content)
    except FileNotFoundError:
        print(f"Erro: O arquivo '{input_file}' não foi encontrado.")
        return
    except Exception as e:
        print(f"Erro ao ler o arquivo '{input_file}': {e}")
        return

    # Processar o arquivo source_content.md
    source_file = './source_content.md'
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            source_content = f.read()
        processed_source_content = process_content(source_content)
    except FileNotFoundError:
        print(f"Erro: O arquivo '{source_file}' não foi encontrado.")
        return
    except Exception as e:
        print(f"Erro ao ler o arquivo '{source_file}': {e}")
        return

    # Escrever o conteúdo processado no arquivo de saída
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(processed_content)
            f.write('\n\n')  # Adiciona duas linhas em branco antes de anexar
            f.write(processed_source_content)
        print(f"Substituição concluída. Arquivo traduzido salvo em '{output_file}'.")
        print(f"Conteúdo de '{source_file}' processado e adicionado ao final do arquivo de saída '{output_file}'.")
    except Exception as e:
        print(f"Erro ao escrever no arquivo '{output_file}': {e}")

def main():
    parser = argparse.ArgumentParser(description='Substitua números por palavras em um arquivo com base no mapeamento e nível de confiança.')
    parser.add_argument('--input', type=str, default='./books_frequency_filtered_spaces.md',
                        help='Caminho para o arquivo de entrada (default: ./books_frequency_filtered_spaces.md)')
    parser.add_argument('--output', type=str, default='./books_frequency_translated.md',
                        help='Caminho para o arquivo de saída (default: ./books_frequency_translated.md)')
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