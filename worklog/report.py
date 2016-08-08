
from datetime import timedelta

import color
from state import GoHome, DummyRightNow
from time_utils import Duration

class Report:

	def __init__(self):


	def __call__( worklog, config ):
		lines = []
		self.total = timedelta( seconds = 0 )
		self._rollup = dict()

	def header(self):
		return '{} {}'.format(
				color.bold( 'Worklog Report for' ),
				color.purple( self.worklog.when.strftime( '%F' ), bold = True )
				)

	def _make_entries( self ):
		if len( self.worklog ) == 0:
			return '\tno entries'
		else:
			for task, next_task in worklog.pairwise():
				if isinstance( task, GoHome ):
					continue
				if isinstance( next_task, DummyRightNow ):
					colorize_end_time = color.yellow
				else:
					colorize_end_time = color.green
				delta = next_task.start - task.start
				if task.include_in_rollup():
					self.total += delta
					if task.description not in rollup:
						self._rollup[task.description] = delta
					else:
						self._rollup[task.description] += delta
				if delta > timedelta():
					if not task.logged:
						task.logged = False
					self._add_entry(task, next_task)

	def _add_entry( self, task, next_task ):
		start_time = color.green( task.start.strftime( '%H:%M' ) )
		start_end_delimiter = color.black( '-', intense = True )
		end_time = colorize_end_time( next_task.start.strftime( '%H:%M' ) )
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

	def footer( self ):
		return '\n\t{!s:>7}  {}'.format(
				Duration( total ).colorized( underline = True ),
				color.colorize( 'TOTAL', bold = True, underline = True )
				)

	def rollup(self):
		lines = []
		for key in sorted( rollup.keys() ):
			lines.append( '	{!s:>7}  {}'.format(
				Duration( rollup[key] ).colorized(),
				color.bold( key )
			) )
		return '\n'.join( lines )
