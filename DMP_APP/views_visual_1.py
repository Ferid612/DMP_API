from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import numpy as np
import math
import json
import pandas as pd
from .views_search_1 import main_searching_algoritm
from .custom_logic import *
from .helpers import *
from datetime import date
import plotly.graph_objects as go
import plotly.express as px
from django.core.mail import send_mail
import os
import plotly.offline as opy
from .helpers_2 import *
from DMP_API.settings import engine
from sqlalchemy.orm import Session
from .models import DMP_USERS
import traceback
import logging

class DMP:
    plot_bg='rgba(255, 255,255, 0.8)'
    uploaded_historical_data = []
    
    @csrf_exempt
    def __init__(self):
        print("_init_")


    @csrf_exempt 
    def upload_file_historical(request): 
        # Build the POST parameters
        if request.method == 'POST':
            try:
                    
                #*cheking user status
                user_type=check_user_status(request)['user_type']  
                if 'customer' == 'customer':
                
                    df=upload_file_helpers(request)
                    DMP.uploaded_historical_data = df
                   
                    df.to_csv(str(BASE_DIR) + "/static/uploaded_historical_data.csv",index = False)
                    response = JsonResponse({'answerr': "Success", })
                
                    add_get_params(response)
                    return response
                else:
                    response = JsonResponse({'Answer': "You have have not access to this query.", })
                    response.status_code=501
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
    def check_file_historical(request): 
       
        # Build the POST parameters
        if request.method == 'POST':
            
            user_type = check_user_status(request)['user_type']  
            
            if user_type != 'not_user':
                check_data=False
                try:    
             
                    #* check uploaded historical data 
                    df=DMP.uploaded_historical_data
                    if df.shape[0]>0:
                        check_data=True
                        
                except:
                    
                    check_data=False
                    print("\033[94m Info: Historical data not uploaded yet. \033[0m") 
                
                #* return user type and uploaded historical data cheking
                response = JsonResponse({'answer': check_data, 
                                        'user_type':user_type,
                                        })
                
                #* adding response parameters
                add_get_params(response)
                return response
            else:
        
                #* return user not access code - 501
                response = JsonResponse({'error_text':"You have not access"})
                response.status_code = 501
                add_get_params(response)
                return response        
        else:
            
            response = JsonResponse({'Answer': "This request method is not POST", })
            add_get_params(response)
            return response
        

    @csrf_exempt
    def searching(request):
        if request.method =='POST':
            try: 
                user_type=check_user_status(request)['user_type']    
                if user_type != 'not_user':
                    #* get all input data in inputs
                    DMP.input_region_name = request.POST.get('region')  
                    DMP.input_material_id = request.POST.get('material')  
                    DMP.input_description = request.POST.get('description')  
                    DMP.input_manufacturer_part_number = request.POST.get('manufactureId')
                    DMP.input_manufacturer_name = request.POST.get('manufacture')  
                    DMP.input_material_quantity= request.POST.get('material_quantity')
                    DMP.input_unit_of_measure = request.POST.get('unit_of_meas')

                    DMP.input_vendor_names = request.POST.getlist('vendor_names[]')
                    DMP.input_proposed_prices= request.POST.getlist('proposed_prices[]')
                    DMP.input_currencies = request.POST.getlist('currencies[]')
                    DMP.input_incoterm_names = request.POST.getlist('incoterms[]')

                    # upload_historical_data=DMP.uploaded_historical_data
                    df = DMP.uploaded_historical_data

                    processed_df = preprocess_search_data(df, DMP.input_region_name)
                    DMP.df_org = processed_df.copy()
                    all_dataframes_from_searching = main_searching_algoritm(DMP.input_material_id, DMP.input_description, DMP.input_manufacturer_part_number, DMP.input_manufacturer_name, processed_df)
                    DMP.all_dataframes_from_searching = all_dataframes_from_searching
                    DMP.all_dataframe = pd.DataFrame(all_dataframes_from_searching['all_dataframe'])
                    DMP.result_data_app = pd.DataFrame(all_dataframes_from_searching['result_app_to_app'])
                    DMP.result_data_app_copy = DMP.result_data_app.copy()
                    DMP.result_data_all = pd.DataFrame(all_dataframes_from_searching['result_data_all'])
                    DMP.result_content = all_dataframes_from_searching['result_content']

                    DMP.proposed_prices = DMP.convert_usd(DMP.input_proposed_prices, DMP.input_currencies)
                    # get most similar vendor name
                    vendor_names_all_dataframe = processed_df['Vendor Name'].value_counts().index.tolist()
                    # print('vendor_names_all_dataframe: ', vendor_names_all_dataframe)
                    input_vendor_names_fuzzy=[]
                    for a in DMP.input_vendor_names:
                        if a not in vendor_names_all_dataframe:  
                            fuzzy_score = []
                            for vendor in vendor_names_all_dataframe:
                                lst_vendor = list(vendor.upper().replace(' ',''))
                                lst_a = list(a.replace(' ',''))
                                s1 = fuzz.partial_ratio(lst_vendor, lst_a)
                                fuzzy_score.append(s1)
                            max_score = max(fuzzy_score)
                            max_score_index = fuzzy_score.index(max_score)
                            result_vendor = vendor_names_all_dataframe[max_score_index]

                            if max_score >= 0.6:
                                input_vendor_names_fuzzy.append(result_vendor)

                        else:
                            input_vendor_names_fuzzy.append(a)

                    DMP.input_vendor_names = input_vendor_names_fuzzy   # vendor names


                    if DMP.result_data_all.shape[0]>0:
                        DMP.app_unit_of_measure = ['ALL', 'EA', 'PH']
                        if DMP.result_data_app.shape[0]>0:
                            for i in DMP.result_data_app['PO Item Quantity Unit'].value_counts().index.tolist():
                                DMP.app_unit_of_measure.append(i)

                            df_item = DMP.result_data_app.drop_duplicates(['Material/Service No.'])
                            
                            DMP.categories_in_result = DMP.result_data_app['Product Category Description'].value_counts().index.tolist()
                            DMP.item_numbers_in_result = DMP.result_data_app['Material/Service No.'].value_counts().index.tolist()
                            DMP.short_desc_in_result = DMP.result_data_app['PO Item Description'].value_counts().index.tolist()
                            DMP.new_manufacturer_name = [df_item['Manufacturer Name'].value_counts().index.tolist()[0]]
                                    
                            data_list=[]
                            data_list.append(DMP.item_numbers_in_result)
                            data_list.append(DMP.short_desc_in_result)
                            DMP.data_list=data_list
                        
                        DMP.apple_to_apple_count = DMP.result_data_app.shape[0]  
                        DMP.result_count = DMP.result_data_all.shape[0]    
                        #***************** for visual data and filters *****************
                    

                        all_headers=["PO No.","PO Item No.","Incoterms Name", "Material/Service No.","Vendor Name","PO Item Description","Manufacturer Name",
                        "Manufacturer Part No.","Long Description","PO Item Creation Date","PO Item Value (GC)","PO Item Value (GC) Unit", "PO Item Quantity Unit", "Unit Price","Converted Price", "score","path",
                        "desc","Select","desc_words_short", "desc_words_long"]
                        
                        DMP.all_headers=all_headers

                        json_records_all=DMP.result_data_all.to_json(orient='records')
                        DMP.result_data_all_json=json.loads(json_records_all)
                        
                        json_records_app=DMP.result_data_app.to_json(orient='records')
                        DMP.result_data_app_json=json.loads(json_records_app)

                        response = JsonResponse({
                                'result_data_all':  DMP.result_data_all_json,
                                'result_app_to_app':  DMP.result_data_app_json,
                                'user_input_desc': all_dataframes_from_searching['user_input_desc'],
                                'all_headers': all_headers,
                                'display_converted_uom':all_dataframes_from_searching['display_converted_uom'],
                                'apple_to_apple_count':DMP.apple_to_apple_count,
                            })
                            
                        add_get_params(response)
                        return response
                    else:
                        response = JsonResponse({
                                'result_data_all':  "space data",
                                'user_input_desc':"space data",
                                'all_headers':"space data",
                                'apple_to_apple_count':"0",
                                })
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
                response = JsonResponse({'error_text':"You have not access"})
                response.status_code = 501
                add_get_params(response)
                return response  

    @csrf_exempt
    def get_filter_data(request):
        if request.method =='POST':
            #! return finded rows data in table 
            response = JsonResponse({
                    'region':DMP.input_region_name,
                    'material_items':DMP.item_numbers_in_result,
                    'manufacture_names':DMP.new_manufacturer_name,      
                    'apple_to_apple_count':DMP.apple_to_apple_count,
                    'result_count':DMP.result_count,
                    'vendor_names':  DMP.input_vendor_names,
                    'categories':  DMP.categories_in_result,
                    'app_unit_of_measure':DMP.app_unit_of_measure,
                    'prices':DMP.input_proposed_prices,
                    'quantity':DMP.input_material_quantity,
                    'incoterms':DMP.input_incoterm_names,
                    'currencies':DMP.input_currencies,
                    'descriptions':DMP.short_desc_in_result,
                    'data_list':DMP.data_list,
                })
                
            add_get_params(response)
            return response
        else:
            response = JsonResponse({'this_post': "DMP.total_spend",})
                
            add_get_params(response)
            return response

    @csrf_exempt
    def save_app_to_app_in_search(request):
        if request.method =='POST':

            # * cheking user status
            user_type="not_user"
            user_type = check_user_status(request)['user_type']
            if user_type == "customer":

                approve_list= request.POST.getlist('approve_list[]')
                DMP.approve_list_in_search=approve_list


                #! return finded rows data in table 
                response = JsonResponse({
                    "success":"success",
                    })

                add_get_params(response)
                return response
            else:
            
                #* return user not access code - 501
                response = JsonResponse({'error_text':"You have not access"})
                response.status_code = 501
                add_get_params(response)
                return response        
        else:
            response = JsonResponse({'this_post': "DMP save app to app in search",})    
            add_get_params(response)
            return response

    # Visualization
    def convert_usd(proposed_prices, currencies):
        proposed_prices_in_usd = []
        for index, i in enumerate(currencies):
            proposed_prices_in_usd.append(float(proposed_prices[index]) * (1/DMP.result_content['quotes']['USD'+i]))
        return proposed_prices_in_usd

    @csrf_exempt
    def visual_ajax_1_2_3(request):
        if request.method =='POST':
           
            app_to_app = pd.DataFrame(DMP.result_data_app)            
            input_app_unit_of_measure= request.POST.get('app_unit_of_measure')
           
            if input_app_unit_of_measure != 'ALL':
                app_to_app = app_to_app[app_to_app['PO Item Quantity Unit'] == input_app_unit_of_measure]

            
            input_min_date, input_max_date = get_dates(request)
    
            #! Plot 1
            app_to_app['PO Item Creation Date'] = pd.DatetimeIndex(app_to_app['PO Item Creation Date'])
            app_to_app=  app_to_app[( app_to_app['PO Item Creation Date'] >= input_min_date) & ( app_to_app['PO Item Creation Date'] <= input_max_date)]
            app_to_app.sort_values(by='PO Item Creation Date', inplace=True)
            fig_1 = (px.scatter(app_to_app, x="PO Item Creation Date", y="Unit Price", color='Vendor Name', title='', text="Incoterms Name", )
            .update_traces(mode='lines+markers', textposition='top center'))
            
            today = date.today()
            for index, i in enumerate(DMP.proposed_prices):
                fig_1.add_trace(go.Scatter(x=[today], y=[i], mode='markers', name=DMP.input_vendor_names[index], marker_symbol='star-triangle-up', marker_size=15))
            
            fig_1 = update_layout_fig_1_3(fig_1, DMP.plot_bg)



            #! Plot 2
            a=app_to_app
            if input_app_unit_of_measure != 'ALL':
                a = a[a['PO Item Quantity Unit'] == input_app_unit_of_measure]

            a['PO Item Value (GC)'] = a['PO Item Value (GC)'].astype('float').astype(int)
            a['New PO Item Value (GC)'] = a['Unit Price'] * a['PO Item Quantity']
            a['New PO Item Value (GC)'] = a['New PO Item Value (GC)'].astype('float').astype(int)
            a['Year'] = a['PO Item Creation Date'].dt.year
            a['Year'] = pd.to_datetime(a.Year, format='%Y')
            a = pd.DataFrame(a.groupby(by=['Year', 'Vendor Name'])['New PO Item Value (GC)'].sum())
            a2 = pd.DataFrame(a.groupby(by=['Year'])['New PO Item Value (GC)'].sum())
            max_val = a2['New PO Item Value (GC)'].max()
            a['New PO Item Value (GC) Text'] =  a['New PO Item Value (GC)'].apply(lambda x : "{:,}".format(x))
            a.reset_index(inplace=True)
            a['Year'] = pd.DatetimeIndex(a['Year'])
            a['Year'] = a['Year'].dt.year

            fig_2 = px.bar(a, x='Year', y='New PO Item Value (GC)', color='Vendor Name',
                           barmode='stack', text='New PO Item Value (GC) Text', color_discrete_sequence=px.colors.qualitative.Set3,)
            
            fig_2 = update_layout_fig_2(fig_2, max_val, DMP.plot_bg)


            #! Plot 3
            fig_3 = (px.scatter(app_to_app, x="PO Item Creation Date", y="Unit Price", color='Incoterms Name', title='').update_traces(mode='lines+markers'))
            for index, i in enumerate(DMP.proposed_prices):
                fig_3.add_trace(go.Scatter(x=[today], y=[i], mode='markers', name=DMP.input_incoterm_names[index] + ' (' + DMP.input_vendor_names[index] + ')', marker_symbol='star-triangle-up', marker_size=15))

            fig_3 = update_layout_fig_1_3(fig_3, DMP.plot_bg)


            #! return finded rows data in table 
           
            div_1 = opy.plot(fig_1, auto_open=False, output_type='div')
            div_2 = opy.plot(fig_2, auto_open=False, output_type='div')     
            div_3 = opy.plot(fig_3, auto_open=False, output_type='div')
            # json_dumps=json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

                #! return finded rows data in table 
            response = JsonResponse({
                'plot_div_1': div_1,
                'plot_div_2': div_2,  
                'plot_div_3': div_3,
                    })
            print("ajax_1_2_3_succcessfull")
                    
            add_get_params(response)
            return response
        else:
            response = JsonResponse({
                'this_not_post': "DMP.2_2_3",
            })
            
        add_get_params(response)
        return response
    
    #!chart 4 stage 4 with ajax
    @csrf_exempt
    def visual_ajax_4(request):
        if request.method =='POST':
            input_vendor_1= request.POST.get('vendor_name')
            item_quantity = int(request.POST.get('input_quantity'))
            time_left = request.POST.get('input_min_date')
            time_right= request.POST.get('input_max_date')
            input_app_unit_of_measure= request.POST.get('app_unit_of_measure')
            result=DMP.result_data_app.copy()
            result = result[(result['PO Item Creation Date'] >= time_left) & (result['PO Item Creation Date'] <= time_right)]
            
            if input_app_unit_of_measure != 'ALL':
                result = result[result['PO Item Quantity Unit'] == input_app_unit_of_measure]
        
            vendor_names_2 = []
            po_creation_date = []
            po_incoterms = []
            
            flag = 1
            vendor_names = DMP.input_vendor_names
            proposed_price = DMP.proposed_prices[vendor_names.index(input_vendor_1)]

            if (len(vendor_names) == 1) or (proposed_price == min(DMP.proposed_prices)):
                flag = 0

            vendor_name = input_vendor_1
            input_incoterm = DMP.input_incoterm_names[vendor_names.index(vendor_name)]

            vendor_names_2.append(input_vendor_1)
            po_incoterms.append(input_incoterm)
            po_creation_date.append(date.today())
            

            ab = result.copy()
            min_ven_name = vendor_name
            min_ven_val = proposed_price
            min_incoterm = input_incoterm

            if flag == 1:
                for index, v_name in enumerate(vendor_names):
                    aa = DMP.proposed_prices[vendor_names.index(v_name)]
                    if aa < min_ven_val:
                        min_ven_val = aa
                        min_ven_name = v_name
                        min_incoterm = DMP.input_incoterm_names[index]
                vendor_names_2.insert(0, min_ven_name)
                po_creation_date.insert(0, date.today())
                po_incoterms.insert(0, min_incoterm)

            spend = []

        # Last
            last_purchase_df = result[result['PO Item Creation Date'] == result['PO Item Creation Date'].max()].iloc[0]
            last_price = last_purchase_df['Unit Price']
            vendor_last = last_purchase_df['Vendor Name']
            date_last = last_purchase_df['PO Item Creation Date'].strftime('%Y-%m-%d')
            incoterm_last = last_purchase_df['Incoterms Name']
            vendor_names_2.insert(0, vendor_last)
            po_creation_date .insert(0, date_last)
            po_incoterms.insert(0, incoterm_last)
            
        # Cheapest
            min_price_df = result[result['Unit Price'] ==  result['Unit Price'].min()].iloc[0]
            min_price = min_price_df['Unit Price']
            vendor_lowest = min_price_df['Vendor Name']
            date_lowest = min_price_df['PO Item Creation Date'].strftime('%Y-%m-%d')
            incoterm_lowest = min_price_df['Incoterms Name']
            vendor_names_2.insert(0, vendor_lowest)
            po_creation_date .insert(0, date_lowest)
            po_incoterms.insert(0, incoterm_lowest)

        # Average     
            avg_price = result['Unit Price'].mean()
            vendor_names_2.insert(0, ' ')
            po_creation_date .insert(0, ' ')
            po_incoterms.insert(0,' ')
            
            spend.append((avg_price * item_quantity))
            spend.append((min_price * item_quantity))
            spend.append((last_price * item_quantity))
            if flag == 1:
                spend.append((min_ven_val * item_quantity))
            spend.append(int(proposed_price * item_quantity))

            delta, colors = find_colors_for_vlines(spend)
            
            # -------------------------------------  Recommendation Start -------------------------------------
            new_flag = 0
            if len(vendor_names) > 1:
                new_flag =  1
            DMP.message_recomandation = recommendation_alg(proposed_price, min_price, last_price, avg_price, item_quantity, vendor_name,  min_ven_name, min_ven_val, new_flag)
            # -------------------------------------  Recommendation End -------------------------------------


            # # -------------------------------------  Negotiation Start ------------------------------------- 
            negotiation_alg(proposed_price, min_price, last_price, avg_price, input_vendor_1)
            # -------------------------------------  Negotiation End ------------------------------------- 


            if flag == 1:
                y_ = ['$' + str(int(avg_price)) + ' ', ' $' + str(int(min_price)) + ' ', '  $' + str(int(last_price)) + ' ',  '   $' + str(int(min_ven_val)) + ' ',         '    $' + str(int(proposed_price)) + ' ']
                y_2 = ['Average', 'Lowest', 'Last', 'Proposed Lowest', 'Proposed']
                aa = ['Average ', 'Lowest', 'Last', 'Proposed Lowest', 'Proposed  (' + vendor_name + ')']

            else:
                y_ = ['$' + str(int(avg_price)) + ' ', ' $' + str(int(min_price)) + ' ', '  $' + str(int(last_price)) + ' ', '   $' + str(int(proposed_price)) + ' ']
                y_2 = ['Average', 'Lowest', 'Last', 'Proposed']
                aa = ['Average ', 'Lowest', 'Last', 'Proposed  (' + vendor_name + ')']

            temp_df = pd.DataFrame(list(zip(y_, delta, spend,aa, vendor_names_2, po_creation_date, po_incoterms)), columns =['y_', 'delta', 'spend', 'color', 'Vendor', 'Date', 'Incoterm']).copy()

            fig = px.bar(temp_df, x='spend', y= 'y_', color = 'color', hover_data = ['Vendor', 'Date', 'Incoterm'], orientation = 'h', height = 400,
                        color_discrete_map={'Proposed': 'rgb(144, 238, 144)', 'Lowest': '#add8e6', 'Last': '#fbc02d',  'Average': '#FF7F7F', 'Proposed Lowest': 'rgb(120, 200, 67)', },)

            fig = update_layout_fig_4(fig, spend, delta, y_, y_2, colors, DMP.plot_bg)

            div_4 = opy.plot(fig, auto_open=False, output_type='div')     
            response = JsonResponse({
                'plot_div_4': div_4,
                'message': DMP.message_recomandation
            })               
                
            add_get_params(response)
            print("ajax_4_succcessfull")
            
            return response
        else:
            response = JsonResponse({'this_not_post': "DMP.4",})
            add_get_params(response)
            return response

    @csrf_exempt
    def visual_ajax_5_7(request):
        if request.method =='POST':

            input_plot_type = request.POST.get('input_plot_type')
            input_vendor_1= request.POST.get('vendor_name')
            time_left= request.POST.get('input_min_date')
            time_right= request.POST.get('input_max_date')
            df=pd.DataFrame(DMP.all_dataframe)
        
            #! stage 5  
            vendor_name=input_vendor_1
            category_name = DMP.categories_in_result[0]
            if input_plot_type == "vendor":
                temp = df[df['Vendor Name'] == vendor_name]        
            else:
                temp = df[df['Product Category Description'] == category_name] 

            temp['PO Item Creation Date'] = pd.DatetimeIndex(temp['PO Item Creation Date'])
            temp = temp[(temp['PO Item Creation Date'] > time_left) & (temp['PO Item Creation Date'] < time_right)]

            df_agg = temp.groupby(['Material/Service No.']).agg({'PO Item Value (GC)':sum})
            res = df_agg.apply(lambda x: x.sort_values(ascending=False))
            idx = res.index.tolist()
            list_of_idx = []

            i=0
            for index in idx:
                if temp[temp['Material/Service No.'] == index].shape[0] > 1 and index != '#':
                    list_of_idx.append(index)
                    if i == 9:
                        break
                    i +=1

            if len(list_of_idx) > 0:

                result_5 = temp[temp['Material/Service No.'].isin(list_of_idx)]        
                result_5['Unit Price'] = round(result_5['PO Item Value (GC)'].astype(float) / result_5['PO Item Quantity'].astype(float), 2)

                fig = go.Figure()
                groups = result_5.groupby("Material/Service No.") ##.apply(lambda x: x.sort_values('abs_percentage', ascending=False))
                i=0
                for name, group in groups:
                    list_of_dates = []
                    list_of_usd_prices = []
                    group.sort_values(by='PO Item Creation Date', inplace=True)
                    for index, row in group.iterrows():
                            list_of_usd_prices.append(row['Unit Price'])
                            list_of_dates.append(row['PO Item Creation Date']) 

                    if row['Material/Service No.'] in list_of_idx[0]:
                        fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='lines+markers+text', textposition='top center', name=name, marker_size=5, line=dict(color=px.colors.qualitative.Bold[i]),))
                        fig.update_traces()
                    else:
                        fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='lines+markers+text', textposition='top center', name=name, marker_size=5, visible='legendonly', line=dict(color=px.colors.qualitative.Bold[i]),))
                    i += 1
              
                fig = update_layout_fig_5_7(fig, DMP.plot_bg)

                div_5 = opy.plot(fig, auto_open=False, output_type='div')

                #! return finded rows data in table 
                response = JsonResponse({            
                    'plot_div': div_5,
                        })
                        
                add_get_params(response)
                print("ajax_5_succcessfull")

                return response
            else:
                response = JsonResponse({            
                    'plot_div': "div_5",
                })
                            
                add_get_params(response)
               
                print("ajax_5_not_succcessfull")
                return response
        else:
            response = JsonResponse({
            'this_not_post': "DMP.5",
            })
            
            add_get_params(response)
            return response
                
    # ! visual_ajax_6 category names:
    @csrf_exempt    
    def visual_ajax_6(request):
        if request.method =='POST':
            vendor_name = request.POST.get('vendor_name')
            input_min_date = request.POST.get('input_min_date')
            input_max_date = request.POST.get('input_max_date')
            
            df = DMP.df_org 
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

            a = df[df['Vendor Name'].str.lower() == vendor_name.lower()]
            a['PO Item Creation Date'] = pd.DatetimeIndex(a['PO Item Creation Date'])
            a = a[(a['PO Item Creation Date'] >= input_min_date) & (a['PO Item Creation Date'] <= input_max_date)]
            
            total_spend = a['PO Item Value (GC)'].sum() / 1000000
            DMP.total_spend = str(round(total_spend, 2)) + 'M'

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
            fig = px.bar(e, x='Year', y='PO Item Value (GC)', color='Product Category Description', barmode='stack', text='PO Item Value (GC) Text', color_discrete_sequence=px.colors.qualitative.Set3,)
            fig.update_traces(marker_line_width=0)

            a_line = pd.DataFrame(c.groupby('Year')['PO Item Value (GC)'].sum())
            a_line.reset_index(inplace=True)
            a_line['PO Item Value (GC) Text'] = a_line['PO Item Value (GC)'].apply(lambda x: str(round(x/1000000, 2)) + 'M')

            fig2 = px.line(a_line, x='Year', y='PO Item Value (GC)', text='PO Item Value (GC) Text')
            fig2.update_traces(textposition='top center')
            fig.add_trace(fig2.data[0])

            fig = update_layout_fig_6(fig, DMP.plot_bg)
            fig.update(layout_coloraxis_showscale=False)

            div_6 = opy.plot(fig, auto_open=False, output_type='div')
            
            response = JsonResponse({            
                'plot_div_6': div_6,
                'total_spend': DMP.total_spend
                    })
            print("ajax_6_succcessfull")
                    
            add_get_params(response)
            return response

        else:
            response = JsonResponse({
            'this_not_post': "DMP.6",
            })
            
            add_get_params(response)
            return response