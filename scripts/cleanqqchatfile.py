#so far just some lines for you to use in the interactive console

from BeautifulSoup import BeautifulSoup

f1 = open('/home/leon/doc/class/wuqi-2012-07-08-clean.html')

soup = BeautifulSoup(f1)

clickable = soup.findAll('span', attrs={'class':'clickable'})

removed = [c.extract() for c in clickable]

imgs = soup.findAll('img')

imgs_removed = [img.extract() for img in imgs]

f2 = open('/home/leon/doc/class/wuqi-2012-07-08-cleaned.html', 'w')

f2.write(str(soup))

f1.close()

f2.close()

