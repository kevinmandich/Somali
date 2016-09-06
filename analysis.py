import os
import json 
from collections import defaultdict, Counter

print ''
HEADERS = ['name','p_yd','p_td','int','r_yd','r_td','rcv_yd','rcv_td','fum','proj']
weird_char = [',','.',]

# tuneable parameters
f_tier = {'1':1.0, '2':0.8, '3':0.65, '4':0.55, '5':0.50, '6': 0.45, '7': 0.40}
f_pos = {'QB':0.8, 'TE':0.8, 'WR':1.0, 'RB':1.0, 'D':0.4, 'K':0.20}
proj_weights = {'cbs':0.5, 'espn':0.25, 'fps':2.0, 'fs':1.0, 'mfl':1.0, 'nfl':0.5}

def tier_lookup(rank):
  if rank <= 5:
    return '1'
  elif rank <= 10:
    return '2'
  elif rank <= 15:
    return '3'
  elif rank <= 20:
    return '4'
  elif rank <= 25:
    return '5'
  elif rank <= 30:
    return '6'
  return '7'


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
for s, ds in sources.iteritems():
  for p in ds:
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

def info(pd, player):
  print '\n\nInfo for player {}:\n'
  try:
    print 'Auction: {}'.format(pd[player]['auction'])
  except:
    pass
  try:
    print 'Avg pick: {}'.format(pd[player]['avg_pick'])
  except:
    pass
  try:
    print 'Num drafts: {} of {}'.format(pd[player]['num_drafts'], max_num_drafts)
  except:
    pass

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

# build projections data
misses = 0
proj = defaultdict(dict)
for s, ds in sources.iteritems():
  for p in ds:
    try:
      proj[p['name']].update({s:float(p['proj'])})
    except:
      misses += 1
print '{} missed projections'.format(misses)
projections = {}
for player, pro in proj.iteritems():
  weights, sum_ = 0, 0
  for s, p in pro.iteritems():
    weights += proj_weights[s]
    sum_ += proj_weights[s] * p
    projections[player] = float(sum_)/weights

# build auctions data
auctions = {}
misses = 0
for player, stats in pd.iteritems():
  try:
    auctions[player] = stats['auction']
  except:
    misses += 1
print '{} missed auctions'.format(misses)

# build tiers
tiers = {} # {player: tier}
mid = defaultdict(list)
for player, pos in positions.iteritems():
  mid[pos].append(player)
mid2 = {}
for pos, players in mid.iteritems():
  new_list = []
  for player in players:
    new_list.append((player, projections.get(player, 0)))
  mid2[pos] = new_list
for pos, player_list in mid2.iteritems():
  player_list = sorted(player_list, key=lambda x: x[1], reverse=True)
  for i, p in enumerate(player_list):
    tiers[p[0]] = tier_lookup(i)


class Draft(object):

  def __init__(self, projections={}, historic={}, positions={}, tiers={}, starting_cash=200.0):

    self.turn = 0
    self.round = 0
    self.starting_cash = starting_cash
    self.projections = projections
    self.historic = historic
    self.positions = positions
    self.tiers = tiers
    self.auctions = defaultdict(lambda: defaultdict(list)) # {team: {player: (price, historic, projection)}}
    self.prices = {}   # {player: price}
    self.team_players = {'draz':[],'kev':[],'lock':[],'gor':[],'brett':[],'john':[], \
                         'danny':[],'jack':[],'andrew':[],'noah':[],'luke':[],'mu':[]}
    self.team_prices = {'draz':200,'kev':200,'lock':200,'gor':200,'brett':200,'john':200, \
                        'danny':200,'jack':200,'andrew':200,'noah':200,'luke':200,'mu':200}
    self.team_strength = {'draz':0.0,'kev':0.0,'lock':0.0,'gor':0.0,'brett':0.0,'john':0.0, \
                          'danny':0.0,'jack':0.0,'andrew':0.0,'noah':0.0,'luke':0.0,'mu':0.0}
    self.team_strength_trace = {'draz':[],'kev':[],'lock':[],'gor':[],'brett':[],'john':[], \
                                'danny':[],'jack':[],'andrew':[],'noah':[],'luke':[],'mu':[]}
    self.state_directory = os.getcwd() + '/draft_state/'

  def __str__(self):

    print '\nDraft turn {} round {}'.format(self.turn, self.round)

    print '\nTeam strengths:'
    strengths = sorted([ (x, y) for x, y in self.team_strength.iteritems() ], key=lambda x: x[1], reverse=True)
    len_ = len(strengths)/2
    for i in range(len_):
      j = i + len_
      first  = '%s: %0.2f' % (strengths[i][0].ljust(7), strengths[i][1])
      second = '%s: %0.2f' % (strengths[j][0].ljust(7), strengths[j][1])
      print first + '\t' + second

    print '\nMoney left on each team:'
    prices = sorted([ (x, y) for x, y in self.team_prices.iteritems() ], key=lambda x: x[1], reverse=True)
    len_ = len(prices)/2
    for i in range(len_):
      j = i + len_
      first  = '%s: %0.2f' % (prices[i][0].ljust(7), prices[i][1])
      second = '%s: %0.2f' % (prices[j][0].ljust(7), prices[j][1])
      print first + '\t' + second

    print '\nPlayers on each team:'
    team_players = sorted([ (x, len(y)) for x, y in self.team_players.iteritems() ], key=lambda x: x[1], reverse=True)
    len_ = len(team_players)/2
    for i in range(len_):
      j = i + len_
      first  = '%s: %i' % (team_players[i][0].ljust(7), team_players[i][1])
      second = '%s: %i' % (team_players[j][0].ljust(7), team_players[j][1])
      print first + '\t' + second

    print '\nAverage price per player:'
    avg_prices = []
    for team, team_players in self.team_players.iteritems():
      num_players = len(team_players)
      total_price_spent = self.starting_cash - self.team_prices[team]
      avg_price = float(total_price_spent) / num_players if num_players > 0 else 0.0
      avg_prices.append((team, avg_price))
    avg_prices = sorted(avg_prices, key=lambda x: x[1], reverse=True)
    len_ = len(avg_prices)/2
    for i in range(len_):
      j = i + len_
      first  = '%s: %i' % (avg_prices[i][0].ljust(7), avg_prices[i][1])
      second = '%s: %i' % (avg_prices[j][0].ljust(7), avg_prices[j][1])
      print first + '\t' + second

    print '\nPositions per team:'
    team_positions = []
    for team, players in self.team_players.iteritems():
      pos = []
      for player in players:
        pos.append(str(self.positions[player]))
      c = Counter(pos)
      team_positions.append([team, c, sum(c.values())])
    team_positions = sorted(team_positions, key=lambda x: x[2], reverse=True)
    #len_ = len(team_positions)/2
    #for i in range(len_):
    #  j = i + len_
    #  first  = '%s: %s' % (team_positions[i][0].ljust(7), str(team_positions[i][1]))
    #  second = '%s: %s' % (team_positions[j][0].ljust(7), str(team_positions[j][1]))
    #  print first + '\t' + second
    for t in team_positions:
      print '%s: %s' % (t[0].ljust(7), str(t[1]))

    return ''

  def update(self, team, player, price):
    print '{} got {} for {} (historic is {})'.format(team, player, price, self.historic[player])
    historic = self.historic.get(player, 0)
    projections = self.projections.get(player, 0)
    position = self.positions.get(player, '??')
    self.team_players[team].append(player)
    self.auctions[team][player].append((price, historic, projections))
    self.prices[player] = price
    self.team_prices[team] -= price

    strength = 10 * f_tier[self.tiers[player]] * f_pos[self.positions[player]] \
             * ((self.historic[player] - float(price)) / self.historic[player]) \
             * (self.projections[player] / self.starting_cash)
    self.team_strength[team] += strength
    self.team_strength_trace[team].append(strength)

    self.turn += 1
    self.round = self.turn / 12
    self.save_state()

    return None

  def save_state(self):

    state_json = {}
    state_json['turn']                = self.turn
    state_json['round']               = self.round
    state_json['starting_cash']       = self.starting_cash
    state_json['projections']         = self.projections
    state_json['historic']            = self.historic
    state_json['positions']           = self.positions
    state_json['tiers']               = self.tiers
    state_json['auctions']            = self.auctions
    state_json['prices']              = self.prices
    state_json['team_players']        = self.team_players
    state_json['team_prices']         = self.team_prices
    state_json['team_strength']       = self.team_strength
    state_json['team_strength_trace'] = self.team_strength_trace

    self.make_directory(self.state_directory)
    state_path = self.state_directory + 'turn_{}.json'.format(self.turn)
    f = open(state_path, 'w')
    f.write(json.dumps(state_json))
    f.close()

    return None

  def load_state(self, state_json):

    self.turn                = state_json['turn']
    self.round               = state_json['round']
    self.starting_cash       = state_json['starting_cash']
    self.projections         = state_json['projections']
    self.historic            = state_json['historic']
    self.positions           = state_json['positions']
    self.tiers               = state_json['tiers']
    self.auctions            = state_json['auctions']
    self.prices              = state_json['prices']
    self.team_players        = state_json['team_players']
    self.team_prices         = state_json['team_prices']
    self.team_strength       = state_json['team_strength']
    self.team_strength_trace = state_json['team_strength_trace']

    return None

  def make_directory(self, directory):

    if not os.path.exists(directory):
      print 'Creating directory: {}'.format(directory)
      os.makedirs(directory)

    return None

def load_draft(turn=1000):

  d = Draft(projections=projections, \
            historic=auctions, \
            positions=positions, \
            tiers=tiers)
  path = os.getcwd() + '/draft_state/turn_{}.json'.format(str(turn))
  saved_state = json.loads(open(path, 'r').read())
  d.load_state(saved_state)

  return d

if __name__ == '__main__':

  #'''
  d = Draft(projections=projections, \
            historic=auctions, \
            positions=positions, \
            tiers=tiers)

  #d.update('draz','antonio brown', 20)
  #d.update('draz','philip rivers', 2)
  # d.update('lock','odell beckham', 65)
  #'''
  #d = load_draft(3)


