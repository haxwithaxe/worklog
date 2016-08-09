
from collections.abc import MutableSequence
from datetime import date, datetime, timedelta
import json
import os
import re
import pprint


from worklog.time_utils import now


class Abort( Exception ):
	pass


def _get_cls( cls_name ):
	return { 'Task': Task, 'GoHome': GoHome }[cls_name]



class Task:

	
	def __init__( self, start = None, ticket = False, description = None, logged = None, config = None ):
		self.config = config
		self.start = start or now()
		self.ticket = ticket
		self.description = (description or '').strip()
		self.logged = logged
		if self.config and self.config.features.get( 'scrape-ticket' ) and self.description and not self.ticket:
			self._pull_ticket_from_description()

	
	def include_in_rollup(self):
		return self.description.lower() not in ( "lunch", "break" )

	def _pull_ticket_from_description( self ):
		if not self.description:
			return None
		ticket_re = re.compile( '({})-[0-9]+'.format( '|'.join( self.config.jira.get( 'projects', [] ) ) ) )
		re_match = ticket_re.search( self.description )
		if re_match:
			self.ticket = re_match.group()

	
	def __getstate__( self ):
		start = self._start_to_dict()
		return { '__klass__': self.__class__.__name__, 'start': start, 'ticket': self.ticket, 'description': self.description, 'logged': self.logged }

	
	def __setstate__( self, state ):
		state.pop('__klass__')
		self._start_from_dict( state.pop('start') )
		self.__dict__.update( state )

	
	def _start_to_dict( self ):
		if not self.start:
			return None
		return {
			"__klass__": "datetime",
			"year": self.start.year,
			"month": self.start.month,
			"day": self.start.day,
			"hour": self.start.hour,
			"minute": self.start.minute,
			"second": self.start.second,
			"microsecond": self.start.microsecond
		}

	
	def _start_from_dict( self, datetime_dict ):
		if not datetime_dict:
			return None
		datetime_dict.pop('__klass__')
		year = datetime_dict.pop( 'year' )
		month = datetime_dict.pop( 'month' )
		day = datetime_dict.pop( 'day' )
		self.start = datetime( year, month, day, **datetime_dict )

	
	def __repr__(self):
		return pprint.pformat(self.__getstate__())



class GoHome( Task ):

	
	def __getstate__( self ):
		return { '__klass__': self.__class__.__name__, 'start': self._start_to_dict() }

	
	def __setstate__( self, state ):
		self._start_from_dict( state['start'] )



class DummyRightNow( Task ):

	def __init__( self ):
		Task.__init__( self, start = now(), ticket = '', description = '', logged = True, config = None )

	def __getstate__( self ):
		pass

	def __setstate__( self, state ):
		pass


class Worklog( MutableSequence ):

	def __init__( self, when = None, config = None ):
		self.store = []
		self.config = config
		if when is None:
			self.when = date.today()
		elif isinstance(when, str):
			if re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}", when):
				self.when = datetime.strptime(when, "%Y-%m-%d").date()
			else:
				self.when = datetime.today()+timedelta( days=int(when) )
		filename = self.config.state.store_filename_format.format( self.when.strftime( self.config.state.when_format ) )
		self.filename = os.path.expandvars( os.path.expanduser( filename ) )

	def __enter__(self):
		self.load()
		return self

	def __exit__(self, exc_type, exc_value, exc_traceback ):
		if not exc_type:
			self.dump()

	def __getitem__(self, index ):
		return self.store[index]

	def __setitem__(self, index, value ):
		self.store[index] = value

	def __delitem__(self, index ):
		del self.store[index]

	def __len__(self):
		return len(self.store)

	def insert(self, task):
		if task:
			self.store.append(task)
			self.store = [ x for x in self.store if x ]
			self.store.sort( key=lambda t: t.start )

	def pairwise(self):
		offset = self.store[1:]
		offset.append( DummyRightNow() )
		return zip(self.store, offset)


	def load( self ):
		if not os.path.exists( self.filename ):
			return None
		with open(self.filename, 'r') as file_handle:
			state = json.load( file_handle )
		self.__setstate__( state )


	def dump( self ):
		state = self.__getstate__()
		if state:
			with open(self.filename, 'w') as file_handle:
				json.dump( state, file_handle )


	def __getstate__( self ):
		state = []
		for item in self.store:
			if item:
				state.append( item.__getstate__() )
		return state


	def __setstate__( self, state ):
		for item in state:
			cls = _get_cls( item['__klass__'] )()
			cls.__setstate__( item )
			self.store.append( cls )

	def __repr__( self ):
		return pprint.pformat( [ x.__getstate__() for x in self.store ] )
