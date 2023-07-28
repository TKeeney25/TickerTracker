import requests
import csv
headers = {}
params = {'e': 'USMF'}
tracked_funds = set()
with requests.get('https://apps.csidata.com/factsheets.php?type=stock&format=csv&exchangeid=MUTUAL', stream=True) as response:
    reader = csv.reader(response.iter_lines(decode_unicode=True))
    for content in reader:
        if len(content) > 1:
            tracked_funds.add(content[1])
with requests.get('https://apps.csidata.com/factsheets.php?type=stock&format=csv&isetf=1', stream=True) as response:
    reader = csv.reader(response.iter_lines(decode_unicode=True))
    for content in reader:
        if len(content) > 1:
            tracked_funds.add(content[1])
# response = requests.get('https://apps.csidata.com/factsheets.php?type=stock&format=csv&exchangeid=MUTUAL')
# response = requests.get('https://apps.csidata.com/factsheets.php?type=stock&format=csv&isetf=1')
# print(response)
# print(response.content)
# exit(-1)
# response = requests.get('http://ftp.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt')
# reader = csv.reader(response.iter_lines(decode_unicode=True), delimiter='|')
# tracked_funds = set()
# for line in reader:
#     if len(line) == 0:
#         continue
#     tracked_funds.add(line[1])
with open('./funds.csv') as funds_csv:
    funds = funds_csv.read().split('\n')
    i = 0
    for line in funds:
        line = line.rstrip()
        if line not in tracked_funds:
            i+=1
            print(line)
    print(i)

            # NYSE Arca