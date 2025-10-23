import json
import pandas as pd
import glob
import os

def load_graph_indices():
    """Загружает соответствия номеров из graph_indices.txt"""
    indices = {}
    try:
        with open('graph_indices.txt', 'r') as f:
            for line in f:
                if '-' in line:
                    parts = line.strip().split(' - ')
                    if len(parts) == 2:
                        file_num = int(parts[0])
                        graph_index = int(parts[1])
                        indices[file_num] = graph_index
        print(f"Загружено {len(indices)} соответствий из graph_indices.txt")
        return indices
    except Exception as e:
        print(f"Ошибка при загрузке graph_indices.txt: {e}")
        return {}

def process_all_graph_files():
    # Загружаем соответствия номеров
    graph_indices = load_graph_indices()
    
    if not graph_indices:
        print("Не удалось загрузить graph_indices.txt, завершение работы.")
        return
    
    # Находим все файлы, соответствующие шаблону
    file_pattern = 'post_processed_routes_graph_*.json'
    json_files = glob.glob(file_pattern)
    
    if not json_files:
        print(f"Файлы по шаблону '{file_pattern}' не найдены.")
        return
    
    # Создаем списки для накопления данных
    all_submission_data = []
    all_total_time_data = []
    
    for json_file_path in json_files:
        # Извлекаем номер из имени файла
        base_name = os.path.basename(json_file_path)
        try:
            # Ищем число в имени файла
            file_number = int(''.join(filter(str.isdigit, base_name)))
        except Exception as e:
            print(f"Ошибка при извлечении номера из файла {base_name}: {e}")
            continue
        
        # Получаем соответствующий graph_index из словаря
        if file_number not in graph_indices:
            print(f"Для файла {base_name} (номер {file_number}) не найдено соответствие в graph_indices.txt, пропускаем.")
            continue
            
        graph_index = graph_indices[file_number]
        
        # Загрузка JSON файла
        try:
            with open(json_file_path, 'r') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Ошибка при чтении файла {json_file_path}: {e}")
            continue
        
        # Проверяем наличие необходимых ключей
        if 'repaired_paths' not in data:
            print(f"Файл {json_file_path} не содержит необходимого ключа 'repaired_paths'")
            continue
        
        repaired_paths = data['repaired_paths']
        
        # Добавляем данные в общий список для submission
        for driver_index, route in enumerate(repaired_paths):
            all_submission_data.append({
                'graph_index': graph_index,  # Используем значение из graph_indices.txt
                'driver_index': driver_index,
                'route': str(route)
            })
        
        # Добавляем данные в общий список для total_time
        all_total_time_data.append({
            'graph_index': graph_index,  # Используем значение из graph_indices.txt
            'total_time': 0.0  # Замените на реальное вычисление времени
        })
        
        print(f"Обработан файл {json_file_path}:")
        print(f"  - Номер файла: {file_number} -> graph_index: {graph_index}")
        print(f"  - Добавлено {len(repaired_paths)} маршрутов")
    
    # Создаем общие DataFrame из накопленных данных
    submission_df = pd.DataFrame(all_submission_data)
    total_time_df = pd.DataFrame(all_total_time_data)
    
    # Сохраняем в единые CSV файлы
    submission_df.to_csv('submission.csv', index=False)
    total_time_df.to_csv('total_time.csv', index=False)
    
    print(f"\nИтоги обработки:")
    print(f"  - Обработано файлов: {len(json_files)}")
    print(f"  - Создан submission.csv с {len(submission_df)} маршрутами")
    print(f"  - Создан total_time.csv с {len(total_time_df)} записями")

# Запуск обработки всех файлов
process_all_graph_files()
