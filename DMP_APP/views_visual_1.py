from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import numpy as np
import json
import pandas as pd
from .views_search_1 import main_searching_algoritm
from .helpers import *
from datetime import date
import plotly.graph_objects as go
import plotly.express as px
from django.core.mail import send_mail
import plotly.offline as opy
from .helpers_2 import *
from DMP_API.settings import engine
from sqlalchemy.orm import  Session

import traceback
import logging
from .models import USER_SESSION_WITH_DATA
from .custom_logic import check_user_status, add_get_params
from fuzzywuzzy import fuzz
from DMP_API.settings import engine, BASE_DIR
plot_bg='rgba(255, 255,255, 0.8)'

class DMP:
    # plot_bg='rgba(255, 255,255, 0.8)'
    uploaded_historical_data = []
    global plot_bg
    @csrf_exempt
    def __init__(self):
        print("_init_")




    @csrf_exempt 
    def upload_file_historical(request): 
        # Build the POST parameters
        if request.method == 'POST':
            try:    
                
                #*cheking user status
                user_type = check_user_status(request)['user_type']  
                if user_type == 'customer':
                    user_id = request.POST.get('user_id')                
                    df = upload_file_helpers(request)
                    
                   
                    df.to_csv(str(BASE_DIR) + "/static/uploaded_historical_data_" + str(user_id) + ".csv", index = False)
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
            
            #*cheking user status
            user_response = check_user_status(request)
            user_type = user_response['user_type']
            user_id = user_response['user_id']

            if user_type != 'not_user':
                check_data=False
                try:    
             
                    #* check uploaded historical data
                     
                    df = pd.read_csv(str(BASE_DIR) + "/static/uploaded_historical_data_" + str(user_id) + ".csv")
                    
                    if str(type(df)).split() != "<class 'list'>".split():
                        print("Uploaded historical data df type: ", type(df))
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
                 #*cheking user status
                user_response = check_user_status(request)
                user_type = user_response['user_type']
                user_id = user_response['user_id']
                
                if user_type != 'not_user':
                    #* get all input data in inputs
                    input_region_name = request.POST.get('region')  
                    input_material_id = request.POST.get('material')  
                    input_description = request.POST.get('description')  
                    input_manufacturer_part_number = request.POST.get('manufactureId')
                    input_manufacturer_name = request.POST.get('manufacture')  
                    input_vendor_names = request.POST.getlist('vendor_names[]')
                    input_proposed_prices= request.POST.getlist('proposed_prices[]')
                    input_currencies = request.POST.getlist('currencies[]')     


                    #FIXME: correct dataframe for different user 
                    df = pd.read_csv(str(BASE_DIR) + "/static/uploaded_historical_data_" + str(user_id) + ".csv",)
                    
                    processed_df = preprocess_search_data(df, input_region_name)

                    df_org = processed_df.copy()
                    df_org.to_csv(str(BASE_DIR) + "/static/df_org_" + str(user_id) + ".csv", index = False)
                    
                    
                    all_dataframes_from_searching = main_searching_algoritm(input_material_id, input_description, input_manufacturer_part_number, input_manufacturer_name, processed_df)
                    
                    #FIXME: correct dataframe for different user 
                    all_dataframe = pd.DataFrame(all_dataframes_from_searching['all_dataframe'])
                    all_dataframe.to_csv(str(BASE_DIR) + "/static/all_dataframe_" + str(user_id) + ".csv", index = False)
                    
                    # df_org.to_csv("cheking_size_df_org.csv", index = False)
                   
                    result_data_all = pd.DataFrame(all_dataframes_from_searching['result_data_all'])
                    result_data_app = pd.DataFrame(all_dataframes_from_searching['result_app_to_app'])           
                    result_data_app_copy = result_data_app.copy()
                    result_content = all_dataframes_from_searching['result_content']
                    proposed_prices = DMP.convert_usd(result_content, input_proposed_prices, input_currencies)
                            
                    # get most similar vendor name
                    vendor_names_all_dataframe = processed_df['Vendor Name'].value_counts().index.tolist()
                    input_vendor_names_fuzzy=[]
                    for a in input_vendor_names:
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

                    input_vendor_names = input_vendor_names_fuzzy   # vendor names


                    if result_data_all.shape[0]>0:
                        app_unit_of_measure = ['ALL', 'EA', 'PH']
                        if result_data_app.shape[0]>0:
                            for i in result_data_app['PO Item Quantity Unit'].value_counts().index.tolist():
                                app_unit_of_measure.append(i)

                            df_item = result_data_app.drop_duplicates(['Material/Service No.'])
                            
                            categories_in_result = result_data_app['Product Category Description'].value_counts().index.tolist()
                            item_numbers_in_result = result_data_app['Material/Service No.'].value_counts().index.tolist()
                            short_desc_in_result = result_data_app['PO Item Description'].value_counts().index.tolist()                           
                            new_manufacturer_name = [df_item['Manufacturer Name'].value_counts().index.tolist()[0]]
                            
                            data_list=[]
                            data_list.append(item_numbers_in_result)
                            data_list.append(short_desc_in_result)


                        apple_to_apple_count = result_data_app.shape[0]  
                        result_count = result_data_all.shape[0]    
                       
                        #***************** for visual data and filters *****************
                    

                        user_input_desc = all_dataframes_from_searching['user_input_desc']
                      
                        all_headers=["PO No.","PO Item No.","Incoterms Name", "Material/Service No.","Vendor Name","PO Item Description","Manufacturer Name",
                        "Manufacturer Part No.","Long Description","PO Item Creation Date","PO Item Value (GC)","PO Item Value (GC) Unit", "PO Item Quantity Unit", "Unit Price","Converted Price", "score","path",
                        "desc","Select","desc_words_short", "desc_words_long"]


                        

                        with Session(engine) as session:

                            user_session_with_data = session.query(USER_SESSION_WITH_DATA).filter(USER_SESSION_WITH_DATA.user_id == user_id).first()
                            user_session_with_data.categories_in_result= categories_in_result
                            user_session_with_data.result_data_all = result_data_all.to_json(orient='records')
                            user_session_with_data.result_data_app = result_data_app.to_json(orient='records')
                            user_session_with_data.result_data_app_copy = result_data_app_copy.to_json(orient='records')
                            user_session_with_data.item_numbers_in_result = item_numbers_in_result
                            user_session_with_data.short_desc_in_result = short_desc_in_result
                            user_session_with_data.new_manufacturer_name = new_manufacturer_name
                            user_session_with_data.apple_to_apple_count = apple_to_apple_count
                            user_session_with_data.result_count = result_count
                            user_session_with_data.user_input_desc = user_input_desc
                            user_session_with_data.all_headers = all_headers
                            user_session_with_data.data_list = json.dumps(data_list)
                            session.commit()



                        json_records_all=result_data_all.to_json(orient='records')
                        result_data_all_json=json.loads(json_records_all)
                        
                        json_records_app = result_data_app.to_json(orient='records')
                        result_data_app_json=json.loads(json_records_app)

                        response = JsonResponse({
                                'vendor_names':input_vendor_names,
                                'proposed_prices':proposed_prices,
                                'app_unit_of_measure': app_unit_of_measure,
                                
                                'result_data_all':  result_data_all_json,
                                'result_app_to_app':  result_data_app_json,
                                'user_input_desc': all_dataframes_from_searching['user_input_desc'],
                                'all_headers': all_headers,
                                'display_converted_uom':all_dataframes_from_searching['display_converted_uom'],
                                'apple_to_apple_count': apple_to_apple_count,
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
        # Build the POST parameters
            with Session(engine) as session:
                input_token = request.POST.get('input_token')
                user_session_with_data = session.query(USER_SESSION_WITH_DATA).filter(USER_SESSION_WITH_DATA.user_token == input_token).first()
                categories_in_result = user_session_with_data.categories_in_result
                item_numbers_in_result = user_session_with_data.item_numbers_in_result
                short_desc_in_result =user_session_with_data.short_desc_in_result
                new_manufacturer_name = user_session_with_data.new_manufacturer_name
                apple_to_apple_count = user_session_with_data.apple_to_apple_count
                result_count = user_session_with_data.result_count
                data_list = json.loads(user_session_with_data.data_list) 
                
            user_type = check_user_status(request)['user_type']  
            if user_type != 'not_user':
            #! return finded rows data in table 

                response = JsonResponse({
                        
                        'material_items' : item_numbers_in_result,
                        'manufacture_names': new_manufacturer_name,      
                        'apple_to_apple_count' : apple_to_apple_count,
                        'result_count': result_count,
                        'categories': categories_in_result,
                        'descriptions': short_desc_in_result,
                        'data_list': data_list,

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
            response = JsonResponse({'Answer': "This function only for POST requests",})
                
            add_get_params(response)
            return response



    # Visualization
    def convert_usd(result_content,proposed_prices, currencies):
        proposed_prices_in_usd = []
        for index, i in enumerate(currencies):
            proposed_prices_in_usd.append(float(proposed_prices[index]) * (1/result_content['quotes']['USD'+i]))
        return proposed_prices_in_usd


    @csrf_exempt
    def visual_ajax_1_2_3(request):
        if request.method =='POST':
            try:
                 #*cheking user status
                user_response = check_user_status(request)
                user_type = user_response['user_type']
                user_id = user_response['user_id']
                
                if user_type == "customer":
                
                    global plot_bg
                    with Session(engine) as session:
                        
                        user_session_with_data = session.query(USER_SESSION_WITH_DATA).filter(USER_SESSION_WITH_DATA.user_id == user_id).first()
                        result_data_app_json = json.loads(user_session_with_data.result_data_app)
                        app_to_app = pd.json_normalize(result_data_app_json)
                               
                    input_app_unit_of_measure = request.POST.get('app_unit_of_measure')
                    input_vendor_names = request.POST.getlist('input_vendor_names[]')
                    input_incoterm_names = request.POST.getlist('input_incoterm_names[]')
                    proposed_prices = request.POST.getlist('proposed_prices[]')
                    
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
                    for index, i in enumerate(proposed_prices):
                        fig_1.add_trace(go.Scatter(x=[today], y=[i], mode='markers', name=input_vendor_names[index], marker_symbol='star-triangle-up', marker_size=15))
                    
                    fig_1 = update_layout_fig_1_3(fig_1, plot_bg)



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
                    
                    fig_2 = update_layout_fig_2(fig_2, max_val, plot_bg)


                    #! Plot 3
                    fig_3 = (px.scatter(app_to_app, x="PO Item Creation Date", y="Unit Price", color='Incoterms Name', title='').update_traces(mode='lines+markers'))
                    for index, i in enumerate(proposed_prices):
                        fig_3.add_trace(go.Scatter(x=[today], y=[i], mode='markers', name = input_incoterm_names[index] + ' (' + input_vendor_names[index] + ')', marker_symbol='star-triangle-up', marker_size=15))

                    fig_3 = update_layout_fig_1_3(fig_3, plot_bg)


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
            
                #* return user not access code - 501
                response = JsonResponse({'error_text':"You have not access"})
                response.status_code = 501
                add_get_params(response)
                return response        
        else:
            response = JsonResponse({'Answer': "This request method is not POST", })
            add_get_params(response)
            return response
        
    
    #!chart 4 stage 4 with ajax
    @csrf_exempt
    def visual_ajax_4(request):
        if request.method =='POST':
            try:
                # * cheking user status
                 #*cheking user status
                user_response = check_user_status(request)
                user_type = user_response['user_type']
                user_id = user_response['user_id']
                
                if user_type == "customer":
                    
                    global plot_bg
                    input_vendor_1= request.POST.get('vendor_name')
                    item_quantity = int(request.POST.get('input_quantity'))
                    time_left = request.POST.get('input_min_date')
                    time_right= request.POST.get('input_max_date')
                    input_app_unit_of_measure= request.POST.get('app_unit_of_measure')
                    input_vendor_names = request.POST.getlist('input_vendor_names[]')
                    input_incoterm_names = request.POST.getlist('input_incoterm_names[]')
                    proposed_prices = request.POST.getlist('proposed_prices[]')
                    for i in range(0, len(proposed_prices)):
                        proposed_prices[i] = float(proposed_prices[i])
                        

                    with Session(engine) as session:

                        user_session_with_data = session.query(USER_SESSION_WITH_DATA).filter(USER_SESSION_WITH_DATA.user_id == user_id).first()
                        result_data_app_json = json.loads(user_session_with_data.result_data_app)
                        result_data_app_df = pd.json_normalize(result_data_app_json)
                        result_data_app_df['PO Item Creation Date']= pd.DatetimeIndex(result_data_app_df['PO Item Creation Date'])
                        
                        
                    result = result_data_app_df.copy()
                    result = result[(result['PO Item Creation Date'] >= time_left) & (result['PO Item Creation Date'] <= time_right)]
                    
                    if input_app_unit_of_measure != 'ALL':
                        result = result[result['PO Item Quantity Unit'] == input_app_unit_of_measure]
                
                    vendor_names_2 = []
                    po_creation_date = []
                    po_incoterms = []
                    
                    flag = 1
                    vendor_names = input_vendor_names
                    
                    proposed_price = float(proposed_prices[vendor_names.index(input_vendor_1)])
                    if (len(vendor_names) == 1) or (proposed_price == min(proposed_prices)):
                        flag = 0

                    vendor_name = input_vendor_1
                    input_incoterm = input_incoterm_names[vendor_names.index(vendor_name)]

                    vendor_names_2.append(input_vendor_1)
                    po_incoterms.append(input_incoterm)
                    po_creation_date.append(date.today())
                    

                    ab = result.copy()
                    min_ven_name = vendor_name
                    min_ven_val = int(proposed_price)
                    min_incoterm = input_incoterm

                    if flag == 1:
                        for index, v_name in enumerate(vendor_names):
                            aa = proposed_prices[vendor_names.index(v_name)]
                            if aa < min_ven_val:
                                min_ven_val = aa
                                min_ven_name = v_name
                                min_incoterm = input_incoterm_names[index]
                        vendor_names_2.insert(0, min_ven_name)
                        po_creation_date.insert(0, date.today())
                        po_incoterms.insert(0, min_incoterm)

                    spend = []

                # Last
                    last_purchase_df = result[result['PO Item Creation Date'] == result['PO Item Creation Date'].max()].iloc[0]
                    last_price = last_purchase_df['Unit Price']
                    vendor_last = last_purchase_df['Vendor Name']
                    print("last_purchase_df['PO Item Creation Date']: ", last_purchase_df['PO Item Creation Date'])
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
                    
                    # OLD RECOMMENDATION
                    # -------------------------------------  Recommendation Start -------------------------------------

                    prospoed_price_rec = proposed_price
                    lowest_purchase_price_rec = min_price
                    last_purchase_price_rec = last_price
                    average_purchase_price_rec = avg_price

                    savings = round((last_purchase_price_rec - prospoed_price_rec)*item_quantity, 2)

                    print('\n\n\n')
                    print("lowest_purchase_price_rec: ", lowest_purchase_price_rec )
                    print("prospoed_price_rec: " , prospoed_price_rec)
                    print('\n\n\n')
                    
                    message_recomandation=""
                    if prospoed_price_rec < lowest_purchase_price_rec:
                        print('1111111111111111111111111111111111111111111111111111111111111111111111')
                        message_recomandation='Price is lower than the lowest purchase price, hence recommended to accept. Savings for the next purchase batch is $' + str(savings)

                    elif prospoed_price_rec < last_purchase_price_rec and prospoed_price_rec < average_purchase_price_rec:
                        print('22222222222222222222222222222222222222222222222222222222222222222222222')
                        message_recomandation='Price is lower than last and average purchase price, hence recommended to accept. Savings for the next purchase batch is $' + str(savings)
                        

                    elif prospoed_price_rec < last_purchase_price_rec and prospoed_price_rec > average_purchase_price_rec:
                        lower_percentage = round((last_purchase_price_rec - prospoed_price_rec) / last_purchase_price_rec , 2) * 100
                        higher_percentage = round((prospoed_price_rec - average_purchase_price_rec) / average_purchase_price_rec, 2) * 1000
                        if lower_percentage > higher_percentage:
                            print('33333333333333333333333333333333333333333333333333333333333333333333')
                            message_recomandation="Price is lower than last purchase " +  str(round(lower_percentage))  + "% and higher than average purchase price " +  str(round(higher_percentage))  + "%, hence recommended to accept. Savings for the next purchase batch is $" + str(savings)
                        
                    elif prospoed_price_rec > last_purchase_price_rec and prospoed_price_rec < average_purchase_price_rec:
                        higher_percentage = round((prospoed_price_rec - last_purchase_price_rec) / last_purchase_price_rec , 2) * 100
                        lower_percentage = round((average_purchase_price_rec - prospoed_price_rec) / average_purchase_price_rec, 2) * 100
                        if lower_percentage > higher_percentage:
                            print('4444444444444444444444444444444444444444444444444444444444444444444444444444444444444444')
                            message_recomandation='Price is lower than average purchase ' +  str(round(higher_percentage))   + ' and higher than last purchase price ' +  str(round(lower_percentage))  + '%, hence recommended to accept. Savings for the next purchase batch is $' +  + str(savings)
                    else:
                        message_recomandation = ""
                        
                        print()
                    proposed_price_rec = proposed_price
                    lowest_purchase_price_rec = min_price
                    last_purchase_price_rec = last_price
                    average_purchase_price_rec = avg_price
                    flag_1 = 0
                    message_negotiation=""
                    if proposed_price_rec > last_purchase_price_rec and proposed_price_rec > average_purchase_price_rec:
                        x = round(((proposed_price_rec - last_purchase_price_rec) / last_purchase_price_rec)*100, 2)
                        y = round(((proposed_price_rec - average_purchase_price_rec) / average_purchase_price_rec)*100, 2)
                        message_negotiation = '<p> Dear Supplier <b>' +input_vendor_1+ '</b>, your <i>proposed</i> price is higher than <i>last</i> and <i>average</i> purchase price respectively <b>' + str(round(x)) + '%</b> and <b>'+ str(round(y)) +'%</b>, hence company requests you to provide a discount</p>' 
                        flag_1=1
                    
                    elif proposed_price_rec < last_purchase_price_rec and proposed_price_rec > average_purchase_price_rec:
                        
                        lower_percentage = ((last_purchase_price_rec - proposed_price_rec) / last_purchase_price_rec) * 100
                        higher_percentage = ((proposed_price_rec - average_purchase_price_rec) / average_purchase_price_rec) * 100
                        if higher_percentage > lower_percentage:
                            x = round(higher_percentage)
                            message_negotiation = "<p> Dear Supplier <b>"+input_vendor_1+ "</b>, your <i>proposed</i> price is higher than <i>average</i> purchase price <b>" + str(x) + "%</b> , hence company requests you to provide a discount<p/>"
                            flag_1=1
                            message_recomandation = "Negotiation Message: Dear Supplier "+input_vendor_1+ ", your proposed price is higher than averag purchase price " + str(x) + "%, hence company requests you to provide a discount"
                    
                    elif prospoed_price_rec > last_purchase_price_rec and prospoed_price_rec < average_purchase_price_rec:
                        higher_percentage = ((prospoed_price_rec - last_purchase_price_rec) / last_purchase_price_rec ) * 100
                        lower_percentage = ((average_purchase_price_rec - prospoed_price_rec) / average_purchase_price_rec) * 100
                        if higher_percentage > lower_percentage:
                            x = round(higher_percentage)
                            message_negotiation = '<p> Dear Supplier <b>'+input_vendor_1+ '</b>, your <i>proposed</i> price is higher than <i>last</i> purchase <b>' + str(x) + '</b>, hence company requests you to provide a discount</p>' 
                            flag_1=1

                    if flag_1==1:

                        html_message = message_negotiation #'<p>Dear supplier <b>' + input_vendor_1 + '</b>,  our analysis shows that there is significant increase in some materials, therefore we would request you to provide discount according to the % shown in the table. Thank you for your cooperation.</p><h4> <a href="http://localhost:1000/discount_materials.html" target="_blank">Link for materials that has risen in price</a></h4>'            
                    
                    
                        try:
                            full_name = 'DMP BESTRACK'
                            email = 'dmp.bestrack@gmail.com'
                            message = html_message
                            time='time'

                            #send_mail
                            send_mail(
                        "From: "+ full_name, #subject
                        "User Email: "+email+"\n Request for discount: "+html_message,    #message
                        email, #from email
                        ["hebibliferid20@gmail.com", "cavidan5889@gmail.com"],     html_message=html_message)
                
                        except Exception as e:
                            print("mail sending error: ", e)
                
                    if flag == 1:
                        y_ = ['$' + str(int(avg_price)) + ' ', ' $' + str(int(min_price)) + ' ', '  $' + str(int(last_price)) + ' ',  '   $' + str(int(min_ven_val)) + ' ',         '    $' + str(int(proposed_price)) + ' ']
                        y_2 = ['Average', 'Lowest', 'Last', 'Proposed Lowest', 'Proposed']
                        aa = ['Average ', 'Lowest', 'Last', 'Proposed Lowest', 'Proposed  (' + vendor_name + ')']

                    else:
                        y_ = ['$' + str(int(avg_price)) + ' ', ' $' + str(int(min_price)) + ' ', '  $' + str(int(last_price)) + ' ', '   $' + str(int(proposed_price)) + ' ']
                        y_2 = ['Average', 'Lowest', 'Last', 'Proposed']
                        aa = ['Average ', 'Lowest', 'Last', 'Proposed  (' + vendor_name + ')']



                    # -------------------------------------  Recommendation e -------------------------------------
                    
                    # # -------------------------------------  Recommendation Start -------------------------------------
                    # new_flag = 0
                    # if len(vendor_names) > 1:
                    #     new_flag =  1
                    # try:
                    #     message_recomandation ="Your recommendation succesfully send."
                    #     message_recomandation = recommendation_alg(proposed_price,proposed_prices, min_price, last_price, avg_price, item_quantity, vendor_name,  min_ven_name, min_ven_val, new_flag)
                    # except Exception as e:
                    #     my_traceback = traceback.format_exc()
                    #     logging.error(my_traceback)
                        
                    #     print("redommendation excemption: ",my_traceback)
                    # # -------------------------------------  Recommendation End -------------------------------------


                    # # # -------------------------------------  Negotiation Start ------------------------------------- 
                    # negotiation_alg(proposed_price, min_price, last_price, avg_price, input_vendor_1)
                    # # -------------------------------------  Negotiation End ------------------------------------- 


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

                    fig = update_layout_fig_4(fig, spend, delta, y_, y_2, colors, plot_bg)

                    div_4 = opy.plot(fig, auto_open=False, output_type='div') 
                    print("message_recomandation:   ",message_recomandation)    
                    response = JsonResponse({
                        'plot_div_4': div_4,
                        'message': message_recomandation
                    })               
                        
                    add_get_params(response)
                    print("ajax_4_succcessfull")
                    
                    return response
            except Exception as e:
                my_traceback = traceback.format_exc()
                logging.error(my_traceback)
                print(my_traceback)
                response = JsonResponse({'error_text':str(e),
                                         'error_text_2':my_traceback
                                         })
                response.status_code = 505
                
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
    def visual_ajax_5_7(request):
        if request.method =='POST':
            #*cheking user status
            user_response = check_user_status(request)
            user_type = user_response['user_type']
            user_id = user_response['user_id']
            
            if user_type == "customer":
                global plot_bg
                input_plot_type = request.POST.get('input_plot_type')
                input_vendor_1= request.POST.get('vendor_name')
                time_left= request.POST.get('input_min_date')
                time_right= request.POST.get('input_max_date')
                df = pd.read_csv(str(BASE_DIR) + "/static/all_dataframe_" + str(user_id) + ".csv",)
                
                #! stage 5  
                vendor_name=input_vendor_1
                
             
                #get data from session  
                with Session(engine) as session:

                    # get user object with user token
                    user_session_with_data = session.query(USER_SESSION_WITH_DATA).filter(USER_SESSION_WITH_DATA.user_id == user_id).first()
                    
                    # get the data that belong to user. 
                    categories_in_result = user_session_with_data.categories_in_result


                category_name = categories_in_result[0]
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
                
                    fig = update_layout_fig_5_7(fig, plot_bg)

                    div_5 = opy.plot(fig, auto_open=False, output_type='div')

                    #! return finded rows data in table 
                    response = JsonResponse({            
                        'plot_div': div_5,
                            })
                            
                    add_get_params(response)
                    print("ajax_5_7_succcessfull")

                    return response
                
                else:
                    response = JsonResponse({            
                        'plot_div': "div_5",
                    })
                                
                    add_get_params(response)
                
                    print("ajax_5_7_not_succcessfull")
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
        
                
    # ! visual_ajax_6 category names:
    @csrf_exempt    
    def visual_ajax_6(request):
        if request.method =='POST':

            #*cheking user status
            user_response = check_user_status(request)
            user_type = user_response['user_type']
            user_id = user_response['user_id']
            
            if user_type == "customer":

                global plot_bg
                vendor_name = request.POST.get('vendor_name')
                input_min_date = request.POST.get('input_min_date')
                input_max_date = request.POST.get('input_max_date')
                
                # function download dataframes
                
                df = pd.read_csv(str(BASE_DIR) + "/static/df_org_" + str(user_id) + ".csv")
                
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
                total_spend = str(round(total_spend, 2)) + 'M'

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

                fig = update_layout_fig_6(fig, plot_bg)
                fig.update(layout_coloraxis_showscale=False)

                div_6 = opy.plot(fig, auto_open=False, output_type='div')
                
                response = JsonResponse({            
                    'plot_div_6': div_6,
                    'total_spend': total_spend
                        })
                print("ajax_6_succcessfull")
                        
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
        