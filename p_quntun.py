import json
import numpy as np
import math
from collections import defaultdict
import os
import glob
import time
import traceback


CHECK_INTERVAL = 5  # СЕКУНД
FORCE_REPROCESS = False


class BinaryQAOAPostProcessor:
    """Постобработка результатов QAOA с бинарным кодированием"""
    
    def __init__(self, graph_matrix, n_nodes, n_qubits_per_node):
        self.J = graph_matrix
        self.n_nodes = n_nodes
        self.n_qubits_per_node = n_qubits_per_node
        self.total_qubits = n_qubits_per_node
        
    def binary_to_node(self, bitstring):
        """Преобразует бинарную строку в номер вершины"""
        if len(bitstring) != self.n_qubits_per_node:
            raise ValueError(f"Длина битовой строки {len(bitstring)} не совпадает с n_qubits_per_node {self.n_qubits_per_node}")
        
        node_id = int(bitstring, 2)
        
        if node_id >= self.n_nodes:
            node_id = node_id % self.n_nodes
            
        return node_id
    
    def compute_marginals_from_counts(self, counts, n_qubits):
        """Вычисляет маргинальные вероятности P(x_i=1) из гистограммы"""
        total = sum(counts.values())
        marginals = np.zeros(n_qubits, dtype=float)
        
        if total == 0:
            return marginals
            
        for bitstring, cnt in counts.items():
            bits = [int(bit) for bit in bitstring[::-1]]
            
            for i in range(min(len(bits), n_qubits)):
                marginals[i] += cnt * bits[i]
                
        return marginals / float(total)
    
    def find_best_path_binary(self, counts, start_node, end_node, current_traffic):
        """Находит лучший путь на основе бинарного кодирования"""
        if not counts:
            return start_node, 0.0
            
        marginals = self.compute_marginals_from_counts(counts, self.total_qubits)
        
        best_bitstring = None
        max_count = -1
        
        for bitstring, count in counts.items():
            if count > max_count:
                max_count = count
                best_bitstring = bitstring
        
        if best_bitstring is None:
            return start_node, 0.0
            
        selected_node = self.binary_to_node(best_bitstring)
        
        if start_node < self.n_nodes and selected_node < self.n_nodes:
            if self.J[start_node, selected_node] != np.inf:
                cost = abs(self.J[start_node, selected_node])
                traffic_penalty = current_traffic[start_node, selected_node] * 0.1
                total_cost = cost + traffic_penalty
            else:
                total_cost = 1000
        else:
            total_cost = 1000
            
        return selected_node, total_cost
    
    def greedy_path_construction(self, counts_list, routes, traffic_matrix, max_path_length=10):
        """Строит пути жадным алгоритмом на основе квантовых результатов"""
        paths = []
        total_costs = []
        current_traffic = traffic_matrix.copy()
        
        for car_idx, (start, end) in enumerate(routes):
            if car_idx >= len(counts_list):
                path = [start, end]
                paths.append(path)
                total_costs.append(0.0)
                continue
                
            current_node = start
            path = [start]
            path_cost = 0.0
            
            for step in range(max_path_length):
                if current_node == end:
                    break
                    
                counts = counts_list[car_idx]
                next_node, step_cost = self.find_best_path_binary(counts, current_node, end, current_traffic)
                
                if (next_node not in path and 
                    current_node < self.n_nodes and next_node < self.n_nodes and
                    self.J[current_node, next_node] != np.inf):
                    
                    path.append(next_node)
                    path_cost += step_cost
                    
                    current_traffic[current_node, next_node] += 1
                    current_traffic[next_node, current_node] += 1
                    
                    current_node = next_node
                else:
                    found_alternative = False
                    for node in range(self.n_nodes):
                        if (node not in path and 
                            current_node < self.n_nodes and node < self.n_nodes and
                            self.J[current_node, node] != np.inf):
                            
                            path.append(node)
                            cost = abs(self.J[current_node, node])
                            path_cost += cost
                            current_traffic[current_node, node] += 1
                            current_traffic[node, current_node] += 1
                            current_node = node
                            found_alternative = True
                            break
                    
                    if not found_alternative:
                        break
            
            if path[-1] != end:
                path.append(end)
                
            paths.append(path)
            total_costs.append(path_cost)
            
        return paths, total_costs, current_traffic
    
    def conflict_repair(self, paths, traffic_matrix, capacity_matrix, lam_conflict=3.0):
        """Устраняет конфликты в путях"""
        repaired_paths = paths.copy()
        conf_adj = self.build_conflict_adjacency(paths, capacity_matrix)
        
        improved = True
        iterations = 0
        
        while improved and iterations < 100:
            improved = False
            iterations += 1
            
            conflict_pairs = self.find_conflict_pairs(conf_adj, repaired_paths)
            
            if not conflict_pairs:
                break
                
            ti, tj = conflict_pairs[0]
            best_improvement = (float('inf'), None, None)
            
            for alt_path in self.generate_alternative_paths(repaired_paths[ti], capacity_matrix):
                improvement = self.evaluate_path_change(repaired_paths, ti, alt_path, conf_adj, lam_conflict)
                if improvement < best_improvement[0]:
                    best_improvement = (improvement, ti, alt_path)
            
            for alt_path in self.generate_alternative_paths(repaired_paths[tj], capacity_matrix):
                improvement = self.evaluate_path_change(repaired_paths, tj, alt_path, conf_adj, lam_conflict)
                if improvement < best_improvement[0]:
                    best_improvement = (improvement, tj, alt_path)
            
            if best_improvement[1] is not None:
                repaired_paths[best_improvement[1]] = best_improvement[2]
                improved = True
                
        return repaired_paths
    
    def build_conflict_adjacency(self, paths, capacity_matrix):
        """Строит граф конфликтов между путями"""
        conf_adj = defaultdict(set)
        
        for i, path_i in enumerate(paths):
            edges_i = self.get_path_edges(path_i)
            for j, path_j in enumerate(paths):
                if i == j:
                    continue
                    
                edges_j = self.get_path_edges(path_j)
                common_edges = edges_i.intersection(edges_j)
                
                for edge in common_edges:
                    u, v = edge
                    if (u < capacity_matrix.shape[0] and v < capacity_matrix.shape[1] and
                        capacity_matrix[u, v] <= 1):
                        conf_adj[(i, tuple(path_i))].add((j, tuple(path_j)))
                        conf_adj[(j, tuple(path_j))].add((i, tuple(path_i)))
                        
        return conf_adj
    
    def get_path_edges(self, path):
        """Возвращает множество ребер пути"""
        edges = set()
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            edges.add((min(u, v), max(u, v)))
        return edges
    
    def find_conflict_pairs(self, conf_adj, paths):
        """Находит пары конфликтующих путей"""
        conflicts = []
        path_tuples = [tuple(path) for path in paths]
        
        for i, path_i in enumerate(path_tuples):
            for j, path_j in enumerate(path_tuples):
                if i < j and (j, path_j) in conf_adj.get((i, path_i), set()):
                    conflicts.append((i, j))
                    
        return conflicts
    
    def generate_alternative_paths(self, path, capacity_matrix, n_alternatives=3):
        """Генерирует альтернативные пути"""
        alternatives = [path]
        
        if len(path) <= 2:
            return alternatives
            
        for i in range(1, len(path) - 1):
            new_path = path[:i] + path[i+1:]
            if self.is_valid_path(new_path, capacity_matrix):
                alternatives.append(new_path)
                
            if len(alternatives) >= n_alternatives:
                break
                
        return alternatives
    
    def is_valid_path(self, path, capacity_matrix):
        """Проверяет валидность пути"""
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            if (u >= capacity_matrix.shape[0] or v >= capacity_matrix.shape[1] or
                capacity_matrix[u, v] == 0):
                return False
        return True
    
    def evaluate_path_change(self, paths, changed_idx, new_path, conf_adj, lam_conflict):
        """Оценивает улучшение при изменении пути"""
        old_conflicts = 0
        new_conflicts = 0
        
        for j, path_j in enumerate(paths):
            if j == changed_idx:
                continue
            if (j, tuple(paths[j])) in conf_adj.get((changed_idx, tuple(paths[changed_idx])), set()):
                old_conflicts += 1
        
        for j, path_j in enumerate(paths):
            if j == changed_idx:
                continue
            if (j, tuple(paths[j])) in conf_adj.get((changed_idx, tuple(new_path)), set()):
                new_conflicts += 1
                
        old_cost = self.calculate_path_cost(paths[changed_idx])
        new_cost = self.calculate_path_cost(new_path)
        
        cost_change = new_cost - old_cost
        conflict_change = new_conflicts - old_conflicts
        
        return cost_change + lam_conflict * conflict_change
    
    def calculate_path_cost(self, path):
        """Вычисляет стоимость пути"""
        cost = 0.0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            if (u < self.J.shape[0] and v < self.J.shape[1] and 
                self.J[u, v] != np.inf):
                cost += abs(self.J[u, v])
        return cost

    def calculate_total_time(self, paths):
        """Вычисляет общее время для всех автомобилей (сумма длин всех путей)"""
        total_time = 0.0
        for path in paths:
            total_time += self.calculate_path_cost(path)
        return total_time


def load_quantum_results_for_graph(graph_idx, results_folder="results"):
    """Загружает результаты только для одного графа"""
    
    graph_folder = os.path.join(results_folder, f"graph_{graph_idx}")
    
    if not os.path.exists(graph_folder):
        print(f"  ПРЕДУПРЕЖДЕНИЕ: Папка {graph_folder} не найдена")
        return []
    
    # ИСПРАВЛЕНО: Используем тот же паттерн что и в оригинале
    result_files = glob.glob(os.path.join(graph_folder, "Result_*.json"))
    
    if not result_files:
        print(f"  ПРЕДУПРЕЖДЕНИЕ: Файлы для графа {graph_idx} не найдены")
        return []
    
    # ИСПРАВЛЕНО: Точно такая же сортировка как в оригинале
    result_files.sort(key=lambda x: int(os.path.basename(x).split("_car_")[1].split(".")[0]))
    
    print(f"  ✓ Найдено {len(result_files)} файлов результатов для графа {graph_idx}")
    
    graph_results = []
    for file_path in result_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            counts = {}
            for item in data['data']:
                counts[item['bitstring']] = item['value']
            graph_results.append(counts)
        except Exception as e:
            print(f"  ✗ Ошибка загрузки {os.path.basename(file_path)}: {e}")
            graph_results.append({})
    
    return graph_results


def print_detailed_paths(graph_idx, routes, initial_paths, repaired_paths, costs, total_time, graph):
    """Выводит подробную информацию о путях машин"""
    print(f"\n{'='*60}")
    print(f"ГРАФ {graph_idx}: ДЕТАЛЬНАЯ ИНФОРМАЦИЯ О ПУТЯХ")
    print(f"{'='*60}")
    print(f"Количество машин: {len(routes)}")
    print(f"Общее время всех машин: {total_time:.2f}")
    print(f"\nМаршруты (старт -> финиш): {routes}")
    print(f"\nПУТИ МАШИН:")
    print(f"{'-'*60}")
    
    for i, ((start, end), initial_path, repaired_path, cost) in enumerate(zip(routes, initial_paths, repaired_paths, costs)):
        print(f"Машина {i}: {start} -> {end}")
        print(f"  Начальный путь: {initial_path}")
        print(f"  Оптимизированный путь: {repaired_path}")
        print(f"  Время пути: {cost:.2f}")
        
        if initial_path != repaired_path:
            try:
                initial_cost = sum(abs(graph[initial_path[j], initial_path[j+1]]) 
                                 for j in range(len(initial_path)-1) 
                                 if graph[initial_path[j], initial_path[j+1]] != np.inf)
                improvement = initial_cost - cost
                if improvement > 0:
                    print(f"  УЛУЧШЕНИЕ: -{improvement:.2f} (с {initial_cost:.2f} до {cost:.2f})")
            except Exception:
                pass
        
        print(f"{'-'*40}")


def post_process_single_graph(graph_idx, graph, routes, results_folder="results", output_dir="post_processed_results"):
    """Обрабатывает один конкретный граф по его индексу"""
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    quantum_counts = load_quantum_results_for_graph(graph_idx, results_folder)
    
    if not quantum_counts:
        print(f"  ✗ Нет квантовых результатов для графа {graph_idx}")
        return None
    
    n_nodes = len(graph)
    n_qubits_per_node = math.ceil(math.log2(n_nodes)) if n_nodes > 0 else 0
    
    print(f"\n{'#'*80}")
    print(f"ОБРАБОТКА ГРАФА {graph_idx}")
    print(f"Количество вершин: {n_nodes}, Кубитов на вершину: {n_qubits_per_node}")
    print(f"{'#'*80}")
    
    processor = BinaryQAOAPostProcessor(graph, n_nodes, n_qubits_per_node)
    traffic_matrix = np.zeros_like(graph)
    capacity_matrix = np.where(graph != np.inf, 2, 0)
    
    print(f"Обработка {len(routes)} машин...")
    
    paths, costs, updated_traffic = processor.greedy_path_construction(
        quantum_counts, routes, traffic_matrix
    )
    
    repaired_paths = processor.conflict_repair(paths, updated_traffic, capacity_matrix)
    total_time = processor.calculate_total_time(repaired_paths)
    
    # ИСПРАВЛЕНО: Передаем параметр graph
    print_detailed_paths(graph_idx, routes, paths, repaired_paths, costs, total_time, graph)
    
    results = {
        "graph_index": graph_idx,
        "initial_paths": paths,
        "repaired_paths": repaired_paths,
        "path_costs": costs,
        "final_traffic": updated_traffic.tolist(),
        "total_cost": sum(costs),
        "total_time": total_time,
        "encoding_info": {
            "n_nodes": n_nodes,
            "n_qubits_per_node": n_qubits_per_node,
            "binary_encoding": "vertex_index",
        },
    }
    
    output_file = os.path.join(output_dir, f"post_processed_routes_graph_{graph_idx}.json")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Результаты для графа {graph_idx} сохранены в {output_file}")
    except Exception as e:
        print(f"✗ Ошибка при сохранении результата для графа {graph_idx}: {e}")
        traceback.print_exc()
    
    return results


def load_graphs_from_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
        content = content.replace('inf', 'np.inf')
        graphs = eval(content)
        graphs = [np.array(graph) for graph in graphs]
        return graphs


def load_routes_from_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
        routes = eval(content)
        return routes


def check_graph_has_all_results(graph_idx, routes, results_folder):
    """Проверяет, что для графа есть результаты для всех машин"""
    graph_folder = os.path.join(results_folder, f"graph_{graph_idx}")
    
    if not os.path.exists(graph_folder):
        return False
    
    result_files = glob.glob(os.path.join(graph_folder, "Result_*.json"))
    
    expected_count = len(routes)
    actual_count = len(result_files)
    
    if actual_count < expected_count:
        return False
    
    return True


def background_postprocessor(graph_file, routes_file, results_folder, output_dir, force_reprocess=False):
    """
    Фоновый цикл с обработкой ошибок, ждущий появления новых данных и выполняющий постобработку.
    """
    
    print("="*80)
    print("ЗАПУСК ФОНОВОГО ПОСТПРОЦЕССОРА")
    print("="*80)
    print(f"Файл графов: {graph_file}")
    print(f"Файл маршрутов: {routes_file}")
    print(f"Папка с результатами: {results_folder}")
    print(f"Папка для сохранения: {output_dir}")
    print(f"Интервал проверки: {CHECK_INTERVAL} сек")
    print(f"Переобработка: {'ДА' if force_reprocess else 'НЕТ'}")
    print("="*80)
    
    try:
        print("\nЗагрузка графов...")
        graphs = load_graphs_from_file(graph_file)
        print(f"✓ Загружено графов: {len(graphs)}")
    except Exception as e:
        print(f"✗ КРИТИЧЕСКАЯ ОШИБКА при загрузке графов: {e}")
        traceback.print_exc()
        return
    
    try:
        print("Загрузка маршрутов...")
        all_routes = load_routes_from_file(routes_file)
        print(f"✓ Загружено наборов маршрутов: {len(all_routes)}")
    except Exception as e:
        print(f"✗ КРИТИЧЕСКАЯ ОШИБКА при загрузке маршрутов: {e}")
        traceback.print_exc()
        return
    
    print("\nВхожу в цикл мониторинга...\n")
    
    while True:
        try:
            existing_graphs = set()
            
            if os.path.exists(results_folder):
                graph_folders = glob.glob(os.path.join(results_folder, "graph_*"))
                
                for graph_folder in graph_folders:
                    try:
                        graph_name = os.path.basename(graph_folder)
                        graph_index = int(graph_name.split("_")[1])
                        
                        if graph_index < len(all_routes):
                            if check_graph_has_all_results(graph_index, all_routes[graph_index], results_folder):
                                existing_graphs.add(graph_index)
                    except Exception:
                        continue
            
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            if force_reprocess:
                processed_graphs = set()
            else:
                processed_files = glob.glob(os.path.join(output_dir, "post_processed_routes_graph_*.json"))
                processed_graphs = set()
                for pf in processed_files:
                    try:
                        idx = int(os.path.basename(pf).split("_")[-1].split(".")[0])
                        processed_graphs.add(idx)
                    except Exception:
                        continue
            
            new_graphs = existing_graphs - processed_graphs
            
            if new_graphs:
                print(f"\n{'='*80}")
                print(f"✓ {'Переобработка' if force_reprocess else 'Найдены новые'} графы: {sorted(new_graphs)}")
                print(f"{'='*80}")
                
                for idx in sorted(new_graphs):
                    try:
                        if idx >= len(graphs) or idx >= len(all_routes):
                            continue
                        
                        print(f"\n>>> Запускаю постобработку графа {idx}")
                        
                        result = post_process_single_graph(
                            idx, 
                            graphs[idx], 
                            all_routes[idx],
                            results_folder=results_folder, 
                            output_dir=output_dir
                        )
                        
                        if result:
                            print(f"✓ Граф {idx} успешно обработан")
                        else:
                            print(f"✗ Граф {idx} - обработка вернула None")
                            
                    except Exception as exc:
                        print(f"✗ ОШИБКА при обработке графа {idx}: {exc}")
                        traceback.print_exc()
            else:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Нет новых данных. Ожидание...")
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n✓ Получен сигнал прерывания. Завершение работы...")
            break
            
        except Exception as main_exc:
            print(f"\n✗ ГЛАВНАЯ ОШИБКА в фоновом цикле: {main_exc}")
            traceback.print_exc()
            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    graph_file = r"D:\hack\mini_G_set.txt"
    routes_file = r"D:\hack\mini_routes.txt"
    results_folder = "results"
    output_dir = "post_processed_results"
    
    background_postprocessor(graph_file, routes_file, results_folder, output_dir, force_reprocess=FORCE_REPROCESS)
