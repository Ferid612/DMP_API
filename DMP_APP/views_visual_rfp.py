from .views_visual_1 import *
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import numpy as np
import pandas as pd
import json
import time
from .worker import *
import plotly.graph_objects as go
import plotly.express as px
import re

import datetime
import datetime as dt
from .helpers import *
from functools import reduce
from DMP_API.settings import BASE_DIR
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cluster import DBSCAN
from importlib import reload
# from .search_alg_parallel import searching_algorithm
import sys
import importlib
from DMP_APP import search_alg_parallel
from .helpers_rfp import *
from multiprocessing import Pool



import warnings
warnings.filterwarnings('ignore')
class DMP_RFP(DMP):
    
    all_headers=["PO No.","PO Item No.","Incoterms Name", "Material/Service No.","Vendor Name","PO Item Description","Manufacturer Name",
            "Manufacturer Part No.","Long Description","PO Item Creation Date","PO Item Value (GC)","PO Item Value (GC) Unit", "PO Item Quantity Unit", "Unit Price","Converted Price", "score","path",
            "desc","index","desc_words_short", "desc_words_long", 'Region']

    @csrf_exempt
    def test_function(request):
        response=JsonResponse({"Data":"data"})
        add_get_params(response)
        return response


    @csrf_exempt 
    def upload_file_historical(request): 
        # Build the POST parameters
        if request.method == 'POST':
            try:
                
                df=upload_file_helpers(request)
                DMP_RFP.uploaded_historical_data = df
                response = JsonResponse({'answerr': "Success", })
                add_get_params(response)
                return response
         
            except Exception as e:
                my_traceback = traceback.format_exc()
             
                logging.error(my_traceback)
                response = JsonResponse({'error_text':str(e),
                                         'error_text_2':my_traceback
                                         })
                response.status_code = 505
                
                add_get_params(response)
                return response 
                            
        else:
            response = JsonResponse({'Answer': "Sorry this method running only POST method. Thanks from DRL", })
            add_get_params(response)
            return response

    @csrf_exempt
    def search_rfp_new(request):
        if request.method =='POST':
            try:
                currency_content = get_curency_data()
                currency = str(DMP_RFP.rfp_currency_name)
                currency_ratio = currency_content['USD' + currency]
                rfp_region_name = str(DMP_RFP.rfp_region_name)
                pb_df = DMP_RFP.uploaded_rfp_file

                #! Automatically change column names if needed
                DMP_RFP.new_pb_df = preprocess_pricebook_data(pb_df, currency_ratio)
                a = DMP_RFP.new_pb_df['BP Material / \nService Master No.'].tolist()
                b = DMP_RFP.new_pb_df['Supplier Description'].tolist()
                c = DMP_RFP.new_pb_df['Manufacturer Part Number'].tolist()
                d = DMP_RFP.new_pb_df['Manufacturer Name'].tolist()


                tic = time.time()
                print('CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC')
                DMP_RFP.uploaded_historical_data.to_csv(str(BASE_DIR) + '/static/df_all_regions_uploaded.csv', index=False)
                reload(search_alg_parallel)
        
                with Pool() as pool:
                    result = pd.concat(pool.starmap(search_alg_parallel.searching_algorithm, zip(a, b, c, d)))
                result = result[~result.index.duplicated(keep='first')]

                toc = time.time()
                print('Total Runtime for RFP: ', toc-tic)

                result.to_csv(str(BASE_DIR) + '/static/A2A_28_08_2021.csv')
                a2a = pd.read_csv(str(BASE_DIR) + '/static/A2A_28_08_2021.csv')



                a2a['PO Item Creation Date'] = pd.DatetimeIndex(a2a['PO Item Creation Date'])
                a2a = a2a[a2a['PO Item Creation Date'] >= '2018-01-01']
            
                material_id_list = a2a['Material/Service No.'].value_counts().index.tolist()
                identifier = [1 for i in range(len(material_id_list))]
                
                with Pool() as pool:
                    a2a_conv = pd.concat(pool.starmap(parallel_uom, zip(material_id_list, identifier)))

                display_converted_uom_rfp=True
                if a2a_conv.shape[0] == a2a_conv[a2a_conv['Unit Price'] == a2a_conv['Converted Price']].shape[0] or a2a_conv.shape[0] == a2a_conv[a2a_conv['UoM_label'] == 1].shape[0]:
                    display_converted_uom_rfp=False

                a2a_conv.reset_index(inplace=True)
                a2a_conv['index'] = a2a_conv.index

                DMP_RFP.a2a_conv = a2a_conv 
                DMP_RFP.display_converted_uom_rfp = display_converted_uom_rfp 

                response=JsonResponse({"display_converted_uom_rfp":display_converted_uom_rfp})
                add_get_params(response)
                
                return response
            except Exception as e:
                my_traceback = traceback.format_exc()
                
                logging.error(my_traceback)
                response = JsonResponse({'error_text':str(e),
                                            'error_text_2':my_traceback
                                            })
                response.status_code = 505
        
                add_get_params(response)
                return response 
            
        else:
            response = JsonResponse({'Answer': "Sorry this method running only POST method. Thanks from DRL", })
            add_get_params(response)
            return response



    @csrf_exempt
    def search_rfp(request):
        try:

        # ! ****************** start Region searching ******************
            df_full= pd.read_csv(str(BASE_DIR) + "/static/df_all_regions_uploaded.csv",error_bad_lines=False, dtype="unicode",parse_dates=['PO Item Creation Date'])

            DMP_RFP.df_full_region = df_full
            a2a = pd.read_csv(str(BASE_DIR) + '/static/A2A_28_08_2021_Region.csv',error_bad_lines=False, dtype="unicode",parse_dates=['PO Item Creation Date'])

            DMP_RFP.a2a=a2a
            # DMP_RFP.list_of_regions_rfp = a2a['Region'].unique().tolist()

            intersect = reduce(np.intersect1d, a2a.groupby('Region')['Material/Service No.'].apply(list))
            result_df = a2a.loc[a2a['Material/Service No.'].isin(intersect), :].copy()
            result_df['PO Item Quantity'] = result_df['PO Item Quantity'].astype('float')
            result_df['Unit Price'] = result_df['Unit Price'].astype('float')
            result_df['PO Item Value (GC)'] = result_df['PO Item Value (GC)'].astype('float')
            

            DMP_RFP.result_df=result_df
            DMP_RFP.a2a=a2a

            list_of_regions = result_df['Region'].value_counts().index.tolist()
            list_of_regions = list_of_regions[::-1]
            list_of_regions.remove('AGT')
            list_of_regions.append('AGT')

            DMP_RFP.list_of_regions=list_of_regions

        # ! ****************** end Region searching ******************

        #************ RFP searching section start**********************#!****        
            DMP_RFP.df_full =  DMP_RFP.uploaded_historical_data[DMP_RFP.uploaded_historical_data['Region'] == DMP_RFP.rfp_region_name]        
            DMP_RFP.df_full = DMP_RFP.df_full[(DMP_RFP.df_full['PO Status Name'] != 'Deleted') & (DMP_RFP.df_full['PO Status Name'] != 'Held') & (DMP_RFP.df_full['PO Item Deletion Flag'] != 'X')]
        
            DMP_RFP.df_full['PO Item Creation Date'] = pd.DatetimeIndex(DMP_RFP.df_full['PO Item Creation Date'])
            DMP_RFP.min_date = DMP_RFP.df_full.loc[DMP_RFP.df_full['PO Item Creation Date'].idxmin()]['PO Item Creation Date'].strftime('%Y-%m-%d')
            DMP_RFP.max_date = DMP_RFP.df_full.loc[DMP_RFP.df_full['PO Item Creation Date'].idxmax()]['PO Item Creation Date'].strftime('%Y-%m-%d')
            DMP_RFP.categories_rfp = DMP_RFP.a2a_conv['Product Category Description'].value_counts().index.tolist()

            app_to_app_rfp = DMP_RFP.a2a_conv.copy()
            app_to_app_rfp['PO Item Creation Date'] = pd.DatetimeIndex(app_to_app_rfp['PO Item Creation Date'])
            app_to_app_rfp['Material/Service No.'] = app_to_app_rfp['Material/Service No.'].astype('str')

            #!111111
            DMP_RFP.app_to_app_rfp_after_search = app_to_app_rfp.copy()
            DMP_RFP.app_to_app_rfp_after_search_2 = app_to_app_rfp.copy()

            pb_df = DMP_RFP.new_pb_df
            
            #!222222
            DMP_RFP.pb_df_after_search = pb_df.copy()
            idxs = app_to_app_rfp['Material/Service No.'].value_counts().index.tolist()

            pb_df['BP Material / \nService Master No.'] =  pb_df['BP Material / \nService Master No.'].astype('str')
            app_rfp_df = pb_df[pb_df['BP Material / \nService Master No.'].isin(idxs)].copy()
            
            #!333333


            def normalize(app_rfp_df):

                types_of_UoM = { 'Weight': {'KG': 1, 'LO': 0.015, 'BAL': 217.72, 'LB':0.45},
                                'Area':   {'M2': 1, 'JO': 1.6},
                                'Length': {'M': 1, 'FT': 0.3048, 'LN': 1, 'LS': 1, 'IN': 0.0254, 'KM': 1000, 'ROL': 1, 'FOT': 0.3048},
                                'Volume': {'L': 1, 'DR': 208.2, 'GAL': 3.79, 'M3': 1000, 'PL': 1, 'ML': 0.001, 'BTL': 0.75} }


                i = 0
                for index, row in app_rfp_df.iterrows():
                    for key in types_of_UoM:
                        a = types_of_UoM[key]
                        if  row['UOM'] in a.keys():
                            print('BP Material / Service Master No.', app_rfp_df.iat[i, app_rfp_df.columns.get_loc('BP Material / \nService Master No.')])
                            print('2021  rates', app_rfp_df.iat[i, app_rfp_df.columns.get_loc('2021 rates')])
                            print('2021  rates', app_rfp_df.iat[i, app_rfp_df.columns.get_loc('2020 rates')])
                            print('a[row[UOM]]', a[row['UOM']])

                            app_rfp_df.iat[i, app_rfp_df.columns.get_loc('2021 rates')] = app_rfp_df.iat[i, app_rfp_df.columns.get_loc('2021 rates')] / a[row['UOM']]
                            app_rfp_df.iat[i, app_rfp_df.columns.get_loc('2020 rates')] = app_rfp_df.iat[i, app_rfp_df.columns.get_loc('2020 rates')] / a[row['UOM']]
                            app_rfp_df.iat[i, app_rfp_df.columns.get_loc('UOM')] = next(iter(a))
                    i += 1
                
                values_contains = ['pack of', '/pack', 'pk of', '/pk', 'pkt of', '/pkt', 'per pack', 'drum of']
                values_ends = ['/pac', '/pa', '/p']
                app_rfp_df['UOM_label'] = 0
                
                try:
                    app_rfp_df.reset_index(inplace=True, drop=True)
                except:
                    pass

                list_of_mids = []
                for index, row in app_rfp_df.iterrows():
                    material_id = row['BP Material / \nService Master No.']
                    supp_desc = row['Supplier Description'].split(',')
                    short_desc = row['BP Short Description'].split(',')
                    long_desc = row['BP Long Description'][:40].split(',') 
                    material_id = str(material_id).replace(' ', '')
                    if material_id == '11045408':
                        print('11111111111111111111111111111111111111111111111111    Unit Price: ', app_rfp_df.loc[index, '2021 rates'])

                    if row['UOM'] in ['EA', 'PH', 'BOX', 'PK']:
                        flag = 0
                        desc_word_list  = list(set(supp_desc).union(set(short_desc)))
                        for word in desc_word_list:
                            for value in values_contains:
                                if value.lower() in word.lower() or word.lower().endswith('/pac') or word.lower().endswith('/pa') or word.lower().endswith('/p') :
                                    newstr = ''.join((ch if ch in '0123456789.-e' else ' ') for ch in word)
                                    listOfNumbers = [float(i) for i in newstr.split() if is_float(i)]
                                    if len(listOfNumbers) > 1:
                                        try:
                                            newstr =  word.lower()[word.lower().find(value.lower()):word.lower().find(value.lower())+len(value) + 5]
                                            listOfNumbers = [float(i) for i in newstr.split() if is_float(i)]
                                            if len(listOfNumbers) == 0:
                                                listOfNumbers = re.findall(r'\d+', newstr)

                                            if len(listOfNumbers) == 0:
                                                newstr =  word.lower()[word.lower().find(value.lower())-5:word.lower().find(value.lower())]
                                                listOfNumbers = [float(i) for i in newstr.split() if is_float(i)]
                                                if len(listOfNumbers) == 0:
                                                    listOfNumbers = re.findall(r'\d+', newstr)

                                        except:
                                            continue
                                    if len(listOfNumbers) != 1:
                                        continue
                                    each_count = listOfNumbers[0]
                                    list_of_mids.append(row['BP Material / \nService Master No.'])
                                    app_rfp_df.iat[index, app_rfp_df.columns.get_loc('2021 rates')] /= float(each_count)
                                    app_rfp_df.iat[index, app_rfp_df.columns.get_loc('2020 rates')] /= float(each_count)
                                    app_rfp_df.iat[index, app_rfp_df.columns.get_loc('UOM')] = 'EA'
                                    app_rfp_df.iat[index, app_rfp_df.columns.get_loc('UOM_label')] = 1
                                    row['UOM_label'] = 1
                                    flag = 1
                                    break
                            if flag == 1:
                                break

                        if flag == 0:  
                            if fuzz.partial_ratio(short_desc, long_desc) >= 50:
                                desc_word_list  = row['BP Long Description'].split(',') 
                                for word in desc_word_list:
                                    for value in values_contains:
                                        if value.lower() in word.lower() or word.lower().endswith('/pac') or word.lower().endswith('/pa') or word.lower().endswith('/p') :
                                            newstr = ''.join((ch if ch in '0123456789.-e' else ' ') for ch in word)
                                            listOfNumbers = [float(i) for i in newstr.split() if is_float(i)]

                                            if len(listOfNumbers) > 1:
                                                try:
                                                    newstr =  word.lower()[word.lower().find(value.lower()):word.lower().find(value.lower())+len(value) + 5]
                                                    listOfNumbers = [float(i) for i in newstr.split() if is_float(i)]
                                                    if len(listOfNumbers) == 0:
                                                        listOfNumbers = re.findall(r'\d+', newstr)

                                                    if len(listOfNumbers) == 0:
                                                        newstr =  word.lower()[word.lower().find(value.lower())-5:word.lower().find(value.lower())]
                                                        listOfNumbers = [float(i) for i in newstr.split() if is_float(i)]
                                                        if len(listOfNumbers) == 0:
                                                            listOfNumbers = re.findall(r'\d+', newstr)

                                                except:
                                                    continue
                                            if len(listOfNumbers) != 1:
                                                continue
                                            each_count = listOfNumbers[0]
                                        
                                            list_of_mids.append(row['BP Material / \nService Master No.'])
                                            app_rfp_df.iat[index, app_rfp_df.columns.get_loc('2021 rates')] /= float(each_count)
                                            app_rfp_df.iat[index, app_rfp_df.columns.get_loc('2020 rates')] /= float(each_count)
                                            app_rfp_df.iat[index, app_rfp_df.columns.get_loc('UOM')] = 'EA'
                                            app_rfp_df.iat[index, app_rfp_df.columns.get_loc('UOM_label')] = 1
                                            row['UOM_label'] = 1
                                            flag = 1
                                            break
                                    if flag == 1:
                                        break
    

                    alt_uom_df = pd.read_csv(str(BASE_DIR) + '/static/AGT alternative UOM.csv', error_bad_lines=False, dtype="unicode")
                    
                    if alt_uom_df[alt_uom_df['Material ID'] == str(material_id)].shape[0] > 0: #okay just one minute okay          
                        al_un = alt_uom_df[alt_uom_df['Material ID'] == str(material_id)]['AUn'].tolist()[0]
                        b_un = alt_uom_df[alt_uom_df['Material ID'] == str(material_id)]['BUn'].tolist()[0]
                        counter = alt_uom_df[alt_uom_df['Material ID'] == str(material_id)]['Counter'].tolist()[0]
                        denom = alt_uom_df[alt_uom_df['Material ID'] == str(material_id)]['Denom.'].tolist()[0]
                        fraction = (int(counter) / int(denom))
                
                        
                        uom_group_list = ['PH', 'PK', 'PAC']  # holds uoms that represents group

                        if app_rfp_df.iat[index, app_rfp_df.columns.get_loc('UOM_label')] != 1 and  (al_un in uom_group_list  and row['UOM'] in uom_group_list):                        
                                if material_id == '11045408':
                                    print('222222222222222222222222222222222222222222222222222222222222222222222222')
                                app_rfp_df.loc[index, '2021 rates'] = app_rfp_df.loc[index, '2021 rates'] / fraction
                                app_rfp_df.loc[index, '2020 rates'] = app_rfp_df.loc[index, '2020 rates'] / fraction
                                app_rfp_df.loc[index, 'UOM'] = b_un


                return app_rfp_df
        except Exception as e:
            my_traceback = traceback.format_exc()
            
            logging.error(my_traceback)
            response = JsonResponse({'error_text':str(e),
                                        'error_text_2':my_traceback
                                        })
            response.status_code = 505
            
            add_get_params(response)
            return response 
        app_rfp_df = normalize(app_rfp_df)

        # ADD PB Transactions to Basket 2
        DMP_RFP.app_rfp_df_after_search = app_rfp_df.copy()
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!! URGENT !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        new_a2a = pd.merge(app_to_app_rfp, app_rfp_df[['BP Material / \nService Master No.', '2021 rates', '2020 rates']], 
                        how='left', left_on='Material/Service No.', right_on='BP Material / \nService Master No.')


        new_a2a['2021 rates'] = new_a2a['2021 rates'].astype('float')
        weight_df = pd.DataFrame(new_a2a.groupby('Material/Service No.')['PO Item Value (GC)'].sum())
        weight_df.rename(columns={'PO Item Value (GC)':'Item Total Spend'}, inplace=True)
        weight_df.reset_index(inplace=True)

        #!44444
        new_a2a = pd.merge(new_a2a, weight_df,  how='left', on='Material/Service No.')
        new_a2a['Item Weight'] = new_a2a['Item Total Spend'] / (new_a2a['PO Item Value (GC)'].sum())
        new_a2a['delta'] = 0.0
        new_a2a['percentage'] = 0.0            
        new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax(), 'delta'] = new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['2021 rates'] - new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['Unit Price']
        new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax(), 'percentage'] = (new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['delta'] / new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['Unit Price']) * 100

        #!5555
        DMP_RFP.new_a2a_after_search = new_a2a
        
        today = pd.to_datetime("today").normalize()
        current_date = today.strftime('%Y-%m-%d')
        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!  DATE ISSSUE  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1
        rfp_1 = new_a2a.drop_duplicates(subset = ['Material/Service No.'], keep = 'last') 
        rfp_1['PO Item Creation Date'] = current_date
        rfp_1['Unit Price'] =  rfp_1['2021 rates']
        rfp_1['delta'] = 0
        rfp_1['percentage'] = 0
        DMP_RFP.rfp_1_after_search=rfp_1

        #!6666        
        rfp_2 = new_a2a.drop_duplicates(subset = ['Material/Service No.'], keep = 'last') 
        rfp_2['PO Item Creation Date'] = '2020-01-01'
        rfp_2['Unit Price'] =  rfp_1['2020 rates']
        rfp_2['delta'] = 0
        rfp_2['percentage'] = 0
        DMP_RFP.rfp_2_after_search = rfp_2

        #!77777
        temp_dash = rfp_1.append(rfp_2)
        DMP_RFP.temp_dash_after_search=temp_dash
        df_1 = new_a2a.append(temp_dash)
        df_1['PO Item Creation Date'] = pd.DatetimeIndex(df_1['PO Item Creation Date'])
        #! bug
        try:
            df_1.reset_index(inplace=True)
        except: 
            print('Bug solved 422')
        
        df_1['delta'] = df_1['2021 rates'] - df_1['Unit Price']

        #!8888
        DMP_RFP.df_1_after_search = df_1
        total_items_app = pb_df.shape[0]
        app_to_apple_count_pb = app_rfp_df.shape[0]
        benchmark_perscent = (app_to_apple_count_pb/total_items_app)*100
        benchmark_perscent = round(benchmark_perscent, 2)
        
        DMP_RFP.total_items_rfp_after_search=total_items_app
        DMP_RFP.benchmark_perscent_rfp_after_search=benchmark_perscent

        DMP_RFP.plot_bg='rgba(171, 248, 190, 0.8)'

        response=JsonResponse({
            "data":"name is succeess",
        })
        add_get_params(response)
        return response


    #************ RFP searching section end************************   
    @csrf_exempt 
    def upload_file(request): 
        # Build the POST parameters
        if request.method == 'POST':
            try:
                for index, file_ts in enumerate(request.FILES.getlist('input_files')):
                    try:
                        csv_file_name=file_ts.name            
                        rfp_file=pd.read_csv(file_ts.file)
                        DMP_RFP.uploaded_rfp_file=rfp_file

                    except Exception as e:
                        continue
            except:
                print("Not successfully", "file_ts.name")    

            response = JsonResponse({'Answer': "Sorry this method running only POST method. Thanks from DRL", })
            add_get_params(response)
            return response
        else:
            response = JsonResponse({'Answer': "Sorry this method running only POST method. Thanks from DRL", })
            add_get_params(response)
            return response

    #*****************************RFP Visualization SECTION************************************************************

    @csrf_exempt
    def get_filter_data_rfp(request):

        if request.method =='POST':
            # all_apple_to_apple 
          

            #! return finded rows data in table 
            response = JsonResponse({
                    # 'apple_to_apple_count':DMP_RFP.apple_to_apple_count,
                    # 'regions_rfp':DMP_RFP.list_of_regions_rfp,
                    'vendor_names':  ["SOLAR"],
                    'categories': DMP_RFP.categories_rfp,
                    'rfp_name':DMP_RFP.rfp_name,
                    'region_name':DMP_RFP.rfp_region_name,

                    'vendor_name':DMP_RFP.rfp_vendor_name,
                    'currency':DMP_RFP.rfp_currency_name,

                    'benchmark_perscent_rfp':DMP_RFP.benchmark_perscent_rfp_after_search,
                    'total_items_rfp':DMP_RFP.total_items_rfp_after_search
                })
                
            add_get_params(response)
            return response

    @csrf_exempt
    def get_dates(request):
        if request.method =='POST':
            response = JsonResponse({
                 'min_date':DMP_RFP.min_date,
                 'max_date':DMP_RFP.max_date,
                 })
            add_get_params(response)
            return response

    @csrf_exempt
    def get_dates_rfp(request):
        if request.method =='POST':
            # all_apple_to_apple 
            #! return finded rows data in table 
            response = JsonResponse({
                 'min_date':DMP_RFP.min_date_non_pricebook,
                 'max_date':DMP_RFP.max_date_non_pricebook,
                 })
            add_get_params(response)
            return response

    @csrf_exempt
    def get_discount(request):
        if request.method =='POST':
            # json_records_app=DMP_RFP.unique_increase_df.columns.to_json(orient='records')
            # increase_json=json.loads(json_records_app)    
            # pricebook_table=pd.read_csv(str(BASE_DIR) + '/static/unique_increase_df.csv', error_bad_lines=False, dtype="unicode")
            unique_increase_df=DMP_RFP.unique_increase_df
            try:
              unique_increase_df.reset_index(inplace=True)
              unique_increase_df['index'] = unique_increase_df.index
              del unique_increase_df['level_0']

            except Exception as e:
                pass

            DMP_RFP.unique_increase_df=unique_increase_df
         
            df=unique_increase_df

            DMP_RFP.dicount_df=df
            json_string = df.columns.tolist()
            json_records_all=df.to_json(orient='records')
            
            df=json.loads(json_records_all)

            # df=pd.read_csv(str(BASE_DIR) + "/static/unique_increase_df.csv', error_bad_lines=False, dtype="unicode")
         
            response = JsonResponse({
                 'discount_table': df,
                 'discount_columns': json_string,

                 })
            add_get_params(response)
            return response

    @csrf_exempt
    def pricebook_save(request):
        dict = json.loads(request.POST.get('key1'))
        
        pricebook_table=DMP_RFP.dicount_df

        dict_df= pd.DataFrame(dict.items(), columns=['index', 'Input Value'])

        
        dict_df['index']=dict_df['index'].astype('str')
        
        pricebook_table['index']=pricebook_table['index'].astype('str')
        
        
        if 'Proposed Price' in pricebook_table.columns.tolist():
            del pricebook_table['Proposed Price']   



        pricebook_table = pd.merge(pricebook_table, dict_df, how='left',on="index")
        del pricebook_table['index']
    

        pricebook_table.to_csv(str(BASE_DIR) + "/static/discount.csv",index=False)

        response = JsonResponse({
                    'pricebook_columns':"pricebook_columns",
                'pricebook_table':  "pricebook_table",
        })
        add_get_params(response)
        return response


    @csrf_exempt
    def visual_ajax_1_rfp(request):
        if request.method =='POST':
            input_min_date = request.POST.get('input_min_date')
            input_max_date = request.POST.get('input_max_date')
            input_categories =request.POST.getlist('categories_rfp[]')
            today = pd.to_datetime("today").normalize()
            current_date = today.strftime('%Y-%m-%d')


            df_1 = DMP_RFP.df_1_after_search.copy()
            df_1[df_1['Product Category Description'].isin(input_categories)]
            
            temp_dash = DMP_RFP.temp_dash_after_search.copy()
            temp_dash = temp_dash[temp_dash['Product Category Description'].isin(input_categories)]
            
            app_to_app_rfp = DMP_RFP.app_to_app_rfp_after_search.copy()
            app_rfp_df = DMP_RFP.app_rfp_df_after_search.copy()
            new_a2a = get_a2a_df(app_to_app_rfp, app_rfp_df)

            new_a2a = new_a2a[(new_a2a['PO Item Creation Date'] >= input_min_date) & (new_a2a['PO Item Creation Date'] <= input_max_date) & (new_a2a['Product Category Description'].isin(input_categories))]

            if new_a2a.shape[0] > 0:
                list_of_idxes = get_most_spent_material_indexes(new_a2a)

                #!bug   
                if len(list_of_idxes) > 0:
        
                    result = df_1[df_1['Material/Service No.'].isin(list_of_idxes)]
                    result_2 = new_a2a[new_a2a['Material/Service No.'].isin(list_of_idxes)]
                    result_3 = temp_dash[temp_dash['Material/Service No.'].isin(list_of_idxes)]

                    last_purchased = result_2.loc[result_2.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]
                    #  *************************************** FIXXX BUGGGGGGGGGGG ************************************************
                    for index, row in last_purchased.iterrows():
                        result.loc[result['Material/Service No.'] == row['Material/Service No.'], 'Material # + abs percentage'] = row['Material/Service No.'] + '  (' + str(round(row['percentage'],1),) + '%)'
                        result.loc[result['Material/Service No.'] == row['Material/Service No.'], 'percentage'] = row['percentage']
                        result_3.loc[result_3['Material/Service No.'] == row['Material/Service No.'], 'Material # + abs percentage'] = row['Material/Service No.'] + '  (' + str(round(row['percentage'],1),) + '%)'
                    

                    top_10_total_spend = result_2['PO Item Value (GC)'].sum()
                    total_spend = new_a2a['PO Item Value (GC)'].sum()
                    top_10_spend_weight = round((top_10_total_spend / total_spend) * 100, 1)
                    list_of_idxs =  list_of_idxes[0] 


                    fig = go.Figure()

                    fig = plot_1_1_pb(fig, result, list_of_idxs)
                    fig, result_3 = plot_1_2_pb(fig, result_3, list_of_idxs)
                    fig = plot_1_3_pb(fig, result, list_of_idxs, today, current_date)                                    
                    fig = plot_1_4_pb(fig, result_3, list_of_idxs, today, current_date)
    
                    fig = update_layout_fig_1_1(fig)                    
                   
                    div_1 = opy.plot(fig, auto_open=False, output_type='div')
                    
                    #! return finded rows data in table 
                    response = JsonResponse({            
                        'plot_div_1_rfp': div_1,
                        'top_10_spend_weight':top_10_spend_weight,
                            })
                    add_get_params(response)
                    return response
                else:
                    fig = update_layout_fig_1_2(DMP_RFP.plot_bg)
                    div_1 = opy.plot(fig, auto_open=False, output_type='div')
                    #! return finded rows data in table 
                    response = JsonResponse({            
                        'plot_div_1_rfp': div_1,
                        'top_10_spend_weight': "0",
                            })
                    add_get_params(response)
                    return response
            else:
                fig = update_layout_fig_1_2(DMP_RFP.plot_bg)
                div_1 = opy.plot(fig, auto_open=False, output_type='div')
            
                #! return finded rows data in table 
                response = JsonResponse({            
                    'plot_div_1_rfp': div_1,
                    'top_10_spend_weight': "0",
                        })
                add_get_params(response)
                return response
        else:
            response = JsonResponse({            
                    'plot_div_1_rfp': "No Data!",                    
                        })
            add_get_params(response)
            return response


    @csrf_exempt
    def visual_ajax_2_rfp(request):
        if request.method =='POST':
            input_min_date = request.POST.get('input_min_date')
            input_max_date = request.POST.get('input_max_date')
            input_categories =request.POST.getlist('categories_rfp[]')
            today = pd.to_datetime("today").normalize()
            current_date = today.strftime('%Y-%m-%d')

            df_1 = DMP_RFP.df_1_after_search.copy()
            df_1[df_1['Product Category Description'].isin(input_categories)]
            
            rfp_1 = DMP_RFP.rfp_1_after_search.copy()
            rfp_1 = rfp_1[rfp_1['Product Category Description'].isin(input_categories)]

            temp_dash = DMP_RFP.temp_dash_after_search.copy()
            temp_dash = temp_dash[temp_dash['Product Category Description'].isin(input_categories)]
            

            app_to_app_rfp = DMP_RFP.app_to_app_rfp_after_search.copy()
            app_rfp_df = DMP_RFP.app_rfp_df_after_search.copy()
            new_a2a = get_a2a_df(app_to_app_rfp, app_rfp_df)

            new_a2a = new_a2a[(new_a2a['PO Item Creation Date'] >= input_min_date) & (new_a2a['PO Item Creation Date'] <= input_max_date) & (new_a2a['Product Category Description'].isin(input_categories))]

            
            drop_df = new_a2a[new_a2a['delta'] < 0]
            if drop_df.shape[0] > 0:

                drop_df_idxs = drop_df['Material/Service No.'].tolist()
                a_1 = new_a2a[new_a2a['Material/Service No.'].isin(drop_df_idxs)]
                a_2 = rfp_1[rfp_1['BP Material / \nService Master No.'].isin(drop_df_idxs)]
                result_3 = temp_dash[temp_dash['Material/Service No.'].isin(drop_df_idxs)]

                all_drop_df = a_1.append(a_2)
                all_drop_df['PO Item Creation Date'] = pd.DatetimeIndex(all_drop_df['PO Item Creation Date'])


                for index, row in drop_df.iterrows():
                    all_drop_df.loc[all_drop_df['Material/Service No.'] == row['Material/Service No.'], 'Material # + percentage'] = row['Material/Service No.'] + '  (' + str(round(row['percentage'],1),) + '%)'
                    all_drop_df.loc[all_drop_df['Material/Service No.'] == row['Material/Service No.'], 'percentage'] = row['percentage']
                    all_drop_df.loc[all_drop_df['Material/Service No.'] == row['Material/Service No.'], 'Item WEight'] = row['Item Weight']
    
                    result_3.loc[result_3['Material/Service No.'] == row['Material/Service No.'], 'Material # + percentage'] = row['Material/Service No.'] + '  (' + str(round(row['percentage'],1),) + '%)'
                    result_3.loc[result_3['Material/Service No.'] == row['Material/Service No.'], 'percentage 0'] = row['percentage']


                
                result_3 = result_3.sort_values('PO Item Creation Date')
                result_3['delta'] = result_3['2021 rates'] - result_3['2020 rates']
                result_3['percentage'] = (result_3['delta'] / result_3['2020 rates']) * 100

                result_3['Material # + percentage'] = result_3['Material # + percentage'] + '  (' + result_3['percentage'].round(1).astype('str') + '%)'  # 2020 rates
                
                for index, row in result_3.iterrows():
                    all_drop_df.loc[all_drop_df['Material/Service No.'] == row['Material/Service No.'], 'Material # + percentage'] = row['Material # + percentage']
                
                drop_10_total_spend = a_1['PO Item Value (GC)'].sum()
                total_spend = new_a2a['PO Item Value (GC)'].sum()
                drop_10_total_spend_weight = (drop_10_total_spend / total_spend) * 100   
                                
                sorted_list = np.unique(abs(all_drop_df['percentage']).tolist())
                sorted_list = np.round(sorted_list,2)
                sorted_list[::-1].sort()


                fig = go.Figure()

                fig = plot_2_1_pb(fig, all_drop_df, sorted_list)
                fig = plot_2_2_pb(fig, result_3, sorted_list)
                fig = plot_2_3_pb(fig, all_drop_df, sorted_list, today, current_date)
                fig = plot_2_4_pb(fig, result_3, sorted_list, today, current_date)


                fig = update_layout_fig_2_1(fig)

                div_1 = opy.plot(fig, auto_open=False, output_type='div')

                response = JsonResponse({            
                    'plot_div_2_rfp': div_1,
                    'drop_10_total_spend_weight':round(drop_10_total_spend_weight,2),
                        })
                add_get_params(response)
                return response
            else:
                fig = update_layout_fig_1_2(DMP_RFP.plot_bg)

                div_1 = opy.plot(fig, auto_open=False, output_type='div')

                response = JsonResponse({            
                    'plot_div_2_rfp': div_1,
                    'drop_10_total_spend_weight': "0",
                        })
                add_get_params(response)
                return response
        else:
            response = JsonResponse({            
                    'plot_div_2_rfp': "No Data!",
                    'drop_10_total_spend_weight': "0",
                        })
            add_get_params(response)
            return response


    @csrf_exempt
    def visual_ajax_3_rfp(request):
        if request.method =='POST':

            input_min_date= request.POST.get('input_min_date')
            input_max_date= request.POST.get('input_max_date')
            input_categories=request.POST.getlist('categories_rfp[]')
            today = pd.to_datetime("today").normalize()
            current_date = today.strftime('%Y-%m-%d')


            app_to_app_rfp = DMP_RFP.app_to_app_rfp_after_search.copy()
            app_rfp_df = DMP_RFP.app_rfp_df_after_search.copy()
            new_a2a = get_a2a_df(app_to_app_rfp, app_rfp_df)
            new_a2a = new_a2a[(new_a2a['PO Item Creation Date'] >= input_min_date) & (new_a2a['PO Item Creation Date'] <= input_max_date) & (new_a2a['Product Category Description'].isin(input_categories))]

                        

            rfp_1 = DMP_RFP.rfp_1_after_search.copy()
            rfp_1 = rfp_1[rfp_1['Product Category Description'].isin(input_categories)]


            temp_dash = DMP_RFP.temp_dash_after_search.copy()
            temp_dash = temp_dash[temp_dash['Product Category Description'].isin(input_categories)]
            
                
            increase_df = new_a2a[new_a2a['delta'] > 0]
            
            if increase_df.shape[0] > 0:



                increase_df_idxs = increase_df['Material/Service No.'].tolist()
                a_1 = new_a2a[new_a2a['Material/Service No.'].isin(increase_df_idxs)]
                a_2 = rfp_1[rfp_1['BP Material / \nService Master No.'].isin(increase_df_idxs)]
                result_3 = temp_dash[temp_dash['Material/Service No.'].isin(increase_df_idxs)]

                all_increase_df = a_1.append(a_2)
                all_increase_df['PO Item Creation Date'] = pd.DatetimeIndex(all_increase_df['PO Item Creation Date'])


                for index, row in increase_df.iterrows():
                    all_increase_df.loc[all_increase_df['Material/Service No.'] == row['Material/Service No.'], 'Material # + percentage'] = row['Material/Service No.'] + '  (' + str(round(row['percentage'],1),) + '%)'
                    all_increase_df.loc[all_increase_df['Material/Service No.'] == row['Material/Service No.'], 'percentage'] = row['percentage']
                    all_increase_df.loc[all_increase_df['Material/Service No.'] == row['Material/Service No.'], 'Item Weight'] = row['Item Weight']
                    
                    result_3.loc[result_3['Material/Service No.'] == row['Material/Service No.'], 'Material # + percentage'] = row['Material/Service No.'] + '  (' + str(round(row['percentage'],1),) + '%)'
                    result_3.loc[result_3['Material/Service No.'] == row['Material/Service No.'], 'percentage 0'] = row['percentage']
                
                
                
                
                result_3 = result_3.sort_values('PO Item Creation Date')
                result_3['delta'] = result_3['2021 rates'] - result_3['2020 rates']
                result_3['percentage'] = (result_3['delta'] / result_3['2020 rates']) * 100
                result_3['Material # + percentage'] = result_3['Material # + percentage'] + '  (' + result_3['percentage'].round(1).astype('str') + '%)'
                
                for index, row in result_3.iterrows():
                    all_increase_df.loc[all_increase_df['Material/Service No.'] == row['Material/Service No.'], 'Material # + percentage'] = row['Material # + percentage']
              
       
                increase_10_total_spend = a_1['PO Item Value (GC)'].sum()
                total_spend = new_a2a['PO Item Value (GC)'].sum()
                increase_10_total_spend_weight = (increase_10_total_spend / total_spend) * 100
                increase_10_total_spend_weight = round(increase_10_total_spend_weight,2)
                
                sorted_list = np.unique(abs(all_increase_df['percentage']).tolist())
                sorted_list = np.round(sorted_list,2)
                sorted_list[::-1].sort()


                fig = go.Figure()
                fig = plot_3_1_pb(fig, all_increase_df, sorted_list)
                fig = plot_3_2_pb(fig, result_3, sorted_list)
                fig = plot_3_3_pb(fig, all_increase_df, sorted_list, today, current_date)
                fig = plot_3_4_pb(fig, result_3, sorted_list, today, current_date)


                fig = update_layout_fig_2_1(fig)
                
                div_1 = opy.plot(fig, auto_open=False, output_type='div')
                    #! return finded rows data in table 
                response = JsonResponse({       
                    'increase_10_total_spend_weight': increase_10_total_spend_weight,     
                    'plot_div_3_rfp': div_1,
                        })
                        
                add_get_params(response)


                return response
            else:
                fig = update_layout_fig_1_2(DMP_RFP.plot_bg)
                div_1 = opy.plot(fig, auto_open=False, output_type='div')
            
                #! return finded rows data in table 
                response = JsonResponse({            
                    'plot_div_3_rfp': div_1,
                    'increase_10_total_spend_weight': "0",
                    })    

                add_get_params(response)
                return response
        else:
            response = JsonResponse({            
                    'plot_div_3_rfp': "No Data!",
                    'increase_10_total_spend_weight': "0",
                        })
                        
            add_get_params(response)
            return response
                

    @csrf_exempt
    def visual_ajax_4_rfp(request):
        if request.method =='POST':
            
            input_categories = request.POST.getlist('categories_rfp[]')
            app_to_app_rfp = DMP_RFP.app_to_app_rfp_after_search.copy()
            app_to_app_rfp = app_to_app_rfp[app_to_app_rfp['Product Category Description'].isin(input_categories)]
            app_rfp_df = DMP_RFP.app_rfp_df_after_search.copy()
            
            new_a2a = pd.merge(app_to_app_rfp, app_rfp_df[['BP Material / \nService Master No.', '2021 rates', '2020 rates']], 
                               how='left', left_on='Material/Service No.', right_on='BP Material / \nService Master No.')
            new_a2a['2021 rates'] = new_a2a['2021 rates'].astype('float')
            new_a2a = new_a2a[new_a2a['Product Category Description'].isin(input_categories)]
            
            
            today = pd.to_datetime("today").normalize()
            one_year_before = today - datetime.timedelta(days=1*365)
            starting_day_of_last_year = one_year_before.replace(month=1, day=1)    
            ending_day_of_last_year = one_year_before.replace(month=12, day=31)
     
            
            df_4 = new_a2a.copy()
            one_year_df_4 = df_4[(df_4['PO Item Creation Date'] >= '2020-01-01') & (df_4['PO Item Creation Date'] <= '2020-12-31')]
            temp_df = one_year_df_4.groupby('Material/Service No.')['PO Item Quantity'].mean().reset_index()
            temp_df.rename(columns={'PO Item Quantity': 'New Demand'}, inplace=True)
            one_year_df_4 = pd.merge(one_year_df_4, temp_df,  how='left', on='Material/Service No.')

            count = len(one_year_df_4['Material/Service No.'].value_counts().index.tolist())
            rfp_percentage = (count / DMP_RFP.pb_df_after_search.shape[0]) * 100            

            # Current
            one_year_df_4['Curren RFP Last Year Spend'] = one_year_df_4['PO Item Quantity'] * one_year_df_4['2021 rates']
            sum_1 = one_year_df_4['Curren RFP Last Year Spend'].sum()

            # Average
            a_4 = pd.DataFrame(df_4.groupby('Material/Service No.')['Unit Price'].mean())
            a_4.rename(columns={'Unit Price':'Average Price'}, inplace=True)
            a_4.reset_index(inplace=True)
            one_year_df_4 = pd.merge(one_year_df_4, a_4,  how='left',on='Material/Service No.')

            one_year_df_4['Average Spend'] = one_year_df_4['PO Item Quantity'] * one_year_df_4['Average Price']
            sum_2 = one_year_df_4['Average Spend'].sum()



            # Last Purchasing RFP
            l_4 = df_4.loc[df_4.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]
            l_4 = l_4.rename(columns={'Unit Price': 'Last Price of Last Year'})
            one_year_df_4 = pd.merge(one_year_df_4, l_4[['Material/Service No.', 'Last Price of Last Year']],  how='left',on='Material/Service No.')
            one_year_df_4['Last Year Last Price Spend'] = one_year_df_4['PO Item Quantity'] * one_year_df_4['Last Price of Last Year']
            sum_3 = one_year_df_4['Last Year Last Price Spend'].sum()



            # Lowest Purchasing RFP
            a_5 = pd.DataFrame(df_4.groupby('Material/Service No.')['Unit Price'].min())
            a_5.rename(columns={'Unit Price':'Lowest Price'}, inplace=True)
            a_5.reset_index(inplace=True)
            one_year_df_4 = pd.merge(one_year_df_4, a_5,  how='left',on='Material/Service No.')
            one_year_df_4['Lowest Spend'] = one_year_df_4['PO Item Quantity'] * one_year_df_4['Lowest Price']
            sum_5 = one_year_df_4['Lowest Spend'].sum()
            sum_5


            # Pricebook Spend
            one_year_df_4['Pricebook Last Year Spend'] = one_year_df_4['PO Item Quantity'] * one_year_df_4['2020 rates']
            sum_4 = one_year_df_4['Pricebook Last Year Spend'].sum()

            # Plot  
            total_spends = [sum_4, sum_5, sum_3, sum_2, sum_1]
            y_ = ['Pricebook', 'Lowest', 'Last', 'Average', 'Proposed']

            DMP_RFP.total_spends_in_4=total_spends
            
            y_2 = [' ', '  ' , '   ', '    ', '     ']
     
            delta, colors = get_delta_and_index(total_spends)
        
            fig = px.bar(x=total_spends, y= y_2, color = y_, color_discrete_map={'Proposed': 'rgb(144, 238, 144)', 'Average': '#add8e6', 'Last': '#fbc02d',  'Lowest': 'rgb(120, 200, 67)', 'Pricebook': '#FF7F7F',}, orientation = 'h',)

            fig = update_layout_fig_4_1(fig, y_, delta,  total_spends, colors, count)

            div_1 = opy.plot(fig, auto_open=False, output_type='div')


                #! return finded rows data in table 
            response = JsonResponse({            
                'plot_div_4_rfp': div_1,
                'rfp_percentage': round(rfp_percentage,2),
                    })
                    
            add_get_params(response)
            return response
        else:
            response = JsonResponse({            
                    'plot_div_4_rfp': "No Data!",
                        })
                        
            add_get_params(response)
            return response


    @csrf_exempt
    def visual_ajax_5_rfp(request):
        if request.method =='POST':
            input_min_date= request.POST.get('input_min_date')
            input_max_date= request.POST.get('input_max_date')
            input_categories=request.POST.getlist('categories_rfp[]')

            app_to_app_rfp = DMP_RFP.app_to_app_rfp_after_search.copy()
            app_to_app_rfp = app_to_app_rfp[app_to_app_rfp['Product Category Description'].isin(input_categories)]
            app_rfp_df = DMP_RFP.app_rfp_df_after_search.copy()
           
            new_a2a = pd.merge(app_to_app_rfp, app_rfp_df[['BP Material / \nService Master No.', '2021 rates', '2020 rates']], 
                   how='left', left_on='Material/Service No.', right_on='BP Material / \nService Master No.')
            new_a2a = new_a2a[new_a2a['Product Category Description'].isin(input_categories)]

            new_a2a['PO Item Creation Date'] = pd.DatetimeIndex(new_a2a['PO Item Creation Date'])
            new_a2a = new_a2a[(new_a2a['PO Item Creation Date'] >= input_min_date) & (new_a2a['PO Item Creation Date'] <= input_max_date)]
            new_a2a['2021 rates'] = new_a2a['2021 rates'].astype('float')

            
            if new_a2a.shape[0] > 0:
            
                df_all_4 = new_a2a.copy()

                temp_df = df_all_4.groupby('Material/Service No.')['PO Item Quantity'].mean().reset_index()
                temp_df.rename(columns={'PO Item Quantity': 'New Demand'}, inplace=True)
                df_all_4 = pd.merge(df_all_4, temp_df,  how='left', on='Material/Service No.')


                count = len(df_all_4['Material/Service No.'].value_counts().index.tolist())
                rfp_percentage = (count / DMP_RFP.pb_df_after_search.shape[0]) * 100    
                
                # Current
                df_all_4['Curren RFP Total Spend'] = df_all_4['PO Item Quantity'] * df_all_4['2021 rates']
                type_1_df = df_all_4.drop_duplicates(subset = ['Material/Service No.'], keep = 'first') 
                sum_1 = type_1_df['Curren RFP Total Spend'].sum() 

                # Average
                a_4 = pd.DataFrame(df_all_4.groupby('Material/Service No.')['Unit Price'].mean())
                a_4.rename(columns={'Unit Price':'Total Average Price'}, inplace=True)
                a_4.reset_index()

                df_all_4 = pd.merge(df_all_4, a_4,  how='left',on='Material/Service No.')
                df_all_4['Total Average Spend'] = df_all_4['PO Item Quantity'] * df_all_4['Total Average Price']
                type_1_df = df_all_4.drop_duplicates(subset = ['Material/Service No.'], keep = 'first') 

                sum_2 = type_1_df['Total Average Spend'].sum() 

                # Last Purchasing Price
                l_4 = df_all_4.loc[df_all_4.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]
                l_4 = l_4.rename(columns={'Unit Price': 'Overall Last Price'})

                df_all_4 = pd.merge(df_all_4, l_4[['Material/Service No.', 'Overall Last Price']],  how='left',on='Material/Service No.')
                df_all_4['Total Last Price Spend'] = df_all_4['PO Item Quantity'] * df_all_4['Overall Last Price']
                type_1_df = df_all_4.drop_duplicates(subset = ['Material/Service No.'], keep = 'first') 
                sum_3 = type_1_df['Total Last Price Spend'].sum()

                # Lowest Purchasing RFP
                a_5 = pd.DataFrame(df_all_4.groupby('Material/Service No.')['Unit Price'].min())
                a_5.rename(columns={'Unit Price':'Lowest Price'}, inplace=True)
                a_5.reset_index(inplace=True)
                df_all_4 = pd.merge(df_all_4, a_5,  how='left',on='Material/Service No.')
                df_all_4['Lowest Spend'] = df_all_4['PO Item Quantity'] * df_all_4['Lowest Price']
                type_1_df = df_all_4.drop_duplicates(subset = ['Material/Service No.'], keep = 'first') 
                sum_5 = type_1_df['Lowest Spend'].sum()
                


                # Pricebook Spend
                df_all_4['Pricebook Last Year Spend'] = df_all_4['PO Item Quantity'] * df_all_4['2020 rates']
                type_1_df = df_all_4.drop_duplicates(subset = ['Material/Service No.'], keep = 'first') 
                sum_4 = type_1_df['Pricebook Last Year Spend'].sum() 
                
                total_spends = [sum_4, sum_5, sum_3, sum_2, sum_1]
                DMP_RFP.total_spends_in_5=total_spends

                y_ = ['Pricebook', 'Lowest', 'Last', 'Average', 'Proposed']
                y_2 = [' ', '  ' , '   ', '    ', '     ']
                
                delta, colors = get_delta_and_index(total_spends)
                #!bug
                fig = px.bar(x=total_spends, y=y_2, color = y_, color_discrete_map={'Proposed': 'rgb(144, 238, 144)', 'Average': '#add8e6', 'Last': '#fbc02d',  'Lowest': 'rgb(120, 200, 67)',  'Pricebook': '#FF7F7F' }, orientation = 'h',)

                fig = update_layout_fig_5_1(fig, y_, delta,  total_spends, colors, count)

                div_1 = opy.plot(fig, auto_open=False, output_type='div')
                response = JsonResponse({            
                    'plot_div_5_rfp': div_1,
                    'rfp_percentage': round(rfp_percentage,2),
                        })
                add_get_params(response)
                return response
            
            
            
            else:
                fig = update_layout_fig_1_2(DMP_RFP.plot_bg)
                div_1 = opy.plot(fig, auto_open=False, output_type='div')
                response = JsonResponse({            
                    'plot_div_5_rfp': div_1,
                    'top_10_spend_weight': "0",
                        })
                add_get_params(response)
                return response
        else:
            response = JsonResponse({            
                    'plot_div_5_rfp': "No Data!",
                        })
            add_get_params(response)
            return response
               

    @csrf_exempt
    def visual_ajax_6_rfp(request):
        if request.method =='POST':

            pb_df=DMP_RFP.pb_df_after_search.copy()
            pb_df['2021 rates'] = pb_df['2021 rates'].astype(float)
            pb_df['2020 rates'] = pb_df['2020 rates'].astype(float)
            sum_1 = pb_df['2021 rates'].sum()

            pb_df['2020 rates'] = pb_df['2020 rates'].astype('float') 
            sum_2 = pb_df['2020 rates'].sum()

            total_spends = [sum_2, sum_1]
            y_ = ['Pricebook', 'Proposed']
            y_2 = [' ', '  ' ]
            
 
            delta, colors = get_delta_and_index(total_spends)

            count=pb_df.shape[0]
            rfp_percentage = (count/pb_df.shape[0]) * 100
            
            
            fig = px.bar(x=total_spends, y= y_2, color = y_, color_discrete_map={'Pricebook': '#FF7F7F', 'Proposed': 'rgb(144, 238, 144)', }, orientation = 'h', )

            fig = update_layout_fig_5_1(fig, y_, delta,  total_spends, colors, count)


            div_1 = opy.plot(fig, auto_open=False, output_type='div')

            response = JsonResponse({            
                'plot_div_6_rfp': div_1,
                'rfp_percentage': round(rfp_percentage, 2)
                    })
            add_get_params(response)
            return response
        else:
            response = JsonResponse({            
                    'plot_div_6_rfp': "No Data!",
                        })
                        
            add_get_params(response)
            return response
                

    @csrf_exempt
    def visual_ajax_7_rfp(request):
        if request.method =='POST':
        
            input_min_date= request.POST.get('input_min_date')
            input_max_date= request.POST.get('input_max_date')
            input_categories=request.POST.getlist('categories_rfp[]')
            vendor_name = DMP_RFP.rfp_vendor_name
            vendor_name = vendor_name.lower()
            
            df=DMP_RFP.df_full.copy()
            df['PO Item Creation Date'] = pd.DatetimeIndex(df['PO Item Creation Date'])
            df = df[(df['PO Item Creation Date'] >= input_min_date) & (df['PO Item Creation Date'] <= input_max_date)]
            
            if df.shape[0] > 0:
                flag = 1
                vendor_names_all_dataframe = df['Vendor Name'].str.lower().unique().tolist()
                if vendor_name not in vendor_names_all_dataframe:  
                    fuzzy_score = []
                    for vendor in vendor_names_all_dataframe:
                        lst_vendor = list(vendor.lower().replace(' ',''))
                        lst_a = list(vendor_name.replace(' ',''))
                        s1 = fuzz.partial_ratio(lst_vendor, lst_a)
                        fuzzy_score.append(s1)

                    max_score = max(fuzzy_score)
                    max_score_index = fuzzy_score.index(max_score)
                    result_vendor = vendor_names_all_dataframe[max_score_index]
                    if max_score >= 0.4:
                        vendor_name = result_vendor
                        flag = 0
                else:
                    vendor_name = vendor_name.lower()
                    flag = 0

                if flag == 0:
                   
                    a = df[df['Vendor Name'].str.lower() == vendor_name.lower()]
                    a = a[(a['PO Item Creation Date'] >= input_min_date) & (a['PO Item Creation Date'] <= input_max_date)]
                    total_spend = a['PO Item Value (GC)'].sum() / 1000000
                    DMP_RFP.total_spend = str(round(total_spend, 2)) + 'M'
                    
                    b = pd.DataFrame(a.groupby(by=['Product Category'])['PO Item Value (GC)'].sum())
                    b.sort_values(by=['PO Item Value (GC)'], ascending=False, inplace=True)
                    mask = a['Product Category'].isin(b.iloc[5:].index.tolist())
                    a.loc[mask, 'Product Category'] = 'Others'
                    
                    a['PO Item Value (GC)'] = a['PO Item Value (GC)'].astype('float').astype(int)
                    a['Year'] = a['PO Item Creation Date'].dt.year
                    a['Year'] = pd.to_datetime(a.Year, format='%Y')
                    
                    c = pd.DataFrame(a.groupby(by=['Year', 'Product Category'])['PO Item Value (GC)'].sum())            
                    c['PO Item Value (GC) Text'] =  c['PO Item Value (GC)'].apply(lambda x : str(round((x/1000000), 2)) + 'M')
                    c.reset_index(inplace=True)
                    c['Year'] = pd.DatetimeIndex(c['Year'])
                    c['Year'] = c['Year'].dt.year
                    b = c[c['Product Category'] != 'Others']
                    
                    e = pd.merge(b, a[['Product Category', 'Product Category Description']],  
                                 how='left', on='Product Category').drop_duplicates(['Product Category', 'Year'])
                    c_years = c['Year'].unique().tolist()
                    e_years = e['Year'].unique().tolist()
                    ls = list(set(c_years) - set(e_years))

                    for year in ls:
                        temp = e.iloc[-1].copy()
                        temp['PO Item Value (GC)'] = 0
                        temp['PO Item Value (GC) Text'] = ''
                        temp['Year'] = year
                        e = e.append(temp)

                    e.reset_index(drop=True, inplace=True)
                    e.sort_values('Year', inplace=True)
                    fig = px.bar(e, x='Year', y='PO Item Value (GC)', color='Product Category Description', 
                        barmode='stack', text='PO Item Value (GC) Text', color_discrete_sequence=px.colors.qualitative.Set3,)
                    fig.update_traces(marker_line_width=0)
                    
                    a_line = pd.DataFrame(c.groupby('Year')['PO Item Value (GC)'].sum())
                    a_line.reset_index(inplace=True)
                    a_line['PO Item Value (GC) Text'] = a_line['PO Item Value (GC)'].apply(lambda x: str(round(x/1000000,2)) + 'M')

            
                    fig2 = px.line(a_line, x='Year', y='PO Item Value (GC)', text='PO Item Value (GC) Text')
                    fig2.update_traces(textposition='top center')
                    fig.add_trace(fig2.data[0])

                    
                    fig = update_layout_fig_6(fig, DMP.plot_bg)
                    fig.update(layout_coloraxis_showscale=False)
                   
                    div_1 = opy.plot(fig, auto_open=False, output_type='div')
                    response = JsonResponse({            
                        'plot_div_7_rfp': div_1,
                        'total_spend': DMP_RFP.total_spend,
                            })
                    add_get_params(response)
                    return response
                
                else:
                    response = JsonResponse({            
                        'plot_div_7_rfp': "No Data!",
                         })
                        
                    add_get_params(response)
                    return response

            else:
                fig = update_layout_fig_1_2(DMP_RFP.plot_bg)
                div_1 = opy.plot(fig, auto_open=False, output_type='div')

                #! return finded rows data in table 
                response = JsonResponse({            
                    'plot_div_7_rfp': div_1,
                    'top_10_spend_weight': "0",
                    })
                        
                add_get_params(response)
                return response
        else:
            response = JsonResponse({            
                    'plot_div_7_rfp': "No Data!",
                        })
            add_get_params(response)
            return response
                

    @csrf_exempt
    def recommendation(request):
        total_spends = DMP_RFP.total_spends_in_4
        total_spends_2 = DMP_RFP.total_spends_in_5
        y_ = ['Pricebook', 'Last Purchase', 'Average', 'Proposed']
        
        # zip_iterator = zip(y_, total_spends)
        # rec_dict = dict(zip_iterator)
        # rec_dict = {'Pricebook': 904119.06, 'Last Purchase': 888191.44, 'Average': 893475.4722352589, 'Proposed': 700000.44}
        rec_dict = dict(zip(y_, total_spends))

        minval = min(rec_dict.values())
        res = [k for k, v in rec_dict.items() if v==minval]

        df=DMP_RFP.df_full.copy()
        df['PO Item Creation Date'] = pd.to_datetime(df['PO Item Creation Date'])
        df['PO Item Value (GC)'] = df['PO Item Value (GC)'].astype('float')
        df = df[df['Vendor Name'] == DMP_RFP.rfp_vendor_name]
        now = dt.datetime.now()
        last_year = now.year-1
        last_year_df = df[df['PO Item Creation Date'].dt.year == last_year]
        last_year_total_spend = last_year_df['PO Item Value (GC)'].sum()
        pricebook_spend = rec_dict.get('Pricebook')
        rfp_valuation = rec_dict.get('Proposed')
        last_purchase_valuation = rec_dict.get('Last Purchase')
        average_prices_valuation = rec_dict.get('Average')



        #!  ------------------------- START  Evaluation for pricebook items -------------------------
        app_to_app_rfp=DMP_RFP.app_to_app_rfp_after_search.copy()
        app_rfp_df=DMP_RFP.app_rfp_df_after_search.copy()
        
        new_a2a = pd.merge(app_to_app_rfp, app_rfp_df[['BP Material / \nService Master No.', '2021 rates', '2020 rates']], 
            how='left', left_on='Material/Service No.', right_on='BP Material / \nService Master No.')
        
        new_a2a['Average Price'] = new_a2a['Unit Price'].groupby(new_a2a['Material/Service No.']).transform('mean')
        new_a2a['delta'] = 0.0
        new_a2a['Increase percentage'] = 0.0
        new_a2a['PO Item Creation Date'] = pd.DatetimeIndex(new_a2a['PO Item Creation Date'])
        new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax(), 'delta'] = new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['2021 rates'] - new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['Average Price']
        new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax(), 'Increase percentage'] = (new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['delta'] / new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['Unit Price']) * 100
        new_a2a['Increase percentage'] = round(new_a2a['Increase percentage'])


        weight_df = pd.DataFrame(new_a2a.groupby('Material/Service No.')['PO Item Value (GC)'].sum())
        weight_df.rename(columns={'PO Item Value (GC)':'Item Total Spend'}, inplace=True)
        weight_df.reset_index(inplace=True)


        new_a2a = pd.merge(new_a2a, weight_df,  how='left', on='Material/Service No.')
        new_a2a['Item Weight'] = new_a2a['Item Total Spend'] / (new_a2a['PO Item Value (GC)'].sum())
        
    
        increase_df = new_a2a[new_a2a['delta'] > 0]
        unique_increase_df = increase_df.drop_duplicates(subset = ['Material/Service No.'], keep = 'first') 
        unique_increase_df['Proposed Price'] =  unique_increase_df['2021 rates'].astype('str')

        #!  ------------------------- END  Evaluation for pricebook items -------------------------





        #!  ------------------------- START  Evaluation for non-pricebook items -------------------------
        df = pd.read_csv(str(BASE_DIR) + '/static/df_all_regions_new.csv', parse_dates=['PO Item Creation Date'], dtype="unicode")

        df = df[df['Region'] == DMP_RFP.rfp_region_name]
        df = df[df['PO Item Deletion Flag'] != 'X']
        df = df[df['PO Status Name'] != 'Deleted']
        df.loc[df['Vendor Name'] == 'R&M Electrical Group MMC',   'Vendor Name'] = 'R&M Electrical Group'
        df.loc[df['Vendor Name'] == 'R&M Electrical Group Ltd',   'Vendor Name'] = 'R&M Electrical Group'
        df.loc[df['Vendor Name'] == 'R M Electrical Group Limited',   'Vendor Name'] = 'R&M Electrical Group'
        df['PO Item Value (GC)'] = df['PO Item Value (GC)'].astype('float')
        df['PO Item Quantity'] = df['PO Item Quantity'].astype('float')
        df['Unit Price'] = df['PO Item Value (GC)'] / df['PO Item Quantity'] 
        df['PO Item Creation Date'] = pd.DatetimeIndex(df['PO Item Creation Date'])
        df = df[df['Unit Price'] != 0]
        df['PO Item Description'] = df['PO Item Description'].replace(np.nan, ' ', regex=True)    
        df['Long Description'] = df['Long Description'].replace(np.nan, ' ', regex=True)    


        temp_df = df[(df['Vendor Name'].str.lower() == DMP_RFP.rfp_vendor_name.lower())].copy()
        a2a = pd.read_csv(str(BASE_DIR) + '/static/files\A2A_28_08_2021.csv')

        new_df = temp_df.loc[~temp_df.index.isin(a2a.base_index.tolist())]
        # # Step - 1  (material id: yes   |   part number: yes)
        df_1 = new_df[(new_df['Material/Service No.'] != '#') & (new_df['Manufacturer Part No.'] != '#')].copy()
        new_df.loc[df_1.index.tolist(), 'Material/Service No.'] = new_df.loc[df_1.index.tolist(), 'Material/Service No.'] + ' (' + new_df.loc[df_1.index.tolist(), 'Manufacturer Part No.'] + ')'


        # # Step - 2  (material id: no   |   part number: yes)
        df_2 = new_df[(new_df['Material/Service No.'] == '#') & (new_df['Manufacturer Part No.'] != '#')].copy()
        df_2['labels'] = -1
        groups = df_2.groupby("Manufacturer Part No.")
        max_label = 0
        i=0
        for name, group in groups:
            corpus = group['PO Item Description'].tolist()
            vectorizer2 = CountVectorizer(analyzer='word', ngram_range=(1,2))
            X2 = vectorizer2.fit_transform(corpus)

            counts = pd.DataFrame(X2.todense(), columns=vectorizer2.get_feature_names())
            dbscan = DBSCAN(eps=3.8, min_samples=1)
            model = dbscan.fit(counts.values) 
            max_label = len(group['labels'].unique().tolist()) + max_label
            
            group['labels'] = max_label + model.labels_
            df_2.loc[group.index.tolist(), 'labels'] = group['labels']
            i += 1

        df_2['labels'] = df_2['labels'].astype('str')
        new_df.loc[df_2.index.tolist(), 'Material/Service No.'] = new_df.loc[df_2.index.tolist()]['Manufacturer Part No.'] + ' (' + df_2['labels'] + ') B' 

        
        # # Step - 3  (material id: yes   |   part number: no)
        df_3 = new_df[(new_df['Material/Service No.'] != '#') & (new_df['Manufacturer Part No.'] == '#')]
        df_3['labels'] = -1
        groups = df_3.groupby("Material/Service No.")
        max_label = 0
        i=0
        for name, group in groups:
            corpus = group['PO Item Description'].tolist()
            vectorizer2 = CountVectorizer(analyzer='word', ngram_range=(1, 2))
            X2 = vectorizer2.fit_transform(corpus)
            counts = pd.DataFrame(X2.todense(), columns=vectorizer2.get_feature_names())
            
            model = dbscan.fit(counts.values)
            max_label = len(group['labels'].unique().tolist()) + max_label
            group['labels'] = max_label + model.labels_
            df_3.loc[group.index.tolist(), 'labels'] = group['labels']
            i += 1

            
        df_3['labels'] = df_3['labels'].astype('str')
        new_df.loc[df_3.index.tolist(), 'Material/Service No.'] = new_df.loc[df_3.index.tolist()]['Material/Service No.'] + ' (' + df_3['labels'] + ') C' 


        # Step - 4  (material id: no   |   part number: no)
        def check_description_2(x, desc):
            return float(len(set(x).intersection(desc)) / len(set(x).union(desc)))

        df_4 = new_df[(new_df['Material/Service No.'] == '#') & (new_df['Manufacturer Part No.'] == '#')]
        

        list_of_descriptions = df_4['PO Item Description'].value_counts().index.tolist()
        df_4['desc_words_short'] = df_4['PO Item Description'].apply(lambda x: x.replace(':', ' ').replace(': ',' ').replace(',',' ').replace(', ',' ').replace(';',' ').replace('; ',' ').replace('-',' ').split())
        i = 1
        for description in list_of_descriptions:
            
            description = set(description.replace(':',' ').replace(': ',' ').replace(',',' ').replace(', ',' ').replace(';',' ').replace('; ',' ').replace('-',' ').split())
            df_4['score'] = df_4['desc_words_short'].apply(lambda x: check_description_2(x, description))
            out_df = df_4[df_4['score'] > 0.6]
            df_4 = df_4[df_4['score'] <= 0.6]
            new_df.loc[out_df.index.tolist(), 'Material/Service No.'] = 'D (' + str(i) + ')' 
            i += 1
    
    
        new_df['PO Item Creation Date'] = pd.DatetimeIndex(new_df['PO Item Creation Date'])
        min_date_non_pricebook = min(new_df['PO Item Creation Date']).strftime('%Y-%m-%d')
        max_date_non_pricebook = max(new_df['PO Item Creation Date']).strftime('%Y-%m-%d')
        print("mmmmmmmmmmmmmmmmmmm",max_date_non_pricebook)
        DMP_RFP.min_date_non_pricebook = min_date_non_pricebook
        DMP_RFP.max_date_non_pricebook = max_date_non_pricebook
                
        today = pd.to_datetime("today").normalize()
        one_year_before = today - datetime.timedelta(days=3*365)
        starting_date = one_year_before.replace(month=1, day=1)   # 2020-01-01
        one_year_before = today - datetime.timedelta(days=1*365)  # 2020-12-31
        ending_date = one_year_before.replace(month=12, day=31)
        new_df['PO Item Creation Date'] = pd.DatetimeIndex(new_df['PO Item Creation Date'])
        new_df = new_df[(new_df['PO Item Creation Date'] >= starting_date) & (new_df['PO Item Creation Date'] <= ending_date)]
        
        df_23 = new_df.groupby(['Material/Service No.']).filter(lambda x: len(x) > 1)
        df_23['PO Item Value (GC)'] = df_23['PO Item Value (GC)'].astype('float')
        # df_23['Item Total Spend'] = df_23['Item Total Spend'].astype('float')
        weight_df = pd.DataFrame(df_23.groupby('Material/Service No.')['PO Item Value (GC)'].sum())
        weight_df.rename(columns={'PO Item Value (GC)':'Item Total Spend'}, inplace=True)
        weight_df.reset_index(inplace=True)
        df_23 = pd.merge(df_23, weight_df,  how='left', on='Material/Service No.')
        df_23['Item Weight'] = df_23['Item Total Spend'] / (df_23['PO Item Value (GC)'].sum())

        df_23['Average Price'] = df_23['Unit Price'].groupby(df_23['Material/Service No.']).transform('mean')
        df_23['Last Price'] = df_23.loc[df_23.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['Unit Price']

        df_23['Average Price'] = round(df_23['Average Price'], 2)
        df_23['Last Price'] = round(df_23['Last Price'], 2)
        increase_df_23 = df_23[df_23['Average Price'] < df_23['Last Price']]
        increase_df_23['delta'] = 0.0
        increase_df_23['percentage'] = 0.0

        increase_df_23.loc[increase_df_23.groupby('Material/Service No.')['PO Item Creation Date'].idxmax(), 'delta'] = increase_df_23.loc[increase_df_23.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['Last Price'] - increase_df_23.loc[increase_df_23.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['Average Price']
        increase_df_23.loc[increase_df_23.groupby('Material/Service No.')['PO Item Creation Date'].idxmax(), 'percentage'] = (increase_df_23.loc[increase_df_23.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['delta'] / increase_df_23.loc[increase_df_23.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['Average Price']) * 100
        increase_df_23['Increase percentage'] = round(increase_df_23['percentage'])
        increase_df_23['From Pricebook'] = 'NO'
        #!  ------------------------- END  Evaluation for nonpricebook items -------------------------


        # unique_increase_df['Updated Price'] = (unique_increase_df['Unit Price']  + unique_increase_df['2021 rates'])/2
        # unique_increase_df['Discount'] = unique_increase_df['2021 rates'] - unique_increase_df['Updated Price']

        # one_year_df_4 = pd.merge(one_year_df_4, unique_increase_df[['Material/Service No.', 'Discount']],  how='left', on='Material/Service No.')
        # one_year_df_4['Discount Spend'] = one_year_df_4['Discount'] * one_year_df_4['PO Item Quantity']

        unique_increase_df = unique_increase_df.sort_values(by='Item Weight', ascending = False)                 
        unique_increase_df['From Pricebook'] = 'YES'   
        unique_increase_df = unique_increase_df[['Material/Service No.', 'PO Item Description', 'Manufacturer Name', 'Manufacturer Part No.', 'Increase percentage', 'From Pricebook']]


        increase_df_23['Proposed Price'] = increase_df_23['Last Price']   
        increase_df_23 = increase_df_23.sort_values(by='Item Weight', ascending = False)                    
        increase_df_23 = increase_df_23[['Material/Service No.', 'PO Item Description', 'Manufacturer Name', 'Manufacturer Part No.', 'Increase percentage', 'From Pricebook']]


        unique_increase_df = unique_increase_df.append(increase_df_23)
        
        unique_increase_df.to_csv(str(BASE_DIR) + '/static/unique_increase_df.csv')
        increase_df_23.to_csv(str(BASE_DIR) + '/static/increase_df_23_new.csv')            


        DMP_RFP.unique_increase_df = unique_increase_df


        #! If RFP valuation is lower than all positions (last purchase, average, current price book) and if RFP items is covering more than 70% of last year total spend
        #  (price book valuation vs last year total spend) then proceed with acceptance of the prices and show below message: Valuation of the offer is lower than
        #  previous purchase, hence recommended to accept. Savings for the next year demand, based on last year demand, is $XXX (last purchase price proposed difference
        #  from valuation table).  
        rec_case_1=""
        # last_year_total_spend = 10

        cond_1 = rfp_valuation < last_purchase_valuation and rfp_valuation < average_prices_valuation and rfp_valuation < pricebook_spend  and pricebook_spend > last_year_total_spend * 0.7
        cond_2 = rfp_valuation < last_purchase_valuation and rfp_valuation < average_prices_valuation and rfp_valuation < pricebook_spend  and pricebook_spend < last_year_total_spend * 0.7
        cond_3 = rfp_valuation < last_purchase_valuation and rfp_valuation > average_prices_valuation
        cond_4 = rfp_valuation > last_purchase_valuation and rfp_valuation > average_prices_valuation and rfp_valuation > pricebook_spend
        cond_5 = rfp_valuation < average_prices_valuation and rfp_valuation > last_purchase_valuation
        cond_6 = rfp_valuation < pricebook_spend and rfp_valuation > last_purchase_valuation
        DMP_RFP.cond_1=cond_1
        DMP_RFP.cond_2=cond_2
        DMP_RFP.cond_3=cond_3
        DMP_RFP.cond_4=cond_4
        DMP_RFP.cond_5=cond_5
        DMP_RFP.cond_6=cond_6

        if cond_1:
            savings = rec_dict.get('Last Purchase') - rec_dict.get('Proposed')
            print('RFP Valuation is less than all positions and is covering more than 70% of last year total spend')
            message = "Valuation of the offer is lower than previous purchase, hence recommended to accept. Savings for the next year demand, based on last year demand, is $" + str(savings) + "."
            rec_case_1=message
            print('Recommendatiommmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmn: ', message)
    
        elif cond_2 or cond_3 or cond_4 or cond_5 or cond_6:
            print('RFP Valuation is less than all positions and is covering less than 70% of last year total spend')
            # unique_increase_df.to_csv('unique_increase_df.csv')    # Have to display in UI 
            message = "Dear supplier " + DMP_RFP.rfp_vendor_name + " our analysis shows that there is significant increase in the attached list of items, therefore we would request you to provide discount according to the % shown in the table. Thank you for your cooperation." 
            print('Recommendationnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn: ', message)
            html_message='<p>Dear supplier <b>' + DMP_RFP.rfp_vendor_name + ' Ltd</b>,  our analysis shows that there is significant increase in some materials, therefore we would request you to provide discount according to the % shown in the table. Thank you for your cooperation.</p><h4> <a href="http://localhost:1000/discount_materials_user.html" target="_blank">Link for materials that has risen in price</a></h4>'
            rec_case_1=message
        else:
            rec_case_1="There is no recommendation in this case. "



        print('\n*************************************     Recommendation End      ************************************\n')
    

        #! return finded rows data in table 
        response = JsonResponse({            
            'rec_case_1':rec_case_1,
            })
                    
        add_get_params(response)
        return response

    @csrf_exempt
    def display_recommendation(request):
       
        cond_1=DMP_RFP.cond_1
        cond_2=DMP_RFP.cond_2
        cond_3=DMP_RFP.cond_3
        cond_4=DMP_RFP.cond_4
        cond_5=DMP_RFP.cond_5
        cond_6=DMP_RFP.cond_6
       
        if cond_2 or cond_3 or cond_4 or cond_5 or cond_6:
            print('RFP Valuation is less than all positions and is covering less than 70% of last year total spend')
            # unique_increase_df.to_csv('unique_increase_df.csv')    # Have to display in UI 
            message = "Dear supplier " + DMP_RFP.rfp_vendor_name + ", our analysis shows that there is significant increase in the attached list of items, therefore we would request you to provide discount according to the % shown in the table. Thank you for your cooperation." 
            print('Recommendation: ', message)
            html_message='<p>Dear supplier <b>' + DMP_RFP.rfp_vendor_name +'</b>,  our analysis shows that there is significant increase in some materials, therefore we would request you to provide discount according to the % shown in the table. Thank you for your cooperation.</p><h4> <a href="http://localhost:1000/discount_materials.html" target="_blank">Link for materials that has risen in price</a></h4>'
            rec_case_1=message
            
            new_message  = strip_tags(html_message)
            try:
                full_name = 'DMP BESTRACK'
                email = 'dmp.bestrack@gmail.com'
                message = 'I am here ' + ' ' + new_message
                time='time'

                #send_mail
                send_mail(
            "From: "+ full_name, #subject
            "User Email: "+email+"\n Request for discount: "+message,    #message
            email, #from email
            ["hebibliferid20@gmail.com", "cavidan5889@gmail.com"],     html_message=html_message)
            except Exception as e:
                print("mail sending error: ", e)
        response = JsonResponse({            
            'rec_case_1':"rec_case_1",
            })
                    
        add_get_params(response)
        return response

#! <---------------------------------- REGION VISUALIZATION START ---------------------------------------------->
   
    @csrf_exempt
    def visual_ajax_1_region(request):
        if request.method =='POST':
        
            result_df = DMP_RFP.result_df.copy()
            list_of_regions=DMP_RFP.list_of_regions.copy()
            if len(list_of_regions) == 4:
                result_agt_df = result_df[result_df['Region'] == 'AGT']
                avg_result_df = result_df.copy()
                a2a = DMP_RFP.a2a.copy()
                result_agt_df.loc[:, 'Average Demand'] = 0.0
                idx_list_4 = result_agt_df['Material/Service No.'].value_counts().index.tolist()
                len(idx_list_4)
                for item_number in idx_list_4:
                    temp = result_agt_df[result_agt_df['Material/Service No.'] == item_number]
                    count = len(temp.groupby(temp['PO Item Creation Date'].dt.year))
                    summ = temp['PO Item Quantity'].sum()
                    demand = summ/count
                    result_agt_df.loc[result_agt_df['Material/Service No.'] == item_number, ['Average Demand']] = demand
                result_agt_df = result_agt_df.drop_duplicates(subset = ['Material/Service No.'], keep = 'first') 
                result_df = pd.merge(result_df, result_agt_df[['Material/Service No.', 'Average Demand']],  how='left', on='Material/Service No.')
                total_spends = []
                regions = []
                list_of_regions_2=list_of_regions.copy()
                for region in list_of_regions_2:
                    df_2 = result_df[result_df['Region'] == region] 
                    df_2.loc[:, 'Average Price'] = -1
                    idx_list_4 = df_2['Material/Service No.'].value_counts().index.tolist()
                    for item_number in idx_list_4:
                        temp = df_2[df_2['Material/Service No.'] == item_number]
                        average_price = temp['Unit Price'].mean()
                        result_df.loc[temp.index.tolist(), ['Average Price']] = average_price
                result_df['Total Spend'] = result_df['Average Demand'] * result_df['Average Price']
                result_df = result_df.drop_duplicates(subset = ['Material/Service No.', 'Region'], keep = 'first') 
                for region in list_of_regions_2:
                    summ = result_df.loc[result_df['Region'] == region]['Total Spend'].sum()
                    total_spends.append(summ)
                    regions.append(region)
                delta = []
                colors = []
                y_ = regions
                y_2 = [' ', '  ' , '   ', '    ']
                for index, elem in enumerate(total_spends):
                    if index == len(total_spends)-1:
                        delta.append(' ')
                        colors.append('red')
                    else:
                        delta.append(str(abs(int(round(((elem - total_spends[-1])/elem)*100)))))
                        if int(elem - total_spends[-1]) < 0:
                            colors.append('red')
                        else:
                            colors.append('green')
                fig = px.bar(
                            x=total_spends,
                            y= y_2,
                            color = y_,                       
                            orientation = 'h',
                            color_discrete_map={
                                'GOM':  '#FF7F7F',
                                'ANG':  'rgb(251, 192, 45)',
                                'UKS':  'rgb(173, 216, 230)',
                                'AGT': 'rgb(144, 238, 144)'
                        },
                )
                count = len(result_df['Material/Service No.'].unique().tolist() )
                rfp_percentage = (count/len(a2a['Material/Service No.'].unique().tolist())) * 100

                rfp_percentage=round(rfp_percentage, 2)
                fig.update_yaxes(ticksuffix=' ' ) 
                fig.update_layout(
                            title="",
                            xaxis_title="",
                            yaxis_title="",
                            legend_title="Regions (" + str(round(count,2 )) +")",
                            template = 'ggplot2',
                        )

                for a, b in enumerate(y_):
                            fig.add_annotation(
                                    text= '<b>' + "{:,}".format(int(total_spends[a])) + '</b>',
                                    x= total_spends[a] - total_spends[-1]/100,
                                    y=a,
                                    xanchor='right',
                                    font=dict(
                                        family="Courier New, monospace",
                                        size=16,
                                        color="#ffffff",
                                    ),
                        showarrow=False)

                for a, b in enumerate(y_):
                    fig.add_annotation(
                            text= '<b>' + b + '</b>',
                            y=a,
                            x=(100),
                            xanchor='left', 
                            font=dict(
                                family="Courier New, monospace",
                                size=16,
                                color="#ffffff",
                                ),
                            align='left',
                showarrow=False)

                for a, b in enumerate(delta):
                    temp = ''
                    if b != ' ':
                        if len(b) > 0  and float(b) < 0 :
                            color = 'red'
                            temp = abs(float(b))
                        elif len(b) != 0:
                            color = '#006400'
                            temp = abs(float(b))

                        if total_spends[a] > total_spends[-1]:
                            x_ = max(total_spends)
                        else:
                            x_ = total_spends[-1]
                    if a != len(delta)-1:
                        temp = str(int(temp)) + '%'
                    fig.add_annotation(                            
                            text='<b>' + str(temp) + '</b>',
                            x=(x_ + max(total_spends)/15),
                            y=a,
                            font=dict(
                                family="Courier New, monospace",
                                size=16,
                                color=color,
                            ),
                            align="right",
                showarrow=False)
                    
                fig.update_layout(xaxis_range=[0, max(total_spends) + max(total_spends)/7],)
                fig.add_vline(x=total_spends[-1], line_width=2, line_dash="dash", line_color="red")
                new_spend = total_spends[:len(total_spends)-1]
                if max(new_spend) > total_spends[-1]:
                    fig.add_vline(x=max(new_spend), line_width=2, line_dash="dash", line_color="green")


                fig.update_layout(legend=dict(
                                yanchor="top",
                                y=1,
                                xanchor="left",
                                x=0.00
                        ))
                fig.update_layout(
                            height=450,
                            width=690,
                            plot_bgcolor='rgba(255,255,255,0.5)',) 
                

                fig.update_xaxes(visible=True, showticklabels=True)
                fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
                # fig.update_yaxes(showline=True, linewidth=1, linecolor='black')
                fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')
                # fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')    
                
                div_1 = opy.plot(fig, auto_open=False, output_type='div')
                response = JsonResponse({            
                    'plot_div_1_region': div_1,
                    'price-trend-weight-1':rfp_percentage,

                        })
                add_get_params(response)
                return response

            else:
                fig = go.Figure(go.Bar(
                    x=[20],
                    y=[' '],
                    marker_color=[DMP_RFP.plot_bg],
                    orientation='h'))
                fig.add_annotation(
                                text= '<b>' + 'No Data!' + '</b>',
                                x= 10,
                                y=' ',
                                font=dict(
                                    family="Courier New, monospace",
                                    size=16,
                                    color="black",
                                ),
                    showarrow=False)
                fig.update_layout(    plot_bgcolor=DMP_RFP.plot_bg )
                fig.update_layout(xaxis_range=[0,20],  plot_bgcolor=DMP_RFP.plot_bg,)
                fig.update_layout(
                        height=480,
                        width=690,
                        plot_bgcolor=DMP_RFP.plot_bg,)         
                fig.update_xaxes(visible=False, showticklabels=False)
                div_1 = opy.plot(fig, auto_open=False, output_type='div')
               
                response = JsonResponse({            
                                    'plot_div_1_region': div_1,
                                        'rfp-weight-8':0,

                                        })
                add_get_params(response)
                return response

        else:
            response = JsonResponse({            
                    'plot_div_1_region': "No Data!",         
                     'rfp-weight-8':0,           
                        })
            add_get_params(response)
            return response
  
    @csrf_exempt
    def visual_ajax_2_region(request):
        if request.method =='POST':
            
    
            result_df=DMP_RFP.result_df.copy()

            result_temp_df = result_df.copy()
            
            list_of_regions=DMP_RFP.list_of_regions.copy()
            
            a2a=DMP_RFP.a2a.copy()


            if len(list_of_regions) ==4:
                
                max_regions = ['AGT']
                
                max_val = 0

                max_region = ''

                for region in list_of_regions:
                
                    if region != 'AGT':
                        new_a2a = a2a[a2a['Region'].isin(['AGT', region])]
                        intersect = reduce(np.intersect1d, new_a2a.groupby('Region')['Material/Service No.'].apply(list))
                        result_temp_df = new_a2a.loc[new_a2a['Material/Service No.'].isin(intersect), :]


                        if max_val < len(result_temp_df['Material/Service No.'].unique().tolist()):
                            max_val = len(result_temp_df['Material/Service No.'].unique().tolist())
                            max_region = region


                max_regions.append(max_region)
                list_of_regions.remove(max_region)

                max_val = 0
                max_region = ''
                for region in list_of_regions:
                    if region != 'AGT':
                        new_a2a = a2a[a2a['Region'].isin(['AGT', region])]
                        intersect = reduce(np.intersect1d, new_a2a.groupby('Region')['Material/Service No.'].apply(list))
                        result_temp_df = new_a2a.loc[new_a2a['Material/Service No.'].isin(intersect), :]


                        if max_val < len(result_temp_df['Material/Service No.'].unique().tolist()):
                            max_val = len(result_temp_df['Material/Service No.'].unique().tolist())
                            max_region = region
                max_regions.append(max_region)

                list_of_regions=max_regions[::-1].copy()

                result_df = result_df[result_df['Region'].isin(list_of_regions)]
                result_agt_df = result_df[result_df['Region'] == 'AGT']
                avg_result_df = result_df.copy()
                a2a=DMP_RFP.a2a.copy()

                result_agt_df.loc[:, 'Average Demand'] = 0.0
                idx_list_4 = result_agt_df['Material/Service No.'].value_counts().index.tolist()
                len(idx_list_4)
                for item_number in idx_list_4:
                    temp = result_agt_df[result_agt_df['Material/Service No.'] == item_number]
                    count = len(temp.groupby(temp['PO Item Creation Date'].dt.year))
                    temp['PO Item Quantity']=temp['PO Item Quantity'].astype('float')

                    summ = temp['PO Item Quantity'].sum()

                    demand = summ/count
                    result_agt_df.loc[result_agt_df['Material/Service No.'] == item_number, ['Average Demand']] = demand
                result_agt_df = result_agt_df.drop_duplicates(subset = ['Material/Service No.'], keep = 'first') 

                result_df = pd.merge(result_df, result_agt_df[['Material/Service No.', 'Average Demand']],  how='left', on='Material/Service No.')


                total_spends = []
                regions = []
                for region in list_of_regions:
                    df_2 = result_df[result_df['Region'] == region] 
                    df_2.loc[:, 'Average Price'] = -1
                    idx_list_4 = df_2['Material/Service No.'].value_counts().index.tolist()
                
                    for item_number in idx_list_4:

                        temp = df_2[df_2['Material/Service No.'] == item_number]
                        temp['Unit Price']=temp['Unit Price'].astype('float')
                        average_price = temp['Unit Price'].mean()
                        result_df.loc[temp.index.tolist(), ['Average Price']] = average_price
                        
                        if item_number == '10007916':
                            print('Material ID: ', item_number,' and Region: ', region, ' and average price: ', average_price, )
                            
                result_df['Total Spend'] = result_df['Average Demand'] * result_df['Average Price']
                result_df = result_df.drop_duplicates(subset = ['Material/Service No.', 'Region'], keep = 'first') 

                for region in list_of_regions:
                    summ = result_df.loc[result_df['Region'] == region]['Total Spend'].sum()
                    total_spends.append(summ)
                    regions.append(region)

                  

                color_map = {
                        'GOM':  '#FF7F7F',
                        'ANG':  'rgb(251, 192, 45)',
                        'UKS':  'rgb(173, 216, 230)',
                        'AGT': 'rgb(144, 238, 144)'
                }
                                                                                                                                                                                         
                delta = []
                colors = []
                y_ = regions
                y_2 = [' ', '  ' , '   ']
                for index, elem in enumerate(total_spends):
                    if index == len(total_spends)-1:
                        delta.append(' ')
                        colors.append('red')
                    else:
                        # delta.append(str(abs(int(elem - total_spends[-1]))))
                        delta.append(str(abs(int(round(((elem - total_spends[-1])/elem)*100)))))
                        if int(elem - total_spends[-1]) < 0:
                            colors.append('red')
                        else:
                            colors.append('green')

                fig = px.bar(
                            x=total_spends,
                            y= y_2,
                            color = y_,                       
                            orientation = 'h',
                            color_discrete_map={
                                regions[2]: color_map.get(regions[2]),
                                regions[1]: color_map.get(regions[1]),
                                regions[0]: color_map.get(regions[0]),

                                
                        },
                )
                count = len(result_df['Material/Service No.'].unique().tolist() )
                rfp_percentage = (count/len(a2a['Material/Service No.'].unique().tolist())) * 100

                rfp_percentage=round(rfp_percentage, 2)
                fig.update_yaxes(ticksuffix=' ' ) 
                fig.update_layout(
                            title="",
                            xaxis_title="",
                            yaxis_title="",
                            legend_title="Regions (" + str(round(count,2 )) +")",
                            template = 'ggplot2',
                        )

                for a, b in enumerate(y_):
                            fig.add_annotation(
                                    text= '<b>' + "{:,}".format(int(total_spends[a])) + '</b>',
                                    x= total_spends[a] - total_spends[-1]/100,
                                    y=a,
                                    xanchor='right',
                                    font=dict(
                                        family="Courier New, monospace",
                                        size=16,
                                        color="#ffffff",
                                    ),
                        showarrow=False)

                for a, b in enumerate(y_):
                    fig.add_annotation(
                            text= '<b>' + b + '</b>',
                            y=a,
                            x=(100),
                            xanchor='left', 
                            font=dict(
                                family="Courier New, monospace",
                                size=16,
                                color="#ffffff",
                                ),
                            align='left',
                showarrow=False)

                for a, b in enumerate(delta):
                    temp = ''
                    if b != ' ':
                        if len(b) > 0  and float(b) < 0 :
                            color = 'red'
                            temp = abs(float(b))
                        elif len(b) != 0:
                            color = '#006400'
                            temp = abs(float(b))

                        if total_spends[a] > total_spends[-1]:
                            x_ = max(total_spends)
                        else:
                            x_ = total_spends[-1]
                    if a != len(delta)-1:
                        temp = str(int(temp)) + '%'
                    fig.add_annotation(                            
                            text='<b>' + str(temp) + '</b>',
                            x=(x_ + max(total_spends)/15),
                            y=a,
                            font=dict(
                                family="Courier New, monospace",
                                size=16,
                                color=color,
                            ),
                            align="right",
                showarrow=False)
                    
                fig.update_layout(xaxis_range=[0, max(total_spends) + max(total_spends)/7],)
                fig.add_vline(x=total_spends[-1], line_width=2, line_dash="dash", line_color="red")
                new_spend = total_spends[:len(total_spends)-1]
                if max(new_spend) > total_spends[-1]:
                    fig.add_vline(x=max(new_spend), line_width=2, line_dash="dash", line_color="green")
                fig.update_layout(legend=dict(
                                yanchor="top",
                                y=1,
                                xanchor="left",
                                x=0.00
                        ))
                fig.update_layout(
                            height=450,
                            width=690,
                            plot_bgcolor='rgba(255,255,255,0.5)',) 
                fig.update_xaxes(visible=True, showticklabels=True)
                fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
                fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')
                div_1 = opy.plot(fig, auto_open=False, output_type='div')

                response = JsonResponse({            
                    'plot_div_2_region': div_1,
                    'rice-trend-weight-2':rfp_percentage,

                        })
                add_get_params(response)
                return response
            else:
                    
                fig = go.Figure(go.Bar(
                    x=[20],
                    y=[' '],
                    marker_color=[DMP_RFP.plot_bg],
                    orientation='h'))
                fig.add_annotation(
                                text= '<b>' + 'No Data!' + '</b>',
                                x= 10,
                                y=' ',
                                font=dict(
                                    family="Courier New, monospace",
                                    size=16,
                                    color="black",
                                ),
                    showarrow=False)
                fig.update_layout(    plot_bgcolor=DMP_RFP.plot_bg )

                fig.update_layout(xaxis_range=[0,20],  plot_bgcolor=DMP_RFP.plot_bg,)
                fig.update_layout(
                        height=480,
                        width=690,
                        plot_bgcolor=DMP_RFP.plot_bg,)         
                fig.update_xaxes(visible=False, showticklabels=False)
           
                div_1 = opy.plot(fig, auto_open=False, output_type='div')
               
                response = JsonResponse({            
                                    'plot_div_2_region': div_1,
                                        'rfp-weight-2':0,

                                        })
                        
                add_get_params(response)
                return response
            
        else:
            response = JsonResponse({            
                    'plot_div_2_region': "No Data!",         
                     'rfp-weight-9':0,           
                        })
                        
            add_get_params(response)
            return response

    @csrf_exempt
    def visual_ajax_3_region(request):
        if request.method =='POST':
            a2a=DMP_RFP.a2a
            list_of_regions=DMP_RFP.list_of_regions.copy()
            max_val = 0
            max_region = ''
            for region in list_of_regions:
                if region != 'AGT':
                    new_a2a = a2a[a2a['Region'].isin(['AGT', region])]
                    intersect = reduce(np.intersect1d, new_a2a.groupby('Region')['Material/Service No.'].apply(list))
                    result_df = new_a2a.loc[new_a2a['Material/Service No.'].isin(intersect), :]

                    if max_val < len(result_df['Material/Service No.'].unique().tolist()):
                        max_val = len(result_df['Material/Service No.'].unique().tolist())
                        max_region = region
                        
            new_a2a = a2a[a2a['Region'].isin(['AGT', max_region])]
            intersect = reduce(np.intersect1d, new_a2a.groupby('Region')['Material/Service No.'].apply(list))
            result_df = new_a2a.loc[new_a2a['Material/Service No.'].isin(intersect), :]
            result_df['PO Item Quantity'] = result_df['PO Item Quantity'].astype('float')
            result_df['Unit Price'] = result_df['Unit Price'].astype('float')
            result_df['PO Item Value (GC)'] = result_df['PO Item Value (GC)'].astype('float')
            result_df.shape



            list_of_regions = result_df['Region'].value_counts().index.tolist()
            list_of_regions = list_of_regions[::-1]
            list_of_regions.remove('AGT')
            list_of_regions.append('AGT')

            list_of_regions


            result_agt_df = result_df[result_df['Region'] == 'AGT']
            avg_result_df = result_df.copy()


            result_agt_df.loc[:, 'Average Demand'] = 0.0
            idx_list_4 = result_agt_df['Material/Service No.'].value_counts().index.tolist()
            len(idx_list_4)

            for item_number in idx_list_4:
                temp = result_agt_df[result_agt_df['Material/Service No.'] == item_number]
                count = len(temp.groupby(temp['PO Item Creation Date'].dt.year))
                summ = temp['PO Item Quantity'].sum()
                demand = summ/count
                result_agt_df.loc[result_agt_df['Material/Service No.'] == item_number, ['Average Demand']] = demand
            result_agt_df = result_agt_df.drop_duplicates(subset = ['Material/Service No.'], keep = 'first') 

            result_df = pd.merge(result_df, result_agt_df[['Material/Service No.', 'Average Demand']],  how='left', on='Material/Service No.')


            total_spends = []
            regions = []
            for region in list_of_regions:
                df_2 = result_df[result_df['Region'] == region] 
                df_2.loc[:, 'Average Price'] = -1
                idx_list_4 = df_2['Material/Service No.'].value_counts().index.tolist()
            
                for item_number in idx_list_4:
                    temp = df_2[df_2['Material/Service No.'] == item_number]
                    average_price = temp['Unit Price'].mean()
                    result_df.loc[temp.index.tolist(), ['Average Price']] = average_price

            result_df['Total Spend'] = result_df['Average Demand'] * result_df['Average Price']
            result_df = result_df.drop_duplicates(subset = ['Material/Service No.', 'Region'], keep = 'first') 

            for region in list_of_regions:
                summ = result_df.loc[result_df['Region'] == region]['Total Spend'].sum()
                total_spends.append(summ)
                regions.append(region)
                
            delta = []
            colors = []
            y_ = regions
            y_2 = [' ', '  ' ]
            for index, elem in enumerate(total_spends):
                if index == len(total_spends)-1:
                    delta.append(' ')
                    colors.append('red')
                else:
                    # delta.append(str(abs(int(elem - total_spends[-1]))))
                    delta.append(str(abs(int(round(((elem - total_spends[-1])/elem)*100)))))
                    if int(elem - total_spends[-1]) < 0:
                        colors.append('red')
                    else:
                        colors.append('green')

            fig = px.bar(
                        x=total_spends,
                        y= y_2,
                        color = y_,
                        orientation = 'h',
                            color_discrete_map={
                            'AGT': 'rgb(144, 238, 144)',
                            'GOM': 'rgb(173, 216, 230)',                            
                    },
            )
            count = len(result_df['Material/Service No.'].unique().tolist() )
            rfp_percentage = (count/len(a2a['Material/Service No.'].unique().tolist())) * 100

            rfp_percentage=round(rfp_percentage, 2)
            fig.update_yaxes(ticksuffix=' ' ) 
            fig.update_layout(
                        title="",
                        xaxis_title="",
                        yaxis_title="",
                        legend_title="Regions (" + str(round(count,2 )) +")",
                        template = 'ggplot2',
                    )

            for a, b in enumerate(y_):
                        fig.add_annotation(
                                text= '<b>' + "{:,}".format(int(total_spends[a])) + '</b>',
                                x= total_spends[a] - total_spends[-1]/100,
                                y=a,
                                xanchor='right',
                                font=dict(
                                    family="Courier New, monospace",
                                    size=16,
                                    color="#ffffff",
                                ),
                    showarrow=False)

            for a, b in enumerate(y_):
                fig.add_annotation(
                        text= '<b>' + b + '</b>',
                        y=a,
                        x=(100),
                        xanchor='left', 
                        font=dict(
                            family="Courier New, monospace",
                            size=16,
                            color="#ffffff",
                            ),
                        align='left',
            showarrow=False)

            for a, b in enumerate(delta):
                temp = ''
                if b != ' ':
                    if len(b) > 0  and float(b) < 0 :
                        color = 'red'
                        temp = abs(float(b))
                    elif len(b) != 0:
                        color = '#006400'
                        temp = abs(float(b))

                    if total_spends[a] > total_spends[-1]:
                        x_ = max(total_spends)
                    else:
                        x_ = total_spends[-1]
                if a != len(delta)-1:
                    # temp =  "{:,}".format(int(temp))
                    temp = str(int(temp)) + '%'
                fig.add_annotation(                            
                        text='<b>' + str(temp) + '</b>',
                        x=(x_ + max(total_spends)/15),
                        y=a,
                        font=dict(
                            family="Courier New, monospace",
                            size=16,
                            color=color,
                        ),
                        align="right",
            showarrow=False)
                
            fig.update_layout(xaxis_range=[0, max(total_spends) + max(total_spends)/7],)
       
            fig.add_vline(x=total_spends[-1], line_width=2, line_dash="dash", line_color="red")
            new_spend = total_spends[:len(total_spends)-1]
            if max(new_spend) > total_spends[-1]:
                fig.add_vline(x=max(new_spend), line_width=2, line_dash="dash", line_color="green")

            fig.update_layout(legend=dict(yanchor="top", y=1, xanchor="left", x=0.00))
            
            fig.update_layout(
                        height=450,
                        width=690,
                        plot_bgcolor='rgba(255,255,255, 0.5)',) 

            fig.update_xaxes(visible=True, showticklabels=True)
            fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
            fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')
            div_1 = opy.plot(fig, auto_open=False, output_type='div')
        
            #! return finded rows data in table 
            response = JsonResponse({            
                'plot_div_3_region': div_1,
                 'rfp-weight-10':rfp_percentage,

                    })
                    
            add_get_params(response)
            return response
            
        else:
            response = JsonResponse({            
                    'plot_div_3_region': "No Data!",
                   'rfp-weight-10':0,

                        })
                        
            add_get_params(response)
            return response

    @csrf_exempt
    def visual_ajax_4_region(request):
        if request.method =='POST':

            result_df=DMP_RFP.result_df.copy()
            list_of_regions=DMP_RFP.list_of_regions.copy()
            if len(list_of_regions) ==4:

                result_agt_df = result_df[result_df['Region'] == 'AGT']
                avg_result_df = result_df.copy()
                a2a=DMP_RFP.a2a.copy()

                result_agt_df.loc[:, 'Average Demand'] = 0.0
                idx_list_4 = result_agt_df['Material/Service No.'].value_counts().index.tolist()
                len(idx_list_4)
                for item_number in idx_list_4:
                    temp = result_agt_df[result_agt_df['Material/Service No.'] == item_number]
                    count = len(temp.groupby(temp['PO Item Creation Date'].dt.year))
                    summ = temp['PO Item Quantity'].sum()
                    demand = summ/count
                    result_agt_df.loc[result_agt_df['Material/Service No.'] == item_number, ['Average Demand']] = demand
                result_agt_df = result_agt_df.drop_duplicates(subset = ['Material/Service No.'], keep = 'first') 

                result_df = pd.merge(result_df, result_agt_df[['Material/Service No.', 'Average Demand']],  how='left', on='Material/Service No.')



                total_spends = []
                regions = []
                for region in list_of_regions:
                    df_2 = result_df[result_df['Region'] == region] 
                    df_2.loc[:, 'Average Price'] = -1
                    idx_list_4 = df_2['Material/Service No.'].value_counts().index.tolist()
                
                    for item_number in idx_list_4:
                        temp = df_2[df_2['Material/Service No.'] == item_number]
                        average_price = temp['Unit Price'].mean()
                        result_df.loc[temp.index.tolist(), ['Average Price']] = average_price
                        
     
                result_df['Total Spend'] = result_df['Average Demand'] * result_df['Average Price']
                result_df = result_df.drop_duplicates(subset = ['Material/Service No.', 'Region'], keep = 'first') 

                for region in list_of_regions:
                    summ = result_df.loc[result_df['Region'] == region]['Total Spend'].sum()
                    total_spends.append(summ)
                    regions.append(region)

                                                                            
                                                                                                                                
                delta = []
                colors = []
                y_ = regions
                y_2 = [' ', '  ' , '   ', '    ']
                # for index, elem in enumerate(total_spends):
                #     if index == len(total_spends)-1:
                #         delta.append(' ')
                #         colors.append('red')
                #     else:
                #         # delta.append(str(abs(int(elem - total_spends[-1]))))
                #         delta.append(str(abs(int(round(((elem - total_spends[-1])/elem)*100)))))
                #         if int(elem - total_spends[-1]) < 0:
                #             colors.append('red')
                #         else:
                #             colors.append('green')

                for index, elem in enumerate(total_spends):
                    if elem == 0:
                        elem += 0.00001
                    if index == len(total_spends)-1:
                        delta.append(' ')
                        colors.append('red')
                    else:
                        # delta.append(str(abs(round((elem - total_spends[-1])/elem,2 )*100)))                    
                        delta.append(str(abs(int(round(((elem - total_spends[-1])/elem)*100)))))
                        if int(elem - total_spends[-1]) < 0:
                            colors.append('red')
                        else:
                            colors.append('green')
             
                fig = px.bar(
                            x=total_spends,
                            y= y_2,
                            color = y_,
                            orientation = 'h',
                            color_discrete_map={
                                'GOM':  '#FF7F7F',
                                'ANG':  'rgb(251, 192, 45)',
                                'UKS':  'rgb(173, 216, 230)',
                                'AGT': 'rgb(144, 238, 144)'
                        },
        
                )
                count = len(result_df['Material/Service No.'].unique().tolist() )
                rfp_percentage = (count/len(a2a['Material/Service No.'].unique().tolist())) * 100

                rfp_percentage=round(rfp_percentage, 2)
                fig.update_yaxes(ticksuffix=' ' ) 
                fig.update_layout(
                            title="",
                            xaxis_title="",
                            yaxis_title="",
                            legend_title="Regions (" + str(round(count,2 )) +")",
                            template = 'ggplot2',
                        )

                for a, b in enumerate(y_):
                            fig.add_annotation(
                                    text= '<b>' + "{:,}".format(int(total_spends[a])) + '</b>',
                                    x= total_spends[a] - total_spends[-1]/100,
                                    y=a,
                                    xanchor='right',
                                    font=dict(
                                        family="Courier New, monospace",
                                        size=16,
                                        color="#ffffff",
                                    ),
                        showarrow=False)

                for a, b in enumerate(y_):
                    fig.add_annotation(
                            text= '<b>' + b + '</b>',
                            y=a,
                            x=(100),
                            xanchor='left', 
                            font=dict(
                                family="Courier New, monospace",
                                size=16,
                                color="#ffffff",
                                ),
                            align='left',
                showarrow=False)

                for a, b in enumerate(delta):
                    temp = ''
                    if b != ' ':
                        if len(b) > 0  and float(b) < 0 :
                            color = 'red'
                            temp = abs(float(b))
                        elif len(b) != 0:
                            color = '#006400'
                            temp = abs(float(b))

                        if total_spends[a] > total_spends[-1]:
                            x_ = max(total_spends)
                        else:
                            x_ = total_spends[-1]
                    if a != len(delta)-1:
                        # temp =  "{:,}".format(int(temp))
                        temp = str(int(temp)) + '%'
                    fig.add_annotation(                            
                            text='<b>' + str(temp) + '</b>',
                            x=(x_ + max(total_spends)/15),
                            y=a,
                            font=dict(
                                family="Courier New, monospace",
                                size=16,
                                color=colors[a],
                            ),
                            align="right",
                showarrow=False)
                    
                fig.update_layout(xaxis_range=[0, max(total_spends) + max(total_spends)/7],)

                fig.add_vline(x=total_spends[-1], line_width=2, line_dash="dash", line_color="red")
                new_spend = total_spends[:len(total_spends)-1]
                if max(new_spend) > total_spends[-1]:
                    fig.add_vline(x=max(new_spend), line_width=2, line_dash="dash", line_color="green")

    
                fig.update_layout(
                            height=450,
                            width=690,
                            plot_bgcolor='rgba(255,255,255, 0.5)',) 

                fig.update_xaxes(visible=True, showticklabels=True)
                fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
                # fig.update_yaxes(showline=True, linewidth=1, linecolor='black')
                fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')
            
                fig.update_layout(
                            height=450,
                            width=690,
                            plot_bgcolor='rgba(255, 255, 255, 0.5)',) 

                div_1 = opy.plot(fig, auto_open=False, output_type='div')

            
                #! return finded rows data in table 
                response = JsonResponse({            
                    'plot_div_1_region': div_1,
                    'price-trend-weight-1':rfp_percentage,


                        })
                        
                add_get_params(response)
                return response
            else:
                
                fig = go.Figure(go.Bar(
                    x=[20],
                    y=[' '],
                    marker_color=[DMP_RFP.plot_bg],
                    orientation='h'))
                fig.add_annotation(
                                text= '<b>' + 'No Data!' + '</b>',
                                x= 10,
                                y=' ',
                                font=dict(
                                    family="Courier New, monospace",
                                    size=16,
                                    color="black",
                                ),
                    showarrow=False)
                fig.update_layout(    plot_bgcolor=DMP_RFP.plot_bg )

                fig.update_layout(xaxis_range=[0,20],  plot_bgcolor=DMP_RFP.plot_bg,)
                fig.update_layout(
                        height=480,
                        width=690,
                        plot_bgcolor=DMP_RFP.plot_bg,)         
                fig.update_xaxes(visible=False, showticklabels=False)
           
                div_1 = opy.plot(fig, auto_open=False, output_type='div')
               
                response = JsonResponse({ 'plot_div_2_region': div_1, 'top_10_spend_weight':0,})
                        
                add_get_params(response)
                return response

            
        else:
            response = JsonResponse({            
                    'plot_div_1_region': "No Data!",                    
                        })
                        
            add_get_params(response)
            return response

    @csrf_exempt
    def visual_ajax_5_region(request):
        if request.method =='POST':

            list_of_regions=DMP_RFP.list_of_regions.copy()
            last_result_df=DMP_RFP.result_df.copy()
            result_df=DMP_RFP.result_df.copy()
            a2a=DMP_RFP.a2a.copy()

            
            if len(list_of_regions) == 4:
           
                max_regions = ['AGT']
                
                max_val = 0

                max_region = ''

                for region in list_of_regions:
                
                    if region != 'AGT':
                        new_a2a = a2a[a2a['Region'].isin(['AGT', region])]
                        intersect = reduce(np.intersect1d, new_a2a.groupby('Region')['Material/Service No.'].apply(list))
                        result_temp_df = new_a2a.loc[new_a2a['Material/Service No.'].isin(intersect), :]


                        if max_val < len(result_temp_df['Material/Service No.'].unique().tolist()):
                            max_val = len(result_temp_df['Material/Service No.'].unique().tolist())
                            max_region = region


                max_regions.append(max_region)
                list_of_regions.remove(max_region)

                max_val = 0
                max_region = ''
                for region in list_of_regions:
                    if region != 'AGT':
                        new_a2a = a2a[a2a['Region'].isin(['AGT', region])]
                        intersect = reduce(np.intersect1d, new_a2a.groupby('Region')['Material/Service No.'].apply(list))
                        result_temp_df = new_a2a.loc[new_a2a['Material/Service No.'].isin(intersect), :]


                        if max_val < len(result_temp_df['Material/Service No.'].unique().tolist()):
                            max_val = len(result_temp_df['Material/Service No.'].unique().tolist())
                            max_region = region
                max_regions.append(max_region)

                list_of_regions=max_regions[::-1].copy()

            
                result_agt_df = last_result_df[last_result_df['Region'] == 'AGT']
                result_agt_df = result_agt_df.loc[result_agt_df.groupby(['Material/Service No.'])['PO Item Creation Date'].idxmax()]
                result_agt_df['Last Demand'] = result_agt_df['PO Item Quantity']


                last_result_df = pd.merge(last_result_df, result_agt_df[['Material/Service No.', 'Last Demand']],  how='left',on='Material/Service No.')
                last_result_df[last_result_df['Material/Service No.'] == '11042217'][['Region', 'Material/Service No.', 'PO Item Value (GC)', 'PO Item Quantity', 'PO Item Quantity Unit',  'Last Demand', 'Unit Price',  'Incoterms Name', 'PO Item Creation Date']]
                last_result_df.shape


                l_1 = last_result_df.loc[last_result_df.groupby(['Material/Service No.', 'Region'])['PO Item Creation Date'].idxmax()]

                l_1['Total Spend'] = l_1['Last Demand'] * l_1['Unit Price']

                total_spends = []
                regions = []

                for region in list_of_regions:
                    temp_df = l_1[l_1['Region'] == region]
                    total_spends.append(temp_df['Total Spend'].sum())
                    regions.append(region)
                    
                    
                    
                delta = []
                colors = []
                y_ = regions
                y_2 = [' ', '  ' , '   ' ]
                for index, elem in enumerate(total_spends):
                    if index == len(total_spends)-1:
                        delta.append(' ')
                        colors.append('red')
                    else:
                        # delta.append(str(abs(int(elem - total_spends[-1]))))
                        delta.append(str(abs(int(round(((elem - total_spends[-1])/elem)*100)))))
                        if int(elem - total_spends[-1]) < 0:
                            colors.append('red')
                        else:
                            colors.append('green')

                color_map={
                        'GOM':  '#FF7F7F',
                        'ANG':  'rgb(251, 192, 45)',
                        'UKS':  'rgb(173, 216, 230)',
                        'AGT': 'rgb(144, 238, 144)'
                }

                fig = px.bar(
                            x=total_spends,
                            y= y_2,
                            color = y_,
                            orientation = 'h',
                            color_discrete_map={
                                regions[2]: color_map.get(regions[2]),
                                regions[1]: color_map.get(regions[1]),
                                regions[0]: color_map.get(regions[0]),                                                 
                        },
                )
                count = len(result_df['Material/Service No.'].unique().tolist() )
                rfp_percentage = (count/len(a2a['Material/Service No.'].unique().tolist())) * 100

                rfp_percentage=round(rfp_percentage, 2)
                fig.update_yaxes(ticksuffix=' ' ) 
                fig.update_layout(
                            title="",
                            xaxis_title="",
                            yaxis_title="",
                            legend_title="Regions (" + str(round(count,2 )) +")",
                            template = 'ggplot2',
                        )

                for a, b in enumerate(y_):
                            fig.add_annotation(
                                    text= '<b>' + "{:,}".format(int(total_spends[a])) + '</b>',
                                    x= total_spends[a] - total_spends[-1]/7,
                                    y=a,
                                    xanchor='right',
                                    font=dict(
                                        family="Courier New, monospace",
                                        size=16,
                                        color="#ffffff",
                                    ),
                        showarrow=False)

                for a, b in enumerate(y_):
                    fig.add_annotation(
                            text= '<b>' + b + '</b>',
                            y=a,
                            x=(100),
                            xanchor='left', 
                            font=dict(
                                family="Courier New, monospace",
                                size=16,
                                color="#ffffff",
                                ),
                            align='left',
                showarrow=False)

                # for a, b in enumerate(delta):
                #     temp = ''
                #     if b != ' ':
                #         if len(b) > 0  and float(b) < 0 :
                #             color = 'red'
                #             temp = abs(float(b))
                #         elif len(b) != 0:
                #             color = '#006400'
                #             temp = abs(float(b))

                #         if total_spends[a] > total_spends[-1]:
                #             x_ = max(total_spends)
                #         else:
                #             x_ = total_spends[-1]
                #     if a != len(delta)-1:
                #         # temp =  "{:,}".format(int(temp))
                #         temp = str(int(temp)) + '%'
                #     fig.add_annotation(                            
                #             text='<b>' + str(temp) + '</b>',
                #             x=(x_ + max(total_spends)/15),
                #             y=a,
                #             font=dict(
                #                 family="Courier New, monospace",
                #                 size=16,
                #                 color=colors,
                #             ),
                #             align="right",
                # showarrow=False)


            for a, b in enumerate(delta):
                temp = ''
                if b != ' ':
                    if len(b) > 0  and float(b) < 0 :                        
                        temp = abs(float(b))
                    elif len(b) != 0:
                        temp = abs(float(b))

                    if total_spends[a] > total_spends[-1]:
                        x_ = max(total_spends)
                    else:
                        x_ = total_spends[-1]
                if a != len(delta)-1:
                    temp = str(int(temp)) + '%' 
                fig.add_annotation(   
                        text='<b>' + str(temp) +  '</b>',
                        x = x_ + max(total_spends)/100,
                        xanchor='left', 
                        y=a,
                        font=dict(
                            family="Courier New, monospace",
                            size=16,
                            color=colors[a],
                        ),
                        
                        align="right",
            showarrow=False)
                    
                fig.update_layout(xaxis_range=[0, max(total_spends) + max(total_spends)/7],)
                # fig.add_vline(x=total_spends[-1], line_width=2, line_dash="dash", line_color="red")
                # fig.add_vline(x=max(total_spends), line_width=2, line_dash="dash", line_color="green")
                fig.update_layout(plot_bgcolor='rgba(171, 248, 190, 0.8)')


                fig.add_vline(x=total_spends[-1], line_width=2, line_dash="dash", line_color="red")
                new_spend = total_spends[:len(total_spends)-1]
                if max(new_spend) > total_spends[-1]:
                    fig.add_vline(x=max(new_spend), line_width=2, line_dash="dash", line_color="green")
                # fig.show()
                fig.update_layout(legend=dict(yanchor="top", y=1, xanchor="left", x=0.00))
                fig.update_layout(
                            height=450,
                            width=690,
                            plot_bgcolor='rgba(255, 255, 255, 0.5)',) 

                fig.update_xaxes(visible=True, showticklabels=True)
                fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
                # fig.update_yaxes(showline=True, linewidth=1, linecolor='black')
                fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')
                # fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')    
            

                
                div_1 = opy.plot(fig, auto_open=False, output_type='div')

            
                #! return finded rows data in table 
                response = JsonResponse({            
                    'plot_div_2_region': div_1,
                    'price-trend-weight-2':rfp_percentage,
                        })
                        
                add_get_params(response)
                return response
            else:            
                fig = go.Figure(go.Bar(
                    x=[20],
                    y=[' '],
                    marker_color=[DMP_RFP.plot_bg],
                    orientation='h'))
                fig.add_annotation(
                                text= '<b>' + 'No Data!' + '</b>',
                                x= 10,
                                y=' ',
                                font=dict(
                                    family="Courier New, monospace",
                                    size=16,
                                    color="black",
                                ),
                    showarrow=False)
                fig.update_layout(    plot_bgcolor=DMP_RFP.plot_bg )

                fig.update_layout(xaxis_range=[0,20],  plot_bgcolor=DMP_RFP.plot_bg,)
                fig.update_layout(
                        height=480,
                        width=690,
                        plot_bgcolor=DMP_RFP.plot_bg,)         
                fig.update_xaxes(visible=False, showticklabels=False)
           
                div_1 = opy.plot(fig, auto_open=False, output_type='div')
               
                response = JsonResponse({            
                                    'plot_div_2_region': div_1,
                                        'rfp-weight-8':0,

                                        })
                        
                add_get_params(response)
                return response
            
        else:
            response = JsonResponse({            
                    'plot_div_2_region': "No Data!",  
                       'rfp-weight-8':0,                  
                        })
                        
            add_get_params(response)
            return response

    @csrf_exempt
    def visual_ajax_6_region(request):
        if request.method =='POST':

            a2a=DMP_RFP.a2a.copy()
            list_of_regions=DMP_RFP.list_of_regions.copy()
            last_result_df=DMP_RFP.result_df.copy()



            max_val = 0
            max_region = ''
            for region in list_of_regions:
                if region != 'AGT':
                    new_a2a = a2a[a2a['Region'].isin(['AGT', region])]
                    intersect = reduce(np.intersect1d, new_a2a.groupby('Region')['Material/Service No.'].apply(list))
                    result_df = new_a2a.loc[new_a2a['Material/Service No.'].isin(intersect), :]

                    if max_val < len(result_df['Material/Service No.'].unique().tolist()):
                        max_val = len(result_df['Material/Service No.'].unique().tolist())
                        max_region = region
                        
            new_a2a = a2a[a2a['Region'].isin(['AGT', max_region])]

            intersect = reduce(np.intersect1d, new_a2a.groupby('Region')['Material/Service No.'].apply(list))
            result_df = new_a2a.loc[new_a2a['Material/Service No.'].isin(intersect), :]
            result_df['PO Item Quantity'] = result_df['PO Item Quantity'].astype('float')
            result_df['Unit Price'] = result_df['Unit Price'].astype('float')
            result_df['PO Item Value (GC)'] = result_df['PO Item Value (GC)'].astype('float')
            result_df.shape



            list_of_regions = result_df['Region'].value_counts().index.tolist()
            list_of_regions = list_of_regions[::-1]
            list_of_regions.remove('AGT')
            list_of_regions.append('AGT')

            last_result_df=result_df

            result_agt_df = last_result_df[last_result_df['Region'] == 'AGT']
            result_agt_df = result_agt_df.loc[result_agt_df.groupby(['Material/Service No.'])['PO Item Creation Date'].idxmax()]
            result_agt_df['Last Demand'] = result_agt_df['PO Item Quantity']
            result_agt_df.shape



            last_result_df = pd.merge(last_result_df, result_agt_df[['Material/Service No.', 'Last Demand']],  how='left',on='Material/Service No.')
            last_result_df[last_result_df['Material/Service No.'] == '11042217'][['Region', 'Material/Service No.', 'PO Item Value (GC)', 'PO Item Quantity', 'PO Item Quantity Unit',  'Last Demand', 'Unit Price',  'Incoterms Name', 'PO Item Creation Date']]
            last_result_df.shape
            l_1 = last_result_df.loc[last_result_df.groupby(['Material/Service No.', 'Region'])['PO Item Creation Date'].idxmax()]

            l_1['Total Spend'] = l_1['Last Demand'] * l_1['Unit Price']


            total_spends = []
            regions = []

            for region in list_of_regions:
                temp_df = l_1[l_1['Region'] == region]
                total_spends.append(temp_df['Total Spend'].sum())
                regions.append(region)


            delta = []
            colors = []
            y_ = regions
            y_2 = [' ', '  ']
            for index, elem in enumerate(total_spends):
                if index == len(total_spends)-1:
                    delta.append(' ')
                    colors.append('red')
                else:
                    # delta.append(str(abs(int(elem - total_spends[-1]))))
                    delta.append(str(abs(int(round(((elem - total_spends[-1])/elem)*100)))))
                    if int(elem - total_spends[-1]) < 0:
                        colors.append('red')
                    else:
                        colors.append('green')

            fig = px.bar(
                        x=total_spends,
                        y= y_2,
                        color = y_,
                        orientation = 'h',
                        color_discrete_map={
                            'AGT': 'rgb(144, 238, 144)',
                            'GOM': 'rgb(173, 216, 230)',                            
                    },
            )
            count = len(result_df['Material/Service No.'].unique().tolist() )
            rfp_percentage = (count/len(a2a['Material/Service No.'].unique().tolist())) * 100

            rfp_percentage=round(rfp_percentage, 2)
            fig.update_yaxes(ticksuffix=' ' ) 
            fig.update_layout(
                        title="",
                        xaxis_title="",
                        yaxis_title="",
                        legend_title="Regions (" + str(round(count,2 )) +")",
                        template = 'ggplot2',
                    )

            for a, b in enumerate(y_):
                        fig.add_annotation(
                                text= '<b>' + "{:,}".format(int(total_spends[a])) + '</b>',
                                x= total_spends[a] - total_spends[-1]/7,
                                y=a,
                                xanchor='right',
                                font=dict(
                                    family="Courier New, monospace",
                                    size=16,
                                    color="#ffffff",
                                ),
                    showarrow=False)

            for a, b in enumerate(y_):
                fig.add_annotation(
                        text= '<b>' + b + '</b>',
                        y=a,
                        x=(100),
                        xanchor='left', 
                        font=dict(
                            family="Courier New, monospace",
                            size=16,
                            color="#ffffff",
                            ),
                        align='left',
            showarrow=False)

            for a, b in enumerate(delta):
                temp = ''
                if b != ' ':
                    if len(b) > 0  and float(b) < 0 :
                        color = 'red'
                        temp = abs(float(b))
                    elif len(b) != 0:
                        color = '#006400'
                        temp = abs(float(b))

                    if total_spends[a] > total_spends[-1]:
                        x_ = max(total_spends)
                    else:
                        x_ = total_spends[-1]
                        
                if a != len(delta)-1:
                    # temp =  "{:,}".format(int(temp))
                    temp = str(int(temp)) + '%'
                fig.add_annotation(                            
                        text='<b>' + str(temp) + '</b>',
                        x=(x_ ),
                        y=a,
                        font=dict(
                            family="Courier New, monospace",
                            size=16,
                            color=color,
                        ),
                        xanchor="left",
            showarrow=False)
                
            fig.update_layout(xaxis_range=[0, max(total_spends) + max(total_spends)/7],)

            fig.add_vline(x=total_spends[-1], line_width=2, line_dash="dash", line_color="red")
            new_spend = total_spends[:len(total_spends)-1]
            if max(new_spend) > total_spends[-1]:
                fig.add_vline(x=max(new_spend), line_width=2, line_dash="dash", line_color="green")


            
            fig.update_layout(
                        height=450,
                        width=690,
                        plot_bgcolor='rgba(255, 255, 255, 0.5)',) 
            
            fig.update_xaxes(visible=True, showticklabels=True)
            fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
            fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')
            
            div_1 = opy.plot(fig, auto_open=False, output_type='div')

        
            #! return finded rows data in table 
            response = JsonResponse({            
                'plot_div_3_region': div_1,
                'price-trend-weight-3':rfp_percentage,
                    })
                    
            add_get_params(response)
            return response
            
        else:
            response = JsonResponse({            
                    'plot_div_3_region': "No Data!",       
                       'rfp-weight-9':0,             
                        })
                        
            add_get_params(response)
            return response
