from bs4 import BeautifulSoup
import time
import urllib2
import re
import csv
import requests


def findSrc(soup):
	try:
		for link in soup.find_all('img'):
			if "https://image.tmdb.org" not in link.get('src'):
				continue
			src = link.get('src')
			src1 = re.sub("/w[0-9]+", "/original", src)
			return src1
	except:
		pass
	return ""

def scrape():
	mainSite = "https://www.themoviedb.org/movie/"
	lang = "?language=en"
	sources= []
	with open("./data/links.csv") as csvfile:
	    reader = csv.reader(csvfile, delimiter=',')
	    i = 0
	    for data in reader:
	        i += 1	        
	        sources.append(data[2])
	dic = []
	
	ct = 0
	for pc in sources:
		mainLink = mainSite+pc+lang
		r  = requests.get(mainLink)
		data = r.text
		soup = BeautifulSoup(data)
		links =findSrc(soup)
		print [ct, pc, links]
		dic.append([pc, links])
		ct += 1
		time.sleep(4)


	with open('header3.csv', 'wb') as csvfile:
	    writer = csv.writer(csvfile, delimiter=',')
	    for line in dic:
	    	writer.writerow(line)


if __name__ == "__main__":
	scrape()








