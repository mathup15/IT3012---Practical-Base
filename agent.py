# agent.py
import random
import heapq
from collections import deque
class GreedyGridAgent:
    """A simple agent that tries to move around systematically to clear the grid."""

    def __init__(self):
        self.actions_pool = ['Up', 'Down', 'Left', 'Right']

    def sense_and_act(self, percept: dict) -> str:
        # If standing directly on food, or just wander / move towards coordinates
        pos = percept['agent_pos']
        # Simple heuristic or fallback random sweep
        return random.choice(self.actions_pool)
class SimpleReflexAgent:
    """Simple reflex agent from Lab 01."""

    def sense_and_act(self, percept):
        if percept['food_here']:
            return 'Suck'

        if percept['wall_ahead']:
            return 'Left'

        return 'Up'


class ModelBasedAgent:
    """Model-based agent from Lab 02."""

    def __init__(self):
        self.position = (0, 0)
        self.facing = 'Right'
        self.visited_cells = {(0, 0)}
        self.blocked_cells = set()
        self.last_action = None
        self.previous_wall_ahead = False

    def cell_in_direction(self, direction):
        direction_changes = {
            'Up': (0, 1),
            'Right': (1, 0),
            'Down': (0, -1),
            'Left': (-1, 0)
        }

        dx, dy = direction_changes[direction]

        return (
            self.position[0] + dx,
            self.position[1] + dy
        )

    def update_state(self, percept):
        directions = ['Up', 'Right', 'Down', 'Left']

        if self.last_action == 'TurnLeft':
            current_index = directions.index(self.facing)
            self.facing = directions[(current_index - 1) % 4]

        elif self.last_action == 'TurnRight':
            current_index = directions.index(self.facing)
            self.facing = directions[(current_index + 1) % 4]

        elif (
            self.last_action == 'MoveForward'
            and not self.previous_wall_ahead
        ):
            self.position = self.cell_in_direction(
                self.facing
            )
            self.visited_cells.add(self.position)

        if percept['wall_ahead']:
            wall_cell = self.cell_in_direction(
                self.facing
            )
            self.blocked_cells.add(wall_cell)

    def sense_and_act(self, percept):
        self.update_state(percept)

        # Collect food when standing on it
        if percept['food_here']:
            action = 'Suck'

        # Alternate turns when encountering walls
        elif percept['wall_ahead']:
            if self.last_action == 'TurnLeft':
                action = 'TurnRight'
            else:
                action = 'TurnLeft'

        else:
            action = 'MoveForward'

        self.last_action = action
        self.previous_wall_ahead = percept['wall_ahead']

        return action
        
class SearchAgent:
    """Goal-based agent that plans paths using BFS, DFS, or UCS."""

    def __init__(self):
        self.plan = []
        self.active_algo = 'BFS'

        self.directions = [
            ('Up', (0, 1)),
            ('Right', (1, 0)),
            ('Down', (0, -1)),
            ('Left', (-1, 0))
        ]

    def get_successors(self, state, walls, grid_size):
        """Return valid neighbouring states and their actions."""
        width, height = grid_size
        walls = set(walls)

        for action, (dx, dy) in self.directions:
            next_state = (state[0] + dx, state[1] + dy)

            inside_grid = (
                0 <= next_state[0] < width
                and 0 <= next_state[1] < height
            )

            if inside_grid and next_state not in walls:
                yield next_state, action

    def bfs_search(self, start, goal, walls, grid_size):
        """Breadth-First Search using a FIFO queue."""
        frontier = deque([(start, [])])
        reached = {start}

        while frontier:
            state, path = frontier.popleft()

            if state == goal:
                return path

            for next_state, action in self.get_successors(
                state, walls, grid_size
            ):
                if next_state not in reached:
                    reached.add(next_state)
                    frontier.append(
                        (next_state, path + [action])
                    )

        return None

    def dfs_search(self, start, goal, walls, grid_size):
        """Depth-First Search using a LIFO stack."""
        frontier = [(start, [])]
        reached = {start}

        while frontier:
            state, path = frontier.pop()

            if state == goal:
                return path

            for next_state, action in self.get_successors(
                state, walls, grid_size
            ):
                if next_state not in reached:
                    reached.add(next_state)
                    frontier.append(
                        (next_state, path + [action])
                    )

        return None

    def ucs_search(self, start, goal, walls, grid_size):
        """Uniform-Cost Search using a priority queue."""
        frontier = [(0, start, [])]
        best_cost = {start: 0}

        while frontier:
            cost, state, path = heapq.heappop(frontier)

            if state == goal:
                return path

            if cost > best_cost.get(state, float('inf')):
                continue

            for next_state, action in self.get_successors(
                state, walls, grid_size
            ):
                new_cost = cost + 1

                if new_cost < best_cost.get(
                    next_state, float('inf')
                ):
                    best_cost[next_state] = new_cost

                    heapq.heappush(
                        frontier,
                        (
                            new_cost,
                            next_state,
                            path + [action]
                        )
                    )

        return None

    def find_closest_food(self, start, food_positions):
        """Choose the food with the smallest Manhattan distance."""
        if not food_positions:
            return None

        return min(
            food_positions,
            key=lambda food: (
                abs(food[0] - start[0])
                + abs(food[1] - start[1])
            )
        )

    def sense_and_act(self, percept):
        """Create an offline plan and execute one action at a time."""
        if percept['food_here']:
            self.plan = []
            return 'Suck'

        if not self.plan:
            start = tuple(percept['agent_pos'])
            food_positions = [
                tuple(food)
                for food in percept['all_food']
            ]

            goal = self.find_closest_food(
                start,
                food_positions
            )

            if goal is None:
                return 'NoOp'

            walls = percept['walls']
            grid_size = percept['grid_size']
            algorithm = self.active_algo.upper()

            if algorithm == 'BFS':
                result = self.bfs_search(
                    start, goal, walls, grid_size
                )
            elif algorithm == 'DFS':
                result = self.dfs_search(
                    start, goal, walls, grid_size
                )
            elif algorithm == 'UCS':
                result = self.ucs_search(
                    start, goal, walls, grid_size
                )
            else:
                raise ValueError(
                    f"Unknown algorithm: {self.active_algo}"
                )

            self.plan = result or []

        if self.plan:
            return self.plan.pop(0)

        return 'NoOp'