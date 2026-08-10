from collections import defaultdict
from itertools import combinations
from a_models import Session
from database_upgraded import load_database
import collections

def adjacency_list(session: Session):

    graph = defaultdict(list)
    events_by_session = defaultdict(list)
    for event in session.events:
        events_by_session[event.session_id].append(event.brand)
    print(events_by_session)

    for brands in events_by_session.values():
        for brand1, brand2 in combinations(set(brands), 2):
            graph[brand1].append(brand2)
            graph[brand2].append(brand1)
    return graph

def bfs(graph, start, max_depth): 
    visited = {}
    queue = collections.deque()
    layers = {}

    visited = {start}
    queue.append((start, 0))

    while queue:
        brand, depth = queue.popleft()
        if depth == max_depth:
            continue
        for neighbor in graph[brand]:
            if neighbor in visited:
                layers[depth + 1][neighbor] = layers[depth + 1].get(neighbor, 0) + 1
                continue
            visited.add(neighbor)
            layers.setdefault(depth + 1, {})
            layers[depth+1].update({neighbor: 1})
            queue.append((neighbor, depth + 1))

    print(layers) 
    return layers


if __name__ == "__main__":
    graph = adjacency_list(Session(load_database()))
    bfs(graph, "Adidas", 1)