
import argparse
import os
import textwrap

from worklog import actions
from worklog import color
from worklog.alias import handle_alias, BadAlias
from worklog.config import ConfigFile
from worklog.state import Abort


def handle_arguments( args, config ):
	action = args.alias or args.start or args.stop or args.resume or args.report or args.upload
	print('handle_arguments', action)
	switch = {
		'--start': actions.start,
		'--stop': actions.stop,
		'--resume': actions.resume,
		'--report': actions.report,
		'--upload': actions.upload
	}
	handler = switch.get( action )
	if not handler:
		args = handle_alias( args, config )
		handle_arguments( args, config )
	else:
		handler( args, config )



def main():
	parser = argparse.ArgumentParser(
		description = "manage and report time allocation",
		formatter_class = argparse.RawDescriptionHelpFormatter,
		epilog = textwrap.dedent("""
			DURATIONs
			  Spans of time can be provided in a concise format, a series of integers or
			  floats each appended with a unit: d, h, m. Whitespace between each component
			  is optional. Fractions less than 1 require a leading 0.

			  Note that a day is 8 hours.

			  Examples:
				15m
				0.5h
				1.5h
				1d 4.5h
				1d 4h 30m
				1d4h30m

			  Note that, while whitespace is optional, if you do specify a duration on the
			  command line and it includes whitespace, you"ll have to quote it.

			DATEs
			  Dates should be provided in the form YYYY-MM-DD.

			TIMEs
			  Times should be provided in the form HH:MM. All times used, including "now",
			  have their seconds zeroed out. All times provided on the command line are
			  assumed to occur today.

			Config File:
			  ~/.worklog/config.json - Can be created to store username and password to avoid
			  being prompted to type in your credentials for Jira authentication.

			  Example File:
				{ "username" : "jsmith" }

			  WARNING:
				Uploading multiple times in one calendar day will cause inconsistencies with time tracking
				on the server side.
		""" ),
		)
	parser.add_argument( '--day', '-d', help = 'manage the worklog for DATE, defaults to today' )

	start_blurb = 'start a new task, closing the currently open task if any'
	parser.add_argument( '--start', help = start_blurb )
	parser.add_argument( '--ago', metavar = 'DURATION', help = 'start the task DURATION time ago, instead of now' )
	parser.add_argument( '--at', metavar = 'TIME', help = 'start the task at TIME, instead of now' )
	parser.add_argument( '-t', '--ticket', metavar = 'TICKET', help = 'the TICKET associated with the task' )
	parser.add_argument( 'description', metavar = 'DESCRIPTION', nargs = argparse.REMAINDER, help = "specify the task's description on the command line" )

	resume_blurb = 'like start, but reuse the description from a previous task in this worklog by seleting it from a list'
	parser.add_argument( '--resume', help = resume_blurb )

	stop_blurb = 'close the currently open task'
	parser.add_argument( '--stop', help = stop_blurb )

	report_blurb = 'report the current state of the worklog'
	parser.add_argument( '--report', help = report_blurb )

	upload_blurb = 'uploads worklog time to jira'
	parser.add_argument( '--upload', default=None, action='store', help = upload_blurb )

	parser.add_argument( 'alias', nargs='+', default = [], help = 'take aliases as commands' )

	print('parsing')
	args = parser.parse_args()
	print('parsed')
	config_path = os.path.expanduser( '~/.worklog/config.json' )
	config = ConfigFile( config_path )
	color.ENABLED = config.features.colorize
	try:
		handle_arguments( args, config )
	except BadAlias:
		print('Invalid command or alias.')
		parser.print_help()



if __name__ == "__main__":
	try:
		main()
	except Abort:
		pass
