
from oauth2client.client import flow_from_clientsecrets
flow = flow_from_clientsecrets('client_secrets.json','https://www.googleapis.com/auth/drive.file')
print flow.step1_get_authorize_url('urn:ietf:wg:oauth:2.0:oob')
