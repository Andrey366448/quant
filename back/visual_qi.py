from pathlib import Path
import numpy as np
import pandas as pd
import ast
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from math import ceil, sqrt, log1p
import shutil

def visualize_graph_from_submissions():
    """
    Читает 'submission.csv' и 'total_time.csv' из папки этого файла.
    Для каждого graph_index сохраняет PNG в ПАПКУ 'visualised_qi' (должна быть создана заранее).
    Дополнительно создаёт 'graph_min.png' (копия графа с минимальным total_time) в той же папке.
    """
    # ---------- вспомогательные ----------
    def _parse_route(route_str: str) -> list[int]:
        try:
            return list(map(int, ast.literal_eval(route_str)))
        except Exception:
            cleaned = route_str.strip().replace("'", '"')
            return list(map(int, ast.literal_eval(cleaned)))

    def _edges_from_routes(routes: list[list[int]]):
        edge_counts = {}
        adj = {}
        for r in routes:
            for i in range(len(r) - 1):
                u, v = r[i], r[i + 1]
                if u == v:
                    continue
                a, b = (u, v) if u < v else (v, u)
                edge_counts[(a, b)] = edge_counts.get((a, b), 0) + 1
                adj.setdefault(u, set()).add(v)
                adj.setdefault(v, set()).add(u)
                adj.setdefault(a, adj.get(a, set()))
                adj.setdefault(b, adj.get(b, set()))
        return edge_counts, adj

    def _connected_components(adjacency: dict[int, set[int]]) -> list[list[int]]:
        seen = set()
        comps = []
        for start in adjacency.keys():
            if start in seen:
                continue
            stack = [start]
            comp = []
            seen.add(start)
            while stack:
                u = stack.pop()
                comp.append(u)
                for v in adjacency[u]:
                    if v not in seen:
                        seen.add(v)
                        stack.append(v)
            comps.append(comp)
        return comps

    def _spring_layout_component(nodes: list[int], edges: list[tuple[int,int]],
                                 iters: int = 320, seed: int = 42) -> dict[int, tuple[float,float]]:
        if not nodes:
            return {}
        rng = np.random.default_rng(seed)
        n = len(nodes)
        idx = {node: i for i, node in enumerate(nodes)}
        pos = rng.uniform(0.0, 1.0, size=(n, 2))

        area = 1.0
        k = sqrt(area / max(n, 1))
        t = 0.14
        dt = t / max(iters, 1)
        e_idx = np.array([(idx[u], idx[v]) for (u, v) in edges], dtype=int)

        for _ in range(iters):
            disp = np.zeros_like(pos)

            # Репульсия
            if n <= 600:
                delta = pos[:, None, :] - pos[None, :, :]
                dist2 = (delta ** 2).sum(axis=2) + 1e-9
                inv_dist = 1.0 / np.sqrt(dist2)
                rep = (k * k) * inv_dist
                np.fill_diagonal(rep, 0.0)
                disp += (delta * (rep[:, :, None] * inv_dist[:, :, None])).sum(axis=1)
            else:
                sample_size = min(600, n)
                sample_idx = rng.choice(n, size=sample_size, replace=False)
                delta = pos[:, None, :] - pos[sample_idx][None, :, :]
                dist2 = (delta ** 2).sum(axis=2) + 1e-9
                inv_dist = 1.0 / np.sqrt(dist2)
                rep = (k * k) * inv_dist
                disp += (delta * (rep[:, :, None] * inv_dist[:, :, None])).sum(axis=1) * (n / sample_size)

            # Аттракция
            if len(e_idx) > 0:
                d = pos[e_idx[:, 0]] - pos[e_idx[:, 1]]
                dist = np.sqrt((d ** 2).sum(axis=1)) + 1e-9
                attr = (dist ** 2) / k
                force = (d / dist[:, None]) * attr[:, None]
                for i, (u, v) in enumerate(e_idx):
                    disp[u] -= force[i]
                    disp[v] += force[i]

            lengths = np.linalg.norm(disp, axis=1) + 1e-9
            pos += (disp / lengths[:, None]) * np.minimum(lengths, t)[:, None]
            pos = np.clip(pos, 0.0, 1.0)
            t -= dt
            if t <= 0:
                break

        mn = pos.min(axis=0)
        mx = pos.max(axis=0)
        span = np.maximum(mx - mn, 1e-9)
        pos = (pos - mn) / span
        return {node: (float(pos[idx[node], 0]), float(pos[idx[node], 1])) for node in nodes}

    # ---------- пути ----------
    base_dir = Path(__file__).resolve().parent
    sub_path = base_dir / "submission.csv"
    tt_path = base_dir / "total_time.csv"
    out_dir = base_dir / "visualised_qi"

    if not sub_path.exists():
        raise FileNotFoundError(f"Не найден {sub_path}. Поместите 'submission.csv' рядом с этим файлом.")
    if not tt_path.exists():
        raise FileNotFoundError(f"Не найден {tt_path}. Поместите 'total_time.csv' рядом с этим файлом.")
    # Папка должна существовать заранее (по условию)
    if not out_dir.exists() or not out_dir.is_dir():
        raise FileNotFoundError(f"Папка {out_dir} не найдена. Создайте её заранее (visualised_qi).")

    # Шрифт с кириллицей
    plt.rcParams["font.family"] = "DejaVu Sans"

    # ---------- данные ----------
    df = pd.read_csv(sub_path)
    required = {"graph_index", "driver_index", "route"}
    if not required.issubset(df.columns):
        raise ValueError(f"submission.csv должен содержать колонки: {required}")
    if df.empty:
        raise ValueError("В submission.csv нет строк.")

    tdf = pd.read_csv(tt_path)
    tdf["graph_index"] = pd.to_numeric(tdf["graph_index"], errors="coerce")
    tdf = tdf[tdf["graph_index"].notna()].copy()
    tdf["graph_index"] = tdf["graph_index"].astype(int)

    req_t = {"graph_index", "total_time"}
    if not req_t.issubset(tdf.columns):
        raise ValueError(f"total_time.csv должен содержать колонки: {req_t}")
    if tdf.empty:
        raise ValueError("В total_time.csv нет валидных строк (после фильтра).")

    time_map = {int(r.graph_index): float(r.total_time) for r in tdf.itertuples(index=False)}

    graphs = sorted(df["graph_index"].unique())
    present_times = [(int(g), time_map[int(g)]) for g in graphs if int(g) in time_map]
    if not present_times:
        raise ValueError("Не найдено совпадений graph_index между submission.csv и total_time.csv.")
    min_g, _ = min(present_times, key=lambda x: x[1])

    outputs = []
    for g in graphs:
        g = int(g)
        dfg = df[df["graph_index"] == g].copy()
        if dfg.empty:
            continue

        routes = [_parse_route(s) for s in dfg["route"].astype(str).tolist()]
        all_nodes = sorted({n for r in routes for n in r})
        if not all_nodes:
            continue

        edge_counts, adjacency = _edges_from_routes(routes)
        for n in all_nodes:
            adjacency.setdefault(n, set())

        comps = _connected_components(adjacency)

        comp_positions = []
        for comp in comps:
            comp_edges = [(u, v) for (u, v), c in edge_counts.items() if (u in comp and v in comp)]
            pos = _spring_layout_component(comp, comp_edges, iters=320, seed=42)
            comp_positions.append(pos)

        c = len(comps)
        cols = int(ceil(sqrt(c)))
        rows = int(ceil(c / cols))
        cell_w, cell_h = 1.0 / cols, 1.0 / rows
        inner = 0.80
        sx, sy = cell_w * inner, cell_h * inner

        final_pos = {}
        for idx_c, comp in enumerate(comps):
            r = idx_c // cols
            col = idx_c % cols
            ox_cell, oy_cell = col * cell_w, 1.0 - (r + 1) * cell_h
            ox = ox_cell + (cell_w - sx) / 2.0
            oy = oy_cell + (cell_h - sy) / 2.0
            for n in comp:
                x, y = comp_positions[idx_c][n]
                final_pos[n] = (ox + x * sx, oy + y * sy)

        # размеры узлов
        deg = {n: 0 for n in all_nodes}
        for (u, v), cnt in edge_counts.items():
            deg[u] += cnt
            deg[v] += cnt
        sizes = np.array([deg.get(n, 1) for n in all_nodes], dtype=float)
        sizes = 90.0 + 160.0 * np.sqrt(sizes)

        # ---------- рисуем ----------
        fig = plt.figure(figsize=(18, 18))
        ax = fig.add_subplot(111)
        ax.set_aspect("equal")
        ax.axis("off")
        fig.patch.set_alpha(0.0)
        ax.set_facecolor("none")

        # рёбра
        for (u, v), cnt in edge_counts.items():
            xu, yu = final_pos[u]
            xv, yv = final_pos[v]
            lw = 2.0 + 4.0 * log1p(cnt)
            ax.plot([xu, xv], [yu, yv], linewidth=lw)

        xs = [final_pos[n][0] for n in all_nodes]
        ys = [final_pos[n][1] for n in all_nodes]
        ax.scatter(xs, ys, s=sizes)

        # подписи узлов (жирные с белой обводкой)
        if len(all_nodes) <= 250:
            for n in all_nodes:
                x, y = final_pos[n]
                ax.text(
                    x, y, str(n),
                    fontsize=9, fontweight="bold", ha="center", va="center", color="black",
                    path_effects=[pe.Stroke(linewidth=2.2, foreground="white"), pe.Normal()],
                )

        # заголовок
        ax.set_title(
            f"Граф №{g} (силовой расклад; компоненты по сетке)",
            fontweight="bold", fontsize=16, color="black", loc="center", pad=10,
        )

        # подпись времени (если есть)
        if g in time_map:
            t_val = float(time_map[g])
            t_str = f"{t_val:,.2f}".replace(",", " ").replace(".", ",")
            ax.text(
                0.01, 0.99, f"Время графа: {t_str}",
                transform=ax.transAxes,
                fontsize=18, fontweight="bold", color="black", va="top", ha="left",
                path_effects=[pe.Stroke(linewidth=3.5, foreground="white"), pe.Normal()],
            )

        out_path = out_dir / f"graph_{g}.png"
        fig.tight_layout(pad=0.6)
        fig.savefig(out_path, dpi=400, bbox_inches="tight", transparent=True)
        plt.close(fig)

        # graph_min.png для минимального времени — туда же
        if g == min_g:
            shutil.copyfile(out_path, out_dir / "graph_min.png")

        outputs.append(out_path)

    return outputs


#matplotlib