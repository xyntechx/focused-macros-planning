INFINITY = 999999 # basically infinity


def get_init_actions(index: str):
    """
    Get initial actions from cam/domains/cube/random_starts with index=index (e.g. index=0 => start-000.txt) to set the initial state of the cube
    """
    assert int(index) < 100, "There are only 100 files/predetermined initial states range=[0, 99]"

    with open(f"cam/domains/cube/random_starts/start-{index}.txt") as f:
        init_actions = f.read().strip().split(" ")
    
    return init_actions


def join_int_list(lst):
    lst_str = [str(i) for i in lst]
    return "".join(lst_str)
