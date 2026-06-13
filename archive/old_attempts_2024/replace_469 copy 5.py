import argparse
import re
import os

def replace_numbers_with_words(input_file, output_file, confidence_threshold):
    # Definindo o mapeamento de números para palavras com seus níveis de confiança
    mapping = {
    "0": ("destroy", 3),               # Contexto de ação nas frases | Frequência: 37
    "467": ("the", 5),                  # Palavra mais frequente | Frequência: 101
    "81": ("and", 5),                   # Conjunção comum | Frequência: 65
    "67": ("to", 5),                    # Alta frequência | Frequência: 94
    "60": ("is", 4),                    # Verbo auxiliar comum | Frequência: 73
    "36": ("are", 4),                   # Verbo auxiliar plural | Frequência: 65
    "11800": ("from", 4),               # Preposição comum | Frequência: 59
    "1288": ("do", 4),                   # Verbo auxiliar ou principal | Frequência: 57
    "595": ("he", 4),                    # Pronome pessoal masculino | Frequência: 54
    "857": ("must", 4),                  # Contexto de obrigação | Frequência: 50
    "54": ("see", 4),                    # Verbo comum nas frases das criaturas | Frequência: 49
    "30": ("now", 4),                    # Advérbio de tempo | Frequência: 46
    "345": ("of", 5),                    # Preposição frequente | Frequência: 40
    "2435": ("power", 3),                # Palavra de contexto específico | Frequência: 17
    "9": ("go", 4),                      # Verbo de ação | Frequência: 30
    "5": ("a", 4),                       # Artigo indefinido comum | Frequência: 26
    "8": ("an", 4),                      # Artigo indefinido usado antes de vogais | Frequência: 25
    "1": ("I", 4),                       # Uso frequente como pronome sujeito | Frequência: 22
    "3478": ("beholder", 3),             # Palavra de contexto específico | Frequência: 23
    "3046": ("with", 4),                 # Preposição comum | Frequência: 19
    "19": ("it", 4),                     # Uso frequente como pronome objeto | Frequência: 19
    "764": ("you", 4),                   # Pronome pessoal | Frequência: 18
    "65": ("has", 4),                    # Verbo auxiliar de posse | Frequência: 13
    "14636": ("have", 4),                # Verbo auxiliar ou principal | Frequência: 12
    "659": ("let", 4),                   # Verbo nas frases das criaturas | Frequência: 12
    "978": ("me", 4),                    # Pronome objeto | Frequência: 12
    "653": ("look", 5),                  # Verbo nas frases das criaturas | Frequência: 10
    "500": ("she", 2),                   # Pronome pessoal feminino | Frequência: 3
    "501": ("her", 2),                   # Pronome objeto feminino | Frequência: 2
    "503": ("them", 2),                  # Pronome objeto plural | Frequência: 2
    "512": ("know", 4),                  # Verbo de conhecimento | Frequência: 4
    "38": ("on", 4),                     # Preposição comum | Frequência: 11
    "768": ("at", 4),                    # Preposição comum nas frases das criaturas | Frequência: 8
    "29639": ("we", 4),                  # Pronome coletivo | Frequência: 4
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