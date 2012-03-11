import cookielib
import urllib
import urllib2
import json
import re
from BeautifulSoup import BeautifulSoup

HOST = "http://davesgalaxy.com/"
URL_LOGIN = HOST + "/login/"
URL_VIEW = HOST + "/view/"
URL_PLANETS = HOST + "/planets/list/all/%d/"
URL_PLANET_DETAIL = HOST + "/planets/%d/info/"

class Galaxy:
  class Planet:
    def __init__(self, galaxy, planetid, name):
      self.galaxy = galaxy
      self.planetid = int(planetid)
      self.name = name
      self._loaded = False
    def __repr__(self):
      return "<Planet \"%s\" %d>" % (self.name, self.planetid)
    def load(self):
      if self._loaded: return
      req = self.galaxy.opener.open(URL_PLANET_DETAIL % self.planetid)
      soup = BeautifulSoup(json.load(req)['tab'])
      self.soup = soup

      self.society = int(soup('div',{'class':'info1'})[0]('div')[2].string)
      data = [x.string.strip() for x in soup('td',{'class':'planetinfo2'})]
      self.location=map(float, re.findall(r'[0-9.]+', data[2]))
      i=6
      if soup.find(text='Distance to Capital:'): i+=1
      if soup.find(text='Open Trading:'): i+=2
      self.population=int(data[i]) ; i+=1
      self.money=int(data[i].split()[0]) ; i+=1
      self.steel=map(int, data[i:i+3]) ; i+=3
      self.unobtainium=map(int, data[i:i+3]) ; i+=3
      self.food=map(int, data[i:i+3]) ; i+=3
      self.antimatter=map(int, data[i:i+3]) ; i+=3
      self.consumergoods=map(int, data[i:i+3]) ; i+=3
      self.hydrocarbon=map(int, data[i:i+3]) ; i+=3
      self.krellmetal=map(int, data[i:i+3]) ; i+=3

      self._loaded = True

  def __init__(self):
    self._planets = None
    self._fleets = None
    self.jar = cookielib.LWPCookieJar()
    try:
      self.jar.load("login.dat")
    except:
      pass
    self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.jar))
  def login(self, u, p):
    self.opener.open(URL_LOGIN,
      urllib.urlencode(dict(usernamexor=u, passwordxor=p)))
    self.jar.save("login.dat")

  @property
  def planets(self):
    if self._planets: return self._planets
    i=1
    planets = []
    while True:
      try:
        req = self.opener.open(URL_PLANETS % i)
        soup = BeautifulSoup(json.load(req)['tab'])
        for row in soup('tr')[1:]:
          cells=row('td')
          planetid=re.search(r'/planets/([0-9]*)/',
                             str(row('td')[0])).group(1)
# </th><th class="rowheader">Name</th>
# <th class="rowheader">Society</th>
# <th class="rowheader">Population</th>
# <th class="rowheader">Tax Rate</th>
# <th class="rowheader">Tariff Rate</th>

          planets.append(Galaxy.Planet(self, planetid, cells[4].string))
        i += 1
      except urllib2.HTTPError:
        break
    self._planets = planets
    return planets
