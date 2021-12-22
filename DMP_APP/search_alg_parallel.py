list_of_general_sources = { '[1.1.1]': "Material/Services numbers and Manufacture part numbers match      (apple to apple)",
                            '[1.1.2]': "Material/Services numbers match but Manufacture part numbers don't match",
                            '[1.1.3]': "Material/Services numbers match but Manufacture part numbers don't match",
                            '[1.2.2]': "Material/Services numbers don't match but Material/Services numbers matches with Manufacture part number",
                            '[1.2.1.3]': "Material/Services numbers is in description and Manufacture part numbers match       (apple to apple)"  ,
                            '[1.2.1.4]': "Material/Services numbers is in description but Manufacture part numbers don't match",
                            '[1.2.1.5]': "Material/Services numbers is in description but Manufacture part numbers don't match",
                            '[1.3.2]': "Item numbers and manufacturer names match and similarity for description is more than fifty percent",
                            '[2.1.1]': "Manufacture part numbers and manufacture names match  (apple to apple)",
                            '[2.1.2]': "Manufacture part numbers match but manufacture names don't match",
                            '[2.1.3]': "Description base after fetching",
                            '[2.3.1]': "Manufacture part numbers don't match but Manufacture part numbers matches with Material/Services numbers",
                            '[2.4.1]': "Manufacture part number is in description",
                            '[3.1]': "Manufacture names match",
                            '[3.3.1]': "Manufacture name matches with Vendor name",
                            '[3.4.1]': "Manufacture name is in description",
                            '[4]': "Only descriptions are similar"}
                            

def check_description(desc, df, threshold, path, list_of_sources):
    a = pd.DataFrame(columns = df.columns)
    s1 = set(desc.replace(':',' ').replace(': ',' ').replace(',',' ').replace(', ',' ').replace(';',' ').replace('; ',' ').replace('-',' ').split())
    # print('Length is ', len(df), '   for description checking')
    for index_i, row in enumerate(df[['PO Item Description', 'Long Description']].values):
        s2_small = set(row[0].replace(':',' ').replace(': ',' ').replace(',',' ').replace(', ',' ').replace(';',' ').replace('; ',' ').replace('-',' ').split())
        sim_score_small = float(len(s1.intersection(s2_small)) / len(s1.union(s2_small)))
        s2_long = set(row[1].replace(':',' ').replace(': ',' ').replace(',',' ').replace(', ',' ').replace(';',' ').replace('; ',' ').replace('-',' ').split())
        sim_score_long = float(len(s1.intersection(s2_long)) / len(s1.union(s2_long)))
        flag = 's'
        if sim_score_small >= sim_score_long:
            df.iat[index_i, df.columns.get_loc('score')] = sim_score_small
        else:
            df.iat[index_i, df.columns.get_loc('score')] = sim_score_long
            flag = 'l'
                        
        if df.iat[index_i, df.columns.get_loc('score')] > threshold:
            df.iat[index_i, df.columns.get_loc('path')] = path
            df.iat[index_i, df.columns.get_loc('desc')] = str(flag)
            a = a.append(df.iloc[index_i])
            if path not in list_of_sources:
                list_of_sources[path] = list_of_general_sources[path]
    return a


from .worker import *
import numpy as np
import pandas as pd
import json
import time
from .custom_logic import *
import logging 
# from .helpers import *
import os.path




import warnings
warnings.filterwarnings('ignore')



try:
    df = pd.DataFrame()
    uploaded_file_path = str(BASE_DIR) + '/static/df_all_regions_uploaded.csv'
    if os.path.isfile(uploaded_file_path)  : 
        
        df = pd.read_csv(uploaded_file_path, parse_dates=['PO Item Creation Date'], dtype="unicode")
        
        print('TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT')

        df = df[df['Region'] == 'AGT']
        df = df[df['PO Status Name'] != 'Deleted']
        df = df[df['PO Status Name'] != 'Held']
        df = df[df['PO Item Deletion Flag'] != 'X']

        all_rows=["PO No.","PO Item No.","Incoterms Name", "Material/Service No.","PO Item Description", "Manufacturer Name", "Vendor Name", 
                    "Manufacturer Part No.", "Long Description","PO Item Creation Date","PO Item Quantity", "PO Item Quantity Unit", "PO Item Value (GC)",
                    "PO Item Value (GC) Unit", "Product Category", "Product Category Description", "PO Status Name", 'Region']


        df = df[all_rows]
        df['PO Item Description'] = df['PO Item Description'].replace(np.nan, ' ', regex=True)    
        df['Long Description'] = df['Long Description'].replace(np.nan, ' ', regex=True)
        
        df['score'] = -1.0
        df['path'] = ''
        df['desc'] = ''
        
        df['desc_words_short'] = [short_desc.replace(':',' ').replace(': ',' ').replace(',',' ').replace(', ',' ').replace(';',' ').replace('; ',' ').replace('-',' ').replace('/',' ').split() for short_desc in df['PO Item Description'].values]
        df['desc_words_long'] = [long_desc.replace(':',' ').replace(': ',' ').replace(',',' ').replace(', ',' ').replace(';',' ').replace('; ',' ').replace('-',' ').replace('/',' ').split() for long_desc in df['Long Description'].values]

except Exception as e:

    df = pd.DataFrame()
    print('EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE')
    logging.warning(e)

   
def searching_algorithm(item_number, desc_short_in, part_number, manufacture_name, df=df):

    tic = time.time()

    # tic = time.time()
    apple_to_apple = 0
    list_of_sources = {}

    # --------------------------------------------------------   Part_1 start   --------------------------------------------------------margin-left: -5rem; 
    # print('\nPhase 1')
    df_item = df[df['Material/Service No.'] == item_number]
    result = pd.DataFrame(columns=df.columns)

    if df_item.shape[0] > 0:    # (1.1) Left True
        path = '[1.1]'
        df_item_part_part = df_item[df_item['Manufacturer Part No.'] == part_number]  

        if df_item_part_part.shape[0] > 0:         # (1.1.1)  if item number and part number both are same
            path =  '[1.1.1]'
            df_item_part_part.loc[df_item_part_part.index.tolist(), 'score'] = 0.9
            df_item_part_part.loc[df_item_part_part.index.tolist(), 'path'] = path
            df_item_part_part.loc[df_item_part_part.index.tolist(), 'desc'] = 'm_p'
            apple_to_apple += df_item_part_part.shape[0]
            result = result.append(df_item_part_part)

    
    
        # -------- END LEFT PART --------
        # Additional case (if item numbers and manufacturer names match check desc if satisfied then take as app to app)
        part_1 = df_item[df_item['Manufacturer Name'].str.contains(manufacture_name)]
        part_2 = df_item[df_item['Manufacturer Name'].apply(lambda x: True if x in manufacture_name else False)]
        df_item_manf_manf = part_1.append(part_2)
        df_item_manf_manf = df_item_manf_manf[~df_item_manf_manf.index.duplicated(keep='first')]

        if df_item_manf_manf.shape[0] > 0:
            path = '[1.3.2]'
            temp_add_1 = check_description(desc_short_in, df_item_manf_manf, 0.3, path, list_of_sources)
            if temp_add_1.shape[0] > 0:
                temp_add_1.loc[temp_add_1.index.tolist(), 'score'] = 0.9
                temp_add_1.loc[temp_add_1.index.tolist(), 'path'] = path
                temp_add_1.loc[temp_add_1.index.tolist(), 'desc'] = 'm_p'
                result = result.append(temp_add_1)
            

    df_item_in_desc = pd.DataFrame(columns = result.columns) #/////////////////////////////////////////////////////
    df_item_in_desc = check_in_desc(df_item_in_desc, df, item_number)

    if df_item_in_desc.shape[0] > 0:  # if item number in description
        path = '[1.2.1.2]'
        df_item_in_desc_match_part = df_item_in_desc[df_item_in_desc['Manufacturer Part No.'] == part_number]
        if df_item_in_desc_match_part.shape[0] > 0:  # if manufacture part numbers match
            path = '[1.2.1.3]'
            df_item_in_desc_match_part.loc[df_item_in_desc_match_part.index.tolist(), 'score'] = 0.9
            df_item_in_desc_match_part.loc[df_item_in_desc_match_part.index.tolist(), 'path'] = path
            df_item_in_desc_match_part.loc[df_item_in_desc_match_part.index.tolist(), 'desc'] = 'm_p'
            apple_to_apple += df_item_in_desc_match_part.shape[0]
            result = result.append(df_item_in_desc_match_part)

    # --------------------------------------------------------   Part_1 end   --------------------------------------------------------


    # *************************************************************************************************************************************************************************************


    # --------------------------------------------------------   Part_2 start   --------------------------------------------------------
    df_part = df[df['Manufacturer Part No.'] == part_number]
    if df_part.shape[0] > 0:
        path = '[2.1]'
        df_part_manf_name = df_part[df_part['Manufacturer Name'] == manufacture_name]  
        if df_part_manf_name.shape[0] > 0:         # (1.1.1)  if item number and part number both are same
            path =  '[2.1.1]'
            df_part_manf_name.loc[df_part_manf_name.index.tolist(), 'score'] = 0.9
            df_part_manf_name.loc[df_part_manf_name.index.tolist(), 'path'] = path
            df_part_manf_name.loc[df_part_manf_name.index.tolist(), 'desc'] = 'm_p'
            apple_to_apple += df_part_manf_name.shape[0]
            result = result.append(df_part_manf_name)
    

    app = pd.DataFrame(columns=result.columns)
    
    if result.shape[0] > 0:
        result['PO Item Value (GC)'] = result['PO Item Value (GC)'].astype(float)
        result['Unit Price'] = result['PO Item Value (GC)'].astype('float') / result['PO Item Quantity'].astype('float').astype('int')
        app = result[result['desc'] == 'm_p']
        app = app[~app.index.duplicated(keep='first')]
        app = app[app['PO Item Value (GC)'] > 0] 
        app.loc[app['Material/Service No.'] != item_number, 'Material/Service No.']  = item_number
        
        
    toc = time.time()

    print('Total running time from searching algorithm: ', toc-tic)

    app['base_index'] = app.index
    return app

