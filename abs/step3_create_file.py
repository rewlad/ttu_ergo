
def http_and_service():
    import httplib2
    from apiclient.discovery import build
    from oauth2client.client import Credentials

    with open('credentials.json','r') as ff: 
        credentials = Credentials.new_from_json(ff.read())
    http = httplib2.Http()
    http = credentials.authorize(http)
    return http, build('drive', 'v2', http=http)

http, service = http_and_service()
service.files().insert(body={'mimeType':'text/csv','title':'test'},convert=True).execute()
