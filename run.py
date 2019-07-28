import pandas as pd
from sklearn.preprocessing import OrdinalEncoder
import subprocess
import ast


player_data = pd.read_csv('player_data.csv')
player_data_transformed = player_data.copy()

player_data_transformed['Team Id'] = OrdinalEncoder().fit_transform(player_data['Team'].values.reshape(-1, 1))
player_data_transformed['Team Id'] = pd.to_numeric(player_data_transformed['Team Id'], downcast='integer')
player_data_transformed['Pos Id'] = player_data['Pos'].apply(lambda p : {'GK': 0, 'DEF': 1, 'MID': 2, 'FWD': 3}[p])

def to_scaled_int(col):
    return pd.to_numeric(10 * col, downcast='integer')


for gw in range(6):
    gw_str = 'GW' + str(gw + 1)
    player_data_transformed[gw_str] = to_scaled_int(player_data[gw_str])
player_data_transformed['FPL Price'] = to_scaled_int(player_data['FPL Price'])

num_players = player_data_transformed.shape[0]
team_size = 12
max_points = max([player_data_transformed['GW' + str(gw + 1)].max() for gw in range(6)])
points = player_data_transformed['GW1'].tolist()
positions = player_data_transformed['Pos Id'].tolist()
clubs = player_data_transformed['Team Id'].tolist()

min_price , max_price = player_data_transformed['FPL Price'].min(), player_data_transformed['FPL Price'].max()
price_limit = 1000
prices = player_data_transformed['FPL Price'].tolist()

param_file = """
language ESSENCE' 1.0

letting numPlayers be {}
letting teamSize be {}
letting maxPoints be {}
letting points be {}
letting positions be {}
letting minPrice be {}
letting maxPrice be {}
letting priceLimit be {}
letting prices be {}
letting clubs be {}
""".format(num_players, team_size, max_points, points, positions, min_price, max_price, price_limit, prices, clubs)

player_data = player_data.drop([], axis=1)

with open("fpl.param", "w") as text_file:
    print(param_file, file=text_file)

subprocess.run(['./savilerow-1.7.0RC-linux/savilerow -run-solver fpl.eprime fpl.param'], stdout=subprocess.PIPE, shell=True)

with open('fpl.param.solution') as f:
    solution_lines = f.readlines()
solution = map(lambda v : v - 1, ast.literal_eval(solution_lines[5][16:]))

solution_df = player_data.loc[solution]
solution_df['tmp'] = player_data_transformed['Pos Id']
solution_df = solution_df.sort_values(by='tmp')
solution_df = solution_df.drop(['tmp'], axis=1)

with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    print(solution_df.to_string(index=False))
print("Total Price: {}".format(solution_df['FPL Price'].sum()))
print("Total Points: {}".format(solution_df['GW1-6 Pts'].sum()))
print("Points Per GW: {}".format(round(solution_df['GW1-6 Pts'].sum() / 6.0, 2)))

#subprocess.run(['rm fpl.param.info* fpl.param.minion fpl.param.solution'], shell=True)