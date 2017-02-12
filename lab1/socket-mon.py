#!/usr/bin/python
import collections
import psutil
import csv
import sys
process_list = psutil.net_connections(kind='tcp')
csv_writer = csv.writer(sys.stdout, quotechar='"', quoting=csv.QUOTE_ALL)
csv_writer.writerow(('pid', 'laddr','raddr','status'))
counts = collections.Counter(t[6] for t in process_list)
sorted_list = sorted(process_list, key=lambda t:counts[t[6]], reverse= True)
for listrow in sorted_list:
    if all(listrow):
        csv_writer.writerow((listrow[6],str(listrow[3][0])+"@"+ str(listrow[3][1]), str(listrow[4][0])+"@"+ str(listrow[4][1]),listrow[5]))



