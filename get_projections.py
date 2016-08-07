#!/usr/bin/env python

import os
import re
import urllib2
import datetime
import time

from BeautifulSoup import BeautifulSoup


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



if __name__ == '__main__':

  espn = GetESPNProjections()
  espn.get()



