
def http_and_service():
    import httplib2
    from apiclient.discovery import build
    from oauth2client.client import Credentials

    with open('credentials.json','r') as ff: 
        credentials = Credentials.new_from_json(ff.read())
    http = httplib2.Http()
    http = credentials.authorize(http)
    return http, build('drive', 'v2', http=http)

#from pprint import pprint
import re, os
http, service = http_and_service()
for file in service.files().list().execute()['items']:
    if 'downloadUrl' in file: print file['downloadUrl']
    if 'exportLinks' in file:
        url = file['exportLinks']['application/x-vnd.oasis.opendocument.spreadsheet']
        resp, content = http.request(url)
        print resp.status, url
        if resp.status==200:
            fn = 'docs/' + re.sub('\W','_',file['title']) + '.ods'
            with open(fn,'w') as ff: ff.write(content)
            
#http://wiki.openoffice.org/wiki/Documentation/DevGuide/Spreadsheets/Filter_Options
#not tried: http://www.linuxjournal.com/content/convert-spreadsheets-csv-files-python-and-pyuno-part-1v2
#not tried: http://www.logilab.org/blogentry/6130
os.system('unoconv -f csv -i "44,34,utf-8,1" docs/*.ods')
