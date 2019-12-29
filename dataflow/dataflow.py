
class CellException(Exception):
    """base exception class"""    
    pass

class CellNotFoundException(CellException):
    pass

class CellSelfReferenceException(CellException):
    pass

class CellIdExistsException(CellException):
    pass


class Cell(object):
    
    def __init__(self,cellflow=None,id=None):
        
        self.cellflow = cellflow
        
        self.id = id
        self.error = None
        
        self.meta = {}
        
        self.func = None
        
        self._val = None
        self._val_old = None
                
        self.source_ref = None
        self.data_sinks = []
        self.watching = set()
             
        
    def __repr__(self):
        return "<Cell val=" + repr(self.val) + " meta=" + repr(self.meta) \
                    + " func=" + repr(self.func) \
                    + " trigger=" + repr(self.has_trigger()) \
                    + " error=" + repr(self.error) \
                    + ">"
    
    def _getval(self):
        return self._val
    
    def _setval(self,val):
        self._val_old, self._val = self._val, val
        if val != self._val_old:
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
            if self.func is None:
                self.val = self.source_ref.val
            else:
                self.val = self.func( self, self.source_ref.val )
        except Exception as ex:
            self.error = ex
        self.reset_trigger()    


class CellDataFlow():
    
    def __init__(self):
        self.cells = []
        self.ids = {}
       
    def __call__(self,*args,**kargs):
        if len(args)==1:
            return self.find(*args)
        return self.create_cell(**kargs)
       
    def cell(self,**kargs):
        return self.create_cell(**kargs)
       
    def create_cell(self,id=None,watching=None,auto_watch=False,func=None):
        c = Cell(cellflow=self,id=id)
        c.func = func
        
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
        todo = []
        for c in self.cells:
            if c.has_trigger():
                todo.append(c)
        for c in todo:
            c.sink()
        return len(todo) 

    def loop(self,func=None,runs=-1):
        """
        propagate until nothing more is to do, 
        or stop after number of runs
        """
        if runs<0:
            runs = len(self.cells)+1
        cnt = 0
        while self.propagate()>0 and runs>0:
            runs -= 1
            cnt += 1
            if func:
                func() 
        return cnt  
            
            