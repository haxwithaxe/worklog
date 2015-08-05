
from collections import Callable
from collections.abc import MutableSequence
from datetime import date, datetime, timedelta, time
import errno
import json
import os

class Worklog( MutableSequence ):

    def __init__( self, when = None ):
        if when is None:
            self.when = date.today()
        elif isinstance( when, str ):
            self.when = datetime.strptime( when, '%Y-%m-%d' ).date()
        else:
            self.when = date
        self.persist_path = os.path.expanduser( '~/.worklog/{}-2.json'.format( self.when.strftime( '%F' ) ) )
        try:
            with open( self.persist_path, 'r' ) as json_file:
                self.store = json.load( json_file, object_hook = dict_to_object )
        except IOError as err:
            if err.errno == errno.ENOENT:
                self.store = list()
            else:
                raise

    def __getattr__( self, attr ):
        if attr in ( '__getitem__', '__setitem__', '__delitem__', '__len__' ):
            return getattr( self.store, attr )
        raise AttributeError('{} has no attribute {}'.format( self.__class__.__name__, attr ) )

    def insert( self, task ):
        self.store.append( task )
        self.store.sort( key = lambda t: t.start )

    def save( self ):
        directory = os.path.split( self.persist_path )[0]
        if not os.access( directory, os.F_OK ):
            os.makedirs( directory, mode = 0o755 )
        with open( self.persist_path, 'w' ) as json_file:
            json.dump( self.store, json_file, cls = KlassEncoder, indent = 4 )

    def pairwise( self ):
        offset = self.store[1:]
        offset.append( DummyRightNow() )
        return zip( self.store, offset )



class KlassEncoder( json.JSONEncoder ):
    """Encodes Task objects and datetime objects to JSON using __klass__ indicator key"""

    def default( self, obj ):
        if isinstance( obj, ( Task, GoHome ) ):
            d = obj.__dict__.copy()
            d['__klass__'] = type( obj ).__name__
            return d
        elif isinstance( obj, datetime ):
            return {
                '__klass__' : 'datetime',
                'year' : obj.year,
                'month' : obj.month,
                'day' : obj.day,
                'hour' : obj.hour,
                'minute' : obj.minute,
                'second' : obj.second,
                'microsecond' : obj.microsecond,
            }
        else:
            return super( KlassEncoder, self ).default( obj )


# When this was an instance method on a subclass of json.JSONDecoder, python totally fucked up giving me
# TypeError: __init__() got multiple values for argument 'object_hook'
# even though I was overriding, not adding, my own object_hook
# pulling it out into a global function (ugh) and passing it along to json.load as the object_hook option
# worked around this stupid problem.
def dict_to_object( d ):
    if '__klass__' not in d: return d

    klass = d.pop( '__klass__' )
    try:
        konstructor = globals()[klass]
    except KeyError:
        d['__klass__'] = klass
        return d
    else:
        return konstructor( **d )
