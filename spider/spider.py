import requests
from bs4 import BeautifulSoup
url = "https://www1.pu.edu.tw/~tcyang/course.html"
Data = requests.get(url, verify=False)
Data.encoding = "utf-8"
#print(Data.text)
sp = BeautifulSoup(Data.text, "html.parser")
result=sp.select("a")
for item in result:
	print(item.text)
	print(item.get("herf"))
	print()
#print(result)
info = ""
for item in result:
	info += item.text + "\n\n"
print(info)
