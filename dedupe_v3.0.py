import os #Filing pathing
import csv #CSV reading and wrting
import re #Used to normalze text
import logging #provides more inforamtion information use with -v
import optparse #Allows for more information to be displayed in cmd line
# import xml.etree.ElementTree as et #Used to minipulate XML files
# import easygui #Used to create user interface
import dedupe #Series of algerithums that locate duplicate items
from unidecode import unidecode #Used so program can read utf-8 text
import unicodedata #Used to normalize utf-8 text

"""
***Requirements***
C++  --  https://visualstudio.microsoft.com/visual-cpp-build-tools/
Be sure to select V14
"""

"""
Adapted from:
Parts of the following code was adapted from dedupe.oi - dedupe-examples
   https://dedupeio.github.io/dedupe-examples/docs/csv_example.html (3/21/2019)

Dedupe Package Documentation:
   https://media.readthedocs.org/pdf/dedupe/latest/dedupe.pdf

The following Code

"""

#*******************************************************************************
#*****************File Locations************************************************
#*******************************************************************************
#Utilize easyGUI to select a file location.... later
# file_path = easygui.diropenbox()
base_path = os.path.dirname(os.path.realpath(__file__))
#xml_outputfile is the output file
xml_file = os.path.join(base_path, "PivotTableProject_2019.xml")
# xml_file = os.path.join(base_path, "PivotTableProject_2019_Subset.xml")
xml_outputfile = os.path.join(base_path, "XMLOutput_test1.xml")#Not in use
csv_imputfile = os.path.join(base_path, "DeDupValidation2019.csv")
csv_outputfile = os.path.join(base_path, "dedupe_v3.0.csv")
settings_file = os.path.join(base_path, "learned_settings_v3.0")
training_file = os.path.join(base_path, "training_v3.0.json")

#*******************************************************************************
#*****************Verbose Logging***********************************************
#*******************************************************************************
#If I understand this correctly, this will provide more detailed debug errors

optp = optparse.OptionParser()
optp.add_option('-v', '--verbose', dest='verbose', action='count',
                help='Increase verbosity (specify multiple times for more)'
                )
(opts, args) = optp.parse_args()
log_level = logging.WARNING
if opts.verbose:
    if opts.verbose == 1:
        log_level = logging.INFO
    elif opts.verbose >= 2:
        log_level = logging.DEBUG
logging.getLogger().setLevel(log_level)

#*******************************************************************************
#*****************Data Cleaning and setup***************************************
#*******************************************************************************
def preProcess(column):

    try : # python 2/3 string differences
        column = column.decode('utf8')
    except AttributeError:
        pass
    column = unidecode(column)
    unicodedata.normalize('NFKD', column).encode('ascii', 'ignore')
    column = re.sub('  +', ' ', column)
    column = re.sub('\n', ' ', column)
    column = column.strip().strip('"').strip("'").lower().strip()
    if not column:
        column = None
    return column

def readData(filename):

    data_d = {}
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            clean_row = [(k, preProcess(v)) for (k, v) in row.items()]
            row_id = int(row['ENID'])
            data_d[row_id] = dict(clean_row)

    return data_d

print('importing data ...')
data_d = readData(csv_imputfile)

if os.path.exists(settings_file):
    print('reading from', settings_file)
    with open(settings_file, 'rb') as f:
        deduper = dedupe.StaticDedupe(f)
else:

#*******************************************************************************
#*****************Training******************************************************
#*******************************************************************************
#['ENID', 'Authors', 'Title', 'Journal', 'Year', 'Vol', 'Issue', 'Pages', 'DOI', 'Search', 'Database']
    fields = [
        {'field' : 'Authors', 'type': 'String', 'has missing' : True},
        {'field' : 'Title', 'type': 'String', 'has missing' : True},
        {'field' : 'Journal', 'type': 'String', 'has missing' : True},
        {'field' : 'Year', 'type': 'Exact', 'has missing' : True},
        {'field' : 'Vol', 'type': 'Exact', 'has missing' : True},
        {'field' : 'Issue', 'type': 'ShortString', 'has missing' : True},
        {'field' : 'Pages', 'type': 'ShortString', 'has missing' : True},
        {'field' : 'DOI', 'type': 'Exact', 'has missing' : True},
        {'field' : 'ISSN/ISBN', 'type': 'Exact', 'has missing' : True},
        {'field' : 'Abst', 'type': 'Text', 'has missing' : True},
        ]

    deduper = dedupe.Dedupe(fields)

    deduper.sample(data_d, 15000)

    if os.path.exists(training_file):
        print('Reading labeled examples from ', training_file)
        with open(training_file, 'rt') as f:
            deduper.readTraining(f)

#*******************************************************************************
#*****************Active Learning***********************************************
#*******************************************************************************

    print('Starting active labeling...')

    dedupe.consoleLabel(deduper)

    deduper.train()

    with open(training_file, 'w') as tf:
        deduper.writeTraining(tf)

    with open(settings_file, 'wb') as sf:
        deduper.writeSettings(sf)

threshold = deduper.threshold(data_d, recall_weight=1)

#*******************************************************************************
#*****************Clustering****************************************************
#*******************************************************************************

print('clustering...')
clustered_dupes = deduper.match(data_d, threshold)

print('# duplicate sets', len(clustered_dupes))

#*******************************************************************************
#*****************Writing Results***********************************************
#*******************************************************************************

cluster_membership = {}
cluster_id = 0
for (cluster_id, cluster) in enumerate(clustered_dupes):
    id_set, scores = cluster
    cluster_d = [data_d[c] for c in id_set]
    canonical_rep = dedupe.canonicalize(cluster_d)
    for record_id, score in zip(id_set, scores):
        cluster_membership[record_id] = {
            "cluster id" : cluster_id,
            "canonical representation" : canonical_rep,
            "confidence": score
        }

singleton_id = cluster_id + 1

with open(csv_outputfile, 'wt', newline='', encoding='utf-8') as f_output, open(csv_imputfile, encoding='utf-8') as f_input:
    writer = csv.writer(f_output)
    reader = csv.reader(f_input)

    heading_row = next(reader)
    heading_row.insert(0, 'confidence_score')
    heading_row.insert(0, 'Cluster ID')
    canonical_keys = canonical_rep.keys()
    for key in canonical_keys:
        heading_row.append('canonical_' + key)

    writer.writerow(heading_row)

    for row in reader:
        row_id = int(row[0])
        if row_id in cluster_membership:
            cluster_id = cluster_membership[row_id]["cluster id"]
            canonical_rep = cluster_membership[row_id]["canonical representation"]
            row.insert(0, cluster_membership[row_id]['confidence'])
            row.insert(0, cluster_id)
            for key in canonical_keys:
                row.append(canonical_rep[key].encode('utf8'))
        else:
            row.insert(0, None)
            row.insert(0, singleton_id)
            singleton_id += 1
            for key in canonical_keys:
                row.append(None)
        writer.writerow(row)

#*******************************************************************************
#*****************Final Printing Messages***************************************
#*******************************************************************************
print()
print("Complete")
