import random
from inspect import signature
from typing import Callable, Union

import numpy as np
import pygame

_MOVES = ["Up", "Down", "Left", "Right"]

_KEYMAP = {"Up": pygame.K_UP, "Down": pygame.K_DOWN, "Left": pygame.K_LEFT, "Right": pygame.K_RIGHT}
_REVERSE_KEYMAP = {v: k for k, v in _KEYMAP.items()}

HEURISTICS = ["greedy", "safe", "safest", "monotonic", "smooth", "corner_dist", "expert"]


class _Node(object):
    def __init__(self, parent=None):
        self.depth = 0
        self.num_visits = 0
        self.visit_score = 0
        self.avg_score = 0
        self.parent = parent
        super(_Node, self).__init__()


class StateNode(_Node):
    def __init__(self, state: np.ndarray, parent=None):
        self.state = state
        self.moves = {}  # Maps hashes of moves ("Up", "Down",...) to MoveNodes
        self.unvisited = valid_moves(state)
        super(StateNode, self).__init__(parent=parent)

    def __hash__(self):
        return str(self.state.tolist()).__hash__()

    def add_move(self, move):
        if hash(move) not in self.moves:
            new_move = MoveNode(move, self)
            new_move.depth = self.depth
            self.moves.update({new_move.__hash__(): new_move})

    def select_next_move(self, max_score):
        moves = []
        UCT = []
        for _, v in self.moves.items():
            moves.append(v.move)
            score = v.avg_score / max_score + (2 * np.log(self.num_visits + 1) / self.num_visits) ** 0.5
            UCT.append(score)

        UCT = np.array(UCT)
        return moves[np.random.choice(np.flatnonzero(UCT == UCT.max()))]

    def get_best_move(self):
        moves = []
        scores = []
        for _, v in self.moves.items():
            moves.append(v.move)
            scores.append(v.avg_score)

        scores = np.array(scores)
        return moves[np.random.choice(np.flatnonzero(scores == scores.max()))]


class MoveNode(_Node):
    def __init__(self, move: str, parent=None):
        self.move = move
        self.states = {}  # Maps StateNode hashes to StateNodes
        super(MoveNode, self).__init__(parent=parent)

    def __hash__(self):
        return self.move.__hash__()

    def add_state(self, state: np.ndarray):
        if hash(str(state.tolist())) not in self.states:
            new_state = StateNode(state, self)
            new_state.depth = self.depth + 1
            self.states.update({new_state.__hash__(): new_state})


class GameTree(object):
    def __init__(self, grid: np.ndarray, max_search_depth=10, num_rollouts=100, epsilon=0, UCT=False,
                 use_expert_score=False):
        self.root = StateNode(np.copy(grid))
        self.cur_node = self.root
        self.max_search_depth = max_search_depth
        self.num_rollouts = num_rollouts
        self.epsilon = epsilon
        self.UCT = UCT
        self.last_move = None
        self.max_score = 0
        self.use_expert_score = use_expert_score
        super(GameTree, self).__init__()

    def MCTS(self, cur_grid: np.ndarray, cur_score, heuristic_type=None):

        if self.last_move is not None:
            # If this isn't our first search, update our current position in the tree (else we start at the root)
            self.cur_node.moves[hash(self.last_move)].add_state(cur_grid)
            self.cur_node = self.cur_node.moves[hash(self.last_move)].states[hash(str(cur_grid.tolist()))]
            self.cur_node.visit_score = expert_score(cur_grid) if self.use_expert_score else cur_score

        moves = valid_moves(self.cur_node.state)
        search_node = self.cur_node

        for move in moves:
            for _ in range(self.num_rollouts):
                for d in range(self.max_search_depth + 1):
                    if d == 0:
                        new_move = move
                    else:
                        if len(valid_moves(search_node.state)) == 0:
                            break
                        # Choose a move
                        else:
                            if self.UCT:
                                if len(search_node.unvisited) > 0:
                                    ind = random.choice(range(len(search_node.unvisited)))
                                    new_move = search_node.unvisited[ind]
                                    del search_node.unvisited[ind]
                                else:
                                    new_move = search_node.select_next_move(self.max_score)
                            else:
                                if random.random() < self.epsilon or heuristic_type is None:
                                    new_move = _REVERSE_KEYMAP[random_move_event(search_node.state).dict["key"]]
                                else:
                                    if len(search_node.moves) == 0:
                                        new_move = _REVERSE_KEYMAP[heuristic_move_event(search_node.state,
                                                                                        heuristic_type).dict["key"]]
                                    else:
                                        new_move = search_node.get_best_move()

                    # Add move to children if not present
                    search_node.add_move(new_move)
                    move_node = search_node.moves[hash(new_move)]

                    # Simulate move
                    new_state, new_score = simulate_move(search_node.state, new_move, search_node.visit_score)
                    new_score = expert_score(new_state) if self.use_expert_score else new_score
                    move_node.add_state(new_state)
                    search_node = move_node.states[hash(str(new_state.tolist()))]
                    search_node.visit_score = new_score
                    self.max_score = max(self.max_score, new_score)

                # All moves simulated; do backup
                while search_node != self.cur_node:
                    search_node.avg_score = search_node.avg_score + (
                                search_node.visit_score - search_node.avg_score) / (
                                                    search_node.num_visits + 1)
                    search_node.num_visits += 1
                    parent_move = search_node.parent
                    parent_move.visit_score = search_node.visit_score
                    parent_move.avg_score = search_node.avg_score
                    parent_move.num_visits += 1
                    search_node = parent_move.parent
                    search_node.visit_score = parent_move.visit_score

                # Update the node for the current state (for sake of completeness)
                search_node.avg_score = search_node.avg_score + (search_node.visit_score - search_node.avg_score) / (
                        search_node.num_visits + 1)
                search_node.num_visits += 1

        # Choose best move
        self.last_move = self.cur_node.get_best_move()
        return pygame.event.Event(pygame.KEYDOWN, {"key": _KEYMAP[self.last_move]})


def rollouts(grid: np.ndarray, score, heuristic_type=None, max_search_depth=10, num_rollouts=100, epsilon=0,
             use_expert_score=False, hotfix=True):
    moves = valid_moves(grid)
    move_visits = [0] * len(moves)
    move_scores = [0] * len(moves)
    for move in range(len(moves)):
        avg_score = 0
        for _ in range(num_rollouts):
            for d in range(max_search_depth + 1):
                if d == 0:
                    new_grid, new_score = simulate_move(grid, moves[move], score)
                else:
                    if len(valid_moves(new_grid)) == 0:
                        break
                    if random.random() < epsilon or heuristic_type is None:
                        new_move = _REVERSE_KEYMAP[random_move_event(new_grid).dict["key"]]
                    else:
                        new_move = _REVERSE_KEYMAP[heuristic_move_event(new_grid, heuristic_type).dict["key"]]

                    new_grid, new_score = simulate_move(new_grid, new_move, new_score)
            if use_expert_score:
                avg_score = avg_score + (expert_score(new_grid) - avg_score) / (move_visits[move] + 1)
            else:
                avg_score = avg_score + (new_score - avg_score) / (move_visits[move] + 1)
            move_visits[move] += 1
            if hotfix:
                new_grid, new_score = new_grid, new_score
        move_scores[move] = avg_score
    move_scores = np.array(move_scores)
    return pygame.event.Event(pygame.KEYDOWN, {"key": _KEYMAP[moves[np.random.choice(
        np.flatnonzero(move_scores == move_scores.max()))]]})


def _get_merge_directions(grid: np.ndarray):
    move_list = [[] for _ in range(grid.size)]
    ind_array = np.arange(grid.size).reshape(grid.shape)

    for r in range(grid.shape[0]):
        row = grid[r, :]
        inds = ind_array[r, :][row != 0]
        row = row[row != 0]
        if row.size >= 2:
            for i in range(row.size):
                value = row[i]
                if i > 0 and inds[i] % grid.shape[0] != 0 and row[i - 1] == value:  # Left
                    move_list[inds[i]].append("Left")
                if i < row.size - 1 and (inds[i] + 1) % grid.shape[0] != 0 and row[i + 1] == value:  # Right
                    move_list[inds[i]].append("Right")

    for c in range(grid.shape[1]):
        col = grid[:, c]
        inds = ind_array[:, c][col != 0]
        col = col[col != 0]
        if col.size >= 2:
            for i in range(col.size):
                value = col[i]
                if i > 0 and inds[i] % grid.shape[1] != 0 and col[i - 1] == value:  # Up
                    move_list[inds[i]].append("Up")
                if i < col.size - 1 and (inds[i] + 1) % grid.shape[1] != 0 and col[i + 1] == value:  # Down
                    move_list[inds[i]].append("Down")

    return move_list


def _heuristic_choose_direction(moves: list, heuristic_type="greedy"):
    """
    Given a list of possible merge directions, chooses a direction to move. Heuristic type 1 picks any possible
    merge; heuristic type 2 prioritizes moving to the bottom right, since grouping the largest tiles is an effective
    strategy.

    :param moves: A list of possible merge directions from _get_merge_directions
    :param heuristic_type: The heuristic type to use. See the README for more info.
    :return: A direction, either "Up", "Down", "Left", or "Right", or False if no merges are possible.
    """
    if len(moves) == 0:
        return False
    elif heuristic_type == "greedy":
        return random.choice(moves)
    else:
        if "Down" in moves:
            if "Right" in moves:
                return random.choice(["Down", "Right"])
            return "Down"
        elif "Right" in moves:
            return "Right"
        else:
            return random.choice(moves)


def random_move_event(grid: np.ndarray):
    return pygame.event.Event(pygame.KEYDOWN, {"key": random.choice([_KEYMAP[move] for move in valid_moves(grid)])})


def quick_merge_row(row, right=True, old_score=None, count_merges=False):
    """
    Quick merge for a single row, courtesy of
    https://stackoverflow.com/questions/22970210/most-efficient-way-to-shift-and-merge-the-elements-of-a-list-in-python-2048

    Works for columns as well (right = down in that case)

    :param row: Row of the game grid to merge
    :param right: Whether to merge to the right or to the left (right by default)
    :param old_score: The current game score if a new score should be calculated; None otherwise
    :param count_merges: If True, additionally return a count of the number of tiles that were merged in the move
    :return: The merged row if old_score is None; else a tuple of (merged_row, new_score), (merged_row, merge_count), or
             (merged_row, new_score, merge_count), depending on the supplied parameters.
    """
    if right:
        row = row[::-1]
    values = []
    merge_vals = []
    empty = 0
    merges = 0
    for n in row:
        if values and n == values[-1]:
            values[-1] = 2 * n
            if count_merges:
                merges += 1
            if old_score is not None:
                old_score += 2 * n
            empty += 1
        elif n:
            values.append(n)
        else:
            empty += 1
    values += [0] * empty
    if right:
        values = values[::-1]

    if count_merges:
        return (values, merges) if old_score is None else (values, old_score, merges)
    else:
        return values if old_score is None else (values, old_score)


def quick_merge(grid: np.ndarray, direction: str, cur_score=None, count_merges=False):
    merged = grid.copy()
    count = 0
    if direction in ["Up", "Down"]:
        for c in range(grid.shape[1]):
            if count_merges:
                if cur_score is None:
                    merged[:, c], count = quick_merge_row(grid[:, c], direction == "Down", cur_score, count_merges)
                else:
                    merged[:, c], cur_score, count = quick_merge_row(grid[:, c], direction == "Down", cur_score,
                                                                     count_merges)
            else:
                if cur_score is None:
                    merged[:, c] = quick_merge_row(grid[:, c], direction == "Down", cur_score)
                else:
                    merged[:, c], cur_score = quick_merge_row(grid[:, c], direction == "Down", cur_score)

    else:
        for r in range(grid.shape[0]):
            if count_merges:
                if cur_score is None:
                    merged[r, :], count = quick_merge_row(grid[r, :], direction == "Right", cur_score, count_merges)
                else:
                    merged[r, :], cur_score, count = quick_merge_row(grid[r, :], direction == "Right", cur_score,
                                                                     count_merges)
            else:
                if cur_score is None:
                    merged[r, :] = quick_merge_row(grid[r, :], direction == "Right", cur_score)
                else:
                    merged[r, :], cur_score = quick_merge_row(grid[r, :], direction == "Right", cur_score)

    if count_merges:
        return (merged, count) if cur_score is None else (merged, cur_score, count)
    else:
        return merged if cur_score is None else (merged, cur_score)


def simulate_move(grid: np.ndarray, direction: str, cur_score):
    grid, new_score = quick_merge(grid, direction, cur_score)
    r, c = np.where(grid == 0)
    if len(r) > 0 and len(c) > 0:
        i = random.choice(range(len(r)))
        grid[r[i], c[i]] = 2 if random.random() < 0.9 else 4
    return grid, new_score


def is_valid_move(grid: np.ndarray, direction: str):
    return ~np.all(grid == quick_merge(grid, direction))


def valid_moves(grid: np.ndarray):
    return [move for move in _MOVES if is_valid_move(grid, move)]


def is_safe_move(grid: np.ndarray, direction: str):
    max_pos = np.unravel_index(grid.argmax(), grid.shape)
    new_max_pos = np.unravel_index(quick_merge(grid, direction).argmax(), grid.shape)
    return is_valid_move(grid, direction) and np.all(new_max_pos >= max_pos)


def safe_moves(grid: np.ndarray):
    return [move for move in _MOVES if is_safe_move(grid, move)]


def choose_move(grid: np.ndarray, moves: list, eval_func: Union[Callable[[np.ndarray], Union[int, float, complex]],
                                                                Callable[[np.ndarray, np.ndarray],
                                                                             Union[int, float, complex]]],
                compare_func=np.min):
    """
    Choose a move to take based on an evaluation function. The move chosen will be the argmin of the function.
    :param grid: The current game grid
    :param moves: A list of moves to evaluate. Possible values are "Up", "Down", "Left", "Right"
    :param eval_func: The evaluation function, which will be evaluated using the current grid and/or the grids
                      resulting from making the moves in 'moves'. This can either have the signature eval_func(
                      new_grid) -> Number or eval_func(cur_grid, new_grid) -> Number.
    :param compare_func: The function used to compare the outputs of 'eval_func'. Choices are either numpy.min or
                         numpy.max.
    :return: The chosen move. This will be the argmin/argmax of 'eval_func' when it is evaluated for each move.
    """
    move_evals = []
    for move in moves:
        new_grid = quick_merge(grid, move)
        if len(signature(eval_func).parameters) == 2:
            move_evals.append(eval_func(grid, new_grid))
        else:
            move_evals.append(eval_func(new_grid))
    move_evals = np.array(move_evals)
    return moves[np.random.choice(np.flatnonzero(move_evals == compare_func(move_evals)))]


def move_diff(cur_grid: np.ndarray, new_grid: np.ndarray):
    return int(np.sum(new_grid[new_grid != cur_grid]))


def smoothness(grid: np.ndarray):
    return np.abs(grid[:-1, :] - grid[1:, :]).sum() + np.abs(grid[1:, :] - grid[:-1, :]).sum() + np.abs(
        grid[:, :-1] - grid[:, 1:]).sum() + np.abs(grid[:, 1:] - grid[:, :-1]).sum()


def monotonicity(grid: np.ndarray):
    return np.sum((grid < np.roll(grid, 1, axis=0))[1:, :]) + np.sum((grid < np.roll(grid, 1, axis=1))[:, 1:])


def dist_from_corner(grid: np.ndarray):
    r, c = grid.nonzero()
    return ((grid.shape[0] - 1 - r + grid.shape[1] - 1 - c) * grid[r, c]).sum()


def expert_score(grid: np.ndarray):
    pow_grid = np.log2(grid, out=np.zeros_like(grid), where=(grid != 0), casting='unsafe')
    heuristic_score = 1600000
    heuristic_score -= np.sum(pow_grid ** 3.5) * 11
    heuristic_score += np.count_nonzero(grid == 0) * 540

    _, merge_count = quick_merge(grid, "Right", count_merges=True)
    _, new_count = quick_merge(grid, "Down", count_merges=True)
    merge_count += new_count
    heuristic_score += merge_count * 700

    left_mask = pow_grid[:, :-1] > pow_grid[:, 1:]
    top_mask = pow_grid[:-1, :] > pow_grid[1:, :]

    horizontal_monotonicity = np.min([np.sum(pow_grid[:, :-1][left_mask] ** 4 - pow_grid[:, 1:][left_mask] ** 4),
                                      np.sum(pow_grid[:, 1:][~left_mask] ** 4 - pow_grid[:, :-1][~left_mask] ** 4)])

    vertical_monotonicity = np.min([np.sum(pow_grid[:-1, :][top_mask] ** 4 - pow_grid[1:, :][top_mask] ** 4),
                                    np.sum(pow_grid[1:, :][~top_mask] ** 4 - pow_grid[:-1, :][~top_mask] ** 4)])

    heuristic_score -= (horizontal_monotonicity + vertical_monotonicity) * 47

    return heuristic_score


def heuristic_move_event(grid: np.ndarray, heuristic_type="greedy"):
    if heuristic_type in ["greedy", "safe", "safest"]:
        moves = [_heuristic_choose_direction(move, heuristic_type) for move in _get_merge_directions(grid)]
        moves = np.array(moves)
        inds = grid.argsort(axis=None)[::-1]
        cell_move_priority = inds[grid.flatten()[inds] != 0]
        for move_ind in cell_move_priority:
            if moves[move_ind] == "Up":
                if heuristic_type == "greedy":
                    return pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_UP})
                else:
                    # If up is an option, there is a companion tile that can merge down
                    return pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_DOWN})
            elif moves[move_ind] == "Down":
                return pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_DOWN})
            elif moves[move_ind] == "Left":
                if heuristic_type == "greedy":
                    return pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_LEFT})
                else:
                    # If left is an option, there is a companion tile that can merge right
                    return pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT})
            elif moves[move_ind] == "Right":
                return pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT})

        if heuristic_type == "safe":
            valid = valid_moves(grid)
            safe = safe_moves(grid)
            if safe:
                return pygame.event.Event(pygame.KEYDOWN, {"key": random.choice([_KEYMAP[move] for move in safe])})
            else:
                return pygame.event.Event(pygame.KEYDOWN, {"key": random.choice([_KEYMAP[move] for move in valid])})

        elif heuristic_type == "safest":
            valid = valid_moves(grid)
            safe = safe_moves(grid)
            if safe:
                return pygame.event.Event(pygame.KEYDOWN, {"key": _KEYMAP[choose_move(grid, safe, move_diff)]})
            else:
                return pygame.event.Event(pygame.KEYDOWN, {"key": _KEYMAP[choose_move(grid, valid, move_diff)]})

        else:
            return pygame.event.Event(pygame.KEYDOWN,
                                      {"key": random.choice([_KEYMAP[move] for move in valid_moves(grid)])})

    elif heuristic_type == "monotonic":
        valid = valid_moves(grid)
        return pygame.event.Event(pygame.KEYDOWN, {"key": _KEYMAP[choose_move(grid, valid, monotonicity)]})

    elif heuristic_type == "smooth":  # Smooth
        valid = valid_moves(grid)
        return pygame.event.Event(pygame.KEYDOWN, {"key": _KEYMAP[choose_move(grid, valid, smoothness)]})

    elif heuristic_type == "corner_dist":
        grid = np.array(grid)
        valid = valid_moves(grid)
        return pygame.event.Event(pygame.KEYDOWN, {"key": _KEYMAP[choose_move(grid, valid, dist_from_corner)]})
    else:  # Expert
        grid = np.array(grid)
        valid = valid_moves(grid)
        return pygame.event.Event(pygame.KEYDOWN, {"key": _KEYMAP[choose_move(grid, valid, expert_score, np.max)]})
