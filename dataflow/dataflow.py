
class CellException(Exception):
    """base exception class"""    
    pass

class CellNotFoundException(CellException):
    pass

class CellSelfReferenceException(CellException):
    pass

class CellIdExistsException(CellException):
    pass

class CellValErrorException(CellException):
    pass


class Cell(object):
    
    def __init__(self,cellflow=None,id=None,debug=False):
        
        self.cellflow = cellflow
        self.debug = debug
        
        self.id = id
        self.error = None
        
        self.meta = {}
        
        self.func = None
        self.errfunc = None
        self.before = None
        
        self._val = None
        self._val_old = None
                
        self.source_ref = None
        self.data_sinks = []
        self.watching = set()
       
    def _print_d(self,*args):
        if self.debug:
            print( "(debug)", *args )
        
    def __repr__(self):
        return "<Cell id=" + repr(self.id) \
                    + " val=" + repr(self._val) + " meta=" + repr(self.meta) \
                    + " func=" + repr(self.func) \
                    + " trigger=" + repr(self.has_trigger()) \
                    + " error=" + repr(self.error) \
                    + ">"
    
    def _getval(self):
        if self.error:
            raise CellValErrorException("cell function error before")
        return self._val
    
    def _setval(self,val):
        self._print_d("receive id=", self.id or id(self), "val=", repr(val))
        self._val_old, self._val = self._val, val
        if val != self._val_old:
            self._print_d( "changed id=", self.id or id(self))
            self.inform_all()
        
    def _delval(self):
        self.setval( None )
    
    val = property(_getval, _setval, _delval)
        
    def register_sink(self, c ):
        if c == self:
            raise CellSelfReferenceException()
        if c not in self.data_sinks:
            self.data_sinks.append( c )
        c.watching.add( self )
    
    def unregister_sink(self, c ):
        self.data_sinks.remove( c )
        c.watching.remove(self)

    def unregister_all(self):
        for c in self.data_sinks:
            self.unregister_sink( c )
            
    # more lingual ...

    def watches( self, c ):
        c.register_sink( self )

    def unwatches( self, c ):
        c.unregister_sink( self )

    # 

    def inform_all(self):
        for dl in self.data_sinks:
            dl.source_ref = self
            
    def has_trigger(self):
        return self.source_ref is not None
    
    def reset_trigger(self):
        self.source_ref = None

    def sink( self ):
        try:
            self.clr_error()
            
            val = self.source_ref.val
            
            if self.before:
                r = self.before(self,val)
                if r == False:
                    return
            
            if self.func is None:
                self.val = val
            else:
                self.val = self.func( self, val )
                
        except Exception as ex:
            self.error = ex
            if self.errfunc:
                try:
                    self.errfunc( self, self.source_ref.val, ex )
                except Exception as errex:
                    self.error = Exception("multiple errors", ex, errex )
        finally:            
            self.reset_trigger()    

    def clr_error(self):
        self.error = None
        

class CellDataFlow():
    
    def __init__(self,debug=False):
        self.debug=debug
        self.cells = []
        self.ids = {}
        self.last_error = []
       
    def __call__(self,*args,**kargs):
        if len(args)==1:
            return self.find(*args)
        return self.create_cell(**kargs)
       
    def cell(self,**kargs):
        return self.create_cell(**kargs)
       
    def create_cell(self,id=None,
                    watching=None,auto_watch=False,
                    func=None, err=None ):
        c = Cell(cellflow=self,id=id,debug=self.debug)
        c.func = func
        c.errfunc = err
        
        if id:
            if id in self.ids:
                raise CellIdExistsException()
            self.ids[c.id]=c
        self.cells.append(c)
        
        if watching:            
            if isinstance( watching, list ):
                for dr in watching:
                    dr.register_sink(c)
            else:
                watching.register_sink(c)
        return c
    
    def find(self,watches,recursion_level=5):
        """find depending cells"""
        found = set(watches) if isinstance(watches,list) else set([watches])
        
        if self in found:
            raise CellSelfReferenceException
        
        related = set(found)
        
        while recursion_level>0:
            recursion_level-=1
                   
            for w in related:
                related = related.union(w.watching)
            if self in related:
                # do not circle
                related.remove(self) 
                
            if len(related)==0:
                break
            if related.issubset( found ):
                break
            
            found = found.union( related )
        
        return list(found)
    
    def drop_cell(self,c):
        if c in self.cells:
            c.unregister_all()
            self.cells.remove(c)
            if c.id:
                del self.ids[c.id]
        else:
            raise CellNotFoundException(c)
    
    def propagate(self):
        """
        push the data to the next cell
        returns the number of cells involved
        """
        self.last_error = []
        todo = []
        for c in self.cells:
            if c.has_trigger():
                todo.append(c)
        for c in todo:
            c.sink()
            if c.error:
                self.last_error.append(c)
        return len(todo) 

    def loop(self,func=None,runs=-1,stop_on_error=False):
        """
        propagate until nothing more is to do, 
        or stop after number of runs
        """
        if runs<0:
            runs = len(self.cells)+1
        cnt = 0
        while self.propagate()>0 and runs>0:
            if stop_on_error and len(self.last_error)>0:
                break
            runs -= 1
            cnt += 1
            if func:
                func() 
        return cnt  
            
            