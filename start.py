
from nba_api.stats import endpoints
from nba_api.stats.static import players, teams
import numpy as np
from scipy import stats
from datetime import datetime
import csv
import os
import os.path
import pandas as pd


def get_team_data():
	# input team 3-letter abbreviation
	home_input = input("home team: ")
	away_input = input("away team: ")
	home_info_list = teams.find_team_by_abbreviation(home_input)
	away_info_list = teams.find_team_by_abbreviation(away_input)

	# check if teams exists
	if len(home_info_list) == 0:
		print(f"{home_input} team not found.")
	if len(away_info_list) == 0:
		print(f"{away_input} team not found.")

	home_name = home_info_list['nickname']
	home_id = home_info_list['id']
	home_abbrev = home_info_list['abbreviation'] 
	away_name = away_info_list['nickname']
	away_id = away_info_list['id']
	away_abbrev = away_info_list['abbreviation']

	return {'home_name': home_name, 'home_id': home_id, 'home_abbrev': home_abbrev, 'away_name': away_name, 'away_id': away_id, 'away_abbrev': away_abbrev}

def get_active_players(team_id):
	endpoint = endpoints.CommonAllPlayers()
	data = endpoint.get_data_frames()[0]
	team_data = data[data['TEAM_ID'] == team_id]
	active_players = team_data[team_data['ROSTERSTATUS'] == 1][['DISPLAY_FIRST_LAST', 'PERSON_ID','TEAM_ID']]

	return active_players

def get_selected_player(team_data):
	home_players = get_active_players(team_data['home_id'])
	away_players = get_active_players(team_data['away_id'])

	print(f"{team_data['home_name']}:")
	for i in range(len(home_players)):
		player = home_players.iloc[i]
		print(f"{i+1}. {player['DISPLAY_FIRST_LAST']}")

	print(f"{team_data['away_name']}:")
	for i in range(len(away_players)):
		player = away_players.iloc[i]
		print(f"{i+len(home_players)+1}. {player['DISPLAY_FIRST_LAST']}")

	player_index_input= input("which player?: ")

	if not player_index_input:
		return None

	try:
		player_index = int(player_index_input) - 1
		if player_index < len(home_players):
			selected_player = home_players.iloc[player_index]
		else:
			selected_player = away_players.iloc[player_index - len(home_players)]
	
		print(f"{selected_player['DISPLAY_FIRST_LAST']}")		
		return {'player_name': selected_player['DISPLAY_FIRST_LAST'], 'player_id': selected_player['PERSON_ID'], 'player_team_id': selected_player['TEAM_ID']}

	except:
		return None

def get_stat():
	stat = input('what stat? <enter> to save and exit: ').upper()
	if stat == '':
		return None
	else:
		return stat

def get_num_games(game_log):
	num_games = input('how many games? <enter> if whole season: ')
	
	if num_games != '':
		return { 'num_games': int(num_games) }
	else:
		return { 'num_games': game_log.shape[0] }

def query_game_log(selected_player):
	game_log = endpoints.PlayerGameLog(player_id = selected_player['player_id']).get_data_frames()[0]

	game_log['PRA'] = game_log['PTS'] + game_log['REB'] + game_log['AST']
	game_log['PR'] = game_log['PTS'] + game_log['REB']
	game_log['PA'] = game_log['PTS'] + game_log['AST']
	game_log['RA'] = game_log['REB'] + game_log['AST']
	game_log['BS'] = game_log['BLK'] + game_log['STL']
	game_log['FS'] = game_log['PTS'] + 1.2*game_log['REB'] + 1.5*game_log['AST'] + 3*game_log['BLK'] + 3*game_log['STL'] - game_log['TOV']

	return game_log

def query_league_game_log():
	league_game_log = endpoints.LeagueGameLog(season = '2022-23').get_data_frames()[0]

	league_game_log['PRA'] = league_game_log['PTS'] + league_game_log['REB'] + league_game_log['AST']
	league_game_log['PR'] = league_game_log['PTS'] + league_game_log['REB']
	league_game_log['PA'] = league_game_log['PTS'] + league_game_log['AST']
	league_game_log['RA'] = league_game_log['REB'] + league_game_log['AST']
	league_game_log['BS'] = league_game_log['BLK'] + league_game_log['STL']
	league_game_log['FS'] = league_game_log['PTS'] + 1.2*league_game_log['REB'] + 1.5*league_game_log['AST'] + 3*league_game_log['BLK'] + 3*league_game_log['STL'] - league_game_log['TOV']

	return league_game_log 

def get_opp_opp_team_stats(selected_player, team_data, league_game_log, stat):
	opp_team = team_data['away_abbrev'] if selected_player['player_team_id'] == team_data['home_id'] else team_data['home_abbrev']
	all_opp_games = league_game_log[league_game_log['MATCHUP'].str.contains(opp_team)] 
	opp_games = all_opp_games[all_opp_games['MATCHUP'].str.split('@|vs.').str[1].str.strip() == opp_team]

	opp_opp_team_stats = []

	for i, game in opp_games.iterrows():
		matchup = game['MATCHUP']
		opp_opp_stat = game[stat]
		opp_opp_team_stats.append(opp_opp_stat)

	opp_opp_team_stats = pd.Series(opp_opp_team_stats)

	opp_avg = opp_opp_team_stats.mean()
	league_avg = league_game_log[stat].mean()
	weight = opp_avg / league_avg
	
	return {'weight': weight}

def get_line():
	return {'line': float(input('what\'s the line?: '))}

def get_simple_data(game_log, stat, line, num_games, opp_opp_team_stats):
	mean = game_log[stat].mean()
	std_dev = game_log[stat].std()
	weighted_avg = opp_opp_team_stats['weight']*mean
	line_hit = game_log[game_log[stat] >= line]
	hit_rate = len(line_hit) / num_games

	return { 'mean': round(mean, 2), 'std_dev': round(std_dev, 2), 'weighted_avg': round(weighted_avg,2), 'hit_rate': round(hit_rate, 2)}

def get_probabilities(line, simple_data):
	# calculate distributions and probabilities
	dist = stats.norm(loc=simple_data['mean'], scale=simple_data['std_dev'])
	dist_p = stats.poisson(mu=simple_data['mean'])
	dist_w = stats.poisson(mu=simple_data['weighted_avg'])
	prob = 1 - dist.cdf(line)
	prob_p = 1 - dist_p.cdf(line) 
	prob_w = 1 - dist_w.cdf(line)
	
	return { 'normal': round(prob, 2), 'poisson': round(prob_p, 2), 'weighted_poisson': round(prob_w, 2)}

def write_to_csv(data, filename):
	os.makedirs(os.path.dirname(filename), exist_ok=True)
	file_exists = os.path.isfile(filename)
	with open(filename, 'a', newline='') as csvfile:
		writer = csv.DictWriter(csvfile, fieldnames=data.keys())
		if not file_exists:
			writer.writeheader()

		writer.writerow(data)

def main():
	team_data = get_team_data()

	while True:

		selected_player = get_selected_player(team_data)
		if selected_player is None:
			break

		game_log = query_game_log(selected_player)
		league_game_log = query_league_game_log()

		while True:
			stat = get_stat()
			if stat is None:
				break
			
			opp_opp_team_stats = get_opp_opp_team_stats(selected_player, team_data, league_game_log, stat)
			line = get_line()
			num_games = [5,10,20,game_log.shape[0]]
					
			for num in num_games:
				simple_data = get_simple_data(game_log.head(num), stat, line['line'], num, opp_opp_team_stats)
				probabilities = get_probabilities(line['line'], simple_data)
				combined_data = {
					'timestamp': datetime.now(),
					'home_abbrev': team_data['home_abbrev'],
					'away_abbrev': team_data['away_abbrev'],
					'num_games': num,
					'player_name': selected_player['player_name'],
					'stat': stat,
					**line,
					**simple_data, 
					**probabilities
				}
				write_to_csv(combined_data, './dist/records.csv')

			write_to_csv({}, './dist/records.csv') # write an empty row

			print('written: ', num_games, ' games for: ', stat)

if __name__ == '__main__':
	main()