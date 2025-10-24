import json
import pandas as pd
import glob
import os
import numpy as np

def extract_graph_number(filename):
    """Извлекает номер графа из имени файла"""
    try:
        # Ищем числа в имени файла
        numbers = ''.join(filter(str.isdigit, filename))
        return int(numbers) if numbers else -1
    except:
        return -1

def calculate_path_cost(path, graph_matrix):
    """Вычисляет стоимость пути на основе матрицы графа"""
    if graph_matrix is None:
        return len(path) * 10.0  # Примерная оценка если матрицы нет
    
    cost = 0.0
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        if (u < graph_matrix.shape[0] and v < graph_matrix.shape[1] and
            graph_matrix[u, v] != np.inf):
            cost += abs(graph_matrix[u, v])
    return cost

def load_graph_matrices():
    """Загружает все матрицы графов из файлов"""
    graph_matrices = {}
    
    # Ищем файлы с графами
    graph_files = glob.glob('G_set*.txt')
    if not graph_files:
        print("Файлы графов (new_G_set*.txt) не найдены")
        return graph_matrices
    
    for graph_file in graph_files:
        print(f"Загрузка графов из {graph_file}...")
        try:
            with open(graph_file, 'r') as f:
                content = f.read()
            
            # Разделяем на срезы
            slices = content.split('# Slice')[1:]
            
            for slice_idx, slice_content in enumerate(slices):
                lines = slice_content.strip().split('\n')
                matrix_lines = []
                
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        matrix_lines.append(line)
                
                if not matrix_lines:
                    continue
                
                # Создаем матрицу
                matrix_size = len(matrix_lines)
                matrix = []
                
                for line in matrix_lines:
                    values = line.split()
                    row = []
                    for val in values:
                        if val == 'inf':
                            row.append(np.inf)
                        else:
                            try:
                                row.append(float(val))
                            except ValueError:
                                row.append(np.inf)
                    
                    # Дополняем строку до нужного размера если необходимо
                    if len(row) < matrix_size:
                        row.extend([np.inf] * (matrix_size - len(row)))
                    elif len(row) > matrix_size:
                        row = row[:matrix_size]
                    
                    matrix.append(row)
                
                if len(matrix) == matrix_size:
                    graph_matrices[slice_idx] = np.array(matrix)
                    print(f"  Загружен граф {slice_idx}: {matrix_size}x{matrix_size}")
                else:
                    print(f"  Предупреждение: граф {slice_idx} имеет неверный размер")
                    
        except Exception as e:
            print(f"Ошибка при загрузке {graph_file}: {e}")
    
    print(f"Всего загружено матриц графов: {len(graph_matrices)}")
    return graph_matrices


def process_all_graph_files():
    """Обрабатывает все файлы с результатами и создает CSV файлы"""
    
    # Загружаем матрицы графов для вычисления времени
    graph_matrices = load_graph_matrices()
    
    # Находим все файлы с результатами
    file_pattern = 'post_processed_results/post_processed_routes_graph_*.json'
    json_files = glob.glob(file_pattern)
    
    if not json_files:
        print(f"Файлы результатов '{file_pattern}' не найдены")
        print("Сначала запустите основную обработку графов")
        return
    
    print(f"Найдено файлов результатов: {len(json_files)}")
    
    # Создаем списки для данных
    all_submission_data = []
    all_total_time_data = []
    total_overall_time = 0.0
    
    for json_file in json_files:
        # Извлекаем номер графа из имени файла
        graph_index = extract_graph_number(os.path.basename(json_file))
        
        if graph_index == -1:
            print(f"Не удалось извлечь номер графа из {json_file}, пропускаем")
            continue
        
        # Загружаем данные из JSON
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки {json_file}: {e}")
            continue
        
        # Проверяем наличие путей
        if 'repaired_paths' not in data:
            print(f"Файл {json_file} не содержит repaired_paths")
            continue
        
        repaired_paths = data['repaired_paths']
        
        # Добавляем маршруты в submission данные
        for driver_index, route in enumerate(repaired_paths):
            all_submission_data.append({
                'graph_index': graph_index,
                'driver_index': driver_index,
                'route': str(route)
            })
        
        # Вычисляем общее время для этого графа
        graph_total_time = 0.0
        
        # Пробуем разные способы получить время
        if 'total_time' in data:
            # Используем сохраненное значение
            graph_total_time = data['total_time']
        elif 'path_costs' in data:
            # Суммируем стоимости путей
            graph_total_time = sum(data['path_costs'])
        elif graph_index in graph_matrices:
            # Вычисляем по матрице графа
            for path in repaired_paths:
                graph_total_time += calculate_path_cost(path, graph_matrices[graph_index])
        else:
            # Оценочное время
            graph_total_time = len(repaired_paths) * 150.0
        
        total_overall_time += graph_total_time
        
        # Добавляем в total_time данные
        all_total_time_data.append({
            'graph_index': graph_index,
            'total_time': graph_total_time
        })
        
        print(f"Обработан граф {graph_index}: {len(repaired_paths)} маршрутов, время: {graph_total_time:.2f}")
    
    # Создаем DataFrame
    submission_df = pd.DataFrame(all_submission_data)
    total_time_df = pd.DataFrame(all_total_time_data)
    
    # Добавляем итоговую строку
    total_time_df = pd.concat([
        total_time_df,
        pd.DataFrame([{'graph_index': 'Total', 'total_time': total_overall_time}])
    ], ignore_index=True)
    
    # Сохраняем CSV файлы
    submission_df.to_csv('submission.csv', index=False)
    total_time_df.to_csv('total_time.csv', index=False)
    
    # Выводим статистику
    print(f"\n=== РЕЗУЛЬТАТЫ ===")
    print(f"Создан submission.csv с {len(submission_df)} маршрутами")
    print(f"Создан total_time.csv с {len(total_time_df)} записями")
    print(f"Общее время всех графов: {total_overall_time:.2f}")
    
    # Показываем примеры данных
    if len(submission_df) > 0:
        print(f"\nПример submission данных:")
        print(submission_df.head())
    
    if len(total_time_df) > 0:
        print(f"\nПример total_time данных:")
        print(total_time_df.head())

# Основная функция
if __name__ == "__main__":
    print("=== ГЕНЕРАЦИЯ CSV ФАЙЛОВ ===")
    
    # Обрабатываем все файлы
    process_all_graph_files()
    
    print("\n=== ЗАВЕРШЕНО ===")
