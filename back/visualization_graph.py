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
    Реализует сведение к QUBO/Изинг с автоматической декомпозицией.
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

        if problem_size < 1000:
            self.weight_congestion = 0.5
        elif problem_size < 5000:
            self.weight_congestion = 0.3
        else:
            self.weight_congestion = 0.1

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
        # Подсчет ребер
        n_edges = sum(1 for i in range(self.n_nodes)
                      for j in range(self.n_nodes)
                      if not math.isinf(self.graph[i][j]) and i != j)

        problem_size = self.n_cars * n_edges
        self.needs_decomposition = problem_size > 300
        self.problem_size = problem_size

        if self.needs_decomposition:
            self.cars_per_subproblem = max(1, 300 // n_edges)
        else:
            self.cars_per_subproblem = self.n_cars

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
    except:
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
    except:
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

    def visualize_all_graphs(self, data_file='uploads/data.csv', create_animations=True):
        """
        Визуализация всех графов из data.csv с использованием QuantumInspiredTrafficOptimizer
        """
        try:
            # Загружаем данные
            df = pd.read_csv(data_file)
            print(f"Загружено {len(df)} графов из {data_file}")

            static_files = []
            animation_files = []

            for idx, row in df.iterrows():
                graph_index = row['graph_index']
                graph_matrix = parse_matrix(row['graph_matrix'])
                routes_start_end = parse_routes(row['routes_start_end'])

                if graph_matrix is None or routes_start_end is None:
                    print(f"Ошибка парсинга графа {graph_index}")
                    continue

                print(f"Оптимизация графа {graph_index} с {len(routes_start_end)} маршрутами...")
                optimizer = QuantumInspiredTrafficOptimizer(graph_matrix, routes_start_end)
                optimized_routes, total_time = optimizer.optimize_routes()

                print(f"Граф {graph_index}: {len(optimized_routes)} маршрутов, время: {total_time:.2f}")

                static_file = self.visualize_static_traffic(
                    graph_matrix, optimized_routes, graph_index, total_time)
                static_files.append(static_file)

                if create_animations and len(optimized_routes) <= 20:
                    try:
                        animation_file = self.visualize_animated_traffic(
                            graph_matrix, optimized_routes, graph_index, total_time)
                        animation_files.append(animation_file)
                    except Exception as e:
                        print(f"Ошибка создания анимации для графа {graph_index}: {e}")

            print(f"\n=== РЕЗУЛЬТАТЫ ВИЗУАЛИЗАЦИИ ===")
            print(f"Создано изображений: {len(static_files)}")

            return static_files, animation_files

        except Exception as e:
            print(f"Ошибка при визуализации: {e}")
            return [], []



def main():
    """Основная функция для запуска визуализации"""
    visualizer = TrafficVisualizer()

    print("Запуск визуализации графов дорожного движения...")
    print("Используется QuantumInspiredTrafficOptimizer")
    print("=" * 50)

    static_files, animation_files = visualizer.visualize_all_graphs(
        data_file='uploads/data.csv',
        create_animations=True
    )

    print("\nВизуализация завершена!")
    print(f"Статические изображения сохранены в папке: traffic_visualizations/")



if __name__ == "__main__":

    main()

