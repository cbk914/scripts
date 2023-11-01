import json
import argparse

def search_terms(file_path, terms):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    results = {}
    for term in terms:
        results[term] = []
        for entry in data:
            if 'choices' in entry:
                for choice in entry['choices']:
                    if 'text' in choice and term.lower() in choice['text'].lower():
                        results[term].append(choice)
    return results

def main():
    parser = argparse.ArgumentParser(description='Search for terms in a ChatGPT exported JSON file.')
    parser.add_argument('-i', '--input', required=True, help='Path to the JSON file.')
    parser.add_argument('-t', '--terms', nargs='+', required=True, help='Terms to search for.')
    args = parser.parse_args()

    file_path = args.input
    terms = args.terms
    search_results = search_terms(file_path, terms)

    for term, occurrences in search_results.items():
        print(f'Term: {term}')
        for occurrence in occurrences:
            print(f'Occurrence: {occurrence}')

if __name__ == '__main__':
    main()
