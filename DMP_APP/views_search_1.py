import numpy as np
import pandas as pd
import json
import time
from .helpers import *
from .custom_logic import *

import warnings
warnings.filterwarnings('ignore')


def main_searching_algoritm(item_number, desc_short_in, part_number, manufacture_name, df): 
    if desc_short_in == '':
        desc_short_in = '_'
    

    print('SSSSSSSSSSSSSSSSSSSSSSSSSSS: df.shape  ', df.shape)
    
    tic = time.time()
    list_of_sources = {}
    part_number_original =part_number
    part_number  = part_number.replace(' ', '')
    manufacturer_name_original =manufacture_name 
    manufacture_name = manufacture_name.replace(' ', '')
    
    print(df.info())
    print(df['Material/Service No.'].tolist()[:10])
    # --------------------------------------------------------   Part_1 start   --------------------------------------------------------
    print('\nPhase 1')
    df_item = df[df['Material/Service No.'] == item_number]

    print('\n\n df_item shape:  ', df_item['Manufacturer Part No.'], '\n\n')
    result = pd.DataFrame(columns=df.columns)
    flag_1_1 = 0
    flag_1_2 = 0
    path = ''
    #! -------- START LEFT PART --------
    if df_item.shape[0] > 0:    # (1.1df_item_match_part) Left True
        path = '[1.1]'
        flag_1_1 = 1
        df_item_part_part = df_item[df_item['Manufacturer Part No.'] == part_number]  
        print('\n\n df_item_part_part shape:  ', df_item_part_part.shape)
        print('part nuumber',   part_number ,'\n\n')

        if df_item_part_part.shape[0] > 0:         # (1.1.1)  if item number and part number both are same
            print('1.1.1')
            path =  '[1.1.1]'
            result = result.append(append_as_a2a(df_item_part_part, path))
            if path not in list_of_sources:
                list_of_sources[path] = list_of_general_sources[path]

            # Continue
            print('1.1.3')
            path = '[1.1.3]'
            df_item_part_n_part = df_item[df_item['Manufacturer Part No.'] != part_number]
            if df_item_part_n_part.shape[0] > 0:
                result = result.append(check_description_similarity(desc_short_in, df_item_part_n_part, 0.0, path, list_of_sources))                

        else:
            # (1.1.2) FALSE
            print('1.1.2')
            path = '[1.1.2]'
            result = result.append(check_description_similarity(desc_short_in, df_item, 0.0, path, list_of_sources))

    # -------- END LEFT PART --------
        # Additional case (if item numbers and manufacturer names match check desc if satisfied then take as app to app)
        if manufacture_name != '':
            part_1 = df_item[df_item['Manufacturer Name'].str.contains(manufacture_name)]
            part_2 = df_item[df_item['Manufacturer Name'].apply(lambda x: True if x in manufacture_name else False)]
        
            df_item_manf_manf = part_1.append(part_2)
            df_item_manf_manf = df_item_manf_manf[~df_item_manf_manf.index.duplicated(keep='first')]

            if df_item_manf_manf.shape[0] > 0:
                path = '[1.3.2]'
                temp_add_1 = check_description_similarity(desc_short_in, df_item_manf_manf, 0.2, path, list_of_sources)
                if temp_add_1.shape[0] > 0:
                    result = result.append(append_as_a2a(temp_add_1, path))
                    if path not in list_of_sources:
                        list_of_sources[path] = list_of_general_sources[path]


            
    if  df_item.shape[0] == 0 or flag_1_1 == 1:      # Right False
        # This is totally different
        if flag_1_1 == 1:
            print('1.1.4')
            path = '[1.1.4]'
        else:
            print('1.2')
            path = '[1.2]'

        df_item_match_part = df[df['Manufacturer Part No.'] == item_number]

        if df_item_match_part.shape[0] > 0:
            print('1.2.2')
            path = '[1.2.2]'
            result = result.append(check_description_similarity(desc_short_in, df_item_match_part, 0.0, path, list_of_sources))
            flag_1_2 = 1

        if df_item_match_part.shape[0] == 0 or flag_1_2 == 1:
            if flag_1_2 == 1:
                print('1.2.3')
                path = '[1.2.3]'

            else:   
                print('1.2.1')
                path = '[1.2.1]'

                df_item_in_desc = pd.DataFrame(columns = result.columns) #/////////////////////////////////////////////////////
                df_item_in_desc = check_in_desc(df_item_in_desc, df, item_number)

                if df_item_in_desc.shape[0] > 0:  # if item number in description
                    print('1.2.1.2')
                    path = '[1.2.1.2]'
                    df_item_in_desc_match_part = df_item_in_desc[df_item_in_desc['Manufacturer Part No.'] == part_number]
                    if df_item_in_desc_match_part.shape[0] > 0:  # if manufacture part numbers match
                        print('1.2.1.3')
                        path = '[1.2.1.3]'
                        result = result.append(append_as_a2a(df_item_in_desc_match_part, path))
                        if path not in list_of_sources:
                            list_of_sources[path] = list_of_general_sources[path]

                        #Continue
                        print('1.2.1.5')
                        path = '[1.2.1.5]'
                        new_df_item_in_desc_n_match_part = df_item_in_desc[df_item_in_desc['Manufacturer Part No.'] != part_number]
                        result = result.append(check_description_similarity(desc_short_in, new_df_item_in_desc_n_match_part, 0.0, path, list_of_sources))
                        print('1.2.1.6')
                        path =  '[1.2.1.6]'
                        print('Go to second step')

                    else:
                        print('1.2.1.4')
                        path = '[1.2.1.4]'
                        result = result.append(check_description_similarity(desc_short_in, df_item_in_desc, 0.0, path, list_of_sources))
                        print('1.2.1.6')
                        path =  '[1.2.1.6]'
                        print('Go to second step')
                        # go to second step
                else:
                    print('1.2.1.1')
                    path =  '[1.2.1.1]'
                    print('Go to second step')
                    # go to second step

    print('\nPhase 2')
    # # --------------------------------------------------------   Part_1 end   --------------------------------------------------------

    # *************************************************************************************************************************************************************************************


    # --------------------------------------------------------   Part_2 start   --------------------------------------------------------
    flag_2_1 = 0
    flag_2_2 = 0
    flag_2_3 = 0
    # --------- START LEFT SIDE ---------
    df_part = df[df['Manufacturer Part No.'] == part_number]
    if df_part.shape[0] > 0:
        print('2.1')
        path = '[2.1]'
        flag_2_1 = 1

        df_part_manf_name = df_part[df_part['Manufacturer Name'] == manufacture_name]  
        if df_part_manf_name.shape[0] > 0:         # (1.1.1)  if item number and part number both are same
            print('2.1.1')
            path =  '[2.1.1]'
            result = result.append(append_as_a2a(df_part_manf_name, path))
            if path not in list_of_sources:
                list_of_sources[path] = list_of_general_sources[path]

            # Continue
            print('2.1.3')
            path = '[2.1.3]'
            df_part_n_part = df_part[df_part['Manufacturer Name'] != manufacture_name]
            if df_part_n_part.shape[0] > 0:
                result = result.append(check_description_similarity(desc_short_in, df_part_n_part, 0.0, path, list_of_sources))

        else:
            print('2.1.2')
            path = '[2.1.2]'
            result = result.append(check_description_similarity(desc_short_in, df_part, 0.0, path, list_of_sources))
    # --------- END LEFT SIDE ---------

    if df_part.shape[0] == 0 or flag_2_1 == 1:
        if flag_2_1 == 1:
            print('2.1.4')
            path = '[2.1.4]'
        else:
            print('2.2')
            path = '[2.2]'


        df_part_item = df[df['Material/Service No.'] == part_number]

        if df_part_item.shape[0] > 0:
            print('2.3.1')
            path = '[2.3.1]'
            result = result.append(check_description_similarity(desc_short_in, df_part_item, 0.0, path, list_of_sources))
            flag_2_2  = 1

        if df_part_item.shape[0] == 0 or flag_2_2 == 1:
            if flag_2_2 == 1:
                print('2.3.2')
                path =  '[2.3.2]'
            else:
                print(2.3)
                path = '[2.3]'

        df_part_in_desc = pd.DataFrame(columns = result.columns)
        df_part_in_desc = check_in_desc(df_part_in_desc, df, part_number)     

        if df_part_in_desc.shape[0] > 0:  # if part number in description
            print('2.4.1')
            path = '[2.4.1]'
            result = result.append(check_description_similarity(desc_short_in, df_part_in_desc, 0.0, path, list_of_sources))
            flag_2_3 = 1

        if df_part_in_desc.shape[0] == 0 or flag_2_3 == 1:
            if flag_2_3 == 1:
                print('2.4.2')
                path = '[2.4.2]'
            else:
                print('2.4')
                path =  '[2.4]'
            print('Go to third step')
    # --------------------------------------------------------   Part_2 end   --------------------------------------------------------

    # *************************************************************************************************************************************************************************************
    
    # --------------------------------------------------------   Part_3 start   --------------------------------------------------------
    print('\nPhase 3')
    flag_3_1 = 0
    flag_3_2 = 0
    flag_3_3 = 0 

    df_manf_name = df[df['Manufacturer Name'] == manufacture_name]

    if df_manf_name.shape[0] > 0:
        print('3.1')
        path = '[3.1]'
        result = result.append(check_description_similarity(desc_short_in, df_manf_name, 0.0, path, list_of_sources))
        flag_3_1 = 1

    if flag_3_1 == 1:
        print('3.1.2')
        path = '[3.1.2]'
    else:
        print('3.2')
        path = '[3.2]'

    df_manf_name_vendor = df[df['Vendor Name'] == manufacture_name]

    if df_manf_name_vendor.shape[0] > 0:
        print('3.3.1')
        path = '[3.3.1]'
        result = result.append(check_description_similarity(desc_short_in, df_manf_name_vendor, 0.0, path, list_of_sources))
        flag_3_2  = 1

    if flag_3_2 == 1:
        print('3.3.2')
        path = '[3.3.2]'
    else:
        print('3.3')
        path ='[3.3]'

    df_manf_name_in_desc = pd.DataFrame(columns = result.columns)   #/////////////////////////////////////////////////////

    df_manf_name_in_desc = check_in_desc(df_manf_name_in_desc, df, manufacture_name)     

    if df_manf_name_in_desc.shape[0] > 0:  # if manufacture_name in description
        print('3.4.1')
        path = '[3.4.1]'
        result = result.append(check_description_similarity(desc_short_in, df_manf_name_in_desc, 0.0, path, list_of_sources))
        flag_3_3 = 1

    if df_manf_name_in_desc.shape[0] == 0 or flag_3_3 == 1:
        if flag_3_3 == 1:
            print('3.4.2')
            path = '[3.4.2]'
        else:
            print('3.4')
            path =  '[3.4]'
        print('Go to fourth step')

    # --------------------------------------------------------   Part_3 end   --------------------------------------------------------

    # *************************************************************************************************************************************************************************************

    # --------------------------------------------------------   Part_4 start   --------------------------------------------------------
    print('\nPhase 4')
    # tic = time.time()
    path = '[4]'
    
    tic_2 = time.time()
    
    c = check_description_similarity(desc_short_in, df, 0.4, path, list_of_sources)
    toc_2 = time.time()
    print(toc_2-tic_2)
    result = result.append(c)
    
    # print('SSSSSSSSSSSSSS: ', c.shape)


    # --------------------------------------------------------   Part_4 end   --------------------------------------------------------


    # --------------------------------------------------------   Part_5 end   --------------------------------------------------------
    if manufacturer_name_original != '' and part_number_original != '':
        df_manf_in_desc =  df[(df['PO Item Description'].str.contains(manufacturer_name_original)) | (df['PO Item Description'].str.contains(manufacture_name))]
        if df_manf_in_desc.shape[0] > 0: 
            df_manf_and_part_in_desc = df_manf_in_desc[(df_manf_in_desc['PO Item Description'].str.contains(part_number_original))  |  (df_manf_in_desc['PO Item Description'].str.contains(part_number))]

            temp_df_1 = check_description_similarity(desc_short_in, df_manf_and_part_in_desc, 0.1, path, list_of_sources)
            if temp_df_1.shape[0] > 0:         # (1.1.1)  if item number and part number both are same
                print('Rule 5')
                path =  '[5.1]'
                result = result.append(append_as_a2a(temp_df_1, path))
    # --------------------------------------------------------   Part_5 end   --------------------------------------------------------

    # --------------------------------------------------------   Part_6 start   --------------------------------------------------------
    if manufacture_name == '' and part_number == '' and item_number != '' and desc_short_in != '':
        df_6 = df[df['Material/Service No.'] == item_number]
        if len(df_6.groupby(['Manufacturer Part No.', 'Manufacturer Name'])) == 1 and df_6['Manufacturer Part No.'].iloc[0] == '#' and df_6['Manufacturer Name'].iloc[0] == 'NotAssigned':
            temp_df_6 = check_description_similarity(desc_short_in, df_6, 0.8, path, list_of_sources)
            in_ = desc_short_in.replace(':',' ').replace(': ',' ').replace(',',' ').replace(', ',' ').replace(';',' ').replace('; ',' ').replace('-',' ').split()
            mask_6 =  temp_df_6['desc_words_short'].apply(lambda x: generic_desc_sim(x, in_))
            result_6_df  = temp_df_6[mask_6].copy()
            if result_6_df.shape[0] > 0:
                path =  '[6.1]'
                result = result.append(append_as_a2a(result_6_df, path))
          
    # ----------------------------------------  ----------------   Part_6 end   --------------------------------------------------------

    # --------------------------------------------------------   Part_7 start   --------------------------------------------------------
    if item_number == '' and part_number == '' and manufacture_name == '' and desc_short_in != '':
        temp_df_7 = df[df['PO Item Description'] == desc_short_in] 
        if temp_df_7.shape[0] > 0:
            path =  '[7.1]'
            result = result.append(append_as_a2a(temp_df_7, path))
    # --------------------------------------------------------   Part_7 end   --------------------------------------------------------



    app = pd.DataFrame(columns=result.columns)
    user_input_desc = list(set(desc_short_in.replace(':',' ').replace(': ',' ').replace(',',' ').replace(', ',' ').replace(';',' ').replace('; ',' ').replace('-',' ').split()))
    if result.shape[0] > 0:
        result = result[result['PO Item Value (GC)'] > 0]
        result['Unit Price'] = result['PO Item Value (GC)'] / result['PO Item Quantity']
        app = result[result['desc'] == 'm_p'].copy()
        app = app[~app.index.duplicated(keep='first')]
        a = result[result['desc'] == 'm_p']
        b = result[result['desc'] != 'm_p']
        b = b[~b.index.duplicated(keep='first')]
        a = a.append(b)
        a = a[~a.index.duplicated(keep='first')]
        result = a

    toc = time.time()
    print('Total running time: ', toc-tic)    

    # Normalization
    display_converted_uom=False
    if app.shape[0] > 0:
        app['base_index'] = app.index
        app = normalize(app)
        display_converted_uom=True
        if app.shape[0] == app[app['Unit Price'] == app['Converted Price']].shape[0] or app.shape[0] == app[app['UoM_label'] == 1].shape[0]:
            display_converted_uom=False

    app.reset_index(inplace=True, drop=True)
    app['index']=app.index

    result.reset_index(inplace=True, drop=True)
    result['index']=result.index

    json_records=result.reset_index().to_json(orient='records')
    result_data=json.loads(json_records)

    json_records=app.reset_index().to_json(orient='records')
    app_data=json.loads(json_records)  

    return {
        "display_converted_uom":display_converted_uom,
        "all_dataframe":df,
        "result_data_all":result_data,
        "result_app_to_app": app_data,
        "user_input_desc":user_input_desc, 
        "result_content":content,
        }
