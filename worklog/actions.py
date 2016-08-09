import os
import textwrap

from worklog.jira import log_to_jira
from worklog.report import Report
from worklog.state import Worklog, Task, GoHome, Abort
from worklog.time_utils import resolve_at_or_ago



def start( args, config ):
	with Worklog( when = args.day, config = config ) as worklog:
		start = resolve_at_or_ago( args, date = worklog.when )
		ticket = args.ticket
		description = " ".join(args.description)
		while len(description.strip()) == 0:
			try:
				description = input("Task description: ")
			except KeyboardInterrupt:
				raise Abort()
			except EOFError:
				raise Abort()
		worklog.insert( Task( start = start, ticket = ticket, description = description, logged = False, config = config ) )
	return Report( worklog, config )



def resume( args, config ):
	with Worklog( when = args.day, config = config ) as worklog:
		start = resolve_at_or_ago( args, date = worklog.when )
		descriptions = list()
		for description in reversed([ task.description for task in worklog if isinstance(task, Task) ]):
			if description not in descriptions:
				descriptions.append( description )
		# when using resume, it means we're no longer working on the description that is now the first
		# item in this list, because of how we've sorted it. It is quite inconvenient for the first
		# choice to be the one we know for sure the user won't pick, bump it to the end of the line
		most_recent_description = descriptions.pop( 0 )
		descriptions.append( most_recent_description )
		for idx, description in enumerate( descriptions ):
			print( '[{:d}] {}'.format( idx, description ) )
		description = None
		while description is None:
			try:
				idx = int(input("Which description: "))
				description = descriptions[idx]
				for task in worklog:
					if task.description == description:
						ticket = task.ticket
			except KeyboardInterrupt:
				raise Abort()
			except EOFError:
				raise Abort()
			except ( ValueError, IndexError ):
				print( 'Must be an integer between 0 and {:d}'.format( len( descriptions ) ) )
		worklog.insert( Task( start = start, ticket = ticket, description = description, logged = True, config = config ) )
	return Report( worklog, config )



def stop( args, config ):
	with Worklog( when = args.day, config = config ) as worklog:
		worklog.insert( GoHome( start = resolve_at_or_ago( args, date = worklog.when ) ) )
	return Report( worklog, config )



def report( args, config ):
	with Worklog( when = args.day, config = config ) as worklog:
		report = Report( worklog, config )
	return report



def upload( args, config ):
	with Worklog( when = args.day, config = config ) as worklog:
		log_to_jira( worklog, config )
