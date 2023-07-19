import os
import rollbar

rollbar.init(
  # access_token=os.environ["ROLLBAR_TOKEN"],
  access_token='***REMOVED***c',
  environment='testenv',
  code_version='1.0',
)
# rollbar.payload_data['custom'] = {'slack': {'channel': '#errors'}}
rollbar.report_message('fdwq')
rollbar.report_message('Rollbar is configured correctly', 'info')