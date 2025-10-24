import json
import numpy as np
import math
from collections import defaultdict
import os
import glob
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

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

        # Преобразуем бинарную строку в целое число
        node_id = int(bitstring, 2)

        # Проверяем, что номер вершины в допустимом диапазоне
        if node_id >= self.n_nodes:
            node_id = node_id % self.n_nodes  # Циклическое отображение если вышли за границы

        return node_id

    def compute_marginals_from_counts(self, counts, n_qubits):
        """Вычисляет маргинальные вероятности P(x_i=1) из гистограммы"""
        total = sum(counts.values())
        marginals = np.zeros(n_qubits, dtype=float)

        if total == 0:
            return marginals

        for bitstring, cnt in counts.items():
            # Преобразуем битовую строку в массив битов
            bits = [int(bit) for bit in bitstring[::-1]]  # младший бит сначала

            for i in range(min(len(bits), n_qubits)):
                marginals[i] += cnt * bits[i]

        return marginals / float(total)

    def find_best_path_binary(self, counts, start_node, end_node, current_traffic):
        """Находит лучший путь на основе бинарного кодирования"""
        if not counts:
            return start_node, 0.0

        # Вычисляем маргинальные вероятности
        marginals = self.compute_marginals_from_counts(counts, self.total_qubits)

        # Находим наиболее вероятную битовую строку
        best_bitstring = None
        max_count = -1

        for bitstring, count in counts.items():
            if count > max_count:
                max_count = count
                best_bitstring = bitstring

        if best_bitstring is None:
            return start_node, 0.0

        # Преобразуем в номер вершины
        selected_node = self.binary_to_node(best_bitstring)

        # Вычисляем стоимость перехода (используем граф для вычисления реальной стоимости)
        if start_node < self.n_nodes and selected_node < self.n_nodes:
            if self.J[start_node, selected_node] != np.inf:
                cost = abs(self.J[start_node, selected_node])
                # Учитываем трафик
                traffic_penalty = current_traffic[start_node, selected_node] * 0.1
                total_cost = cost + traffic_penalty
            else:
                total_cost = 1000  # Большой штраф за недостижимость
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
                # Если нет результатов для этой машины, используем прямой путь
                path = [start, end]
                paths.append(path)
                total_costs.append(0.0)
                continue

            current_node = start
            path = [start]
            path_cost = 0.0

            # Строим путь шаг за шагом
            for step in range(max_path_length):
                if current_node == end:
                    break

                counts = counts_list[car_idx]
                next_node, step_cost = self.find_best_path_binary(counts, current_node, end, current_traffic)

                # Проверяем допустимость перехода
                if (next_node not in path and
                    current_node < self.n_nodes and next_node < self.n_nodes and
                    self.J[current_node, next_node] != np.inf):

                    path.append(next_node)
                    path_cost += step_cost

                    # Обновляем трафик
                    current_traffic[current_node, next_node] += 1
                    current_traffic[next_node, current_node] += 1

                    current_node = next_node
                else:
                    # Пытаемся найти альтернативный узел
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

            # Если не достигли цели, добавляем конечную вершину
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

            # Находим лучшее исправление для первого конфликта
            ti, tj = conflict_pairs[0]
            best_improvement = (float('inf'), None, None)

            # Пробуем изменить путь ti
            for alt_path in self.generate_alternative_paths(repaired_paths[ti], capacity_matrix):
                improvement = self.evaluate_path_change(repaired_paths, ti, alt_path, conf_adj, lam_conflict)
                if improvement < best_improvement[0]:
                    best_improvement = (improvement, ti, alt_path)

            # Пробуем изменить путь tj
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
                        capacity_matrix[u, v] <= 1):  # Конфликт если capacity <= 1
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
        alternatives = [path]  # Всегда включаем исходный путь

        if len(path) <= 2:
            return alternatives

        # Генерируем варианты с небольшими изменениями
        for i in range(1, len(path) - 1):
            # Пропускаем промежуточную вершину
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

        # Подсчитываем конфликты для старого пути
        for j, path_j in enumerate(paths):
            if j == changed_idx:
                continue
            if (j, tuple(paths[j])) in conf_adj.get((changed_idx, tuple(paths[changed_idx])), set()):
                old_conflicts += 1

        # Подсчитываем конфликты для нового пути
        for j, path_j in enumerate(paths):
            if j == changed_idx:
                continue
            if (j, tuple(paths[j])) in conf_adj.get((changed_idx, tuple(new_path)), set()):
                new_conflicts += 1

        # Вычисляем изменение стоимости
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


class ImprovedQuantumTrafficOptimizer:
    def __init__(self, graph_matrix, traffic_penalty=0.3):
        self.J = graph_matrix
        self.n_nodes = len(graph_matrix)
        self.traffic_penalty = traffic_penalty

        self.n_qubits_per_node = math.ceil(math.log2(self.n_nodes)) if self.n_nodes > 0 else 0
        self.total_qubits = self.n_qubits_per_node

        # Улучшенная нормализация
        valid_weights = self.J[np.isfinite(self.J)]
        if len(valid_weights) > 0:
            max_weight = np.max(np.abs(valid_weights))
            min_weight = np.min(np.abs(valid_weights[valid_weights > 0]))
            # Нормализуем к диапазону [0.1, 1.0] для лучшей численной стабильности
            self.J_normalized = np.where(
                np.isfinite(self.J),
                np.maximum(0.1, np.abs(self.J) / max_weight),
                0
            )
        else:
            self.J_normalized = np.ones_like(self.J) * 0.5

    def create_enhanced_circuit(self, start, end, current_traffic, p=3):
        """Улучшенная схема с умной инициализацией и усиленными cost layers"""
        qc = QuantumCircuit(self.total_qubits, self.total_qubits)

        # 1. Умная инициализация с учетом стартовой вершины
        self.smart_initialization(qc, start)

        # 2. Детерминированные но разнообразные параметры для лучшей сходимости
        for layer in range(p):
            gamma = 0.5 + 0.2 * layer  # Детерминированные, но разные по слоям
            beta = 0.3 + 0.15 * layer

            # 3. Усиленный cost layer
            self.enhanced_cost_layer(qc, gamma, current_traffic, start, end, layer)

            # 4. Чередующиеся mixer layers для лучшего перемешивания
            if layer % 2 == 0:
                for qubit in range(self.total_qubits):
                    qc.rx(2 * beta, qubit)
            else:
                for qubit in range(self.total_qubits):
                    qc.ry(2 * beta, qubit)

        qc.measure(range(self.total_qubits), range(self.total_qubits))
        return qc

    def smart_initialization(self, qc, start):
        """Умная инициализация, учитывающая стартовую вершину в бинарном кодировании"""
        if self.n_qubits_per_node == 0:
            return

        # Кодируем стартовую вершину в бинарном формате
        start_binary = format(start, f'0{self.n_qubits_per_node}b')

        for qubit in range(self.total_qubits):
            if qubit < len(start_binary):
                # Бит стартовой вершины (младший бит сначала)
                bit_value = int(start_binary[-(qubit+1)])
                # Смещаем от равномерной суперпозиции в сторону нужного бита
                angle = (0.2 + 0.6 * bit_value) * np.pi/2
                qc.ry(angle, qubit)
            else:
                # Для дополнительных кубитов - обычная суперпозиция
                qc.h(qubit)

    def enhanced_cost_layer(self, qc, gamma, traffic, start, end, layer):
        """Усиленный cost layer с приоритетом целевой вершины"""
        angles = [0.0] * self.total_qubits

        # Усиленные веса ребер с учетом трафика
        for i in range(self.n_nodes):
            for j in range(i + 1, self.n_nodes):
                if self.J[i, j] != np.inf and self.J[i, j] != 0:
                    base_weight = abs(self.J_normalized[i, j])
                    traffic_cost = traffic[i, j] * self.traffic_penalty

                    # Усиленные коэффициенты для лучшей сходимости
                    effective_strength = (base_weight * 2.0 + traffic_cost * 1.5) * gamma * 0.3

                    # Применяем к соответствующим битам в бинарном представлении
                    diff = i ^ j
                    for bit_pos in range(self.n_qubits_per_node):
                        if (diff >> bit_pos) & 1:
                            angles[bit_pos] += effective_strength * (layer + 1)  # Зависит от слоя

        # Добавляем bias к целевой вершине для направления оптимизации
        if self.n_qubits_per_node > 0:
            end_binary = format(end, f'0{self.n_qubits_per_node}b')
            for qubit in range(min(self.total_qubits, len(end_binary))):
                if end_binary[-(qubit+1)] == '1':
                    angles[qubit] += gamma * 0.4  # Bias к битам целевой вершины

        # Базовый угол, увеличивающийся с глубиной
        base_angle = gamma * (0.5 + 0.2 * layer)
        for i in range(self.total_qubits):
            angles[i] += base_angle

        # Применяем rotations с улучшенной стабильностью
        for qubit, angle in enumerate(angles):
            # Последовательность rotations для лучшей сходимости
            qc.rz(angle * 0.5, qubit)
            qc.ry(angle * 0.3, qubit)
            qc.rz(angle * 0.5, qubit)

    def create_advanced_QAOA(self, start, end, current_traffic, p=4):
        """Совместимость со старым кодом - использует улучшенную версию"""
        return self.create_enhanced_circuit(start, end, current_traffic, p)


def run_quantum_simulation(qc, shots=1024):
    """Запускает квантовую схему на симуляторе и возвращает counts"""
    simulator = AerSimulator()
    compiled_circuit = qc  # В реальности может потребоваться transpile
    job = simulator.run(compiled_circuit, shots=shots)
    result = job.result()
    counts = result.get_counts(qc)
    return counts


def load_quantum_results_from_folder(results_folder="results"):
    """Автоматически загружает все результаты квантовых вычислений из папки results"""
    all_graph_results = {}

    # Проверяем существование папки
    if not os.path.exists(results_folder):
        print(f"Предупреждение: Папка {results_folder} не существует!")
        return all_graph_results

    # Ищем все папки graph_N
    graph_folders = glob.glob(os.path.join(results_folder, "graph_*"))

    if not graph_folders:
        print(f"Предупреждение: В папке {results_folder} не найдено папок graph_*")
        return all_graph_results

    for graph_folder in graph_folders:
        # Извлекаем номер графа из имени папки
        graph_name = os.path.basename(graph_folder)
        try:
            graph_index = int(graph_name.split("_")[1])
        except (IndexError, ValueError):
            print(f"Предупреждение: Не удалось извлечь номер графа из {graph_name}")
            continue

        # Ищем все JSON файлы в папке
        result_files = glob.glob(os.path.join(graph_folder, "Result_*.json"))

        # Сортируем файлы по номеру автомобиля
        result_files.sort(key=lambda x: int(os.path.basename(x).split("_car_")[1].split(".")[0]))

        # Загружаем результаты для каждого автомобиля
        graph_results = []
        for file_path in result_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)

                # Преобразуем в формат словаря counts
                counts = {}
                for item in data['data']:
                    counts[item['bitstring']] = item['value']

                graph_results.append(counts)

            except Exception as e:
                print(f"Ошибка при загрузке файла {file_path}: {e}")
                graph_results.append({})

        all_graph_results[graph_index] = graph_results
        print(f"Загружено результатов для графа {graph_index}: {len(graph_results)} автомобилей")

    return all_graph_results


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

        # Проверяем, изменился ли путь после оптимизации
        if initial_path != repaired_path:
            initial_cost = sum(abs(graph[initial_path[j], initial_path[j+1]])
                             for j in range(len(initial_path)-1)
                             if graph[initial_path[j], initial_path[j+1]] != np.inf)
            improvement = initial_cost - cost
            if improvement > 0:
                print(f"  УЛУЧШЕНИЕ: -{improvement:.2f} (с {initial_cost:.2f} до {cost:.2f})")

        print(f"{'-'*40}")


def post_process_all_graphs(graphs, all_routes, results_folder="results", output_dir="post_processed_results"):
    """Постобработка для всех графов с автоматической загрузкой результатов и подробным выводом"""

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Загружаем все квантовые результаты
    quantum_results = load_quantum_results_from_folder(results_folder)

    if not quantum_results:
        print("Нет квантовых результатов для обработки!")
        return {}, 0.0

    all_results = {}
    total_time_summary = []

    for graph_idx, graph in enumerate(graphs):
        if graph_idx not in quantum_results:
            print(f"Предупреждение: Нет квантовых результатов для графа {graph_idx}, пропускаем...")
            continue

        n_nodes = len(graph)
        n_qubits_per_node = math.ceil(math.log2(n_nodes)) if n_nodes > 0 else 0

        print(f"\n{'#'*80}")
        print(f"ОБРАБОТКА ГРАФА {graph_idx}")
        print(f"Количество вершин: {n_nodes}, Кубитов на вершину: {n_qubits_per_node}")
        print(f"{'#'*80}")

        # Создаем процессор
        processor = BinaryQAOAPostProcessor(graph, n_nodes, n_qubits_per_node)

        # Инициализируем матрицу трафика
        traffic_matrix = np.zeros_like(graph)
        capacity_matrix = np.where(graph != np.inf, 2, 0)  # Базовая пропускная способность

        # Строим пути
        routes = all_routes[graph_idx] if graph_idx < len(all_routes) else []
        quantum_counts = quantum_results[graph_idx]

        # Проверяем соответствие количества машин
        if len(routes) > len(quantum_counts):
            print(f"Предупреждение: Для графа {graph_idx} машин больше ({len(routes)}), чем результатов ({len(quantum_counts)}). Обрабатываем только первые {len(quantum_counts)}.")
            routes = routes[:len(quantum_counts)]
        elif len(quantum_counts) > len(routes):
            print(f"Предупреждение: Для графа {graph_idx} результатов больше ({len(quantum_counts)}), чем машин ({len(routes)}). Используем только первые {len(routes)} результатов.")
            quantum_counts = quantum_counts[:len(routes)]

        paths, costs, updated_traffic = processor.greedy_path_construction(
            quantum_counts, routes, traffic_matrix
        )

        # Устраняем конфликты
        repaired_paths = processor.conflict_repair(paths, updated_traffic, capacity_matrix)

        # Вычисляем общее время
        total_time = processor.calculate_total_time(repaired_paths)

        # ВЫВОДИМ ПУТИ МАШИН В КОНСОЛЬ
        print_detailed_paths(graph_idx, routes, paths, repaired_paths, costs, total_time, graph)

        # Сохраняем результаты для этого графа
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
                "binary_encoding": "vertex_index"
            }
        }

        output_file = os.path.join(output_dir, f"post_processed_routes_graph_{graph_idx}.json")
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        all_results[graph_idx] = results
        total_time_summary.append({
            "graph_index": graph_idx,
            "total_time": total_time
        })

        print(f"Результаты для графа {graph_idx} сохранены в {output_file}")

    # Сохраняем суммарную статистику
    summary_file = os.path.join(output_dir, "total_time_summary.json")
    with open(summary_file, 'w') as f:
        json.dump(total_time_summary, f, indent=2)

    # Вычисляем общее время для всех графов
    overall_total_time = sum(item["total_time"] for item in total_time_summary)

    # ФИНАЛЬНЫЙ ВЫВОД
    print(f"\n{'='*80}")
    print(f"ФИНАЛЬНАЯ СТАТИСТИКА")
    print(f"{'='*80}")
    print(f"Обработано графов: {len(total_time_summary)}")
    print(f"Общее время всех автомобилей во всех графах: {overall_total_time:.2f}")

    # Детали по каждому графу
    print(f"\nДетали по графам:")
    for item in total_time_summary:
        print(f"  Граф {item['graph_index']}: {item['total_time']:.2f}")

    return all_results, overall_total_time


def load_graphs_from_file(filename):
    """Загружает графы из нового текстового формата с исправленной обработкой"""
    graphs = []
    
    try:
        with open(filename, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"Ошибка при чтении файла {filename}: {e}")
        return graphs
    
    # Определяем общую форму из заголовка
    shape = None
    if '# Shape:' in content:
        shape_line = content.split('# Shape:')[1].split('\n')[0].strip()
        try:
            shape = eval(shape_line)  # Например (30, 100, 100)
            print(f"Обнаружена форма графов: {shape}")
        except:
            print(f"Не удалось распарсить форму: {shape_line}")
    
    # Разделяем на срезы
    slices = content.split('# Slice')[1:]
    print(f"Найдено срезов: {len(slices)}")
    
    for slice_idx, slice_content in enumerate(slices):
        lines = slice_content.strip().split('\n')
        
        # Определяем размер матрицы
        if shape is not None:
            matrix_size = shape[1]  # Берем из формы (n_slices, size, size)
        else:
            # Если нет формы, определяем по максимальному количеству строк
            non_empty_lines = [line for line in lines if line.strip() and not line.startswith('#')]
            matrix_size = len(non_empty_lines)
        
        matrix = []
        
        for line in lines:
            if not line.strip() or line.startswith('#'):
                continue
                
            values = line.split()
            row = []
            for val in values:
                if val == 'inf':
                    row.append(np.inf)
                else:
                    try:
                        row.append(float(val))
                    except ValueError:
                        continue
            
            if len(row) > 0:
                # Если строка короче нужного размера, дополняем inf
                while len(row) < matrix_size:
                    row.append(np.inf)
                # Если строка длиннее, обрезаем
                if len(row) > matrix_size:
                    row = row[:matrix_size]
                matrix.append(row)
                
                # Останавливаемся когда достигли нужного размера
                if len(matrix) >= matrix_size:
                    break
        
        # Если матрица меньше нужного размера, дополняем строками с inf
        while len(matrix) < matrix_size:
            matrix.append([np.inf] * matrix_size)
        
        if len(matrix) == matrix_size:
            # Проверяем что все строки одинаковой длины
            if all(len(row) == matrix_size for row in matrix):
                graphs.append(np.array(matrix))
                print(f"Загружен граф {slice_idx}: {matrix_size}x{matrix_size}")
            else:
                print(f"Предупреждение: Срез {slice_idx} имеет строки разной длины")
        else:
            print(f"Предупреждение: Срез {slice_idx} имеет неверный размер: {len(matrix)} вместо {matrix_size}")
    
    print(f"Успешно загружено графов: {len(graphs)}")
    return graphs


def load_routes_from_file(filename):
    """Загружает маршруты из нового текстового формата"""
    all_routes = []
    
    try:
        with open(filename, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"Ошибка при чтении файла {filename}: {e}")
        return all_routes
    
    # Определяем общую форму из заголовка
    shape = None
    if '# Shape:' in content:
        shape_line = content.split('# Shape:')[1].split('\n')[0].strip()
        try:
            shape = eval(shape_line)  # Например (30, 500, 2)
            print(f"Обнаружена форма маршрутов: {shape}")
        except:
            print(f"Не удалось распарсить форму: {shape_line}")
    
    # Разделяем на срезы
    slices = content.split('# Slice')[1:]
    print(f"Найдено срезов маршрутов: {len(slices)}")
    
    for slice_idx, slice_content in enumerate(slices):
        lines = slice_content.strip().split('\n')
        
        routes = []
        route_count = 0
        
        for line in lines:
            if not line.strip() or line.startswith('#'):
                continue
                
            values = line.split()
            if len(values) >= 2:
                try:
                    start = int(float(values[0]))  # Преобразуем float в int
                    end = int(float(values[1]))
                    routes.append([start, end])
                    route_count += 1
                    
                    # Ограничиваем количество маршрутов если указано в форме
                    if shape is not None and route_count >= shape[1]:
                        break
                        
                except ValueError:
                    continue
        
        all_routes.append(routes)
        print(f"Загружено маршрутов для среза {slice_idx}: {len(routes)}")
    
    print(f"Успешно загружено наборов маршрутов: {len(all_routes)}")
    return all_routes


def generate_and_simulate_circuits(graphs, all_routes, output_dir="results"):
    """Генерирует квантовые схемы и запускает их на симуляторе"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    total_graphs = len(graphs)
    print(f"Начинаем обработку {total_graphs} графов...")

    for graph_idx, graph in enumerate(graphs):
        graph_dir = os.path.join(output_dir, f"graph_{graph_idx}")
        if not os.path.exists(graph_dir):
            os.makedirs(graph_dir)

        routes = all_routes[graph_idx] if graph_idx < len(all_routes) else []
        
        if not routes:
            print(f"Предупреждение: Для графа {graph_idx} нет маршрутов, пропускаем...")
            continue

        print(f"Обработка графа {graph_idx + 1}/{total_graphs}: {len(routes)} машин")
        
        optimizer = ImprovedQuantumTrafficOptimizer(graph)
        current_traffic = np.zeros_like(graph)

        total_cars = len(routes)
        for car_idx, route in enumerate(routes):
            if car_idx % 50 == 0:  # Прогресс каждые 50 машин
                print(f"  Машина {car_idx + 1}/{total_cars}")

            start, end = route[0], route[1]

            # Создаем квантовую схему
            qc = optimizer.create_enhanced_circuit(start, end, current_traffic, p=4)

            # Запускаем на симуляторе
            counts = run_quantum_simulation(qc, shots=1024)

            # Сохраняем результаты в формате JSON
            result_data = {
                "data": [{"bitstring": bitstring, "value": count} for bitstring, count in counts.items()]
            }

            result_file = os.path.join(graph_dir, f"Result_car_{car_idx}.json")
            with open(result_file, 'w') as f:
                json.dump(result_data, f, indent=2)

            # Обновляем трафик
            if start < len(current_traffic) and end < len(current_traffic):
                current_traffic[start, end] += 1
                current_traffic[end, start] += 1

    print("Все квантовые схемы выполнены и результаты сохранены")


def start_func(G_file_path, routes_file_path, result_file_path):
    """Основная функция для запуска всей обработки"""

    print("=" * 80)
    print("ЗАГРУЗКА ДАННЫХ")
    print("=" * 80)
    
    # Загружаем граф и маршруты
    print("Загрузка графов...")
    graphs = load_graphs_from_file(G_file_path)
    print(f"Загружено {len(graphs)} графов")
    
    print("Загрузка маршрутов...")
    all_routes = load_routes_from_file(routes_file_path)
    print(f"Загружено {len(all_routes)} наборов маршрутов")

    # Проверяем соответствие количества графов и наборов маршрутов
    if len(graphs) != len(all_routes):
        print(f"Предупреждение: Количество графов ({len(graphs)}) не совпадает с количеством наборов маршрутов ({len(all_routes)})")
        # Используем минимальное количество
        min_count = min(len(graphs), len(all_routes))
        graphs = graphs[:min_count]
        all_routes = all_routes[:min_count]
        print(f"Будет обработано {min_count} графов")

    if len(graphs) == 0:
        print("Ошибка: Не удалось загрузить ни одного графа!")
        return {}, 0.0

    # Проверяем существование результатов квантовых вычислений
    quantum_results_exist = os.path.exists(result_file_path)
    
    if not quantum_results_exist:
        print("=" * 80)
        print("ГЕНЕРАЦИЯ И ВЫПОЛНЕНИЕ КВАНТОВЫХ СХЕМ")
        print("=" * 80)
        
        # Генерируем и запускаем квантовые схемы
        generate_and_simulate_circuits(graphs, all_routes, output_dir=result_file_path)
    else:
        print("=" * 80)
        print("НАЙДЕНЫ СУЩЕСТВУЮЩИЕ РЕЗУЛЬТАТЫ КВАНТОВЫХ ВЫЧИСЛЕНИЙ")
        print("=" * 80)
        print("Используем существующие результаты...")

    print("=" * 80)
    print("ПОСТОБРАБОТКА РЕЗУЛЬТАТОВ")
    print("=" * 80)
    
    # Запускаем постобработку для всех графов
    results, total_time = post_process_all_graphs(
        graphs,
        all_routes,
        results_folder=result_file_path,
        output_dir="post_processed_results"
    )

    print(f"\nОбработка завершена!")
    print(f"Итоговое общее время: {total_time:.2f}")

    return results, total_time


# Пример использования
if __name__ == "__main__":
    graph_file = "G_set1.txt"
    routes_file = "routes1.txt"
    results_file = "results"

    # Проверяем существование файлов
    if not os.path.exists(graph_file):
        print(f"Ошибка: Файл {graph_file} не существует!")
    elif not os.path.exists(routes_file):
        print(f"Ошибка: Файл {routes_file} не существует!")
    else:
        start_func(graph_file, routes_file, results_file)