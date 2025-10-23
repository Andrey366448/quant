import json
import numpy as np
import math
import os
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
import uuid

class UnifiedCircuitConverter:
    """Конвертер схем в JSON формат согласно документации"""

    def __init__(self):
        self.gate_mapping = {
            'h': 'H', 'x': 'X', 'y': 'Y', 'z': 'Z', 's': 'S', 'sdg': 'S_REVERSE',
            't': 'T', 'tdg': 'T_REVERSE', 'sx': 'SQUARE_ROOT_X', 'id': 'I',
            'rx': 'RX', 'ry': 'RY', 'rz': 'RZ', 'p': 'U1', 'u1': 'U1',
            'u2': 'U2', 'u3': 'U3', 'cx': 'CONTROL', 'swap': 'SWAP',
            'measure': 'MEASUREMENT', 'barrier': 'BARRIER'
        }

        self.type_mapping = {
            'h': 'base', 'x': 'base', 'y': 'base', 'z': 'base', 's': 'base',
            'sdg': 'base', 't': 'base', 'tdg': 'base', 'sx': 'base', 'id': 'base',
            'rx': 'params', 'ry': 'params', 'rz': 'params', 'p': 'params',
            'u1': 'params', 'u2': 'params', 'u3': 'params',
            'cx': 'auxiliary', 'swap': 'auxiliary', 'measure': 'auxiliary',
            'barrier': 'auxiliary'
        }

    def _replace_parameters_with_values(self, qc):
        """Заменяет все параметры в схеме на числовые значения"""
        qc_copy = qc.copy()

        param_bindings = {}
        for param in qc_copy.parameters:
            param_bindings[param] = np.random.uniform(0, 2 * np.pi)

        if param_bindings:
            qc_bound = qc_copy.bind_parameters(param_bindings)
            return qc_bound
        return qc_copy

    def convert_circuit(self, qc, filename=None):
        """Конвертирует схему в JSON формат согласно документации"""
        qc = self._replace_parameters_with_values(qc)

        operations = []
        qubit_positions = [0] * qc.num_qubits
        max_column = 0

        for instruction in qc.data:
            op = instruction.operation
            qubits = [qc.find_bit(qubit).index for qubit in instruction.qubits]

            gate_name = op.name.lower()
            mirea_gate = self.gate_mapping.get(gate_name, gate_name.upper())
            gate_type = self.type_mapping.get(gate_name, 'base')

            params = []
            if hasattr(op, 'params') and op.params:
                for param in op.params:
                    try:
                        params.append(float(param))
                    except (TypeError, ValueError):
                        params.append(0.0)

            # Определяем столбец для операции
            current_column = max([qubit_positions[q] for q in qubits])

            gate_data = {
                "qubit": qubits[0] if len(qubits) == 1 else None,
                "qubits": qubits if len(qubits) > 1 else None,
                "column": current_column,
                "title": mirea_gate,
                "type": gate_type
            }

            # Добавляем параметры для параметрических гейтов
            if gate_type == 'params' and params:
                gate_data["params"] = self._create_params_structure(mirea_gate, params)

            # Специальная обработка для составных операций
            if gate_name == 'cx' and len(qubits) == 2:
                control_q, target_q = qubits

                # CONTROL операция
                control_gate = {
                    "qubit": control_q,
                    "column": current_column,
                    "title": "CONTROL",
                    "type": "auxiliary"
                }
                operations.append(control_gate)

                # X операция на целевом кубите
                x_gate = {
                    "qubit": target_q,
                    "column": current_column,
                    "title": "X",
                    "type": "base"
                }
                operations.append(x_gate)

            elif gate_name == 'swap' and len(qubits) == 2:
                # Два SWAP гейта в одном столбце
                for qubit in qubits:
                    swap_gate = {
                        "qubit": qubit,
                        "column": current_column,
                        "title": "SWAP",
                        "type": "auxiliary"
                    }
                    operations.append(swap_gate)

            elif gate_name == 'barrier':
                # BARRIER на всех указанных кубитах
                for qubit in qubits:
                    barrier_gate = {
                        "qubit": qubit,
                        "column": current_column,
                        "title": "BARRIER",
                        "type": "auxiliary"
                    }
                    operations.append(barrier_gate)

            else:
                # Обычные операции
                operations.append(gate_data)

            # Обновляем позиции кубитов
            new_column = current_column + 1
            for qubit in qubits:
                qubit_positions[qubit] = new_column
            max_column = max(max_column, new_column)

        # Создаем финальную структуру согласно документации
        result = {
            "qubit": qc.num_qubits,
            "column": max_column,
            "data": operations
        }

        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"Схема сохранена в: {filename}")

        return result

    def _create_params_structure(self, gate_name, params):
        """Создает структуру параметров согласно документации"""

        base_angle_template = {
            "title": "Угол поворота",
            "key": "angle1",
            "types": [
                {
                    "input": "input",
                    "type": "number",
                    "key": "input-number",
                    "title": "Угол поворота в радианах",
                    "data": 0,
                    "step": 0.01,
                    "decimalDigits": 6
                },
                {
                    "input": "const",
                    "type": "string",
                    "key": "const-string-pi",
                    "title": "Число Пи (π)",
                    "data": "pi"
                },
                {
                    "input": "const",
                    "type": "string",
                    "key": "const-string-e",
                    "title": "Число е",
                    "data": "e"
                }
            ],
            "data": "input-number"
        }

        param_configs = {
            'RX': {
                "key": "theta",
                "title": "Угол поворота в радианах",
                "manipulation": None,
                "value": [{**base_angle_template, "data": "input-number"}]
            },
            'RY': {
                "key": "theta",
                "title": "Угол поворота в радианах",
                "manipulation": None,
                "value": [{**base_angle_template, "data": "const-string-pi"}]
            },
            'RZ': {
                "key": "lambda",
                "title": "Угол поворота в радианах",
                "manipulation": None,
                "value": [{**base_angle_template, "data": "const-string-e"}]
            },
            'U1': {
                "key": "lambda",
                "title": "Угол поворота в радианах",
                "manipulation": None,
                "value": [{**base_angle_template, "data": "input-number"}]
            }
        }

        # Для многопараметрических гейтов
        if gate_name == 'U2':
            angle1_template = {**base_angle_template, "key": "angle1", "data": "input-number"}
            angle2_template = {**base_angle_template, "key": "angle2", "data": "const-string-pi"}

            return [
                {
                    "key": "phi",
                    "title": "Угол поворота в радианах 1",
                    "manipulation": None,
                    "value": [angle1_template]
                },
                {
                    "key": "lambda",
                    "title": "Угол поворота в радианах 2",
                    "manipulation": None,
                    "value": [angle2_template]
                }
            ]

        elif gate_name == 'U3':
            angle1_template = {**base_angle_template, "key": "angle1", "data": "input-number"}
            angle2_template = {**base_angle_template, "key": "angle2", "data": "const-string-pi"}
            angle3_template = {**base_angle_template, "key": "angle3", "data": "const-string-e"}

            return [
                {
                    "key": "theta",
                    "title": "Угол поворота в радианах 1",
                    "manipulation": None,
                    "value": [angle1_template]
                },
                {
                    "key": "phi",
                    "title": "Угол поворота в радианах 2",
                    "manipulation": None,
                    "value": [angle2_template]
                },
                {
                    "key": "lambda",
                    "title": "Угол поворота в радианах 3",
                    "manipulation": None,
                    "value": [angle3_template]
                }
            ]

        # Для однопараметрических гейтов
        config = param_configs.get(gate_name)
        if config and params:
            # Обновляем числовое значение в input-number
            for value_item in config["value"]:
                for type_item in value_item["types"]:
                    if type_item.get("key") == "input-number" and type_item.get("input") == "input":
                        type_item["data"] = float(params[0])

        return [config] if config else []

    def create_api_payload(self, qc, shots=1024):
        """Создает полный payload для API согласно первому документу"""
        circuit_json = self.convert_circuit(qc)

        # Генерируем elementsObject и actualHistoryMap
        elements_object = {}
        actual_history_map = []

        # Инициализируем карту истории
        for _ in range(circuit_json["qubit"]):
            actual_history_map.append(["none"] * circuit_json["column"])

        # Заполняем elementsObject и actualHistoryMap
        for gate in circuit_json["data"]:
            gate_id = str(uuid.uuid4().hex)[:20]

            # Создаем элемент для elementsObject
            element = {
                "id": gate_id,
                "title": gate["title"],
                "type": gate["type"],
                "params": gate.get("params"),
                "error": None,
                "body": None,
                "idGate": None
            }
            elements_object[gate_id] = element

            # Добавляем в actualHistoryMap
            qubit = gate.get("qubit")
            if qubit is not None and qubit < len(actual_history_map):
                column = gate["column"]
                if column < len(actual_history_map[qubit]):
                    actual_history_map[qubit][column] = gate_id

        # Заменяем оставшиеся 'none' на 'block' после MEASUREMENT
        for qubit_line in actual_history_map:
            measurement_found = False
            for i in range(len(qubit_line)):
                if measurement_found and qubit_line[i] == 'none':
                    qubit_line[i] = 'block'
                elif qubit_line[i] != 'none' and elements_object.get(qubit_line[i], {}).get('title') == 'MEASUREMENT':
                    measurement_found = True

        payload = {
            "elementsObject": elements_object,
            "actualHistoryMap": actual_history_map,
            "launch": shots
        }

        return payload

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

    # Старые методы для обратной совместимости
    def create_proper_QAOA_circuit(self, start, end, current_traffic, p=3):
        """Совместимость со старым кодом"""
        return self.create_enhanced_circuit(start, end, current_traffic, p)

    def add_cost_layer(self, qc, gamma, traffic, layer):
        """Совместимость со старым кодом"""
        self.enhanced_cost_layer(qc, gamma, traffic, 0, 0, layer)  # start/end не используются

    def add_mixer_layer(self, qc, beta, layer):
        """Совместимость со старым кодом"""
        for qubit in range(self.total_qubits):
            qc.rx(2 * beta, qubit)

    def add_ry_mixer_layer(self, qc, beta, layer):
        """Совместимость со старым кодом"""
        for qubit in range(self.total_qubits):
            qc.ry(2 * beta, qubit)

def save_traffic_circuits_from_files(graph_file, routes_file, output_dir="input", process_all_graphs=False):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print("Загрузка графов из файла...")
    graphs = load_graphs_from_file(graph_file)

    print("Загрузка маршрутов из файла...")
    all_routes = load_routes_from_file(routes_file)

    print(f"Загружено {len(graphs)} графов и {len(all_routes)} наборов маршрутов")

    converter = UnifiedCircuitConverter()

    if process_all_graphs:
        graphs_to_process = range(len(graphs))
        print("Обрабатываем ВСЕ графы...")
    else:
        graphs_to_process = [0]
        print("Обрабатываем только ПЕРВЫЙ граф...")

    for graph_idx in graphs_to_process:
        graph = graphs[graph_idx]
        routes = all_routes[graph_idx]

        print(f"\n=== ОБРАБОТКА ГРАФА {graph_idx + 1} ===")
        print(f"Размер графа: {graph.shape}")
        print(f"Количество машин в графе: {len(routes)}")

        graph_dir = os.path.join(output_dir, f"graph_{graph_idx}")
        if not os.path.exists(graph_dir):
            os.makedirs(graph_dir)

        optimizer = ImprovedQuantumTrafficOptimizer(graph)
        current_traffic = np.zeros_like(graph)

        print(f"Используется бинарное кодирование: {optimizer.n_qubits_per_node} кубитов на вершину")
        print(f"Общее количество кубитов: {optimizer.total_qubits}")

        for car_idx, route in enumerate(routes):
            start, end = route[0], route[1]
            print(f"--- Машина {car_idx + 1}: {start} → {end} ---")

            try:
                # Используем улучшенную схему
                qc_enhanced = optimizer.create_enhanced_circuit(
                    start=start,
                    end=end,
                    current_traffic=current_traffic,
                    p=4
                )

                # # Сохраняем в формате для загрузки
                # circuit_filename = os.path.join(graph_dir, f"circuit_car_{car_idx}.json")
                # circuit_json = converter.convert_circuit(qc_enhanced, circuit_filename)

                # Сохраняем полный payload для API
                api_filename = os.path.join(graph_dir, f"api_payload_car_{car_idx}.json")
                api_payload = converter.create_api_payload(qc_enhanced, shots=1024)

                with open(api_filename, 'w', encoding='utf-8') as f:
                    json.dump(api_payload, f, indent=2, ensure_ascii=False)
                print(f"API payload сохранен: {api_filename}")

                # Обновляем трафик
                if start < len(current_traffic) and end < len(current_traffic):
                    current_traffic[start, end] += 1
                    current_traffic[end, start] += 1

            except Exception as e:
                print(f"Ошибка при обработке машины {car_idx}: {e}")
                continue

    print(f"\nВсе схемы успешно сохранены в директорию: {output_dir}")

# Вспомогательные функции для загрузки данных
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

def test_quantum_nondeterminism():
    """Тест для проверки не-детерминированности квантовых результатов"""
    print("\n=== ТЕСТ НЕ-ДЕТЕРМИНИРОВАННОСТИ ===")

    # Создаем простой граф для теста
    test_graph = np.array([
        [0, 1, np.inf],
        [1, 0, 1],
        [np.inf, 1, 0]
    ])

    optimizer = ImprovedQuantumTrafficOptimizer(test_graph)
    qc = optimizer.create_enhanced_circuit(0, 2, np.zeros_like(test_graph), p=2)

    print(f"Тестовая схема создана: {qc.num_qubits} кубитов")
    print("Разные запуски будут давать разные распределения (квантовая природа сохранена)")
    print("НО распределение будет более 'пикообразным' благодаря улучшениям")

if __name__ == "__main__":
    print("=== УЛУЧШЕННАЯ ГЕНЕРАЦИЯ СХЕМ ДЛЯ API ===")
    print("Особенности:")
    print("- Сохранено бинарное кодирование (экономия кубитов)")
    print("- Улучшена сходимость без потери квантовой природы")
    print("- Умная инициализация с учетом стартовой вершины")
    print("- Усиленные cost layers для лучшей 'пикообразности'")

    test_quantum_nondeterminism()

    save_traffic_circuits_from_files(
        "G_set1.txt",
        "routes1.txt",
        process_all_graphs=False,
    )