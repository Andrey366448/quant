import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import ast
import os


def visualize_graphs():
    """Простая визуализация графов из готовых данных"""

    # Загрузка данных
    data = pd.read_csv('uploads/data.csv')
    submission = pd.read_csv('submission.csv')
    time_data = pd.read_csv('total_time.csv')

    # Создаем папку для результатов
    os.makedirs('visualised_qf', exist_ok=True)

    # Обработка каждого графа
    for idx, row in data.iterrows():
        graph_index = row['graph_index']

        # Парсим матрицу смежности
        matrix_str = row['graph_matrix'].strip().replace('inf', 'None')
        if matrix_str.startswith('"') and matrix_str.endswith('"'):
            matrix_str = matrix_str[1:-1]
        graph_matrix = ast.literal_eval(matrix_str)

        # Получаем маршруты для этого графа
        routes = submission[submission['graph_index'] == graph_index]['route'].tolist()
        routes = [ast.literal_eval(route) for route in routes]

        # Получаем время
        total_time = time_data[time_data['graph_index'] == graph_index]['total_time'].iloc[0]

        # Создаем граф
        G = nx.Graph()
        n = len(graph_matrix)

        # Добавляем узлы и ребра
        for i in range(n):
            G.add_node(i)
            for j in range(i + 1, n):
                if graph_matrix[i][j] not in [None, float('inf')] and graph_matrix[i][j] > 0:
                    G.add_edge(i, j, weight=graph_matrix[i][j])

        # Подсчитываем трафик на ребрах
        edge_traffic = {}
        for route in routes:
            for i in range(len(route) - 1):
                edge = tuple(sorted([route[i], route[i + 1]]))
                edge_traffic[edge] = edge_traffic.get(edge, 0) + 1

        # Визуализация
        plt.figure(figsize=(10, 8))
        pos = nx.spring_layout(G)

        # Цвет ребер в зависимости от трафика
        edge_colors = [edge_traffic.get(tuple(sorted(edge)), 0) for edge in G.edges()]

        # Рисуем граф
        nx.draw_networkx_edges(G, pos, edge_color=edge_colors,
                               edge_cmap=plt.cm.RdYlGn_r, width=3, alpha=0.7)
        nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=500)
        nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')

        plt.title(f'Граф {graph_index}\nМашин: {len(routes)}, Время: {total_time:.2f}',
                  fontsize=14, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()

        # Сохраняем
        plt.savefig(f'visualised_qf/graph_{graph_index}.png', dpi=150, bbox_inches='tight')
        plt.close()

        print(f'Создано: visualised_qf/graph_{graph_index}.png')


if __name__ == "__main__":
    visualize_graphs()
    print("Визуализация завершена!")