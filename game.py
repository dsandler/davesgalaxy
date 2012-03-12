import cookielib
import urllib
import urllib2
import json
import re
from itertools import izip
from BeautifulSoup import BeautifulSoup

HOST = "http://davesgalaxy.com/"
URL_LOGIN = HOST + "/login/"
URL_VIEW = HOST + "/view/"
URL_PLANETS = HOST + "/planets/list/all/%d/"
URL_FLEETS = HOST + "/fleets/list/all/%d/"
URL_PLANET_DETAIL = HOST + "/planets/%d/info/"
URL_FLEET_DETAIL = HOST + "/fleets/%d/info/"

def pairs(t):
  return izip(*[iter(t)]*2)

def parse_coords(s):
  m = re.match(r'\(\s*([0-9.]+)\s*,\s*([0-9.]+)\s*\)', s)
  if m: return map(float, m.groups())
  return None

class Galaxy:
  class Fleet:
    def __init__(self, galaxy, fleetid, coords):
      self.galaxy = galaxy
      self.fleetid = int(fleetid)
      self.coords = coords
      self._loaded = False
    def __repr__(self):
      return "<Fleet #%d%s @ (%.1f,%.1f)>" % (self.fleetid, 
        (' (%s, %s ships)' % (self.disposition, len(self.ships))) \
          if self._loaded else '',
        self.coords[0], self.coords[1])
    def load(self):
      if self._loaded: return
      req = self.galaxy.opener.open(URL_FLEET_DETAIL % self.fleetid)
      soup = self.soup = BeautifulSoup(json.load(req)['pagedata'])
      dest = soup.find(text="Destination:").findNext('td').string
      self.destination = parse_coords(dest)
      if not self.destination: self.destination = dest
      self.disposition = soup.find(text="Disposition:").findNext('td').string
      try:
        self.speed = float(soup.find(text="Current Speed:").findNext('td').string)
      except: self.speed = 0
      self.ships = dict()
      for k,v in pairs(soup('h3')[0].findAllNext('td')):
        self.ships[k.string] = int(v.string)
      self._loaded = True

  class Planet:
    def __init__(self, galaxy, planetid, name):
      self.galaxy = galaxy
      self.planetid = int(planetid)
      self.name = name
      self._loaded = False
    def __repr__(self):
      return "<Planet #%d \"%s\">" % (self.planetid, self.name)
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

  @property
  def fleets(self):
    if self._fleets: return self._fleets
    i=1
    fleets = []
    while True:
      try:
        req = self.opener.open(URL_FLEETS % i)
        soup = BeautifulSoup(json.load(req)['tab'])
        for row in soup('tr')[1:]:
          cells=row('td')
          fleetid=re.search(r'/fleets/([0-9]*)/',
                             str(row('td')[0])).group(1)
#class=\"rowheader\"/>\n      <th class=\"rowheader\">ID</th><th
#class=\"rowheader\">Ships</th>\n      <th
#class=\"rowheader\">Disposition</th><th
#class=\"rowheader\">Destination</th>\n      <th
#class=\"rowheader\">Att.</th><th class=\"rowheader\">Def.</th>\n
          coords = parse_coords(
            re.search(r'gm.centermap(\([0-9.,]+\))', str(row)).group(1))
          fleets.append(Galaxy.Fleet(self, fleetid, coords))
        i += 1
      except urllib2.HTTPError:
        break
    self._fleets = fleets
    return fleets
