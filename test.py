
import pandas as pd


first_row = {'itr': 2,
             'sample_size' : 3,
             'bad_edges' : 4}

df = pd.DataFrame([first_row])

second_row = {'itr': 3,
             'sample_size' : 4,
             'bad_edges' : 5}

df.loc[len(df)] = second_row

print(df)

summary_row = {'itr' : df.loc[df.index[-1], 'itr'],
               'sample_size' : df.loc[df.index[-1], 'sample_size'],
               'bad_edges' : df['bad_edges'].sum()}

df.loc[len(df)] = summary_row

print(df)
