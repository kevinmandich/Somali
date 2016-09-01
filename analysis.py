import json
from collections import defaultdict

HEADERS = ['name','p_yd','p_td','int','r_yd','r_td','rcv_yd','rcv_td','fum','proj']
weird_char = [',','.',]

# data load
cbs  = json.loads(open('projections/CBS/2016.json',  'r').read())
espn = json.loads(open('projections/ESPN/2016.json', 'r').read())
fps  = json.loads(open('projections/FPS/2016.json',  'r').read())
fs   = json.loads(open('projections/FS/2016.json',   'r').read())
mfl  = json.loads(open('projections/MFL/2016.json',  'r').read())
nfl  = json.loads(open('projections/NFL/2016.json',  'r').read())

sources = {'cbs':cbs, 'espn':espn, 'fps':fps, 'fs':fs, 'mfl':mfl, 'nfl':nfl}

# data clean-up - individual sources
for p in fs:
  p['name'] = p['name'].split(',')[1].strip() + ' ' + p['name'].split(',')[0]
for p in mfl:
  p['name'] = p['name'].split(',')[1].strip() + ' ' + p['name'].split(',')[0]
for p in espn:
  p['name'] = p['name'].replace('*','')

# data clean-up - all sources
for s in sources:
  for p in s:
    p['name'] = p['name'].strip() \
                         .replace('.','') \
                         .replace('\'','') \
                         .replace('-','') \
                         .strip() \
                         .lower()

def name(d, n):
  for x in d:
    if n in x['name'].lower():
      print x['name']
  return None

# build player data
positions = {}
pd = defaultdict(dict)
max_auction = 0
for p in fs:
  auction = p['auction'].replace('$','')
  auction = int(auction) if len(auction) > 0 else 0
  if auction > max_auction:
    max_auction = auction
  pd[p['name']].update({'auction':auction})
  positions[p['name']] = p['pos']
for p in espn: # defensive players (teams) from ESPN
  if 'nbsp' in p['name']:
    positions[p['name'].split(' ')[0]] = 'D'
for p in fs:
  auction = p['auction'].replace('$','')
  auction = int(auction) if len(auction) > 0 else 0
  pd[p['name']].update({'auction_norm':float(auction)/max_auction})
  pd[p['name']].update({'auction':auction})

max_num_drafts = max([ int(x['num_drafts']) for x in mfl ])
max_pick_spread = max([ int(x['max_pick']) - int(x['min_pick']) for x in mfl ])
for p in mfl:
  pd[p['name']].update({'num_drafts_norm': float(p['num_drafts'])/max_num_drafts })
  pd[p['name']].update({'num_drafts': float(p['num_drafts'])/max_num_drafts })
  pd[p['name']].update({'pick_spread_norm': (int(p['max_pick']) - int(p['min_pick']))/float(max_pick_spread) })
  pd[p['name']].update({'pick_spread': int(p['max_pick']) - int(p['min_pick']) })
  pd[p['name']].update({'avg_pick': p['avg_pick'] })

sleepers = []
for p, s in pd.iteritems():
  num_drafts_norm = s.get('num_drafts_norm')
  auction_norm = s.get('auction_norm')
  if num_drafts_norm and auction_norm:
    sleeper_value = num_drafts_norm / auction_norm
    s['sleeper'] = sleeper_value
    sleepers.append((p, auction_norm, num_drafts_norm, sleeper_value))


'''
# get names only
cbs_names  = [ x['name'] for x in cbs ]
#espn_names = [ x['name'] for x in espn ]
fps_names  = [ x['name'] for x in fps ]
fs_names   = [ x['name'] for x in fs ]
mfl_names  = [ x['name'] for x in mfl ]
nfl_names  = [ x['name'] for x in nfl ]

print '{} names in CBS'.format(len(cbs_names))
#print '{} names in ESPN'.format(len(espn_names))
print '{} names in FPS'.format(len(fps_names))
print '{} names in FS'.format(len(fs_names))
print '{} names in MFL'.format(len(mfl_names))
print '{} names in NFL'.format(len(nfl_names))
'''

class Draft(object):

  def __init__(self, projections={}, historic={}, positions={}):
    '''
    Teams:
    - draz
    - kev
    - lock
    - gor
    - brett
    - john
    - danny
    - jack
    - andrew
    - noah
    - luke
    - mu
    '''

    self.projections = projections
    self.historic = historic
    self.positions = positions

    self.auctions = defaultdict(lambda: defaultdict(list)) # {team: {player: (price, historic, projection)}}
    self.prices = {}   # {player: price}
    self.team_players = defaultdict(list)
    self.team_prices = {'draz':200,'kev':200,'lock':200,'gor':200,'brett':200,'john':200, \
                        'danny':200,'jack':200,'andrew':200,'noah':200,'luke':200,'mu':200}
    self.team_strength = {'draz':0.0,'kev':0.0,'lock':0.0,'gor':0.0,'brett':0.0,'john':0.0, \
                        'danny':0.0,'jack':0.0,'andrew':0.0,'noah':0.0,'luke':0.0,'mu':0.0}

  def __str__(self):

    print '\nTeam strengths:'
    strengths = [ (x, y) for x, y in self.team_strength.iteritems() ]
    strengths = sorted(strengths, key=lambda x: x[1], reverse=True)
    len_ = len(strengths)/2
    for i in range(len_):
      j = i + len_
      first  = '{}: {}'.format(strengths[i][0].ljust(7), strengths[i][1])
      second = '{}: {}'.format(strengths[j][0].ljust(7), strengths[j][1])
      print first + '\t' + second

    print '\nMoney left on each team:'
    prices = [ (x, y) for x, y in self.team_prices.iteritems() ]
    prices = sorted(prices, key=lambda x: x[1], reverse=True)
    len_ = len(prices)/2
    for i in range(len_):
      j = i + len_
      first  = '{}: {}'.format(prices[i][0].ljust(7), prices[i][1])
      second = '{}: {}'.format(prices[j][0].ljust(7), prices[j][1])
      print first + '\t' + second

    return ''

  def update(self, team, player, price):
    historic = self.historic.get(player, 0)
    projections = self.projections.get(player, 0)
    position = self.positions.get(player, '??')
    self.auctions[team][player].append((price, historic, projections))
    self.prices[player] = price
    self.team_prices[team] -= price


a = Draft()













