import heapq
from collections import defaultdict

def build_graph(edges):
    graph = defaultdict(list)
    for e in edges:
        graph[e.node_a_id].append((e.node_b_id, e.distance))
        graph[e.node_b_id].append((e.node_a_id, e.distance))
    return graph

def shortest_path(graph, start_id, end_id):
    queue = [(0, start_id, [start_id])]
    visited = set()
    while queue:
        cost, node, path = heapq.heappop(queue)
        if node == end_id:
            return path, cost
        if node in visited:
            continue
        visited.add(node)
        for neighbor, weight in graph[node]:
            if neighbor not in visited:
                heapq.heappush(queue, (cost + weight, neighbor, path + [neighbor]))
    return None, None
