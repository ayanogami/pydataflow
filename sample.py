
from dataflow import CellDataFlow, print_error, clear_error


cf = CellDataFlow()

c1 = cf.create_cell() # or shorthand -> c1 = cf()

#lambda function is called with cell,cell.val
c2 = cf(watching=c1, func=lambda c,v: v-1 )
c3 = cf(watching=[c1], func=lambda c,v: v*2 )

# since watching to 2 cells its not predictable what c,v is used in the call
# could be any of the watches, c2 or c3
c4 = cf(watching=[c2,c3], func= lambda c,v: c2.val+c3.val )

c5 = cf(watching=[c4], id="c5", func=lambda c,v : c2.val+c3.val+c4.val )


# new in version v0.0.4, ref and lazy bind

# lazy bound cells are referenced by id rather then object instance
# create a lazy bound cells _before_ cell c5clone is created
c5_lazy = cf(lazy_watching="c5clone", func=lambda c,v : str(v) + "*" )

# refer to c5clone with ref() function by id
c5ref_lazy = cf(lazy_watching="c5clone", func=lambda c,v : str(c.ref("c5clone").val) + "!!" )
c5ref_lazy_array = cf(lazy_watching=["c5clone"], func=lambda c,v : str(c.ref("c5clone").val) + "!!!" )
c5lazy_array = cf(lazy_watching=["c5clone"], func=lambda c,v : str(v) + "<-" )

c5_the_clone = cf( id="c5clone", watching=[c5], func=lambda c,v : str(v) + "!" )

# dont forget to bind all lazy watches before starting the dataflow
cf.bind()


# use find to add all depending watches automatically
# print output will show that the data goes directly forward
# instead of arriving in one of the next round(s)
c6 = cf(watching=cf.find([c2,c5]), func=lambda c,v : c2.val + c5.val )

def cust_func(c,v):
    # print(f"do something usefull because of {v}")
    return v*3.14

c7 = cf(watching=c6, func=cust_func )
# shorthand for cf.find
c8 = cf(watching=cf(c6), func=lambda c,v : v*3.14 )

def sumup(c,v):    
    total = sum(map( lambda x : x.val, c.watching))
    return total
    
c9 = cf(watching=cf(c8), func=sumup )

# no func provided, just get the data from the cell here
# add print_error to see difference in output
c10 = cf(id="c10", watching=c6, func=lambda c,v : 1/0 , err=None )

# err function is called when func fails
# called as errfunc( cell, val, ex )
# use clear_error for clean up
c11 = cf(id="c11", watching=c6, err=None )


def strcats(c,v):
    # watching is a set, so the result combination is unpredictable
    return " ".join(map( lambda x : x.val , c.watching))
    
cs1 = cf()
cs2 = cf()
cs3 = cf(watching=[cs1,cs2], func=strcats )

cs4 = cf(watching=[cs1,cs2], func=lambda c,v : (cs1.val + cs2.val).upper() )

# add some custom data in case val is not sufficient
cs4.meta["extra_data"] = "meta dict can be used for own purposes"

# this will later removed from the flow
cdrop = cf(watching=c6 )

# assignment only after flow is defined
# assignment triggers later processing
c1.val = 3
cs1.val ="hi"
cs2.val ="ya"


def val(x):
    if x.error:
        return "#ERR#"
    try:
        return round(x.val,2)
    except:
        return x.val

for cell in cf.cells:
    print(val(cell),end="\t")
print()

# propagate pushes data to the next depending cells
# and stops after that
# call propagate serveral times to push data completly

# since there is no circle defined its possible to loop
while cf.propagate():
    for cell in cf.cells:
        print(val(cell),end="\t")
    print()


print("drop cell")
cf.drop_cell( cdrop ) # remove from the flow definition


print("recalc with c1=4, change greeting, cdrop will keep old val!")
c1.val = 4
cs2.val = "you"

def printit():
    for c in cf.cells:
        print(val(c),end="\t")
    print(cdrop.val)

# use the loop which calls propagate 
# max calls is number of cells involed (runs parameter set to default:-1)
# call func after every propagate
cf.loop( func=printit, runs=-1 )

print("--- same val---")
c1.val = 4

# nothing happens here since val is unchanged
runs = cf.loop(func=printit)
print( "runs", runs )

printit()

print("---done---")
