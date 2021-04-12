"""
simple interactive sudoko game

when a cell val is set, depending cells (row,col,and block constraints)
are notified by the dataflow and update their list of possible values

interact from python repl by calling the functions

print_board, for printing the board
peek, for getting the possible values
getg, for getting one cells value
setb, for setting one cells value, returns the notified cells
undo, revert last move

or call
resolve, to solve the game

"""

from dataflow import CellDataFlow, print_error, clear_error
from collections import deque
import random


def getid(x, y):
    return f"{x},{y}"


def create_board(cf, type):
    dim = type * type
    cells = dim * dim
    board = []
    for x in range(0, dim):
        for y in range(0, dim):
            c = cf(id=getid(x, y))
            c.meta["x"] = x
            c.meta["y"] = y
            c.meta["dim"] = dim
            c.meta["type"] = type
            board.append(c)
    return board


def dim_board(board):
    dim = board[0].meta["dim"]
    cells = dim * dim
    return dim, cells


def init_board(cf, board):
    dim, cells = dim_board(board)
    type = board[0].meta["type"]

    for x in range(0, dim):
        for y in range(0, dim):
            watch = set()
            for i in range(0, dim):
                # row cells
                watch.add(getid(i, y))
                # col cells
                watch.add(getid(x, i))
            # block cells
            xb = int(x / type) * type
            yb = int(y / type) * type
            for xi in range(xb, xb + type):
                for yi in range(yb, yb + type):
                    watch.add(getid(xi, yi))
            # remove self reference
            selfid = getid(x, y)
            watch.remove(selfid)
            # find myself ;-)
            cell = cf.ids[selfid]
            watching = set()
            for w in watch:
                cell.watches(cf.ids[w])
            cell.meta["watch"] = watch
            cell.meta["watching"] = watching

            def before(c, v):

                # print the cell id
                # print( c.id, end=" " )

                # update hints
                c.hints(c)
                # return false to stop data flow
                return False

            def hints(self):
                constrained = set(map(lambda x: x.val, self.watching))
                h = set(range(1, 10)).difference(constrained)
                self.meta["hints"] = h
                return h

            cell.hints = hints
            cell.before = before


def sanitize(data):
    for s in [" ", "\t", "\n", "\r"]:
        data = data.replace(s, "")
    data = data.replace(".", "0")
    return data


def fill_board(cf, board, data):
    dim, cells = dim_board(board)
    inp = sanitize(data)
    if len(inp) != cells:
        raise Exception(f"input does not match dimension {dim},{cells},{len(inp)}")
    i = 0
    for c in inp:
        c = int(c)
        if c > 0:
            board[i].val = c
        board[i].meta["preset"] = c > 0
        i += 1


def print_board(cf, board):
    dim, cells = dim_board(board)
    print("\t", end=" ")
    for h in range(0, dim):
        print(h, end="\t")
    print()
    for h in range(0, dim + 1):
        print("-" * 4, end="\t")
    print()
    for x in range(0, dim):
        print(str(x) + "  |", end="\t")
        for y in range(0, dim):
            cell = cf.ids[getid(x, y)]
            v = cell._val
            if v is None:
                v = " "
            else:
                v = str(v)
            if cell.meta["preset"]:
                v += "*"
            print(v, end="\t")
        print()


stack = deque()


def getcell(cf, x, y):
    return cf.ids[getid(x, y)]


def getb(cf, x, y):
    return getcell(cf, x, y).val


def setb(cf, x, y, v):
    cell = getcell(cf, x, y)
    if cell.meta["preset"]:
        print("cant overwrite preset cell")
        return
    if v not in cell.meta["hints"]:
        print("not possible", x, y)
        return
    cell.val = v
    stack.append(cell)
    cnt = cf.loop()
    return cnt


def undo(cf):
    cell = stack.pop()
    cell.val = None
    cnt = cf.loop()
    return cnt


def peek(cf, x, y):
    cell = getcell(cf, x, y)
    if cell.val:
        return f"has val {cell.val}"
    return cell.meta["hints"]


cf = CellDataFlow()
board = create_board(cf, 3)
init_board(cf, board)


game = """      
    ... 000 974
    000 230 865
    608 000 301
    975 000 000
    003 008 000
    010 090 000
    000 000 002
    089 104 000
    000 500 610
"""

fill_board(cf, board, game)

# set up the game
for c in cf.cells:
    c.reset_trigger()
    c.hints(c)

# this will trigger no action here...
cnt = cf.loop()

print_board(cf, board)


def sample_calls_like():
    getcell(cf, 0, 0)
    getb(cf, 0, 0)
    peek(cf, 0, 0)
    setb(cf, 0, 0, 1)
    print()
    print_board(cf, board)
    undo(cf)
    print()
    print_board(cf, board)


def resolve(debug=False, shuffle=True):
    """call resolve to solve the game"""
    cells = filter(lambda x: x.meta["preset"] == False, cf.cells)
    rc = _resolve(cells, debug=debug, shuffle=shuffle)
    if rc:
        print_board(cf, board)
    else:
        print("no solution")


cnt = 0


def _resolve(cells=None, lvl=0, debug=False, shuffle=True):
    global cnt
    cnt += 1

    cells = list(filter(lambda x: x.val == None or x.val == 0, cells))
    if len(cells) == 0:
        return True
    # try this several times with debug=True
    # to see that this solving strategy works better on average
    if shuffle:
        random.shuffle(cells)
    # solve cells with less hints first
    cells = sorted(cells, key=lambda x: len(x.meta["hints"]))

    for c in cells:
        x = c.meta["x"]
        y = c.meta["y"]
        all_hints = list(peek(cf, x, y))
        if len(all_hints) == 0:
            return False
        if shuffle:
            random.shuffle(all_hints)

        for h in all_hints:
            debug and print(
                "set", x, y, "=", h, "lvl", lvl, "loops", cnt, "remaining", len(cells)
            )
            setb(cf, x, y, h)
            result = _resolve(cells, lvl=lvl + 1, shuffle=shuffle, debug=debug)
            if result:
                return True
            undo(cf)
        return False
    return False


def print_hints():
    cells = cf.cells
    cells = filter(lambda x: x.meta["preset"] == False, cells)
    cells = filter(lambda x: x.val == None or x.val == 0, cells)
    cells = sorted(cells, key=lambda x: len(x.meta["hints"]))
    for c in cells:
        print(c.id, c.meta["hints"], len(c.meta["hints"]))
