from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from numpy.lib.shape_base import dsplit
import numpy as np
import pandas as pd
import json
import random
from random import randint
import matplotlib.pyplot as plt
import time
from worker import *
import plotly.graph_objects as go
import plotly.express as px
import urllib
import requests
from datetime import date
from search_alg_parallel_short import *

import warnings
warnings.filterwarnings('ignore')

pb_df = pd.read_csv(r'C:\Users\OMEN 30L AD\Desktop\DMP\Data\solar_price_book.csv')
all_columns = ['BP Material / \nService Master No.', 'Manufacturer Name',  'Manufacturer Part Number', 'BP Short Description',
 'Supplier Description', 'Incoterms Key', '2021 rates', '2020 rates']
pb_df.drop([0], inplace=True)
pb_df['Incoterms Key'] = 'FCA'
pb_df = pb_df[all_columns]
pb_df.dropna(subset=['2021 rates'], inplace=True)

def is_float(x):
    try:
        float(x)
    except ValueError:
        return False
    return True

pb_df = pb_df[pb_df['2021 rates'].apply(lambda x: is_float(x))]
pb_df['2021 rates'] = pb_df['2021 rates'].astype('float')

pb_df = pb_df[(pb_df['2021 rates'] > 0) & (pb_df['2020 rates'] > 0)]
pb_df.reset_index(drop=True, inplace=True)
pb_df['app_id'] = pb_df.index

pb_df['BP Material / \nService Master No.'].astype('str')
pb_df['BP Material / \nService Master No.'] = pb_df['BP Material / \nService Master No.'].apply(lambda x: str(x)[:-2])


import random
random.seed(0)
new_pb_df = pb_df.copy()

new_pb_df['PO Item Creation Date'] = '2021-08-02'
new_pb_df['PO Item Creation Date'] = pd.DatetimeIndex(new_pb_df['PO Item Creation Date'])

a = new_pb_df['BP Material / \nService Master No.'].tolist()
b = new_pb_df['Supplier Description'].tolist()
c = new_pb_df['Manufacturer Part Number'].tolist()
d = new_pb_df['Manufacturer Name'].tolist()
e = new_pb_df['app_id'].tolist()
 

# from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Pool


tic = time.time()

def main():

    with Pool() as pool:
        result = pd.concat(pool.starmap(searching_algorithm, zip(a, b, c, d)))
    print(result.shape)
    result.to_csv(r'static\A2A.csv')

# Required for Windows:
if __name__ == '__main__':    
    # freeze_support()
    main()

toc = time.time()

print('Total running time ffff: ', toc-tic)