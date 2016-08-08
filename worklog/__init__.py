
from datetime import timedelta
import os
import textwrap

import color
from config import ConfigFile
from state import Worklog, Task, GoHome, DummyRightNow, Abort



def report( worklog, config ):
	lines = []
	total = timedelta( seconds = 0 )
	rollup = dict()
	lines.append( '{} {}'.format(
		color.bold( 'Worklog Report for' ),
		color.purple( worklog.when.strftime( '%F' ), bold = True )
	) )
	if len( worklog ) == 0:
		lines.append( '	no entries' )
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
				total += delta
				if task.description not in rollup:
					rollup[task.description] = delta
				else:
					rollup[task.description] += delta
			if delta > timedelta():
				if not task.logged:
					task.logged = False
				lines.append( '	{:5s} {} {:5s} {}{!s:>7}{} {} {}  {}'.format(
					color.green( task.start.strftime( '%H:%M' ) ),
					color.black( '-', intense = True ),
					colorize_end_time( next_task.start.strftime( '%H:%M' ) ),
					color.black( '(', intense = True ),
					Duration( delta ).colorized(),
					color.black( ')', intense = True ),
					{True: color.green('*'), False: color.red('*')}[task.logged],
					task.ticket,
					task.description
				) )

		lines.append( '\n	{!s:>7}  {}'.format(
			Duration( total ).colorized( underline = True ),
			color.colorize( 'TOTAL', bold = True, underline = True )
		) )
		for key in sorted( rollup.keys() ):
			lines.append( '	{!s:>7}  {}'.format(
				Duration( rollup[key] ).colorized(),
				color.bold( key )
			) )
		return '\n'.join( lines )
