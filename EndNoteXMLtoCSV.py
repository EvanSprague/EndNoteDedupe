#*****************___CML to CSV file for Dedupe testing___**********************
import os
import dedupe
import easygui
import xml.etree.ElementTree as et
import csv
# from unidecode import unidecode

#*******************************************************************************
#*****************File Locations************************************************
#*******************************************************************************
#Utilize easyGUI to select a file location.... later
# file_path = easygui.diropenbox()
base_path = os.path.dirname(os.path.realpath(__file__))
#xml_outputfile is the output file
#xml_file = os.path.join(base_path, "PivotTableProject_2019.xml")
xml_file = os.path.join(base_path, "demo library 9 23 2019_compressed_full.xml")
# xml_file = os.path.join(base_path, "PivotTableProject_2019_Subset.xml")
xml_outputfile = os.path.join(base_path, "XMLOutput_test1.xml")
#csv_outputfile = os.path.join(base_path, "XMLtoCSV_test1.csv")
csv_outputfile = os.path.join(base_path, "DeDupValidation2019.csv")

#*******************************************************************************
#*****************Preprocess XML File to address Unicode Errors*****************
#*******************************************************************************



#*******************************************************************************
#***************** Create a CVS file with headers*******************************
#*******************************************************************************
with open(csv_outputfile, mode='w', newline='') as csv_file:
    # csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL, encoding='utf-8')
    csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv_writer.writerow(['ENID', 'Authors', 'Title', 'Journal', 'Year', 'Vol', 'Issue', 'Pages', 'DOI', 'ISSN/ISBN','Search', 'Database', 'Abst'])
    # csv_writer.writerow(["ENID", "Authors", "Title", "Journal", "Year", "Vol", "Issue", "Pages", "DOI"])
csv_file.close()

#*******************************************************************************
#*****************XML File reading a parsing************************************
#*******************************************************************************
print("One Moment. Parsing XML file...")
#The following reads parts of the XML file's into memory
tree = et.parse(xml_file)
root = tree.getroot()
rec = root.findall('.records/record')

#Var to track the number of records script looks at
numrec = 0

#The follwing reads relevent parts of the XML file

for article in rec:
    #Var for counting authors in a citation
    authCount = 0
    ENID = article.find('.foreign-keys/key').text
    print("EndNote ID: ", ENID)
    authorList = []
    authorStr = ""
    try:
        for authors in article.findall('.contributors/authors/author'):
            #Places each author into a list for dedupe (authorList)
            #   and a uniform string for the CSV (authorStr)
            auth = authors.find('.style').text
            authorList.append(auth)
            try:
                authL, sep, authF = auth.partition(',')
                try:
                    authF = authF[1]
                    auth = authL + " " + authF
                except IndexError:
                    auth = authL
                    pass
            except TypeError:
                pass
            authCount = authCount+1
            try:
                authorStr += auth + "; "
            except TypeError:
                pass
            # print(auth)
            # print(authCount)
        # print(authorList)
        # print(authorStr)
    except AttributeError:
        authorStr = ""
        pass
    if article.find('.titles/title') is not None:
        # title = article.find('.titles/title/style').text.encode('utf-8')
        title = article.find('.titles/title/style').text
        # print(title)
    else:
        title = ""
    if article.find('.dates') is not None:
        year = article.find('.dates/year/style').text
        # print(year)
    else:
        year = ""

#New
    if article.find('.isbn') is not None:
        ISSN = article.find('.isbn/style').text
        # print(ISSN)
    else:
        ISSN = ""
    if article.find('.abstract') is not None:
        abs = article.find('.abstract/style').text
        # print(abs)
    else:
        abs = ""
#END NEW

    if article.find('.titles/secondary-title') is not None:
        journal = article.find('.titles/secondary-title/style').text
        # print(journal)
    else:
        journal = ""
    if article.find('.pages') is not None:
        pages = article.find('.pages/style').text
        # print(pages)
    else:
        pages = ""
    if article.find('.volume') is not None:
        volume = article.find('.volume/style').text
        # print(volume)
    else:
        volume = ""
    if article.find('.number') is not None:
        issue = article.find('.number/style').text
        # print(issue)
    else:
        issue = ""
    if article.find('.electronic-resource-num') is not None:
        DOI = article.find('.electronic-resource-num/style').text
        # print(DOI)
    else:
        DOI = ""
    if article.find('.custom3') is not None:
        search = article.find('.custom3/style').text
        # print(search)
    else:
        search = ""
    if article.find('.custom4') is not None:
        database = article.find('.custom4/style').text
        # print(database)
    else:
        database = ""
    numrec = numrec+1
    print("--- Analysing Citation Number: ", numrec , "---")
    #The following creates a list of all the vars for a CSV row
    row = [ENID, authorStr, title, journal, year, volume, issue, pages, DOI, ISSN, search, database, abs]
#***************** Append CSV file with new line from XML file******************
    with open(csv_outputfile, 'a', newline='', encoding='utf-8') as csv_file:
        # csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL, encoding='utf-8')
        # csv_writer.writerow(row)

        writer =  csv.writer(csv_file)
        writer.writerow(row)

        # writer.writerows([row.keys()])
        # for row in zip(*row.values()):
        #     row = [s.encode('utf-8' for s in row)]
        #     writer.writerow(row)
    csv_file.close()

#*******************************************************************************
#*****************Final Printing Messages***************************************
#*******************************************************************************
print("No more citations")
print()
print("Number of Records Examined: ", numrec)
