from dataflow import CellDataFlow, print_error, clear_error


def not_gate(cf, a, id=None):
    a_ = cf(id=id, watching=a, func=lambda c, v: not bool(a.val))
    return a_


def and_gate(cf, a, b, id=None):
    c = cf(id=id, watching=[a, b], func=lambda c, v: bool(a.val) and bool(b.val))
    return c


def nand_gate(cf, a, b, id=None):
    c = cf(id=id, watching=[a, b], func=lambda c, v: not (bool(a.val) and bool(b.val)))
    return c


def or_gate(cf, a, b, id=None):
    c = cf(id=id, watching=[a, b], func=lambda c, v: bool(a.val) or bool(b.val))
    return c


def nor_gate(cf, a, b, id=None):
    c = cf(id=id, watching=[a, b], func=lambda c, v: not (bool(a.val) or bool(b.val)))
    return c


def xor_gate(cf, a, b, id=None):
    c = cf(id=id, watching=[a, b], func=lambda c, v: bool(a.val) ^ bool(b.val))
    return c


def rs_flipflop(cf, s_, r_, id=None):
    # rs flipflop contains a circle
    # needs manual wiring
    # https://en.wikipedia.org/wiki/Flip-flop_(electronics)
    and1 = cf(watching=s_)
    not1 = not_gate(cf, and1)
    and2 = cf(watching=r_)
    not2 = not_gate(cf, and2)
    and1.watches(not2)
    and2.watches(not1)
    and1.func = lambda c, v: s_.val and not2.val
    and2.func = lambda c, v: r_.val and not1.val
    return not1, not2


cf = CellDataFlow(debug=False)

# a what-ever circuit

a = cf(id="a")
b = cf(id="b")
st1 = and_gate(cf, a, b, id="st1")

c = cf(id="c")
st2 = or_gate(cf, c, st1, id="st2")

st3 = not_gate(cf, st2, id="st3")

d = cf(id="d")
st4 = xor_gate(cf, st3, d, id="st4")

e = cf(id="e")
st5 = nand_gate(cf, st4, e, id="st5")

f = cf(id="f")
st6 = nor_gate(cf, st5, f, id="st6")


def print_it():
    print(
        a.val,
        b.val,
        st1.val,
        c.val,
        st2.val,
        st3.val,
        d.val,
        st4.val,
        e.val,
        st5.val,
        f.val,
        st6.val,
    )


a.val = True
b.val = False
c.val = True
d.val = True
e.val = True
f.val = False

print("the circuit data flow")
cf.loop(func=print_it)

# a rs flipflop

s_ = cf()
r_ = cf()
q, q_ = rs_flipflop(cf, s_, r_)


def print_rs():
    print(s_.val, r_.val, q.val, q_.val)


print()
print("set rs flip-flop, state is first undefined...")
# simulate set trigger
s_.val = False
r_.val = True
# run until stable
cf.loop(func=print_rs)
# release trigger
s_.val = True
# run until stable
cf.loop(func=print_rs)

print()
print("reset rs flip-flop")
# simulate reset trigger
s_.val = True
r_.val = False
# run until stable
cf.loop(func=print_rs)
# release trigger
r_.val = True
# run until stable
cf.loop(func=print_rs)
