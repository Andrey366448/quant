import csv
import ast
import math

def format_with_newlines(obj):
    """
    Форматирует объект с переносами строк после закрывающих скобок и запятых
    """
    def format_list(lst, indent=0):
        if not lst:
            return "[]"
        
        spaces = " " * indent
        result = "[\n"
        
        for i, item in enumerate(lst):
            if isinstance(item, list):
                formatted_item = format_list(item, indent + 2)
            else:
                formatted_item = str(item)
            
            result += spaces + "  " + formatted_item
            if i < len(lst) - 1:
                result += ","
            result += "\n"
        
        result += spaces + "]"
        return result
    
    if isinstance(obj, list):
        return format_list(obj)
    else:
        return str(obj)

def process_data_file(input_csv, output_matrices, output_routes):
    """
    Обрабатывает CSV файл с матрицами и маршрутами, разделяет их в разные файлы
    с правильным форматированием
    """
    matrices = []
    routes = []    
    processed_count = 0
    
    try:
        with open(input_csv, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Пропускаем заголовок
            
            for row_num, row in enumerate(reader, 1):
                if len(row) >= 3:
                    try:
                        # Обрабатываем матрицу
                        matrix_str = row[1].strip()
                        
                        # Убираем лишние кавычки
                        if matrix_str.startswith('"') and matrix_str.endswith('"'):
                            matrix_str = matrix_str[1:-1]
                        if matrix_str.startswith('"') and matrix_str.endswith('"'):
                            matrix_str = matrix_str[1:-1]
                        
                        # Заменяем inf на math.inf для корректного парсинга
                        matrix_str = matrix_str.replace('inf', 'math.inf')
                        
                        # Парсим матрицу
                        matrix_data = eval(matrix_str, {'math': math})
                        matrices.append(matrix_data)
                        
                        # Обрабатываем маршруты
                        routes_str = row[2].strip()
                        
                        # Убираем лишние кавычки
                        if routes_str.startswith('"') and routes_str.endswith('"'):
                            routes_str = routes_str[1:-1]
                        if routes_str.startswith('"') and routes_str.endswith('"'):
                            routes_str = routes_str[1:-1]
                        
                        # Парсим маршруты
                        routes_data = ast.literal_eval(routes_str)
                        routes.append(routes_data)
                        
                        processed_count += 1
                        
                    except (SyntaxError, ValueError, NameError) as e:
                        print(f"Ошибка при обработке строки {row_num}: {e}")
                        continue
        
        # Сохраняем матрицы в файл с правильным форматированием
        with open(output_matrices, 'w', encoding='utf-8') as f:
            if matrices:
                formatted = format_with_newlines(matrices)
                f.write(formatted)
        
        # Сохраняем маршруты в файл с правильным форматированием
        with open(output_routes, 'w', encoding='utf-8') as f:
            if routes:
                formatted = format_with_newlines(routes)
                f.write(formatted)
        
        print(f"✅ Успешно обработано: {processed_count} записей")
        print(f"📊 Матрицы сохранены в: {output_matrices}")
        print(f"🛣️  Маршруты сохранены в: {output_routes}")
        
    except FileNotFoundError:
        print(f"❌ Файл {input_csv} не найден")
    except Exception as e:
        print(f"❌ Произошла ошибка: {e}")

# Альтернативная версия с более простым форматированием
def process_data_file_simple(input_csv, output_matrices, output_routes):
    """
    Упрощенная версия с базовым форматированием
    """
    matrices = []
    routes = []    
    processed_count = 0
    
    try:
        with open(input_csv, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)
            
            for row_num, row in enumerate(reader, 1):
                if len(row) >= 3:
                    try:
                        # Обрабатываем матрицу
                        matrix_str = row[1].strip()
                        if matrix_str.startswith('"') and matrix_str.endswith('"'):
                            matrix_str = matrix_str[1:-1]
                        matrix_str = matrix_str.replace('inf', 'math.inf')
                        matrix_data = eval(matrix_str, {'math': math})
                        matrices.append(matrix_data)
                        
                        # Обрабатываем маршруты
                        routes_str = row[2].strip()
                        if routes_str.startswith('"') and routes_str.endswith('"'):
                            routes_str = routes_str[1:-1]
                        routes_data = ast.literal_eval(routes_str)
                        routes.append(routes_data)
                        
                        processed_count += 1
                        
                    except Exception as e:
                        print(f"Ошибка при обработке строки {row_num}: {e}")
                        continue
        
        # Сохраняем матрицы с переносами строк
        with open(output_matrices, 'w', encoding='utf-8') as f:
            f.write('[')
            for i, matrix in enumerate(matrices):
                if i > 0:
                    f.write(',')
                f.write('\n')
                f.write(str(matrix).replace('], [', '],\n [').replace(']], [[', ']],\n\n [['))
            f.write('\n]')
        
        # Сохраняем маршруты с переносами строк
        with open(output_routes, 'w', encoding='utf-8') as f:
            f.write('[')
            for i, route in enumerate(routes):
                if i > 0:
                    f.write(',')
                f.write('\n')
                f.write(str(route).replace('], [', '],\n [').replace(']], [[', ']],\n\n [['))
            f.write('\n]')
        
        print(f"✅ Успешно обработано: {processed_count} записей")
        print(f"📊 Матрицы сохранены в: {output_matrices}")
        print(f"🛣️  Маршруты сохранены в: {output_routes}")
        
    except Exception as e:
        print(f"❌ Произошла ошибка: {e}")

# Запуск скрипта
if __name__ == "__main__":
    # Укажите ваши файлы
    input_file = "data.csv"          # Ваш исходный CSV файл
    matrices_output = "G_set1.txt"    # Файл для матриц
    routes_output = "routes1.txt"     # Файл для маршрутов
    
    # Используйте первую версию для красивого форматирования
    # или вторую для более простого
    process_data_file_simple(input_file, matrices_output, routes_output)