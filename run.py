import os
import pathspec

def load_gitignore(directory):
    gitignore_path = os.path.join(directory, '.gitignore')
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            return pathspec.PathSpec.from_lines('gitwildmatch', f)
    return None

# Пример использования функции
directory = '/Users/anton/Documents/vs_projects/showHTTPreq/showHTTPreq/'
spec = load_gitignore(directory)

if spec:
    test_path = '/path/to/your/project/subdir/__pycache__'
    if spec.match_file(test_path + '/'):  # добавляем слеш в конце
        print(f'{test_path} matches .gitignore pattern')
    else:
        print(f'{test_path} does not match .gitignore pattern')
else:
    print('.gitignore not found or is empty')