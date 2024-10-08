import pickle
import math
from tqdm import tqdm
from cam.domains.cube.cubeenv import CubeEnv
from utils import get_init_actions, join_int_list, INFINITY
from fringe import Fringe


def optimized_reset(curr_simulator, curr_sequence, base_actions):
    if len(base_actions) < len(curr_sequence):
        curr_simulator.reset(sequence=base_actions)
    else:
        for action in reversed(curr_sequence):
            curr_simulator.step((action + 6) % 12) # undo action


def learn_macros(base_simulator: CubeEnv, N_m=576, R_m=1, B_m=1_000_000, disable_progress=False):
    # Specs of base_simulator (describing root node of search tree)
    base_state = join_int_list(base_simulator.state)
    base_actions = base_simulator.sequence
    base_net_actions = []

    # Initialize relevant vars for BFS
    fringe = Fringe(max_size=N_m*10)
    fringe.push((base_state, base_net_actions), base_state, INFINITY)
    visited = {} # data dict of all states already visited (init as empty dict)

    # Setting up simulator to be updated during search
    curr_simulator = CubeEnv()
    curr_simulator.reset(sequence=base_actions)

    with tqdm(total=B_m//R_m, disable=disable_progress) as progress:
        counter = 0

        while counter < B_m//R_m:
            best_state, best_actions, best_f = fringe.pop()
            
            if best_state in visited:
                if best_f < visited[best_state]["f"]:
                    visited[best_state] = {"f": best_f, "net_actions": best_actions}

                continue # if I've visited this state before, there's no point in expanding it again
            visited[best_state] = {"f": best_f, "net_actions": best_actions}

            for action in best_actions:
                curr_simulator.step(action)

            for action in base_simulator.action_meanings:
                state, _, _ = curr_simulator.step(action)
                curr_state = join_int_list(state)
                curr_actions = best_actions + [action]
                curr_f = min(curr_simulator.diff(baseline=base_simulator.cube) + len(curr_actions), INFINITY)

                fringe.update((curr_state, curr_actions), curr_state, curr_f)

                curr_simulator.step((action + 6) % 12) # undo action
                counter += 1
                progress.update()

            optimized_reset(curr_simulator, best_actions, base_actions)

    macros = {}
    for _ in range(N_m//R_m):
        best_state = min(visited, key=lambda x: visited[x]["f"] - len(visited[x]["net_actions"]))
        macros[best_state] = visited.pop(best_state)

    # Stats
    best_state = min(macros, key=lambda x: macros[x]["f"] - len(macros[x]["net_actions"]))
    worst_state = max(macros, key=lambda x: macros[x]["f"] - len(macros[x]["net_actions"]))
    print(f"# of Macros Generated: {len(macros)}")
    print(f"Best Net Effect (h) Heuristic: {macros[best_state]["f"] - len(macros[best_state]["net_actions"])}")
    print(f"Worst Net Effect (h) Heuristic: {macros[worst_state]["f"] - len(macros[worst_state]["net_actions"])}")
    print(f"Shortest Macro Length (g): {len(macros[min(macros, key=lambda x: len(macros[x]["net_actions"]))]["net_actions"])}")
    print(f"Longest Macro Length (g): {len(macros[max(macros, key=lambda x: len(macros[x]["net_actions"]))]["net_actions"])}")

    return [macros[state]["net_actions"] for state in macros]


if __name__ == "__main__":
    print("Learn focused macros using best-first search")

    index = input("Enter start sequence index [0-99] (if left empty, default=0): ")
    index = str(index if index else '0').zfill(3)
    init_actions = get_init_actions(index)

    base_simulator = CubeEnv()
    init_seq = [base_simulator.action_lookup[a] for a in init_actions]
    base_simulator.reset(sequence=init_seq)

    macros = []
    sequences = learn_macros(base_simulator)
    for seq in sequences:
        macro = " ".join([base_simulator.action_meanings[s] for s in seq])
        macros.append(macro)

    with open("output/learned_macros.pkl", "wb") as f:
        pickle.dump(macros, f)
