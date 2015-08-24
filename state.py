
from collections import Callable
from collections.abc import MutableSequence
from datetime import date, datetime, timedelta, time
import json
import os
import re


SECONDS_IN_MINUTE = 60
SECONDS_IN_HOUR = SECONDS_IN_MINUTE * 60
SECONDS_IN_DAY = SECONDS_IN_HOUR * 8

DURATION_FACTORS = {
    'd': 60 * 60 * 8,
    'h': 60 * 60,
    'm': 60,
}

DURATION_RE = re.compile( r'\s*(?:\s*(\d+(?:\.\d+)?)([{0}]))\s*'.format( ''.join( DURATION_FACTORS.keys() ) ) )


def load_worklog( when ):
	worklog = Worklog( when )
	return worklog



def now():
    """datetime.now() with seconds zeroed out"""
    now = datetime.now()
    return now.replace( second = 0, microsecond = 0 )



def _get_cls( cls_name ):
	return {'Task': Task, 'GoHome': GoHome}[cls_name]



class Task:

    def __init__( self, start, ticket, description, logged ):
        self.start = start
        self.ticket = ticket
        self.description = description.strip()
		self.logged = logged

    def include_in_rollup(self):
        return self.description.lower() not in ("lunch", "break" )

    def __getstate__( self ):
        return { '__klass__': self.__class__.__name__, 'start': self.start, 'ticket': self.ticket, 'description': self.description, 'logged': self.logged }

    def __setstate__( self, state ):
        state.pop('__klass__')
        self.__dict__.update( state )




class GoHome:

    def __init__( self, start, *unused ):
        self.start = start

	def __getstate__( self ):
		return { '__klass__': self.__class__.__name__, 'start': self.start }

	def __setstate__( self, state ):
		self.start = state.get( 'start' )



class DummyRightNow( Task ):

    def __init__( self ):
        Task.__init__( start = now(), ticket = '', description = '' )



class Worklog( MutableSequence ):

    def __init__( self, when = None ):
        if when is None:
            self.when = date.today()
        elif isinstance(when, str):
            if re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}", when):
                self.when = datetime.strptime(when, "%Y-%m-%d").date()
            else:
                self.when = datetime.today()+timedelta(days=int(when))

    def __getitem__(self, index ):
        return self.store[index]

    def __setitem__(self, index, value ):
        self.store[index] = value

    def __delitem__(self, index ):
        del self.store[index]

    def __len__(self):
        return len(self.store)

    def insert(self, task):
        self.store.append(task)
        self.store.sort( key=lambda t: t.start )

    def pairwise(self):
        offset = self.store[1:]
        offset.append( DummyRightNow() )
        return zip(self.store, offset)


	def load( self ):
		filename = '{}.json'.format(worklog.when)
		with open(filename, 'rb') as file_handle:
			state = json.load( file_handle )
		self.__setstate__( state )


	def dump( self ):
		filename = '{}.json'.format(worklog.when)
		with open(filename, 'wb') as file_handle:
			json.dump( self.__getstate__(), file_handle )


	def __getstate__( self ):
		state = []
		for item in self.store:
			state.append( item.__getstate__() )
		return state


	def __setstate__( self, state ):
		for item in state:
			cls = _get_cls( item['__klass__'] )
			self.store.append( cls().__setstate__( item ) )
