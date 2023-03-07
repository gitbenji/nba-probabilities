
from nba_api.stats import endpoints
from nba_api.stats.static import players
import numpy as np
from scipy import stats

# get player by lastname
# player_id = '1631109'
player_lastname = input("player lastname: ")
player_info_list = players.find_players_by_last_name(player_lastname)
player_object = {}
player_id = ''

# check if more than one player with the same last name
if len(player_info_list) > 1:
	for index, player in enumerate(player_info_list):
		player_object[index] = player['full_name'] if player['is_active'] else ''
	which_player = int(input("which number: "))
	print(player_info_list[which_player])
	player_id = player_info_list[which_player]['id']
else:
	print(player_info_list[0])
	player_id = player_info_list[0]['id']

# retrieve game log data for the season by player_id
game_log = endpoints.PlayerGameLog(player_id = player_id).get_data_frames()[0]

# create cumulative stat columns in the dataframe
game_log['PRA'] = game_log['PTS'] + game_log['REB'] + game_log['AST']
game_log['PR'] = game_log['PTS'] + game_log['REB']
game_log['PA'] = game_log['PTS'] + game_log['AST']
game_log['AR'] = game_log['REB'] + game_log['AST']
game_log['BS'] = game_log['BLK'] + game_log['STL']
game_log['FS'] = game_log['PTS'] + 1.2*game_log['REB'] + 1.5*game_log['AST'] + 3*game_log['BLK'] + 3*game_log['STL'] - game_log['TOV']

# prompt for stat to look up
stat = input('what stat?: ').upper()

# limit number of games if desired
num_games = input('how many games? <enter> if whole season: ')
if num_games != '':
	game_log = game_log.head(int(num_games))

# calculate statistical values
mean = game_log[stat].mean()
std_dev = game_log[stat].std()
print("mean: ", mean)
print("std_dev: ", std_dev)

# prompt for betting line
line = float(input('whats the line?: '))

# calculate distributions and probabilities
if hasattr(game_log, stat):
	dist = stats.norm(loc=mean, scale=std_dev)
	dist_p = stats.poisson(mu=mean)
	print(dist)
	prob = 1 - dist.cdf(line)
	prob_p = 1 - dist_p.cdf(line)
	print("mean: ", mean)
	print("std_dev: ", std_dev)
	print("normal: ", prob)
	print("poisson: ", prob_p)
else:
	print('no stat here')