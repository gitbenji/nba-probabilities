
from nba_api.stats import endpoints
from nba_api.stats.static import players
import numpy as np
from scipy import stats
import time
import csv

def get_player_data():
	# get player by lastname
	# player_id = '1631109'
	player_lastname = input("player lastname: ")
	player_info_list = players.find_players_by_last_name(player_lastname)
	player_id = ''
	player_name = ''

	# check if more than one player with the same last name
	if len(player_info_list) > 1:
		for index, player in enumerate(player_info_list):
			if player['is_active']: 
				print(index, player['full_name'])
		which_player = int(input("which number: "))
		player_id = player_info_list[which_player]['id']
		player_name = player_info_list[which_player]['full_name']
	else:
		player_id = player_info_list[0]['id']
		player_name = player_info_list[0]['full_name']

	return {'name': player_name, 'id': player_id}

def query_game_log(player_data):
	# retrieve game log data for the season by player_id
	game_log = endpoints.PlayerGameLog(player_id = player_data['id']).get_data_frames()[0]

	# create cumulative stat columns in the dataframe
	game_log['PRA'] = game_log['PTS'] + game_log['REB'] + game_log['AST']
	game_log['PR'] = game_log['PTS'] + game_log['REB']
	game_log['PA'] = game_log['PTS'] + game_log['AST']
	game_log['AR'] = game_log['REB'] + game_log['AST']
	game_log['BS'] = game_log['BLK'] + game_log['STL']
	game_log['FS'] = game_log['PTS'] + 1.2*game_log['REB'] + 1.5*game_log['AST'] + 3*game_log['BLK'] + 3*game_log['STL'] - game_log['TOV']

	return game_log

# prompt for stat to look up
def get_stat():
	return { 'stat': input('what stat? type <enter><enter> to save and exit: ').upper() }

# limit number of games if desired
def get_num_games(game_log):
	num_games = input('how many games? <enter> if whole season: ')
	
	if num_games != '':
		return { 'num_games': int(num_games) }

	# set number of games to number of rows in the dataframe
	else:
		return { 'num_games': game_log.shape[0] }

def get_simple_data(game_log, stat):
	mean = game_log[stat].mean()
	std_dev = game_log[stat].std()
	print("mean: ", mean)
	print("std_dev: ", std_dev)
	return { 'mean': mean, 'std_dev': std_dev }

def get_line():
	return { 'line': float(input('what\'s the line?: ')) }

def get_probabilities(line, simple_data):
	# calculate distributions and probabilities
	dist = stats.norm(loc=simple_data['mean'], scale=simple_data['std_dev'])
	dist_p = stats.poisson(mu=simple_data['mean'])
	prob = 1 - dist.cdf(line)
	prob_p = 1 - dist_p.cdf(line)
	print("normal: ", prob)
	print("poisson: ", prob_p)
	return { 'normal': prob, 'poisson': prob_p }

def main():
	player_data = get_player_data()

	game_log = query_game_log(player_data)

	user_input = ''
	while True:

		stat = get_stat()

		# Check if the user double taps enter
		if stat == "" and user_input.endswith('\n\n'):
			break

		num_games = get_num_games(game_log)

		simple_data = get_simple_data(game_log.head(num_games['num_games']), stat['stat'])

		line = get_line()

		probabilities = get_probabilities(line['line'], simple_data)

		combined_data = {**player_data, **stat, **num_games, **simple_data, **line, **probabilities}

		print(combined_data)

if __name__ == '__main__':
	main()
