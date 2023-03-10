
from nba_api.stats import endpoints
from nba_api.stats.static import players
import numpy as np
from scipy import stats
from datetime import datetime
import csv
import os
import os.path

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
	return { 'stat': input('what stat? <enter> to save and exit: ').upper() }

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
	return { 'mean': round(mean, 4), 'std_dev': round(std_dev, 4) }

def get_line():
	return { 'line': float(input('what\'s the line?: ')) }

def get_probabilities(line, simple_data):
	# calculate distributions and probabilities
	dist = stats.norm(loc=simple_data['mean'], scale=simple_data['std_dev'])
	dist_p = stats.poisson(mu=simple_data['mean'])
	prob = 1 - dist.cdf(line)
	prob_p = 1 - dist_p.cdf(line)
	return { 'normal': round(prob, 4), 'poisson': round(prob_p, 4) }

def write_to_csv(data, filename):
	os.makedirs(os.path.dirname(filename), exist_ok=True)
	file_exists = os.path.isfile(filename)
	with open(filename, 'a', newline='') as csvfile:
		writer = csv.DictWriter(csvfile, fieldnames=data.keys())
		if not file_exists:
			writer.writeheader()  # file doesn't exist yet, write a header
		writer.writerow(data)

def main():
	player_data = get_player_data()

	game_log = query_game_log(player_data)

	user_input = ''
	while True:

		stat = get_stat()

		# Check if the user taps enter
		if stat['stat'] == '':
			print('goodbye')
			break

		line = get_line()

		num_games = [5, 10, 20, game_log.shape[0]]

		for num in num_games:
			simple_data = get_simple_data(game_log.head(num), stat['stat'])

			probabilities = get_probabilities(line['line'], simple_data)

			combined_data = {**{'timestamp': datetime.now()}, **player_data, **stat, **{'num_games': num}, **simple_data, **line, **probabilities}

			write_to_csv(combined_data, './dist/records.csv')

		print('written: ', num_games, ' games for: ', stat['stat'])

if __name__ == '__main__':
	main()
