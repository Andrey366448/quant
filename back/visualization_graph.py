import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import numpy as np
import ast
import math
import os
import json
from collections import defaultdict
import heapq


class QuantumInspiredTrafficOptimizer:
    """
    Квантово-вдохновленный оптимизатор дорожного трафика.
    Реализует сведение к QUBО/Изинг с автоматической декомпозицией.
    """

    def __init__(self, graph, routes):
        self.graph = np.array(graph, dtype=np.float64)
        self.routes = routes
        self.n_nodes = len(graph)
        self.n_cars = len(routes)

        self._auto_tune_parameters()
        self.adjacency_list = self._build_adjacency_list()
        self.path_cache = {}
        self._check_decomposition_needed()

    def _auto_tune_parameters(self):
        """Автоматическая настройка гиперпараметров под размер задачи."""
        problem_size = self.n_cars * self.n_nodes
        self.weight_time = 1.0
        self.weight_congestion = 0.5 if problem_size < 1000 else 0.3 if problem_size < 5000 else 0.1
        self.initial_temp = 100.0
        self.cooling_rate = 0.95
        self.tunneling_prob = 0.15
        self.final_temp = 0.1

    def _build_adjacency_list(self):
        """Построение списка смежности для эффективного поиска."""
        adj_list = [[] for _ in range(self.n_nodes)]
        for i in range(self.n_nodes):
            for j in range(self.n_nodes):
                if not math.isinf(self.graph[i][j]) and i != j:
                    adj_list[i].append((j, self.graph[i][j]))
        return adj_list

    def _check_decomposition_needed(self):
        """Проверка необходимости декомпозиции задачи."""
        n_edges = sum(1 for i in range(self.n_nodes)
                      for j in range(self.n_nodes)
                      if not math.isinf(self.graph[i][j]) and i != j)
        problem_size = self.n_cars * n_edges
        self.needs_decomposition = problem_size > 300
        self.problem_size = problem_size
        self.cars_per_subproblem = max(1, 300 // n_edges) if self.needs_decomposition else self.n_cars

    def _find_shortest_path(self, start, end):
        if start == end:
            return [start], 0

        cache_key = (start, end)
        if cache_key in self.path_cache:
            return self.path_cache[cache_key]

        dist = [float('inf')] * self.n_nodes
        prev = [-1] * self.n_nodes
        dist[start] = 0
        heap = [(0, start)]

        while heap:
            current_dist, u = heapq.heappop(heap)
            if u == end:
                break
            if current_dist > dist[u]:
                continue
            for v, weight in self.adjacency_list[u]:
                new_dist = current_dist + weight
                if new_dist < dist[v]:
                    dist[v] = new_dist
                    prev[v] = u
                    heapq.heappush(heap, (new_dist, v))

        if math.isinf(dist[end]):
            result = ([start, end], float('inf'))
        else:
            path = []
            current = end
            while current != -1:
                path.append(current)
                current = prev[current]
            path.reverse()
            result = (path, dist[end])

        self.path_cache[cache_key] = result
        return result

    def _calculate_energy(self, solution):
        """Вычисление энергии решения согласно QUBO формулировке."""
        total_time = 0.0
        edge_usage = defaultdict(int)

        for path in solution:
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                if not math.isinf(self.graph[u][v]):
                    total_time += self.graph[u][v]
                    edge = (min(u, v), max(u, v))
                    edge_usage[edge] += 1

        congestion_penalty = sum(count * (count - 1) for count in edge_usage.values())
        return total_time + self.weight_congestion * congestion_penalty

    def optimize_routes(self):
        """Квантово-вдохновленная оптимизация маршрутов."""
        solution = []
        for start, end in self.routes:
            path, _ = self._find_shortest_path(start, end)
            solution.append(path)

        energy = self._calculate_energy(solution)
        return solution, energy


def parse_matrix(matrix_str):
    """Парсинг матрицы смежности из строки"""
    try:
        matrix_str_clean = matrix_str.strip()
        if matrix_str_clean.startswith('"') and matrix_str_clean.endswith('"'):
            matrix_str_clean = matrix_str_clean[1:-1]
        matrix_str_clean = matrix_str_clean.replace('inf', 'None')

        try:
            matrix_data = ast.literal_eval(matrix_str_clean)
        except:
            matrix_str_clean = matrix_str_clean.replace("'", '"')
            matrix_data = json.loads(matrix_str_clean)

        return [[float('inf') if x is None else x for x in row] for row in matrix_data]
    except Exception as e:
        print(f"Ошибка парсинга матрицы: {e}")
        return None


def parse_routes(routes_str):
    """Парсинг маршрутов из строки"""
    try:
        routes_str_clean = routes_str.strip()
        if routes_str_clean.startswith('"') and routes_str_clean.endswith('"'):
            routes_str_clean = routes_str_clean[1:-1]

        try:
            routes_data = ast.literal_eval(routes_str_clean)
        except:
            routes_str_clean = routes_str_clean.replace("'", '"')
            routes_data = json.loads(routes_str_clean)

        return [tuple(route) for route in routes_data]
    except Exception as e:
        print(f"Ошибка парсинга маршрутов: {e}")
        return None


class TrafficVisualizer:
    """
    Визуализатор графов дорожного движения с использованием QuantumInspiredTrafficOptimizer
    """

    def __init__(self):
        self.colors = plt.cm.Set3(np.linspace(0, 1, 12))
        self.car_markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h']

    def create_graph_from_matrix(self, matrix):
        """Создание графа из матрицы смежности"""
        G = nx.Graph()
        n = len(matrix)

        for i in range(n):
            G.add_node(i)

        for i in range(n):
            for j in range(i + 1, n):
                if not math.isinf(matrix[i][j]) and matrix[i][j] > 0:
                    G.add_edge(i, j, weight=matrix[i][j], traffic=0)

        return G

    def calculate_edge_traffic(self, routes):
        """Подсчет трафика на каждом ребре"""
        edge_traffic = {}

        for route in routes:
            # защита от мусора
            if not isinstance(route, (list, tuple)) or len(route) < 2:
                continue
            for i in range(len(route) - 1):
                edge = tuple(sorted([route[i], route[i + 1]]))
                edge_traffic[edge] = edge_traffic.get(edge, 0) + 1

        return edge_traffic

    def get_node_positions(self, G):
        """Генерация позиций узлов для визуализации"""
        try:
            return nx.spring_layout(G, k=3, iterations=50)
        except:
            return nx.circular_layout(G)

    def visualize_static_traffic(self, graph_matrix, routes, graph_index, total_time,
                                 save_path='visualised_qi'):
        """
        Статическая визуализация графа с цветовой индикацией загруженности ребер
        """
        try:
            G = self.create_graph_from_matrix(graph_matrix)
            edge_traffic = self.calculate_edge_traffic(routes)

            for edge in G.edges():
                edge_key = tuple(sorted(edge))
                traffic = edge_traffic.get(edge_key, 0)
                G.edges[edge]['traffic'] = traffic

            fig, ax = plt.subplots(figsize=(10, 8))
            pos = self.get_node_positions(G)

            traffic_values = [G.edges[edge]['traffic'] for edge in G.edges()]
            max_traffic = max(traffic_values) if traffic_values else 1

            if max_traffic > 0:
                edge_colors = [traffic / max_traffic for traffic in traffic_values]
            else:
                edge_colors = [0] * len(traffic_values)

            nx.draw_networkx_edges(
                G, pos,
                edge_color=edge_colors,
                edge_cmap=plt.cm.RdYlGn_r,
                edge_vmin=0,
                edge_vmax=1,
                width=3,
                alpha=0.7,
                ax=ax
            )

            nx.draw_networkx_nodes(
                G, pos,
                node_color='lightblue',
                node_size=500,
                alpha=0.9,
                ax=ax
            )

            nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold', ax=ax)

            ax.set_title(f'Граф дорожного движения {graph_index}\n'
                         f'Загруженность ребер (всего машин: {len(routes)})\n'
                         f'Общее время движения: {total_time:.2f}',
                         fontsize=14, fontweight='bold')

            ax.axis('off')
            plt.tight_layout()

            os.makedirs(save_path, exist_ok=True)

            filename = f'{save_path}/graph_{graph_index}_traffic.png'
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.close()

            print(f'Сохранено: {filename}')
            return filename

        except Exception as e:
            print(f"Ошибка при визуализации графа {graph_index}: {e}")
            return None

    def process_and_save_results(self, data_file='uploads/data.csv'):
        """
        Основная функция обработки данных и сохранения результатов
        """
        print("=" * 60)
        print("ЗАПУСК ОБРАБОТКИ ДАННЫХ И СОХРАНЕНИЯ РЕЗУЛЬТАТОВ")
        print("=" * 60)

        try:
            # Проверяем существование файла
            if not os.path.exists(data_file):
                print(f"Файл {data_file} не найден!")
                # Пробуем альтернативные пути
                alternative_paths = ['data.csv', '../uploads/data.csv', './uploads/data.csv']
                for path in alternative_paths:
                    if os.path.exists(path):
                        data_file = path
                        print(f"Найден файл по пути: {data_file}")
                        break
                else:
                    print("Не удалось найти файл данных!")
                    return False

            # Загружаем данные
            print(f"Загрузка данных из: {data_file}")
            df = pd.read_csv(data_file)
            print(f"Успешно загружено {len(df)} графов")

            if len(df) == 0:
                print("Файл данных пуст!")
                return False

            all_submission = []
            total_time_data = []
            processed_graphs = 0

            for idx, row in df.iterrows():
                try:
                    graph_index = row['graph_index']
                    print(f"\n--- Обработка графа {graph_index} ---")

                    graph_matrix = parse_matrix(row['graph_matrix'])
                    if graph_matrix is None:
                        print(f"  Ошибка: не удалось распарсить матрицу графа {graph_index}")
                        continue

                    routes_start_end = parse_routes(row['routes_start_end'])
                    if routes_start_end is None:
                        print(f"  Ошибка: не удалось распарсить маршруты графа {graph_index}")
                        continue

                    print(f"  Узлов: {len(graph_matrix)}, Маршрутов: {len(routes_start_end)}")

                    # Оптимизация маршрутов
                    optimizer = QuantumInspiredTrafficOptimizer(graph_matrix, routes_start_end)
                    optimized_routes, total_time = optimizer.optimize_routes()

                    print(f"  Оптимизировано маршрутов: {len(optimized_routes)}, Время: {total_time:.2f}")

                    # Сохраняем результаты
                    total_time_data.append({
                        'graph_index': graph_index,
                        'total_time': total_time
                    })

                    for driver_idx, route in enumerate(optimized_routes):
                        all_submission.append({
                            'graph_index': graph_index,
                            'driver_index': driver_idx,
                            'route': str(route)
                        })

                    processed_graphs += 1
                    print(f"  ✓ Граф {graph_index} обработан успешно")

                except Exception as e:
                    print(f"  ✗ Ошибка при обработке графа {graph_index}: {e}")
                    continue

            # Сохраняем результаты в файлы
            if all_submission and total_time_data:
                print(f"\n--- СОХРАНЕНИЕ РЕЗУЛЬТАТОВ ---")
                print(f"Обработано графов: {processed_graphs} из {len(df)}")
                print(f"Всего маршрутов: {len(all_submission)}")

                # Сохраняем submission_inspired.csv
                submission_df = pd.DataFrame(all_submission)
                submission_path = 'submission_inspired.csv'
                submission_df.to_csv(submission_path, index=False)
                print(f"✓ Маршруты сохранены в: {os.path.abspath(submission_path)}")

                # Сохраняем total_time_inspired.csv
                total_df = pd.DataFrame(total_time_data)
                overall_time = total_df['total_time'].sum()
                total_row = pd.DataFrame([{'graph_index': 'Total', 'total_time': overall_time}])
                total_df = pd.concat([total_df, total_row], ignore_index=True)

                total_time_path = 'total_time_inspired.csv'
                total_df.to_csv(total_time_path, index=False)
                print(f"✓ Время сохранено в: {os.path.abspath(total_time_path)}")
                print(f"✓ Общее время для всех графов: {overall_time:.2f}")

                return True
            else:
                print("\n✗ Нет данных для сохранения!")
                return False

        except Exception as e:
            print(f"\n✗ Критическая ошибка: {e}")
            return False

    def visualize_all_graphs(self, data_file='uploads/data.csv', create_animations=False):
        """
        Визуализация всех графов после обработки
        """
        print("\n" + "=" * 60)
        print("ЗАПУСК ВИЗУАЛИЗАЦИИ")
        print("=" * 60)

        try:
            # Проверяем существование файлов с результатами
            if not os.path.exists('submission_inspired.csv') or not os.path.exists('total_time_inspired.csv'):
                print("Файлы с результатами не найдены. Сначала запустите обработку данных.")
                return [], []

            # Загружаем результаты
            df = pd.read_csv(data_file)
            submission_df = pd.read_csv('submission_inspired.csv')
            time_df = pd.read_csv('total_time_inspired.csv')

            # >>> FIX A: нормализуем graph_index и удаляем агрегатную строку в time_df
            time_df['graph_index'] = pd.to_numeric(time_df['graph_index'], errors='coerce')
            time_df = time_df.dropna(subset=['graph_index']).copy()
            time_df['graph_index'] = time_df['graph_index'].astype(int)
            time_dict = dict(zip(time_df['graph_index'], time_df['total_time']))

            # >>> FIX B: парсим маршруты обратно и нормализуем graph_index в submission_df
            def _parse_route(r):
                if isinstance(r, str):
                    try:
                        return ast.literal_eval(r)
                    except Exception:
                        return None
                return r

            submission_df['route'] = submission_df['route'].apply(_parse_route)
            submission_df['graph_index'] = pd.to_numeric(submission_df['graph_index'], errors='coerce')
            submission_df = submission_df.dropna(subset=['graph_index', 'route']).copy()
            submission_df['graph_index'] = submission_df['graph_index'].astype(int)

            routes_by_graph = (
                submission_df
                .groupby('graph_index')['route']
                .apply(list)
                .to_dict()
            )

            # Нормализуем тип graph_index в исходном датафрейме графов
            df['graph_index'] = pd.to_numeric(df['graph_index'], errors='coerce')
            df = df.dropna(subset=['graph_index']).copy()
            df['graph_index'] = df['graph_index'].astype(int)

            print(f"Загружено {len(df)} графов из {data_file}")
            print(f"Загружено {len(submission_df)} маршрутов из submission_inspired.csv")
            print(f"Загружено время из total_time_inspired.csv")

            # Визуализируем каждый граф
            static_files = []
            successful_visualizations = 0

            for idx, row in df.iterrows():
                graph_index = int(row['graph_index'])
                graph_matrix = parse_matrix(row['graph_matrix'])

                if graph_matrix is None:
                    print(f"Ошибка парсинга графа {graph_index}")
                    continue

                routes = routes_by_graph.get(graph_index, [])
                if not routes:
                    print(f"Нет маршрутов для графа {graph_index}")
                    continue

                total_time = time_dict.get(graph_index)
                if total_time is None:
                    print(f"Нет данных о времени для графа {graph_index}")
                    continue

                print(f"Визуализация графа {graph_index} с {len(routes)} маршрутами...")

                static_file = self.visualize_static_traffic(graph_matrix, routes, graph_index, total_time)
                if static_file:
                    static_files.append(static_file)
                    successful_visualizations += 1

            print(f"\n=== РЕЗУЛЬТАТЫ ВИЗУАЛИЗАЦИИ ===")
            print(f"Успешно визуализировано: {successful_visualizations} графов")
            print(f"Создано изображений: {len(static_files)}")

            return static_files, []

        except Exception as e:
            print(f"Ошибка при визуализации: {e}")
            return [], []


def main():
    """Основная функция для запуска обработки и визуализации"""
    visualizer = TrafficVisualizer()

    # Шаг 1: Обработка данных и сохранение результатов
    success = visualizer.process_and_save_results(data_file='uploads/data.csv')

    if success:
        # Шаг 2: Визуализация результатов
        static_files, animation_files = visualizer.visualize_all_graphs(
            data_file='uploads/data.csv',
            create_animations=False
        )

        print("\n" + "=" * 60)
        print("ВСЕ ОПЕРАЦИИ ЗАВЕРШЕНЫ!")
        print("=" * 60)
        print(f"Создано изображений: {len(static_files)}")
        print(f"Файлы результатов: submission_inspired.csv, total_time_inspired.csv")
        print(f"Изображения сохранены в папке: visualised_qi/")
    else:
        print("\n✗ Программа завершена с ошибками!")

if __name__ == "__main__":
    main()
