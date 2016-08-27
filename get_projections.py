#!/usr/bin/env python

import os
import re
import time
import json
import urllib2
import datetime

from BeautifulSoup import BeautifulSoup

# ugh - should be less lazy about this
HEADERS = ['name','p_yd','p_td','int','r_yd','r_td','rcv_yd','rcv_td','fum','proj']
SRC_HEADERS = {'CBS':{'QB':['name','p_att','p_cmp','p_yd','p_td','cmp_pct','r_yatt','r_att','r_yd','r_avg','r_td','fum','proj'],
                      'RB':['name','r_att','r_yd','r_avg','r_td','rcv_rpt','rcv_yd','rcv_avg','rcv_td','fum','proj'], 
                      'WR':['name','rcv_rcp','rct_yd','rcv_avg','rcv_td','fum','proj'],
                      'TE':['name','rcv_rcp','rct_yd','rcv_avg','rcv_td','fum','proj'],
                       'K':['name','fg','fga','xp','proj'],
                     'DST':['name','int','dfr','sack','dtd','sty','pa','tyda','proj'],
                     },
               'NFL':{'ALL':['name','gp','p_yd','p_td','int','r_yd','r_td','rcv_yd','rcv_td','fum_td','2pt','fum','proj'],
                     },
               'ESPN':{'ALL':['name','p_cmp','p_att','p_yd','p_td','int','r_att','r_yd','r_yd','rcv_rpt','rcv_yd','rcv_td','proj'],
                      },
               'FPS':{'qb':['name','p_att','p_cmp','p_yd','p_td','int','r_att','r_yd','r_td','fum','proj'],
                      'rb':['name','r_att','r_yd','r_td','rcv_rcp','rct_yd','rcv_td','fum','proj'],
                      'wr':['name','r_att','r_yd','r_td','rcv_rcp','rct_yd','rcv_td','fum','proj'],
                      'te':['name','rcv_rcp','rct_yd','rcv_td','fum','proj'],
                       'k':['name','fg','fga','xp','proj'],
                     },
                'MFL':{'ALL':['num','pick','name','avg_pick','min_pick','max_pick','num_drafts'],
                      }
              }
VERBOSE = True


class GetESPNProjections(object):

  def __init__(self, seasons=1, current_year=2016, la_liga_scoring=True, file_suffix = '.csv'):

    self.projection_id = 'ESPN'

    self.primary_directory   = os.getcwd() + '/projections/{}/'.format(self.projection_id)
    self.secondary_directory = None
    self.file_suffix = file_suffix

    self.seasons = seasons
    self.current_year = current_year
    self.la_liga_scoring = la_liga_scoring
    self.url_prefix = 'http://games.espn.com/ffl/tools/projections?&sortMap=AAAAARgAAAAHAQAMc3Rh' \
                    + 'dFNlYXNvbklkAwAAB%2BABAAhjYXRlZ29yeQMAAAACAQAJZGlyZWN0aW9uA%2F%2F%2F%2F%2' \
                    + 'F8BAAZjb2x1bW4D%2F%2F%2F%2F%2FQEAC3NwbGl0VHlwZUlkAwAAAAABABBzdGF0U291cmNl' \
                    + 'VHlwZUlkAwAAAAEBAAtzdGF0UXVlcnlJZAMAAAAB'
    self.url_suffix = ''
    self.verbose = VERBOSE


  def get(self):

    print 'Getting projection data for {}'.format(self.projection_id)
    for i in range(self.seasons):
      season = self.current_year - i
      path = self.primary_directory
      self.make_directory(path)
      data = self.download_content(season)
      path += str(season) + self.file_suffix
      self.write_to_disk(data, path)

    return None


  def download_content(self, season):

    print 'Downloading content for season {}'.format(season)

    csv = ''
    index = 0
    index_increment = 40
    max_index = 600
    players = 0

    while index < max_index:
      print 'Grabbing from index {} to index {}'.format(index, index+index_increment)
      url = self.url_prefix + '&seasonTotals=true&startIndex=' + str(index)
      url += '&seasonId=' + str(season)
      if self.la_liga_scoring:
        url += '&leagueId=359752'
      page = urllib2.urlopen(url).read()
      s1 = BeautifulSoup(page)
      player_info = s1.findAll("tr", {"class": "pncPlayerRow playerTableBgRow0"})
      player_info += s1.findAll("tr", {"class": "pncPlayerRow playerTableBgRow1"})

      for p in player_info:
        s2 = BeautifulSoup(str(p))
        s3 = s2.find('td')
        player_entries = []
        for x in s3.findAllNext():
          datum = str(x.getText())
          if len(datum) == 0 or datum in ['FA','P','O','SSPD']:
            continue
          if ';' in datum:
            datum = datum.split('&nbsp;')[1:]
            player_entries.append(datum[0])
            if len(datum) == 1:
              datum.append('None')
            player_entries.append(datum[-1])
          else:
            player_entries.append(datum)
        player_entries[0], player_entries[2] = player_entries[2], player_entries[0]
        csv += ','.join(player_entries) + '\n'
        players += 1
      index += index_increment

    return csv


  def write_to_disk(self, data, path):

    print 'Writing data to path {}'.format(path)
    f = open(path, 'w')
    f.write(data)
    f.close()

    return None


  def make_directory(self, directory):

    if not os.path.exists(directory):
      print 'Creating directory: {}'.format(directory)
      os.makedirs(directory)

    return None





class GetNFLProjections(object):

  def __init__(self, seasons=1, current_year=2016, la_liga_scoring=True, file_suffix = '.csv'):

    self.projection_id = 'NFL'

    self.primary_directory   = os.getcwd() + '/projections/{}/'.format(self.projection_id)
    self.secondary_directory = None
    self.file_suffix = file_suffix

    self.seasons = seasons
    self.current_year = current_year
    self.la_liga_scoring = la_liga_scoring
    self.url_prefix = 'http://fantasy.nfl.com/research/projections?offset={}&position=O&sort=pro' \
                    + 'jectedPts&statCategory=projectedStats&statSeason=2016&statType=seasonProj' \
                    + 'ectedStats&statWeek=1'
    self.url_suffix = ''
    self.verbose = VERBOSE


  def get(self):

    print 'Getting projection data for {}'.format(self.projection_id)
    for i in range(self.seasons):
      season = self.current_year - i
      path = self.primary_directory
      self.make_directory(path)
      data = self.download_content(season)
      path += str(season) + self.file_suffix
      self.write_to_disk(data, path)

    return None


  def download_content(self, season):

    print 'Downloading content for season {}'.format(season)

    csv = ''
    index = 1
    index_increment = 25
    max_index = 600
    players = 0

    while index < max_index:
      print 'Grabbing from index {} to index {}'.format(index, index+index_increment)
      url = self.url_prefix.format(index)
      try:
        page = urllib2.urlopen(url).read()
      except:
        print 'Trouble accessing index {} for url {}'.format(index, url)
        break
      s1 = BeautifulSoup(page)
      player_info = s1.findAll("tr", {"class": re.compile('player-.*')})

      for p in player_info:
        s2 = BeautifulSoup(str(p))
        s3 = s2.findAll("span", {"class": re.compile('playerStat.*')})
        s4 = s2.findAll("a", {"class": re.compile('playerCard playerName.*')})
        s5 = s2.findAll("td", {"class": re.compile('stat projected.*')})
        player_entries = []
        player_entries.append(str(s4[0].getText())) # player name
        for x in s3:
          datum = str(x.getText())
          datum = datum if not datum == '-' else '0'
          player_entries.append(datum) # individual projections
        player_entries.append(str(s5[0].getText())) # total player projection
        csv += ','.join(player_entries) + '\n'
        players += 1
      index += index_increment
    return csv


  def write_to_disk(self, data, path):

    print 'Writing data to path {}'.format(path)
    f = open(path, 'w')
    f.write(data)
    f.close()

    return None


  def make_directory(self, directory):

    if not os.path.exists(directory):
      print 'Creating directory: {}'.format(directory)
      os.makedirs(directory)

    return None


class GetCBSProjections(object):

  def __init__(self, seasons=1, current_year=2016, la_liga_scoring=True, file_suffix = '.json'):

    self.projection_id = 'CBS'

    self.primary_directory   = os.getcwd() + '/projections/{}/'.format(self.projection_id)
    self.secondary_directory = None
    self.file_suffix = file_suffix

    self.seasons = seasons
    self.current_year = current_year
    self.la_liga_scoring = la_liga_scoring
    self.url_prefix = 'http://www.cbssports.com/fantasy/football/stats/weeklyprojections/{}/season/avg/standard'
    self.url_suffix = ''
    self.headers = SRC_HEADERS.get(self.projection_id)
    self.positions = self.headers.keys()
    self.verbose = VERBOSE


  def get(self):

    print 'Getting projection data for {}'.format(self.projection_id)
    for i in range(self.seasons):
      season = self.current_year - i
      path = self.primary_directory
      self.make_directory(path)
      data = self.download_content(season)
      path += str(season) + self.file_suffix
      self.write_to_disk(data, path)

    return None


  def download_content(self, season):

    print 'Downloading content for season {}'.format(season)

    jsons = []
    players = 0

    for position in self.positions:
      headers = self.headers.get(position)
      print 'Grabbing position {}'.format(position)
      url = self.url_prefix.format(position)
      try:
        page = urllib2.urlopen(url).read()
      except:
        print 'Trouble accessing position {} at url {}'.format(position, url)
        break
      s1 = BeautifulSoup(page)
      player_info = s1.findAll("tr", {"class": re.compile('row1.*')})
      player_info += s1.findAll("tr", {"class": re.compile('row2.*')})

      for p in player_info:
        player_json = {}
        s2 = BeautifulSoup(str(p))
        s3 = s2.findAll("td", {"align": re.compile('left.*')})
        for x, h in zip(s3, headers):
          datum = str(x.getText())
          if h == 'name':
            datum = datum.split(',')[0]
          player_json[h] = datum
        jsons.append(player_json)
        players += 1
        if self.verbose:
          print player_json
    return json.dumps(jsons)


  def write_to_disk(self, data, path):

    print 'Writing data to path {}'.format(path)
    f = open(path, 'w')
    f.write(data)
    f.close()

    return None


  def make_directory(self, directory):

    if not os.path.exists(directory):
      print 'Creating directory: {}'.format(directory)
      os.makedirs(directory)

    return None


class GetFPSProjections(object):

  def __init__(self, seasons=1, current_year=2016, la_liga_scoring=True, file_suffix = '.json'):

    self.projection_id = 'FPS'

    self.primary_directory   = os.getcwd() + '/projections/{}/'.format(self.projection_id)
    self.secondary_directory = None
    self.file_suffix = file_suffix

    self.seasons = seasons
    self.current_year = current_year
    self.la_liga_scoring = la_liga_scoring
    self.url_prefix = 'https://www.fantasypros.com/nfl/projections/{}.php?filters=73:120:152:859'
    self.url_suffix = ''
    self.headers = SRC_HEADERS.get(self.projection_id)
    self.positions = self.headers.keys()
    self.verbose = VERBOSE


  def get(self):

    print 'Getting projection data for {}'.format(self.projection_id)
    for i in range(self.seasons):
      season = self.current_year - i
      path = self.primary_directory
      self.make_directory(path)
      data = self.download_content(season)
      path += str(season) + self.file_suffix
      self.write_to_disk(data, path)

    return None


  def download_content(self, season):

    print 'Downloading content for season {}'.format(season)

    jsons = []
    players = 0

    for position in self.positions:
      headers = self.headers.get(position)
      print 'Grabbing position {}'.format(position)
      url = self.url_prefix.format(position)
      try:
        page = urllib2.urlopen(url).read()
      except:
        print 'Trouble accessing position {} at url {}'.format(position, url)
        break
      s1 = BeautifulSoup(page)
      player_info = s1.findAll("tr", {"class": re.compile('mpb-player-.*')})

      for p in player_info:
        player_json = {}
        s2 = BeautifulSoup(str(p))
        s3 = s2.findAll("td")
        for x, h in zip(s3, headers):
          if h == 'name':
            s4 = BeautifulSoup(str(x))
            s5 = s4.findAll('a')
            datum = str(s5[0].getText())
          else:
            datum = str(x.getText())
          player_json[h] = datum
        jsons.append(player_json)
        players += 1
        if self.verbose:
          print player_json
    return json.dumps(jsons)


  def write_to_disk(self, data, path):

    print 'Writing data to path {}'.format(path)
    f = open(path, 'w')
    f.write(data)
    f.close()

    return None


  def make_directory(self, directory):

    if not os.path.exists(directory):
      print 'Creating directory: {}'.format(directory)
      os.makedirs(directory)

    return None




if __name__ == '__main__':

  espn = GetESPNProjections()
  #espn.get()

  nfl = GetNFLProjections()
  #nfl.get()

  cbs = GetCBSProjections()
  cbs.get()

  fps = GetFPSProjections()
  fps.get()



