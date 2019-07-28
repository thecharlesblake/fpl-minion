import pandas as pd
from sklearn.preprocessing import OrdinalEncoder
import subprocess
import ast

pd.options.mode.chained_assignment = None


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
team_size = 10
max_points = max([player_data_transformed['GW' + str(gw + 1)].max() for gw in range(6)])
points = [player_points.tolist() for _, player_points in player_data_transformed[['GW' + str(gw+1) for gw in range(6)]].iterrows()]
positions = player_data_transformed['Pos Id'].tolist()
clubs = player_data_transformed['Team Id'].tolist()

min_price , max_price = player_data_transformed['FPL Price'].min(), player_data_transformed['FPL Price'].max()
price_limit = 1000
prices = player_data_transformed['FPL Price'].tolist()

param_file = """
language ESSENCE' 1.0

letting gwCount be {}
letting numPlayers be {}
letting teamSize be {}
letting maxPoints be {}
letting positions be {}
letting minPrice be {}
letting maxPrice be {}
letting priceLimit be {}
letting prices be {}
letting clubs be {}
letting points be {}
""".format(6, num_players, team_size, max_points, positions, min_price, max_price, price_limit, prices, clubs, points)

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

total_points = 0
for gw in range(6):
    gw = 'GW' + str(gw+1)
    max_idx = solution_df[gw].idxmax()
    gw_points = solution_df[gw].sum() + solution_df[gw].max()
    total_points += gw_points
    print("{} Points: {}".format(gw, round(gw_points, 2)))
    solution_df[gw][max_idx] = '*' + str(solution_df[gw][max_idx])
print("Total Points: {}".format(round(total_points, 2)))
print("Points Per GW: {}".format(round(total_points / 6.0, 2)))
print("Total Price: {}".format(solution_df['FPL Price'].sum()))

with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    print(solution_df.to_string(index=False))

#subprocess.run(['rm fpl.param.info* fpl.param.minion fpl.param.solution'], shell=True)