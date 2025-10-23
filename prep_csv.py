import csv
import ast
import math

def process_data_file_simple(input_csv, output_matrices, output_routes, output_indices):
    matrices = []
    routes = []    
    graph_indices = []  # Список для хранения соответствий порядковых номеров и номеров матриц
    processed_count = 0
    
    try:
        with open(input_csv, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)
            
            for row_num, row in enumerate(reader, 1):
                if len(row) >= 3:
                    try:
                        # Сохраняем номер матрицы (графа)
                        graph_index = row[0].strip()
                        graph_indices.append((processed_count, graph_index))
                        
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
        
        # Сохраняем матрицы с правильным форматированием (без переноса первой и последней скобки)
        with open(output_matrices, 'w', encoding='utf-8') as f:
            f.write('[')
            for i, matrix in enumerate(matrices):
                if i > 0:
                    f.write(',')
                f.write('')
                # Форматируем матрицу с переносами внутри, но не трогаем внешние скобки
                matrix_str = str(matrix).replace('], [', '],\n [').replace(']], [[', ']],\n\n [[') 
                f.write(matrix_str)
            f.write(']')
        
        # Сохраняем маршруты с правильным форматированием (без переноса первой и последней скобки)
        with open(output_routes, 'w', encoding='utf-8') as f:
            f.write('[')
            for i, route in enumerate(routes):
                if i > 0:
                    f.write(',')
                f.write('')  #sdsfdsfdsfsdfsdfdsf
                # Форматируем маршруты с переносами внутри, но не трогаем внешние скобки
                route_str = str(route).replace('], [', '],\n [').replace(']], [[', ']],\n\n [[')  
                f.write(route_str)
            f.write(']')
        
        # Сохраняем соответствия порядковых номеров и номеров матриц
        with open(output_indices, 'w', encoding='utf-8') as f:
            for i, (order_num, graph_num) in enumerate(graph_indices):
                if i > 0:
                    f.write('\n')
                f.write(f"{order_num} - {graph_num}")
        
        print(f"Успешно обработано: {processed_count} записей")
        print(f"Матрицы сохранены в: {output_matrices}")
        print(f"Маршруты сохранены в: {output_routes}")
        print(f"Соответствия порядковых номеров сохранены в: {output_indices}")
        
    except Exception as e:
        print(f" Произошла ошибка: {e}")

# Запуск скрипта
if __name__ == "__main__":
    # Укажите ваши файлы
    input_file = "data.csv"          # Ваш исходный CSV файл
    matrices_output = "G_set.txt"    # Файл для матриц
    routes_output = "routes.txt"     # Файл для маршрутов
    indices_output = "graph_indices.txt"  # Новый файл для соответствий номеров
    
    process_data_file_simple(input_file, matrices_output, routes_output, indices_output)
