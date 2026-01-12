#!/usr/bin/env python3
"""
Скрипт для конвертации Git-репозитория в единый текстовый файл.
Спрашивает у пользователя путь к репозиторию.
Использование:
  python3 repo_dumper.py        # Интерактивный режим
  python3 repo_dumper.py -q     # Быстрый режим (требует путь)
  python3 repo_dumper.py -q /путь/к/репо  # Быстрый режим с путем
"""

import os
import sys
import argparse
from pathlib import Path
import subprocess
import fnmatch

def parse_arguments():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(
        description='Конвертер Git-репозитория в единый текстовый файл',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Примеры использования:
  %(prog)s                     # Интерактивный режим с вопросами
  %(prog)s -q                  # Быстрый режим, запросит путь
  %(prog)s -q ./my-repo        # Быстрый режим с указанием пути
  %(prog)s -q /путь/к/репо     # Быстрый режим с полным путем
        '''
    )
    
    parser.add_argument(
        '-q', '--quick',
        action='store_true',
        help='Быстрый режим: требует путь к репозиторию, использует значения по умолчанию'
    )
    
    parser.add_argument(
        'path',
        nargs='?',
        help='Путь к репозитории (только в быстром режиме)'
    )
    
    return parser.parse_args()

def parse_gitignore(repo_path):
    """
    Парсинг всех файлов .gitignore в репозитории.
    Возвращает список шаблонов для игнорирования.
    """
    gitignore_patterns = []
    
    # Ищем все файлы .gitignore в репозитории
    for gitignore_file in repo_path.rglob('.gitignore'):
        try:
            with open(gitignore_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # Пропускаем пустые строки и комментарии
                    if not line or line.startswith('#'):
                        continue
                    
                    # Получаем относительный путь от корня репозитория
                    rel_gitignore_path = gitignore_file.parent.relative_to(repo_path)
                    
                    # Обрабатываем шаблон
                    pattern = line
                    
                    # Если шаблон начинается с /, он считается от директории .gitignore
                    if pattern.startswith('/'):
                        pattern = pattern[1:]
                    
                    # Создаем полный относительный путь от корня репозитория
                    if rel_gitignore_path != Path('.'):
                        full_pattern = str(rel_gitignore_path / pattern)
                    else:
                        full_pattern = pattern
                    
                    # Нормализуем разделители путей
                    full_pattern = full_pattern.replace('\\', '/')
                    
                    # Добавляем паттерн для директории (если заканчивается на /)
                    if full_pattern.endswith('/'):
                        # Для директорий добавляем два варианта:
                        # 1. Сам паттерн (для проверки директорий)
                        gitignore_patterns.append(full_pattern)
                        # 2. Паттерн с ** для файлов внутри
                        gitignore_patterns.append(full_pattern + '**')
                        # 3. Паттерн без / для точного совпадения
                        gitignore_patterns.append(full_pattern.rstrip('/'))
                    else:
                        gitignore_patterns.append(full_pattern)
                    
        except (UnicodeDecodeError, IOError):
            # Пропускаем файлы, которые не можем прочитать
            continue
    
    return gitignore_patterns

def parse_gitignore(repo_path):
    """
    Парсинг всех файлов .gitignore в репозитории.
    Возвращает список шаблонов для игнорирования.
    """
    gitignore_patterns = []
    
    # Ищем все файлы .gitignore в репозитории
    for gitignore_file in repo_path.rglob('.gitignore'):
        try:
            with open(gitignore_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # Пропускаем пустые строки и комментарии
                    if not line or line.startswith('#'):
                        continue
                    
                    # Получаем относительный путь от корня репозитория
                    rel_gitignore_path = gitignore_file.parent.relative_to(repo_path)
                    
                    # Обрабатываем шаблон
                    pattern = line
                    
                    # Если шаблон начинается с /, он считается от директории .gitignore
                    if pattern.startswith('/'):
                        pattern = pattern[1:]
                    
                    # Создаем полный относительный путь от корня репозитория
                    if rel_gitignore_path != Path('.'):
                        full_pattern = str(rel_gitignore_path / pattern)
                    else:
                        full_pattern = pattern
                    
                    # Нормализуем разделители путей
                    full_pattern = full_pattern.replace('\\', '/')
                    
                    # Добавляем паттерн для директории (если заканчивается на /)
                    if full_pattern.endswith('/'):
                        # Для директорий добавляем два варианта:
                        # 1. Сам паттерн (для проверки директорий)
                        gitignore_patterns.append(full_pattern)
                        # 2. Паттерн с ** для файлов внутри
                        gitignore_patterns.append(full_pattern + '**')
                        # 3. Паттерн без / для точного совпадения
                        gitignore_patterns.append(full_pattern.rstrip('/'))
                    else:
                        gitignore_patterns.append(full_pattern)
                    
        except (UnicodeDecodeError, IOError):
            # Пропускаем файлы, которые не можем прочитать
            continue
    
    return gitignore_patterns

def should_ignore_path(path, gitignore_patterns, repo_path):
    """
    Проверяет, должен ли путь быть проигнорирован на основе .gitignore шаблонов.
    """
    try:
        # Получаем относительный путь от корня репозитория
        rel_path = path.relative_to(repo_path)
        path_str = str(rel_path).replace('\\', '/')
        
        # Проверяем каждый шаблон
        for pattern in gitignore_patterns:
            # Специальная обработка для шаблонов с **
            if '**' in pattern:
                # Заменяем ** на * для fnmatch
                fnmatch_pattern = pattern.replace('**', '*')
                # Для шаблонов с ** используем более гибкое сравнение
                if fnmatch.fnmatch(path_str, fnmatch_pattern):
                    return True
                # Также проверяем частичные совпадения для директорий
                if pattern.endswith('/**') and path_str.startswith(pattern.rstrip('**')):
                    return True
            elif pattern.endswith('/'):
                # Паттерн для директории
                if path_str == pattern.rstrip('/') or path_str.startswith(pattern):
                    return True
            else:
                # Простое сопоставление с шаблоном
                if fnmatch.fnmatch(path_str, pattern):
                    return True
                # Проверяем, является ли файл внутри игнорируемой директории
                if '/' in pattern and fnmatch.fnmatch(path_str, pattern + '/**'):
                    return True
                # Проверяем, совпадает ли начало пути
                if path_str.startswith(pattern + '/'):
                    return True
        
        return False
    except ValueError:
        # Если не можем получить относительный путь
        return False

def get_repo_path_interactive():
    """Интерактивный запрос пути к репозиторию"""
    print("\n" + "="*60)
    print("КОНВЕРТЕР РЕПОЗИТОРИЯ В ЕДИНЫЙ ФАЙЛ")
    print("="*60)
    
    current_dir = Path.cwd()
    
    print(f"\nТекущая директория: {current_dir}")
    print("Примеры путей:")
    print("  - ../относительный/путь")
    print("  - или Enter для текущей директории")
    
    repo_path = input("\nВведите путь к локальному репозитории (Enter для текущей директории): ").strip()
    repo_path = repo_path.strip('\"\'')
    
    if not repo_path:
        repo_path = current_dir
        print(f"✓ Используется текущая директория")
    else:
        repo_path = Path(repo_path).expanduser()
        if not repo_path.is_absolute():
            repo_path = current_dir / repo_path
        repo_path = repo_path.resolve()
        print(f"✓ Используется путь: {repo_path.name}")
    
    return repo_path

def get_repo_path_quick(cli_path=None):
    """Получить путь к репозиторию в быстром режиме"""
    print("\n" + "="*60)
    print("БЫСТРЫЙ РЕЖИМ (QUICK MODE)")
    print("="*60)
    
    current_dir = Path.cwd()
    
    print(f"\nТекущая директория: {current_dir}")
    print("Примеры путей:")
    print("  - ../относительный/путь")
    print("  - /полный/путь/к/репозиторию")
    
    if cli_path:
        # Путь передан как аргумент
        repo_path = Path(cli_path).expanduser()
        if not repo_path.is_absolute():
            repo_path = current_dir / repo_path
        repo_path = repo_path.resolve()
        print(f"\n✓ Используется путь из аргументов: {repo_path}")
    else:
        # Запрашиваем путь у пользователя
        repo_path = input("\nВведите путь к репозитории (обязательно): ").strip()
        repo_path = repo_path.strip('\"\'')
        
        if not repo_path:
            print("❌ Ошибка: В быстром режиме путь к репозитории обязателен!")
            print("Использование: python3 repo_dumper.py -q /путь/к/репозиторию")
            sys.exit(1)
        
        repo_path = Path(repo_path).expanduser()
        if not repo_path.is_absolute():
            repo_path = current_dir / repo_path
        repo_path = repo_path.resolve()
        print(f"✓ Используется путь: {repo_path}")
    
    return repo_path

def validate_repository(path, quick_mode=False):
    """Проверить, что это Git-репозиторий"""
    if not path.exists():
        print(f"❌ Ошибка: Путь '{path}' не существует!")
        return False
    
    if not path.is_dir():
        print(f"❌ Ошибка: '{path}' не является директорией!")
        return False
    
    # Проверяем, есть ли .git папка
    git_dir = path / '.git'
    if not git_dir.exists():
        if quick_mode:
            print(f"⚠️  Внимание: В '{path.name}' не найдена папка .git")
            print("Продолжаем обработку...")
        else:
            print(f"⚠️  Внимание: В '{path}' не найдена папка .git")
            response = input("Это может быть не Git-репозиторий. Продолжить? (y/N): ").strip().lower()
            if response != 'y':
                return False
    else:
        if quick_mode:
            print(f"✓ Найден Git-репозиторий: {path.name}")
        else:
            print(f"✓ Найден Git-репозиторий")
    
    return True

def select_output_file(repo_path, quick_mode=False):
    """Предложить варианты имени выходного файла"""
    repo_name = repo_path.name
    default_file = f"{repo_name}_dump.txt"
    
    if quick_mode:
        # В быстром режиме всегда используем имя по умолчанию
        output_file = Path.cwd() / default_file
        print(f"✓ Выходной файл: {output_file.name}")
        return output_file
    
    # Интерактивный режим
    print(f"\nИмя репозитория: {repo_name}")
    choice = input(f"Сохранить как '{default_file}'? (Y/n): ").strip().lower()
    
    if choice == 'n':
        custom_name = input("Введите имя файла (например: output.txt): ").strip()
        if custom_name:
            if '.' not in custom_name:
                custom_name += '.txt'
            output_file = Path(custom_name).resolve()
        else:
            output_file = Path(default_file).resolve()
    else:
        output_file = Path.cwd() / default_file
    
    print(f"✓ Файл будет сохранен как: {output_file.name}")
    
    return output_file

def get_file_filter(quick_mode=False):
    """Получить настройки фильтрации файлов"""
    if quick_mode:
        # Значения по умолчанию для быстрого режима
        return {
            'skip_binary': True,
            'skip_git': True,
            'skip_node_modules': True,
            'skip_venv': True,
            'skip_hidden': False,
            'max_file_size': None,
            'use_gitignore': True  # Новая опция: использовать .gitignore
        }
    
    # Интерактивный режим
    print("\n" + "="*60)
    print("НАСТРОЙКА ФИЛЬТРАЦИИ ФАЙЛОВ")
    print("="*60)
    
    filters = {
        'skip_binary': True,
        'skip_git': True,
        'skip_node_modules': True,
        'skip_venv': True,
        'skip_hidden': False,
        'max_file_size': None,
        'use_gitignore': True  # Новая опция: использовать .gitignore
    }
    
    print("\nРекомендуемые настройки:")
    print("1. Пропускать бинарные файлы (картинки, PDF, архивы) - ДА")
    print("2. Пропускать служебные папки (.git, node_modules, venv) - ДА")
    print("3. Пропускать скрытые файлы (.env, .config) - НЕТ")
    print("4. Использовать правила из .gitignore - ДА")
    
    change = input("\nИзменить настройки фильтрации? (y/N): ").strip().lower()
    
    if change == 'y':
        print("\nНастройте фильтрацию:")
        filters['skip_binary'] = input("Пропускать бинарные файлы? (Y/n): ").strip().lower() != 'n'
        filters['skip_git'] = input("Пропускать папку .git? (Y/n): ").strip().lower() != 'n'
        filters['skip_node_modules'] = input("Пропускать node_modules? (Y/n): ").strip().lower() != 'n'
        filters['skip_venv'] = input("Пропускать виртуальные окружения? (Y/n): ").strip().lower() != 'n'
        filters['skip_hidden'] = input("Пропускать скрытые файлы? (y/N): ").strip().lower() == 'y'
        filters['use_gitignore'] = input("Использовать правила из .gitignore? (Y/n): ").strip().lower() != 'n'
        
        max_size = input("Максимальный размер файла в МБ (оставьте пустым для без ограничений): ").strip()
        if max_size:
            try:
                filters['max_file_size'] = int(max_size) * 1024 * 1024
            except ValueError:
                print("⚠️  Неверное значение, ограничение не установлено")
    
    return filters

def should_skip_file(file_path, filters, repo_path, gitignore_patterns, output_file=None):
    """Определить, нужно ли пропускать файл"""
    try:
        rel_path = file_path.relative_to(repo_path)
    except ValueError:
        return True
    
    # Пропускаем выходной файл
    if output_file and file_path.exists() and output_file.exists():
        try:
            if file_path.samefile(output_file):
                return True
        except:
            pass
    
    # Пропускаем по пути
    path_str = str(rel_path)
    parts = path_str.split(os.sep)
    
    # Проверяем правила .gitignore
    if filters.get('use_gitignore', True) and gitignore_patterns:
        if should_ignore_path(file_path, gitignore_patterns, repo_path):
            return True
    
    if filters['skip_git'] and '.git' in parts:
        return True
    if filters['skip_node_modules'] and 'node_modules' in parts:
        return True
    if filters['skip_venv'] and any(x in parts for x in ['venv', '.venv', 'env', '.env']):
        return True
    if filters['skip_hidden'] and any(part.startswith('.') for part in parts if part not in ['.', '..']):
        return True
    
    # Пропускаем по расширению
    if filters['skip_binary']:
        binary_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
                            '.pdf', '.zip', '.tar', '.gz', '.rar', '.7z', '.exe',
                            '.dll', '.so', '.pyc', '.pyo', '.class', '.jar', '.war'}
        if file_path.suffix.lower() in binary_extensions:
            return True
    
    # Проверяем размер файла
    if filters['max_file_size']:
        try:
            if file_path.stat().st_size > filters['max_file_size']:
                return True
        except:
            pass
    
    return False

def create_repo_dump(repo_path, output_file, filters, quick_mode=False):
    """Создать дамп репозитория"""
    if quick_mode:
        print(f"\n{'='*60}")
        print(f"ОБРАБОТКА: {repo_path.name}")
        print(f"{'='*60}")
    else:
        print(f"\n{'='*60}")
        print("НАЧИНАЕМ ОБРАБОТКУ...")
        print(f"{'='*60}")
    
    # Парсим .gitignore файлы
    gitignore_patterns = []
    if filters.get('use_gitignore', True):
        if not quick_mode:
            print("📄 Чтение правил из .gitignore...")
        gitignore_patterns = parse_gitignore(repo_path)
        if gitignore_patterns and not quick_mode:
            print(f"✓ Загружено {len(gitignore_patterns)} правил из .gitignore")
    
    total_files = 0
    processed_files = 0
    skipped_files = 0
    skipped_by_gitignore = 0
    
    # Создаем функцию should_skip с привязкой к output_file
    def should_skip(file_path):
        nonlocal skipped_by_gitignore
        skip = should_skip_file(file_path, filters, repo_path, gitignore_patterns, output_file)
        if skip and filters.get('use_gitignore', True) and gitignore_patterns:
            # Проверяем, был ли файл пропущен из-за .gitignore
            if should_ignore_path(file_path, gitignore_patterns, repo_path):
                skipped_by_gitignore += 1
        return skip
    
    # Сначала посчитаем общее количество файлов
    if not quick_mode:
        print("📁 Сканирование структуры репозитория...")
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not should_skip(Path(root) / d)]
        total_files += len(files)
    
    if not quick_mode:
        print(f"Найдено файлов: {total_files}")
        if gitignore_patterns:
            print(f"Правил .gitignore загружено: {len(gitignore_patterns)}")
    
    # Создаем выходной файл
    with open(output_file, 'w', encoding='utf-8') as out_file:
        # Записываем заголовок
        out_file.write(f"{'='*80}\n")
        out_file.write(f"ДАМП РЕПОЗИТОРИЯ: {repo_path.name}\n")
        if not quick_mode:
            out_file.write(f"ФИЛЬТРЫ: пропускать бинарные={filters['skip_binary']}, .git={filters['skip_git']}, использовать .gitignore={filters.get('use_gitignore', True)}\n")
        out_file.write(f"{'='*80}\n\n")
        
        # Обрабатываем файлы
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if not should_skip(Path(root) / d)]
            
            for file in files:
                file_path = Path(root) / file
                
                if should_skip(file_path):
                    skipped_files += 1
                    continue
                
                try:
                    rel_path = file_path.relative_to(repo_path)
                except ValueError:
                    skipped_files += 1
                    continue
                
                try:
                    # Записываем заголовок файла
                    out_file.write(f"\n{'='*60}\n")
                    out_file.write(f"ФАЙЛ: {rel_path}\n")
                    out_file.write(f"РАЗМЕР: {file_path.stat().st_size} байт\n")
                    out_file.write(f"{'='*60}\n\n")
                    
                    # Читаем содержимое
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        out_file.write(content)
                        
                        if content and content[-1] != '\n':
                            out_file.write('\n')
                    
                    processed_files += 1
                    
                    # Выводим прогресс в быстром режиме
                    if quick_mode and processed_files % 50 == 0:
                        print(f"  Обработано файлов: {processed_files}")
                    elif not quick_mode and processed_files % 10 == 0:
                        progress = (processed_files / total_files) * 100 if total_files > 0 else 0
                        print(f"  Прогресс: {processed_files}/{total_files} файлов ({progress:.1f}%)")
                        
                except Exception as e:
                    out_file.write(f"[ОШИБКА ЧТЕНИЯ ФАЙЛА: {e}]\n")
                    skipped_files += 1
        
        # Добавляем информацию о Git
        out_file.write(f"\n\n{'='*80}\n")
        out_file.write("ИНФОРМАЦИЯ О GIT\n")
        out_file.write(f"{'='*80}\n\n")
        
        git_info = get_git_info(repo_path)
        out_file.write(git_info)
        
        # Добавляем информацию о фильтрации
        if gitignore_patterns:
            out_file.write(f"\n\n{'='*80}\n")
            out_file.write("ПРИМЕНЕННЫЕ ПРАВИЛА .gitignore\n")
            out_file.write(f"{'='*80}\n\n")
            for pattern in sorted(set(gitignore_patterns)):
                out_file.write(f"- {pattern}\n")
    
    return processed_files, skipped_files, skipped_by_gitignore

def get_git_info(repo_path):
    """Получить информацию о Git репозитории"""
    info = []
    
    try:
        # Текущая ветка
        result = subprocess.run(['git', 'branch', '--show-current'], 
                              cwd=repo_path, capture_output=True, text=True)
        current_branch = result.stdout.strip()
        info.append(f"Текущая ветка: {current_branch if current_branch else 'не определена'}")
        
        # Последний коммит
        result = subprocess.run(['git', 'log', '--oneline', '-1'], 
                              cwd=repo_path, capture_output=True, text=True)
        if result.stdout:
            info.append(f"Последний коммит: {result.stdout.strip()}")
        else:
            info.append("История коммитов недоступна")
            
        # Статус репозитория
        result = subprocess.run(['git', 'status', '--short'], 
                              cwd=repo_path, capture_output=True, text=True)
        if result.stdout.strip():
            info.append("\nНесохраненные изменения:")
            info.append(result.stdout.strip())
        else:
            info.append("\nНет несохраненных изменений")
        
    except Exception as e:
        info.append(f"\nНе удалось получить информацию о Git: {e}")
    
    return '\n'.join(info)

def main():
    """Основная функция"""
    args = parse_arguments()
    
    try:
        # Определяем режим работы
        quick_mode = args.quick
        
        if quick_mode:
            # БЫСТРЫЙ РЕЖИМ (-q)
            repo_path = get_repo_path_quick(args.path)
        else:
            # ИНТЕРАКТИВНЫЙ РЕЖИМ
            if args.path:
                print("⚠️  Предупреждение: Путь игнорируется в интерактивном режиме")
                print("   Используйте ключ -q для быстрого режима с путем")
            
            repo_path = get_repo_path_interactive()
        
        # Проверяем репозиторий
        if not validate_repository(repo_path, quick_mode):
            print("❌ Прерывание работы...")
            sys.exit(1)
        
        # Выбираем выходной файл
        output_file = select_output_file(repo_path, quick_mode)
        
        # Получаем фильтры
        filters = get_file_filter(quick_mode)
        
        # В быстром режиме сразу начинаем, в интерактивном - спрашиваем подтверждение
        if not quick_mode:
            print(f"\n{'='*60}")
            print("ПОДТВЕРЖДЕНИЕ:")
            print(f"Репозиторий: {repo_path.name}")
            print(f"Выходной файл: {output_file.name}")
            print(f"Использовать .gitignore: {filters.get('use_gitignore', 'Да')}")
            print(f"{'='*60}")
            
            confirm = input("\nНачать обработку? (y/N): ").strip().lower()
            if confirm != 'y':
                print("❌ Операция отменена пользователем")
                return
        
        # Создаем дамп
        processed, skipped, skipped_by_gitignore = create_repo_dump(repo_path, output_file, filters, quick_mode)
        
        # Выводим результат
        if output_file.exists():
            file_size = output_file.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            file_size_kb = file_size / 1024
        else:
            file_size_kb = file_size_mb = 0
        
        if quick_mode:
            print(f"\n{'='*60}")
            print("✅ ЗАВЕРШЕНО!")
        else:
            print(f"\n{'='*60}")
            print("✅ ОБРАБОТКА ЗАВЕРШЕНА!")
        
        print(f"{'='*60}")
        print(f"Репозиторий: {repo_path.name}")
        print(f"Обработано файлов: {processed}")
        print(f"Пропущено файлов: {skipped}")
        if filters.get('use_gitignore', True):
            print(f"Пропущено по .gitignore: {skipped_by_gitignore}")
        print(f"Выходной файл: {output_file.name}")
        
        if file_size_kb < 1024:
            print(f"Размер файла: {file_size_kb:.1f} KB")
        else:
            print(f"Размер файла: {file_size_mb:.2f} MB")
        
        # В быстром режиме не спрашиваем про открытие файла
        if not quick_mode:
            view = input(f"\nОткрыть полученный файл? (y/N): ").strip().lower()
            if view == 'y':
                try:
                    if sys.platform == 'win32':
                        os.startfile(str(output_file))
                    elif sys.platform == 'darwin':
                        subprocess.run(['open', str(output_file)])
                    else:
                        subprocess.run(['xdg-open', str(output_file)], check=False)
                except:
                    print(f"Файл сохранен: {output_file}")
        
    except KeyboardInterrupt:
        print("\n\n❌ Операция прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
