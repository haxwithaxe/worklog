
from datetime import timedelta

from worklog import color
from worklog.state import GoHome, DummyRightNow
from worklog.time_utils import Duration

class Report:


	def __init__( self, worklog, config ):
		self._entries = []
		self._rollup = dict()
		self.worklog = worklog
		self.total = timedelta( seconds = 0 )
		self._make_entries()

	@property
	def header( self ):
		return '{} {}'.format(
				color.bold( 'Worklog Report for' ),
				color.purple( self.worklog.when.strftime( '%F' ), bold = True )
				)

	@property
	def entries( self ):
		return '\n'.join( self._entries )


	def _make_entries( self ):
		if len( self.worklog ) == 0:
			return '\tno entries'
		else:
			for task, next_task in self.worklog.pairwise():
				if isinstance( task, GoHome ):
					continue
				if isinstance( next_task, DummyRightNow ):
					colorize_end_time = color.yellow
				else:
					colorize_end_time = color.green
				delta = next_task.start - task.start
				if task.include_in_rollup():
					self.total += delta
					if task.description not in self._rollup:
						self._rollup[task.description] = delta
					else:
						self._rollup[task.description] += delta
				if delta > timedelta():
					if not task.logged:
						task.logged = False
					self._add_entry( delta, task, next_task )

	def _add_entry( self, delta, task, next_task ):
		start_time = color.green( task.start.strftime( '%H:%M' ) )
		start_end_delimiter = color.black( '-', intense = True )
		end_time = self.colorize_end_time( next_task )
		duration_open = color.black( '(', intense = True )
		duration = Duration( delta ).colorized()
		duration_close = color.black( ')', intense = True )
		is_logged = {True: color.green('*'), False: color.red('*')}[task.logged]
		entry = '	{:5s} {} {:5s} {}{!s:>7}{} {} {}  {}'.format(
				start_time,
				start_end_delimiter,
				end_time,
				duration_open,
				duration,
				duration_close,
				is_logged,
				task.ticket,
				task.description
				)
		self._entries.append( entry )


	@property
	def footer( self ):
		return '\n\t{!s:>7}  {}'.format(
				Duration( self.total ).colorized( underline = True ),
				color.colorize( 'TOTAL', bold = True, underline = True )
				)


	@property
	def rollup( self ):
		lines = []
		for key in sorted( self._rollup.keys() ):
			lines.append( '	{!s:>7}  {}'.format(
				Duration( self._rollup[key] ).colorized(),
				color.bold( key )
			) )
		return '\n'.join( lines )


	def colorize_end_time( self, next_task ):
		colorizer = color.green
		if isinstance( next_task, DummyRightNow ):
			colorizer = color.yellow
		return colorizer( next_task.start.strftime( '%H:%M' ) )


	def __str__( self ):
		return '\n'.join( (self.header, self.entries, self.footer, self.rollup) )
