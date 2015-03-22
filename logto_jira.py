import jira.client as jirac

from wlconfig import ConfigException

class JiraLog:
    """

    Configs:
    [jira]
    oauth...
    default_issue=<ticket>
    default_project=

    """
    def __init__(self, config):
        self.conf = config
        self.oauth_dict = None
        self._oauth()
        self.default_issue = self.conf.jira_default_issue
        self.jira = jirac(options={"server": self.conf.jira_server}, oauth=oauth_dict)

    def _oauth(self):
        """ initialize an OAuth session. """
        try:
        key_cert_data = None
        with open(self.conf.jira_key_cert_file, 'r') as key_cert_file:
            key_cert_data = key_cert_file.read()

        self.oauth_dict = {
            'access_token': self.conf.jira_oauth_token,
            'access_token_secret': self.conf.jira_oauth_secret,
            'consumer_key': self.conf.jira_oauth_consumer_key,
            'key_cert': key_cert_data
        }
        except AttributeError as excp:
            raise ConfigException("OAuth information ([jira]->(oauth_token, oauth_secret, oauth_consumer_key, key_cert_file)) needs to be included in the configuration file. The values for the config items can be obtained by using jirashell which is part of python-jira.")

    def tickets(self, owner=O_ME, state=ticket_state.INPROGRESS, project=None, sprint=None):
        """ List tickets matching the criteria passed as kwargs. """ 
        pass

    def worklog(self, start=TODAY, stop=TOMORROW, project=None, sprint=None, ticket=None):
        """ List work logged in the time starting `start` and ending `stop` that matches the attributes passed as kwargs """
        pass

    def submit_work(self, **kwargs):
        """ Shim for jira.client.add_work_log().
        Documentation for jira.client.add_work_log():
            Add a new worklog entry on an issue and return a Resource for it.
            Parameters: 
                issue – the issue to add the worklog to
                timeSpent – a worklog entry with this amount of time spent, e.g. “2d”
                adjustEstimate – (optional) allows the user to provide specific instructions to update the remaining time estimate of the issue. The value can either be new, leave, manual or auto (default).
                newEstimate – the new value for the remaining estimate field. e.g. “2d”
                reduceBy – the amount to reduce the remaining estimate by e.g. “2d”
                started – Moment when the work is logged, if not specified will default to now
                comment – optional worklog comment
        """
        pass

    def submit_log(self, *entries):
        """ Submit a local copy of logged work """
        # for each entry
        #   parse entry
        #   submit_work()
        pass

    
