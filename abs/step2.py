
import sys
from oauth2client.client import flow_from_clientsecrets
flow = flow_from_clientsecrets('client_secrets.json','https://www.googleapis.com/auth/drive.file')
flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
credentials = flow.step2_exchange(sys.argv[1])
with open('credentials.json', 'w') as ff: ff.write(credentials.to_json())

