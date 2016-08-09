
from datetime import datetime

from getpass import getpass
from jira.client import JIRA

from worklog.state import GoHome
from worklog.time_utils import Duration



def auth_jira(config):
	if config.jira.auth_type and config.jira.auth_type == 'oauth':
		return auth_jira_oauth( config )
	else:
		return auth_jira_basic( config )


def auth_jira_basic(config):
	options = { 'server': config.jira.server or  input( '\nJira Server: ' ) }
	username = config.jira.username or input( '\nJira Username: ' )
	password = config.jira.password or getpass()
	auth = ( username, password )
	jira = JIRA( options, basic_auth = auth )
	return jira



def auth_jira_oauth(config):
	with open(config.jira.oauth_pem_filename) as pem:
		pem_data = pem.read()

	oauth_dict = {
		'access_token': config.jira.oauth_token,
		'access_token_secret': config.jira.oauth_token_secret,
		'consumer_key': config.jira.oauth_consumer_key,
		'key_cert': pem_data 
	}

	options = { 'server': config.jira.server or  input( '\nJira Server: ' ) }
	username = config.jira.username or input( '\nJira Username: ' )
	jira = JIRA( options = options, oauth = oauth_dict )
	return jira



def log_to_jira( worklog, config ):
	jira = auth_jira( config )
	print( 'Logging work ...' )
	if len( worklog ) > 0:
		for task, next_task in worklog.pairwise():
			if isinstance( task, GoHome ):
				continue
			if task.ticket and not task.logged:
				duration = Duration( delta = next_task.start - task.start )
				if not duration.seconds:
					continue
				started = '{}-{}-{}T{}:{}:00.000-0400'.format(
					task.start.year,
					task.start.month,
					task.start.day,
					task.start.hour,
					task.start.minute
				)
				print('ticket', task.ticket )
				ticket = jira.issue( task.ticket )
				print( '\nLogging {} to ticket {}'.format( duration, ticket ) )
				jira.add_worklog(
					issue = ticket,
					timeSpent = str( duration ),
					started = datetime.strptime( started, '%Y-%m-%dT%H:%M:%S.000%z' )
				)
				task.logged = True
	print( 'Done.' )
