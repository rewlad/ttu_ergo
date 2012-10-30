
import os
import csv
import json

pre = './docs'

for fn in os.listdir(pre):
    if not fn.endswith('.csv'): continue
    with open(pre+'/'+fn,'r') as csvfile:
        with open(pre+'/'+fn+'.json','w') as jsonfile:
            reader = csv.reader(csvfile,delimiter=',',quotechar='"')
            json.dump({'data':list(reader)},jsonfile)
