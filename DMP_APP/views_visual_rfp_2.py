# Non-Pricebook Data Visualization
from .views_visual_rfp import *
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from numpy.lib.shape_base import dsplit
import json
import plotly.express as px
from datetime import date
import datetime
import pandas as pd
import plotly.express as px
from fuzzywuzzy import fuzz
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cluster import DBSCAN
from multiprocessing import Pool
import plotly.graph_objects as go
from .helpers import get_last_3_years_data
CRED = '\033[91m'
CEND = '\033[0m'


import warnings
warnings.filterwarnings('ignore')

plot_bg = 'rgba(171, 248, 190, 0.8)'
class DMP_RFP_2(DMP_RFP):
    


    @csrf_exempt
    def non_pricebook_search(request): 
                # Build the POST parameters
        if request.method == 'POST':
            try:    
                
                #*cheking user status
                user_response = check_user_status(request)
                user_type = user_response['user_type']
                user_id = user_response['user_id']
                
                if user_type == 'customer':
                    input_transaction =  request.POST.get('data')
                    
                    new_df = pd.read_csv(str(BASE_DIR) + "/static/non_pricebook_df_" + str(user_id) + ".csv",error_bad_lines=False, parse_dates=['PO Item Creation Date'])
                    new_df.reset_index(drop=True, inplace=True)
                    non_pricebook_items_count = len(new_df['Material/Service No.'].unique().tolist())        
                    new_df = get_last_3_years_data(new_df)
                    new_df.to_csv(str(BASE_DIR) + "/static/new_df_a2a.csv")

                    #!  ----------------------------------------- Normalization  Start -----------------------------------------
                    # Select transactions that occur after year 2018
                    
                    material_id_list = new_df['Material/Service No.'].value_counts().index.tolist()
                    
                    identifier = [2 for i in range(len(material_id_list))]
                    with Pool() as pool:
                        a2a_conv = pd.concat(pool.starmap(parallel_uom, zip(material_id_list, identifier)))

                    a2a_conv.to_csv(str(BASE_DIR) + '/static/new_df_a2a_conv_new_'+ str(user_id)+'.csv', index = False)
                    
                    new_df  = pd.read_csv(str(BASE_DIR) + '/static/new_df_a2a_conv_new_'+ str(user_id)+'.csv')


                    #!  ----------------------------------------- Normalization  End -----------------------------------------

                # BURAYA GELMELIDI
                    if str(input_transaction) == "2":
                        new_df = new_df.groupby(['Material/Service No.']).filter(lambda x: len(x) > 1)
                    # Transaction Count
                    # 1
                    # 2


                    print('\n\n\n')
                    print(new_df.info())

                    print('\n\n\n')
                    new_df['PO Item Creation Date'] = pd.DatetimeIndex(new_df['PO Item Creation Date'])
                    new_df.to_csv(str(BASE_DIR) + '/static/new_df_np_' + str(user_id) + '.csv', index = False)
                    
                    df_1 = new_df.groupby(['Material/Service No.']).filter(lambda x: len(x) > 1) 
                    weight_df = pd.DataFrame(df_1.groupby('Material/Service No.')['PO Item Value (GC)'].sum())
                    weight_df.rename(columns={'PO Item Value (GC)':'Item Total Spend'}, inplace=True)
                    weight_df.reset_index(inplace=True)

                    df_1 = pd.merge(df_1, weight_df,  how='left', on='Material/Service No.')
                    df_1['Item Weight'] = df_1['Item Total Spend'] / (df_1['PO Item Value (GC)'].sum())

                    last_purchases_df = df_1.loc[df_1.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]
                    last_purchases_df['Last Price'] = last_purchases_df['Unit Price'].copy()

                    df_1 = df_1[~df_1.index.isin(last_purchases_df.index.tolist())]
                    df_1 = pd.merge(df_1, last_purchases_df[['Material/Service No.', 'Last Price']], how='left', on='Material/Service No.') 


                    df_1['delta'] = 0.0
                    df_1['percentage'] = 0.0
                    df_1['Last Price'] = round(df_1['Last Price'], 2)
                    df_1['Unit Price'] = round(df_1['Unit Price'], 2)
                    df_1.loc[df_1.groupby('Material/Service No.')['PO Item Creation Date'].idxmax(), 'delta'] = df_1.loc[df_1.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['Last Price'] - df_1.loc[df_1.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['Unit Price']
                    df_1.loc[df_1.groupby('Material/Service No.')['PO Item Creation Date'].idxmax(), 'percentage'] = (df_1.loc[df_1.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['delta'] / df_1.loc[df_1.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['Unit Price']) * 100


                    app_rfp_df = last_purchases_df[['Material/Service No.', 'Last Price']].copy()
                    new_a2a = pd.merge(new_df, app_rfp_df[['Material/Service No.', 'Last Price']], how='left', on='Material/Service No.', )

                    


                    df_1.to_csv(str(BASE_DIR) + '/static/df_1_np_' + str(user_id) + '.csv', index = False)
                    last_purchases_df.to_csv(str(BASE_DIR) + '/static/last_purchases_df_np_' + str(user_id) + '.csv', index = False)
                    app_rfp_df.to_csv(str(BASE_DIR) + '/static/app_rfp_df_np_' + str(user_id) + '.csv', index = False)
                    new_df.to_csv(str(BASE_DIR) + '/static/df_np_' + str(user_id) + '.csv', index = False)


                    with Session(engine) as session:
                        user_session_with_data = session.query(USER_SESSION_WITH_DATA).filter(USER_SESSION_WITH_DATA.user_id == user_id).first()
                        user_session_with_data.non_pricebook_items_count = non_pricebook_items_count
                        session.commit()

                    #! return finded rows data in table 
                    response = JsonResponse({            
                        'non_pricebook_items_count': non_pricebook_items_count,
                        # 'total_item_count': total_item_count,
                        })
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
    def visual_ajax_1_rfp(request):
        # Build the POST parameters
        if request.method == 'POST':
            try:    
                 #*cheking user status
                user_response = check_user_status(request)
                user_type = user_response['user_type']
                user_id = user_response['user_id']
                
                if user_type == 'customer':
                    global plot_bg
                    input_min_date= request.POST.get('input_min_date')
                    input_max_date= request.POST.get('input_max_date')
                    print('INPUT MIN DATE: ', input_min_date)
                    print('INPUT MAX DATE: ', input_max_date)
                    
                    app_rfp_df = pd.read_csv(str(BASE_DIR) + "/static/app_rfp_df_np_" + str(user_id) + ".csv",error_bad_lines=False)                    
                    app_rfp_df['Material/Service No.'] = app_rfp_df['Material/Service No.'].astype('str')
                    
                   
                    # app_rfp_df[(app_rfp_df['PO Item Creation Date'] >= input_max_date) & (app_rfp_df['PO Item Creation Date'] <= input_max_date)]

                    last_purchases_df = pd.read_csv(str(BASE_DIR) + "/static/last_purchases_df_np_" + str(user_id) + ".csv", error_bad_lines=False, parse_dates=['PO Item Creation Date'])                    
                    last_purchases_df['Material/Service No.'] = last_purchases_df['Material/Service No.'].astype('str')
                    
                    print('\n\n')
                    
                    last_purchases_df['PO Item Creation Date'] = pd.DatetimeIndex(last_purchases_df['PO Item Creation Date'])
                    print('last_purchases_df before: ', last_purchases_df.shape)
                    last_purchases_df = last_purchases_df[(last_purchases_df['PO Item Creation Date'] >= input_min_date) & (last_purchases_df['PO Item Creation Date'] <= input_max_date)]
                    print('last_purchases_df after: ', last_purchases_df.shape)
                    new_df = pd.read_csv(str(BASE_DIR) + "/static/new_df_np_" + str(user_id) + ".csv",error_bad_lines=False, parse_dates=['PO Item Creation Date'])                    
                    new_df['Material/Service No.'] = new_df['Material/Service No.'].astype('str')


                    new_df['PO Item Creation Date'] = pd.DatetimeIndex(new_df['PO Item Creation Date'])
                    print('\n\nnew_df before: ', new_df.shape)
                    new_df = new_df[(new_df['PO Item Creation Date'] >= input_min_date) & (new_df['PO Item Creation Date'] <= input_max_date)]
                    print('new_df after: ', new_df.shape)
                    a=1
                    if a==1:  
                        weight_df = pd.DataFrame(new_df.groupby('Material/Service No.')['PO Item Value (GC)'].sum())
                        weight_df.rename(columns={'PO Item Value (GC)':'Item Total Spend'}, inplace=True)
                        weight_df.reset_index(inplace=True)
                        new_df = pd.merge(new_df, weight_df,  how='left', on='Material/Service No.')
                        new_df['Item Weight'] = new_df['Item Total Spend'] / (new_df['PO Item Value (GC)'].sum())

                        app_to_app_rfp = pd.read_csv(str(BASE_DIR) + "/static/new_df_np_" + str(user_id) + ".csv",error_bad_lines=False, parse_dates=['PO Item Creation Date'])  
                        app_to_app_rfp['Material/Service No.'] = app_to_app_rfp['Material/Service No.'].astype('str')
                        
                        app_to_app_rfp['PO Item Creation Date'] = pd.DatetimeIndex(app_to_app_rfp['PO Item Creation Date'])
                        print('app_to_app_rfp before: ', app_to_app_rfp.shape)
                        app_to_app_rfp = app_to_app_rfp[(app_to_app_rfp['PO Item Creation Date'] >= input_min_date) & (app_to_app_rfp['PO Item Creation Date'] <= input_max_date)]
                        print('app_to_app_rfp after: ', app_to_app_rfp.shape)
                        app_rfp_df = app_to_app_rfp.loc[app_to_app_rfp.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]
                        app_rfp_df['Last Price'] = app_rfp_df['Unit Price']
                        app_rfp_df.shape

                        last_prices_df = app_to_app_rfp.loc[app_to_app_rfp.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]
                        last_prices_df['Last Price'] = last_prices_df['Unit Price']
                        last_prices_df.shape

                        app_to_app_rfp = app_to_app_rfp[~app_to_app_rfp.index.isin(last_prices_df.index.tolist())]
                        app_to_app_rfp.shape

                        new_a2a = pd.merge(app_to_app_rfp, app_rfp_df[['Material/Service No.', 'Last Price']], how='left', on='Material/Service No.')
                        new_a2a['delta'] = 0.0
                        new_a2a['percentage'] = 0.0
                        new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax(), 'delta'] = new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['Last Price'] - new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['Unit Price']
                        new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax(), 'percentage'] = (new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['delta'] / new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['Unit Price']) * 100
                        app_rfp_df['Last Price'] = app_rfp_df['Unit Price']
                        
                        new_a2a['PO Item Creation Date'] = pd.DatetimeIndex(new_a2a['PO Item Creation Date'])
                        print('new_a2a before: ', new_a2a.shape)
                        new_a2a = new_a2a[(new_a2a['PO Item Creation Date'] >= input_min_date) & (new_a2a['PO Item Creation Date'] <= input_max_date)]
                        print('new_a2a after: ', new_a2a.shape)
                        print('SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS: ', new_a2a.shape)

                        temp = new_df.copy()


                        df_agg = temp.groupby(['Material/Service No.']).agg({'PO Item Value (GC)':sum})

                        res = df_agg.apply(lambda x: x.sort_values(ascending=False))
                        idx = res.index.tolist()
                        list_of_idx = []
                        i=0
                        for index in idx:
                            if temp[temp['Material/Service No.'] == index].shape[0] > 1:
                                list_of_idx.append(index)
                                if i == 9:
                                    break
                                i +=1
                        #!bug  


                        result = new_df[new_df['Material/Service No.'].isin(list_of_idx)]

                        result_2 = new_a2a[new_a2a['Material/Service No.'].isin(list_of_idx)]


                        last_purchased = result_2.loc[result_2.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]

                        mask_3 = last_purchased['Material/Service No.'].isin(list_of_idx)
                        result_3 = last_purchased[mask_3]

                        result = pd.merge(result, app_rfp_df[['Material/Service No.', 'Last Price']], how='left', on='Material/Service No.')


                        for index, row in last_purchased.iterrows():
                            result.loc[result['Material/Service No.'] == row['Material/Service No.'], 'Material # + abs percentage'] = row['Material/Service No.'] + '  (' + str(round(row['percentage'],1),) + '%)'
                            result.loc[result['Material/Service No.'] == row['Material/Service No.'], 'percentage'] = row['percentage']
                            result_3.loc[result_3['Material/Service No.'] == row['Material/Service No.'], 'Material # + abs percentage'] = row['Material/Service No.'] + '  (' + str(round(row['percentage'],1),) + '%)'
                            
                            
                        top_10_total_spend = result['PO Item Value (GC)'].sum()
                        total_spend = new_df['PO Item Value (GC)'].sum()
                        top_10_spend_weight = (top_10_total_spend/total_spend)*100
                        top_10_spend_weight = round(top_10_spend_weight,1)

                        size = len(list_of_idx)
                        if size > 0:
                            list_of_idxs =  list_of_idx[0] ##############################


                        fig = go.Figure()
                        groups = result.groupby("Material # + abs percentage")
                        i = 0
                        for name, group in groups:
                            list_of_dates = []
                            list_of_usd_prices = []
                            list_of_text = []
                            hover_data = []
                            group.sort_values(by='PO Item Creation Date', inplace=True)
                            for index, row in group.iterrows():
                                    list_of_usd_prices.append(row['Unit Price'])
                                    list_of_dates.append(row['PO Item Creation Date']) 
                                    list_of_text.append(' ')
                                    hover_data.append('Weight: ' + str(round(row['Item Weight'], 4)))
                            delta =  round(row['percentage'], 1)

                            list_of_text[-1] = str(delta) + '%'

                            if row['Material/Service No.'] in list_of_idxs:
                                fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='lines+markers+text', hovertext=hover_data,
                                        textposition='top center', name=name, marker_size=5, legendgroup=name,
                                                        line=dict(color=px.colors.qualitative.Bold[i]),))
                                fig.update_traces()
                            else:
                                fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='lines+markers+text', hovertext=hover_data,
                                textposition='top center', name=name, marker_size=5, legendgroup=name, visible='legendonly',
                                                        line=dict(color=px.colors.qualitative.Bold[i]),))
                            i += 1
                            
                        groups = result.groupby("Material # + abs percentage")
                        i=0
                        for name, group in groups:
                            
                            # group = group[group['PO Item Creation Date'] != '2021-08-06']
                            try:
                                group.reset_index(inplace=True)
                            except: 
                                pass
                            max_date = group.loc[group['PO Item Creation Date'].idxmax()]['PO Item Creation Date']
                            material_id = group.loc[group['PO Item Creation Date'].idxmax()]['Material/Service No.']
                            p = group.loc[group['PO Item Creation Date'].idxmax()]['percentage']
                        #     y1 = group.loc[group['PO Item Creation Date'].idxmax()]['PO Item Creation Date']
                            y1 = group['PO Item Creation Date'].drop_duplicates(inplace=False).nlargest(2).iloc[-1]

                            try:
                                y1 = pd.Timestamp(y1)
                            except:
                                continue
                            ts1 = y1
                        #     ts2 = (pd.Timestamp('2021-08-06 00:00:00'))
                            ts2 = pd.Timestamp(last_prices_df[last_prices_df['Material/Service No.'] == material_id]['PO Item Creation Date'].iloc[0])
                            
                            x1 = group.loc[group['PO Item Creation Date'].idxmax()]['Unit Price']
                            temp = group.loc[group['PO Item Creation Date'] == max_date]
                            if temp.shape[0] > 1:
                                x1 = group.loc[group['PO Item Creation Date'] == max_date]['Unit Price'].tolist()[-1]
                            x2 = group.loc[group['PO Item Creation Date'].idxmax()]['Last Price']
                            x = (x1 + x2)/2
                            result.loc[result['Material/Service No.'] == material_id, 'mid_x'] = ts1+(ts2-ts1)/2
                            result.loc[result['Material/Service No.'] == material_id, 'mid_y'] = (x1 + x2)/2




                        groups = result.groupby("Material # + abs percentage") ##.apply(lambda x: x.sort_values('abs_percentage', ascending=False))
                        i = 0
                        for name, group in groups:
                            list_of_dates = []
                            list_of_usd_prices = []
                            list_of_text = []
                            hover_data = []
                            group.sort_values(by='PO Item Creation Date', inplace=True)
                            for index, row in group.iterrows():
                                    list_of_usd_prices.append(row['mid_y'])
                                    list_of_dates.append(row['mid_x']) 
                                    list_of_text.append(' ')
                                    hover_data.append('Weight: ' + str(round(row['Item Weight'], 4)))
                            delta =  round(row['percentage'], 1)

                            list_of_text[-1] = str(delta) + '%'
                            if row['Material/Service No.'] in list_of_idxs:
                                fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='text', hovertext=hover_data,
                                        textposition='top center', text=list_of_text, name=name, marker_size=5, legendgroup=name,
                                                        line=dict(color=px.colors.qualitative.Bold[i]),))
                                fig.update_traces()
                            else:
                                fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='text', hovertext=hover_data,
                                textposition='top center', text=list_of_text, name=name, marker_size=5, legendgroup=name, visible='legendonly',
                                                        line=dict(color=px.colors.qualitative.Bold[i]),))

                            names = set()
                            fig.for_each_trace(
                                lambda trace:
                                    trace.update(showlegend=False)
                                    if (trace.name in names) else names.add(trace.name))

                        # fig.show()    
            
                        fig.update_layout(
                                yaxis_title="Price, $",
                            
                                xaxis_title="",
                            )

                        fig.update_layout(
                                yaxis_title="Price, $",
                                xaxis_title="",)
                        fig.update_layout(legend=dict(yanchor="top",y=1,xanchor="left",x=0.00,))
                        fig.update_layout(
                                yaxis_title="Price, $",
                                xaxis_title="",
                                height=450,
                                width=690,plot_bgcolor='rgba(255,255, 255, 0.5)',
                            )
                        fig.update_xaxes(visible=True, showticklabels=True)
                        fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
                        # fig.update_yaxes(showline=True, linewidth=1, linecolor='black')
                        fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')
                        fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')
            
                        div_1 = opy.plot(fig, auto_open=False, output_type='div')


                        #! return finded rows data in table 
                        response = JsonResponse({            
                            'plot_div_1_rfp':div_1,
                            'rfp_percentage':top_10_spend_weight,

                                })
                                
                        add_get_params(response)
                        return response
                    
                    else:
                        fig = go.Figure(go.Bar(
                            x=[20],
                            y=[' '],
                            marker_color=[plot_bg],
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
                        fig.update_layout(    plot_bgcolor = plot_bg )

                        fig.update_layout(xaxis_range=[0,20],  plot_bgcolor = plot_bg,)
                        fig.update_layout(
                                height=450,
                                width=690,
                                plot_bgcolor = plot_bg,)         
                        fig.update_xaxes(visible=False, showticklabels=False)
                        fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
                        # fig.update_yaxes(showline=True, linewidth=1, linecolor='black')
            
                        div_1 = opy.plot(fig, auto_open=False, output_type='div')

                    
                        #! return finded rows data in table 
                        response = JsonResponse({            
                            'plot_div_1_rfp': div_1,
                            'rfp_percentage': "0",

                                })
                                
                        add_get_params(response)
                        print("ajax_1_rfp_not_data_in_this_filter")

            
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
    def visual_ajax_2_rfp(request):

        # Build the POST parameters
        if request.method == 'POST':
            try:    
                 #*cheking user status
                user_response = check_user_status(request)
                user_type = user_response['user_type']
                user_id = user_response['user_id']
                
                if user_type == 'customer':
                    global plot_bg
                    input_min_date= request.POST.get('input_min_date')
                    input_max_date= request.POST.get('input_max_date')
                    # Plot  2
                    
                    df_1 = pd.read_csv(str(BASE_DIR) + "/static/df_1_np_" + str(user_id) + ".csv",error_bad_lines=False, parse_dates=['PO Item Creation Date'])                    
                    df_1['Material/Service No.'] = df_1['Material/Service No.'].astype('str')
                    
                    df_1['PO Item Creation Date'] = pd.DatetimeIndex(df_1['PO Item Creation Date'])
                    df_1 = df_1[(df_1['PO Item Creation Date'] >= input_min_date) & (df_1['PO Item Creation Date'] <= input_max_date)]

                    last_purchases_df = pd.read_csv(str(BASE_DIR) + "/static/last_purchases_df_np_" + str(user_id) + ".csv",error_bad_lines=False)                    
                    last_purchases_df['Material/Service No.'] = last_purchases_df['Material/Service No.'].astype('str')
                    
                    last_purchases_df['PO Item Creation Date'] = pd.DatetimeIndex(last_purchases_df['PO Item Creation Date'])
                    last_purchases_df = last_purchases_df[(last_purchases_df['PO Item Creation Date'] >= input_min_date) & (last_purchases_df['PO Item Creation Date'] <= input_max_date)]
                    
                    new_df = pd.read_csv(str(BASE_DIR) + "/static/new_df_np_" + str(user_id) + ".csv",error_bad_lines=False, parse_dates=['PO Item Creation Date'])                    
                    new_df['Material/Service No.'] = new_df['Material/Service No.'].astype('str')

                    new_df['PO Item Creation Date'] = pd.DatetimeIndex(new_df['PO Item Creation Date'])
                    new_df = new_df[(new_df['PO Item Creation Date'] >= input_min_date) & (new_df['PO Item Creation Date'] <= input_max_date)]
                        
                    print('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz 2: ', df_1.shape)
                    drop_df = df_1[df_1['delta'] < 0]
                    if drop_df.shape[0] > 0:
                        print('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz 3: ', drop_df.shape)
                        print('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  IF: ', drop_df.shape)
                        drop_df_idxs = drop_df['Material/Service No.'].tolist()


                        mask = df_1['Material/Service No.'].isin(drop_df_idxs)
                        a_1 = df_1[mask]

                        mask = last_purchases_df['Material/Service No.'].isin(drop_df_idxs)
                        a_2 = last_purchases_df[mask]

                        all_drop_df = a_1.append(a_2)
                        all_drop_df['PO Item Creation Date'] = pd.DatetimeIndex(all_drop_df['PO Item Creation Date'])
                        all_drop_df['Material # + percentage'] = 'NO'

                        try:
                            del drop_df['level_0']
                        except: 
                            pass

                        for index, row in drop_df.iterrows():
                            all_drop_df.loc[all_drop_df['Material/Service No.'] == row['Material/Service No.'], 'Material # + percentage'] = row['Material/Service No.'] + '  (' + str(round(row['percentage'],1),) + '%)'
                            all_drop_df.loc[all_drop_df['Material/Service No.'] == row['Material/Service No.'], 'percentage'] = row['percentage']
                            
                            all_drop_df.loc[all_drop_df['Material/Service No.'] == row['Material/Service No.'], 'Item WEight'] = row['Item Weight']
                            
                            
                        fig = go.Figure()

                        drop_10_total_spend = all_drop_df['PO Item Value (GC)'].sum()
                        total_spend = new_df['PO Item Value (GC)'].sum()
                        drop_10_total_spend_weight =round((drop_10_total_spend/total_spend)*100,1)

                        sorted_list = np.unique(abs(all_drop_df['percentage']).tolist())
                        sorted_list = np.round(sorted_list,2)
                        sorted_list[::-1].sort()


                        groups = all_drop_df.groupby("Material # + percentage")
                        i=0
                        for name, group in groups:
                            list_of_dates = []
                            list_of_usd_prices = []
                            list_of_text = []
                            text_data = []
                            group.sort_values(by='PO Item Creation Date', inplace=True)
                            group.reset_index(inplace=True)
                            for index, row in group.iterrows():
                                    index = list(sorted_list).index(abs(round(row['percentage'],2 )), )
                                    new_price = row['Unit Price']
                                    list_of_usd_prices.append(new_price)
                                    list_of_dates.append(row['PO Item Creation Date']) 
                                    list_of_text.append(' ')
                                    text_data.append('Weight: ' + str(round(row['Item Weight'],4)))
                            list_of_text[-1] =  str(round(row['percentage'], 1),) + '%'    

                            if index == 0:
                                fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='lines+markers+text', textposition='top center',
                                                hovertext=text_data , name=name, marker_size=7,  legendrank=index, 
                                                        legendgroup=name, line=dict(color=px.colors.qualitative.Dark24[i%24])))

                            else:
                                fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='lines+markers+text', textposition='top center',
                                                hovertext=text_data, name=name, marker_size=7, legendrank=index, visible='legendonly',
                                                        legendgroup=name,  line=dict(color=px.colors.qualitative.Dark24[i%24])))

                            i += 1
                        
                        a_1['Material # + percentage'] = ''
                        for index, row in drop_df.iterrows():
                            a_1.loc[a_1['Material/Service No.'] == row['Material/Service No.'], 'Material # + percentage'] = row['Material/Service No.'] + '  (' + str(round(row['percentage'],1),) + '%)'
                            a_1.loc[a_1['Material/Service No.'] == row['Material/Service No.'], 'percentage'] = row['percentage']

                            a_1.loc[a_1['Material/Service No.'] == row['Material/Service No.'], 'Item WEight'] = row['Item Weight']

                        print('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz: ', drop_df.shape)
                        groups = a_1.groupby("Material # + percentage")
                        i=0
                        for name, group in groups:
                            group = group[group['PO Item Creation Date'] != '2021-08-06']
                            try:
                                group.reset_index(inplace=True)
                            except:
                                pass
                            max_date = group.loc[group['PO Item Creation Date'].idxmax()]['PO Item Creation Date']
                            material_id = group.loc[group['PO Item Creation Date'].idxmax()]['Material/Service No.']
                            p = group.loc[group['PO Item Creation Date'].idxmax()]['percentage']
                            y1 = group.loc[group['PO Item Creation Date'].idxmax()]['PO Item Creation Date']
                            y1 = pd.Timestamp(y1)
                            ts1 = y1
                            ts2 = pd.Timestamp(last_purchases_df[last_purchases_df['Material/Service No.'] == material_id]['PO Item Creation Date'].iloc[0])
                            x1 = group.loc[group['PO Item Creation Date'].idxmax()]['Unit Price']
                            temp = group.loc[group['PO Item Creation Date'] == max_date]
                            if temp.shape[0] > 1:
                                x1 = group.loc[group['PO Item Creation Date'] == max_date]['Unit Price'].tolist()[-1]
                            x2 = group.loc[group['PO Item Creation Date'].idxmax()]['Last Price']
                            x = (x1 + x2)/2
                            all_drop_df.loc[all_drop_df['Material/Service No.'] == material_id, 'mid_x'] = ts1+(ts2-ts1)/2
                            all_drop_df.loc[all_drop_df['Material/Service No.'] == material_id, 'mid_y'] = (x1 + x2)/2

                        groups = all_drop_df.groupby("Material # + percentage")
                        i=0
                        for name, group in groups:
                            list_of_dates = []
                            list_of_usd_prices = []
                            list_of_text = []
                            hover_data = []
                            group.sort_values(by='PO Item Creation Date', inplace=True)
                            for index, row in group.iterrows():
                                    index = list(sorted_list).index(abs(round(row['percentage'],2 )), )
                                    list_of_usd_prices.append(row['mid_y'])
                                    list_of_dates.append(row['mid_x']) 
                                    list_of_text.append(' ')
                                    hover_data.append('Weight: ' + str(round(row['Item Weight'], 4)))
                            delta =  round(all_drop_df[all_drop_df['Material/Service No.'] == row['Material/Service No.']]['percentage'].tolist()[0], 1)

                            list_of_text[0] = str(delta) + '%'
                            if index == 0:
                                fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='text',
                                                    hovertext=hover_data ,textposition='top right', text=list_of_text,
                                                    name=name, legendgroup=name, ))
                            else:
                                fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='text',
                                        hovertext=hover_data ,textposition='top right', text=list_of_text,
                                        name=name, legendgroup=name,  visible='legendonly', legendrank=index, ))
                            i += 1   
                            
                        names = set()
                        fig.for_each_trace(
                            lambda trace:
                                trace.update(showlegend=False)
                                if (trace.name in names) else names.add(trace.name))
                            
                        fig.update_layout( height=450, width=690,plot_bgcolor='rgba(255, 255, 255, 0.5)' ,)
                        fig.update_layout(legend=dict(yanchor="top",y=1,xanchor="left",x=0.00,))
                        
                        fig.update_xaxes(visible=True, showticklabels=True) 
                        fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
                        fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')
                        fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')
                        
                        div_1 = opy.plot(fig, auto_open=False, output_type='div')
                        response = JsonResponse({            
                            'plot_div_2_rfp': div_1,
                            'rfp_percentage':drop_10_total_spend_weight,
                                })
                                
                        add_get_params(response)
                        return response

                    else:
                        print('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  ELSE: ', drop_df.shape)

                        fig = go.Figure(go.Bar(
                            x=[20,],
                            y=[' '],
                            name='No Data',
                            marker_color=[plot_bg],
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
                        fig.update_layout(    plot_bgcolor = plot_bg )

                        fig.update_layout(xaxis_range=[0,20],  plot_bgcolor=plot_bg,)
                        fig.update_layout(
                                height=450,
                                width=690,
                                plot_bgcolor='rgba(255, 255, 255, 0.5)',)         
                        fig.update_xaxes(visible=True, showticklabels=True)
                        fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
                        fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')
                        fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')
                        fig.update_layout( height=450, width=690,plot_bgcolor='rgba(255, 255, 255, 0.5)' ,)
                        
                        fig.update_layout(legend=dict(yanchor="top",y=1,xanchor="left",x=0.00,))

                        div_1 = opy.plot(fig, auto_open=False, output_type='div')

                        response = JsonResponse({            
                                'plot_div_2_rfp': div_1,
                                'rfp_percentage': "0",
                                    })
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
    def visual_ajax_3_rfp(request):
        # Build the POST parameters
        if request.method == 'POST':
            try:    
                 #*cheking user status
                user_response = check_user_status(request)
                user_type = user_response['user_type']
                user_id = user_response['user_id']
                
                if user_type == 'customer':
                    global plot_bg
                        
                    input_min_date= request.POST.get('input_min_date')
                    input_max_date= request.POST.get('input_max_date')
                    # Plot  2
                    df_1 = pd.read_csv(str(BASE_DIR) + "/static/df_1_np_" + str(user_id) + ".csv",error_bad_lines=False, parse_dates=['PO Item Creation Date'])                    
                    df_1['Material/Service No.'] = df_1['Material/Service No.'].astype('str')
                    
                    df_1['PO Item Creation Date'] = pd.DatetimeIndex(df_1['PO Item Creation Date'])
                    df_1 = df_1[(df_1['PO Item Creation Date'] >= input_min_date) & (df_1['PO Item Creation Date'] <= input_max_date)]

                    last_purchases_df = pd.read_csv(str(BASE_DIR) + "/static/last_purchases_df_np_" + str(user_id) + ".csv",error_bad_lines=False)                    
                    last_purchases_df['Material/Service No.'] = last_purchases_df['Material/Service No.'].astype('str')
                    
                    last_purchases_df['PO Item Creation Date'] = pd.DatetimeIndex(last_purchases_df['PO Item Creation Date'])
                    last_purchases_df = last_purchases_df[(last_purchases_df['PO Item Creation Date'] >= input_min_date) & (last_purchases_df['PO Item Creation Date'] <= input_max_date)]
                    
                    new_df = pd.read_csv(str(BASE_DIR) + "/static/new_df_np_" + str(user_id) + ".csv",error_bad_lines=False, parse_dates=['PO Item Creation Date'])                    
                    new_df['Material/Service No.'] = new_df['Material/Service No.'].astype('str')

                    new_df['PO Item Creation Date'] = pd.DatetimeIndex(new_df['PO Item Creation Date'])
                    new_df = new_df[(new_df['PO Item Creation Date'] >= input_min_date) & (new_df['PO Item Creation Date'] <= input_max_date)]
                                        
                    a=1
                    increase_df = df_1[df_1['delta'] > 0]
                    if increase_df.shape[0] > 0:
                        increase_df = increase_df.sort_values(by=['percentage'], ascending=False)
                        increase_df_idxs = increase_df['Material/Service No.'].tolist()

                        mask = df_1['Material/Service No.'].isin(increase_df_idxs)
                        a_1 = df_1[mask]

                        mask = last_purchases_df['Material/Service No.'].isin(increase_df_idxs)
                        a_2 = last_purchases_df[mask]

                        all_increase_df = a_1.append(a_2)
                        all_increase_df['PO Item Creation Date'] = pd.DatetimeIndex(all_increase_df['PO Item Creation Date'])
                        all_increase_df['Material # + percentage'] = 'NO'


                        try:
                            del increase_df['level_0']
                        except: 
                            pass
                        for index, row in increase_df.iterrows():
                            all_increase_df.loc[all_increase_df['Material/Service No.'] == row['Material/Service No.'], 'Material # + percentage'] = row['Material/Service No.'] + '  (' + str(round(row['percentage'],1),) + '%)'
                            all_increase_df.loc[all_increase_df['Material/Service No.'] == row['Material/Service No.'], 'percentage'] = row['percentage']
                            all_increase_df.loc[all_increase_df['Material/Service No.'] == row['Material/Service No.'], 'Item Weight'] = row['Item Weight']

                            
                            
                        fig = go.Figure()

                        increase_10_total_spend = all_increase_df['PO Item Value (GC)'].sum()
                        total_spend = new_df['PO Item Value (GC)'].sum()
                        increase_10_total_spend_weight = round((increase_10_total_spend/total_spend)*100,1)

                        sorted_list = np.unique(abs(all_increase_df['percentage']).tolist())
                        sorted_list = np.round(sorted_list,2)
                        sorted_list[::-1].sort()


                        groups = all_increase_df.groupby("Material # + percentage")
                        i=0
                        for name, group in groups:                
                            list_of_dates = []
                            list_of_usd_prices = []
                            list_of_text = []
                            text_data = []
                            group.sort_values(by='PO Item Creation Date', inplace=True)
                            group.reset_index(inplace=True)
                            for index, row in group.iterrows():
                                    index = list(sorted_list).index(abs(round(row['percentage'],2 )), )
                                    new_price = row['Unit Price']
                                    list_of_usd_prices.append(new_price)
                                    list_of_dates.append(row['PO Item Creation Date']) 
                                    list_of_text.append(' ')
                                    text_data.append('Weight: ' + str(round(row['Item Weight'],4)))
                            list_of_text[-1] =  str(round(row['percentage'], 1),) + '%'    

                            if index == 0:
                                fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='lines+markers+text', textposition='top center',
                                                hovertext=text_data , name=name, marker_size=7,  legendrank=index, 
                                                        legendgroup=name, line=dict(color=px.colors.qualitative.Dark24[i%24])))

                            else:
                                fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='lines+markers+text', textposition='top center',
                                                hovertext=text_data, name=name, marker_size=7, legendrank=index, visible='legendonly',
                                                        legendgroup=name,  line=dict(color=px.colors.qualitative.Dark24[i%24])))

                            i += 1
                            
                        for index, row in all_increase_df.iterrows():
                            a_1.loc[a_1['Material/Service No.'] == row['Material/Service No.'], 'Material # + percentage'] = row['Material/Service No.'] + '  (' + str(round(row['percentage'],1),) + '%)'
                            a_1.loc[a_1['Material/Service No.'] == row['Material/Service No.'], 'percentage'] = row['percentage']

                            a_1.loc[a_1['Material/Service No.'] == row['Material/Service No.'], 'Item WEight'] = row['Item Weight']


                        groups = a_1.groupby("Material # + percentage")
                        i=0
                        for name, group in groups:
                            group = group[group['PO Item Creation Date'] != '2021-08-06']
                            try:
                                group.reset_index(inplace=True)
                            except:
                                pass
                            max_date = group.loc[group['PO Item Creation Date'].idxmax()]['PO Item Creation Date']
                            material_id = group.loc[group['PO Item Creation Date'].idxmax()]['Material/Service No.']
                            p = group.loc[group['PO Item Creation Date'].idxmax()]['percentage']
                            y1 = group.loc[group['PO Item Creation Date'].idxmax()]['PO Item Creation Date']
                            y1 = pd.Timestamp(y1)
                            ts1 = y1
                            ts2 = pd.Timestamp(last_purchases_df[last_purchases_df['Material/Service No.'] == material_id]['PO Item Creation Date'].iloc[0])
                            x1 = group.loc[group['PO Item Creation Date'].idxmax()]['Unit Price']
                            temp = group.loc[group['PO Item Creation Date'] == max_date]
                            if temp.shape[0] > 1:    
                                x1 = group.loc[group['PO Item Creation Date'] == max_date]['Unit Price'].tolist()[-1]
                            x2 = group.loc[group['PO Item Creation Date'].idxmax()]['Last Price']
                            x = (x1 + x2)/2
                            all_increase_df.loc[all_increase_df['Material/Service No.'] == material_id, 'mid_x'] = ts1+(ts2-ts1)/2
                            all_increase_df.loc[all_increase_df['Material/Service No.'] == material_id, 'mid_y'] = (x1 + x2)/2

                        groups = all_increase_df.groupby("Material # + percentage")
                        i=0
                        for name, group in groups:
                            list_of_dates = []
                            list_of_usd_prices = []
                            list_of_text = []
                            hover_data = []
                            group.sort_values(by='PO Item Creation Date', inplace=True)
                            for index, row in group.iterrows():
                                    index = list(sorted_list).index(abs(round(row['percentage'],2 )), )
                                    list_of_usd_prices.append(row['mid_y'])
                                    list_of_dates.append(row['mid_x']) 
                                    list_of_text.append(' ')
                                    hover_data.append('Weight: ' + str(round(row['Item Weight'], 4)))
                            delta =  round(all_increase_df[all_increase_df['Material/Service No.'] == row['Material/Service No.']]['percentage'].tolist()[0], 1)

                            list_of_text[0] = str(delta) + '%'
                            if index == 0:
                                fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='text',
                                                    hovertext=hover_data ,textposition='top right', text=list_of_text,
                                                    name=name, legendgroup=name, ))
                            else:
                                fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='text',
                                        hovertext=hover_data ,textposition='top right', text=list_of_text,
                                        name=name, legendgroup=name,  visible='legendonly', legendrank=index, ))
                            i += 1   
                            
                        names = set()
                        fig.for_each_trace(
                            lambda trace:
                                trace.update(showlegend=False)
                                if (trace.name in names) else names.add(trace.name))

                        fig.update_layout(plot_bgcolor='rgba(255, 255, 255, 0.5)',height=450,width=690,)
                        fig.update_layout(legend=dict(yanchor="top",y=1,xanchor="left",x=0.00,))
                        fig.update_xaxes(visible=True, showticklabels=True)
                        fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
                        # fig.update_yaxes(showline=True, linewidth=1, linecolor='black')
                        fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')
                        fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')

                        div_1 = opy.plot(fig, auto_open=False, output_type='div')

                    
                        #! return finded rows data in table 
                        response = JsonResponse({            
                            'plot_div_3_rfp': div_1,
                            'rfp_percentage': increase_10_total_spend_weight,

                                })
                                
                        add_get_params(response)


                        return response
                    else:

                        fig = go.Figure(go.Bar(
                                x=[20],
                                y=[' '],
                                marker_color=[plot_bg],
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
                        fig.update_layout(    plot_bgcolor=plot_bg )

                        fig.update_layout(xaxis_range=[0,20],  plot_bgcolor=plot_bg,)
                        fig.update_layout(
                                height=450,
                                width=690,
                                plot_bgcolor=plot_bg,)         
                        fig.update_xaxes(visible=False, showticklabels=False)
                    
                        div_1 = opy.plot(fig, auto_open=False, output_type='div')

                    
                        #! return finded rows data in table 
                        response = JsonResponse({            
                            'plot_div_3_rfp': div_1,
                            'rfp_percentage':"0",

                                })
                                
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
    def visual_ajax_4_rfp(request):
        # Build the POST parameters
        if request.method == 'POST':
            try:    
                #*cheking user status
                user_response = check_user_status(request)
                user_type = user_response['user_type']
                user_id = user_response['user_id']
                 
                if user_type == 'customer':
                    global plot_bg
                       
                    input_min_date= request.POST.get('input_min_date')
                    input_max_date= request.POST.get('input_max_date')

                    with Session(engine) as session:
                        user_session_with_data = session.query(USER_SESSION_WITH_DATA).filter(USER_SESSION_WITH_DATA.user_id == user_id).first()
                        non_pricebook_items_count = user_session_with_data.non_pricebook_items_count
                    app_to_app_rfp = pd.read_csv(str(BASE_DIR) + "/static/new_df_np_" + str(user_id) + ".csv",error_bad_lines=False, parse_dates=['PO Item Creation Date'])                    
                    app_to_app_rfp['Material/Service No.'] = app_to_app_rfp['Material/Service No.'].astype('str')

                    app_to_app_rfp['PO Item Creation Date'] = pd.DatetimeIndex(app_to_app_rfp['PO Item Creation Date'])
                    app_to_app_rfp = app_to_app_rfp[(app_to_app_rfp['PO Item Creation Date'] >= input_min_date) & (app_to_app_rfp['PO Item Creation Date'] <= input_max_date)]

                    new_df = pd.read_csv(str(BASE_DIR) + "/static/new_df_np_" + str(user_id) + ".csv",error_bad_lines=False, parse_dates=['PO Item Creation Date'])                    
                    new_df['Material/Service No.'] = new_df['Material/Service No.'].astype('str')

                    new_df['PO Item Creation Date'] = pd.DatetimeIndex(new_df['PO Item Creation Date'])
                    new_df = new_df[(new_df['PO Item Creation Date'] >= input_min_date) & (new_df['PO Item Creation Date'] <= input_max_date)]


                    last_purchases_df_a = app_to_app_rfp.loc[app_to_app_rfp.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]
                    last_purchases_df_a['Last Price'] = last_purchases_df_a['Unit Price']
                    app_rfp_df = last_purchases_df_a[['Material/Service No.', 'Last Price']].copy()
                    new_a2a = pd.merge(app_to_app_rfp, app_rfp_df[['Material/Service No.', 'Last Price']], how='left', on='Material/Service No.', )
                
                    import datetime
                    today = pd.to_datetime("today").normalize()
                    one_year_before = today - datetime.timedelta(days=1*365)
                    starting_day_of_last_year = one_year_before.replace(month=1, day=1)    
                    ending_day_of_last_year = one_year_before.replace(month=12, day=31)

                    df_4 = new_a2a.copy()
                    df_4['PO Item Creation Date'] = pd.DatetimeIndex(df_4['PO Item Creation Date'])
                    df_4 = df_4[(df_4['PO Item Creation Date'] >= input_min_date) & (df_4['PO Item Creation Date'] <= input_max_date)]


                    one_year_df_4 = df_4[(df_4['PO Item Creation Date'] >= starting_day_of_last_year) & (df_4['PO Item Creation Date'] <= ending_day_of_last_year)]
                    temp_df = one_year_df_4.groupby('Material/Service No.')['PO Item Quantity'].mean().reset_index()
                    temp_df.rename(columns={'PO Item Quantity': 'New Demand'}, inplace=True)
                    one_year_df_4 = pd.merge(one_year_df_4, temp_df,  how='left', on='Material/Service No.')

                    count = len(one_year_df_4['Material/Service No.'].value_counts().index.tolist())
                    # Current
                    l_4 = one_year_df_4.loc[one_year_df_4.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]
                    l_4 = l_4.rename(columns={'Unit Price': 'Last Price of Last Year'})
                    one_year_df_4 = pd.merge(one_year_df_4, l_4[['Material/Service No.', 'Last Price of Last Year']],  how='left',on='Material/Service No.')
                    # one_year_df_4 = one_year_df_4.drop_duplicates(subset = ['Material/Service No.'], keep = 'first') 
                    one_year_df_4['Last Year Last Price Spend'] = one_year_df_4['New Demand'] * one_year_df_4['Last Price of Last Year']
                    sum_1 = one_year_df_4['Last Year Last Price Spend'].sum()
                    sum_1



                    # Average
                    a_4 = pd.DataFrame(df_4.groupby('Material/Service No.')['Unit Price'].mean())
                    a_4.rename(columns={'Unit Price':'Average Price'}, inplace=True)
                    a_4.reset_index(inplace=True)
                    one_year_df_4 = pd.merge(one_year_df_4, a_4,  how='left',on='Material/Service No.')
                    # one_year_df_4 = one_year_df_4.drop_duplicates(subset = ['Material/Service No.'], keep = 'first') 
                    one_year_df_4['Average Spend'] = one_year_df_4['New Demand'] * one_year_df_4['Average Price']
                    sum_2 = one_year_df_4['Average Spend'].sum()
                    sum_2

                    # Last-1 Purchasing
                    only_one_time_purchased_df = one_year_df_4.groupby(['Material/Service No.']).filter(lambda x: len(x) == 1)[['Material/Service No.','Unit Price']]
                    temp_df = df_4[df_4['Material/Service No.'].isin(only_one_time_purchased_df['Material/Service No.'].tolist())]
                    test_df = temp_df.loc[temp_df.groupby('Material/Service No.')['PO Item Creation Date'].idxmin()]
                    test_df.rename(columns={'Unit Price': 'Second Last Price'}, inplace=True)

                    at_least_two_times_purchased_df = one_year_df_4.groupby(['Material/Service No.']).filter(lambda x: len(x) > 1)
                    temp_df = at_least_two_times_purchased_df.loc[at_least_two_times_purchased_df.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()][['Material/Service No.','Unit Price']]
                    at_least_two_times_purchased_df = at_least_two_times_purchased_df[~at_least_two_times_purchased_df.index.isin(temp_df.index.tolist())]

                    temp_2_df = at_least_two_times_purchased_df.loc[at_least_two_times_purchased_df.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()][['Material/Service No.','Unit Price']]
                    temp_2_df.rename(columns={'Unit Price': 'Second Last Price'}, inplace=True)
                    second_last_df = temp_2_df.append(test_df)
                    one_year_df_4 = pd.merge(one_year_df_4, second_last_df[['Material/Service No.', 'Second Last Price']], how='left', on='Material/Service No.', )

                    temp_df.rename(columns={'Unit Price': 'Second Last Price'}, inplace=True)

                    # Last Purchasing RFP
                    # one_year_df_4 = one_year_df_4.drop_duplicates(subset = ['Material/Service No.'], keep = 'first') 
                    one_year_df_4['Last Year of Second Last Price Spend'] = one_year_df_4['New Demand'] * one_year_df_4['Second Last Price']
                    sum_3 = one_year_df_4['Last Year of Second Last Price Spend'].sum()
                    sum_3

                    # Lowest Purchasing RFP
                    a_5 = pd.DataFrame(df_4.groupby('Material/Service No.')['Unit Price'].min())
                    a_5.rename(columns={'Unit Price':'Lowest Price'}, inplace=True)
                    a_5.reset_index(inplace=True)
                    one_year_df_4 = pd.merge(one_year_df_4, a_5,  how='left',on='Material/Service No.')
                    # one_year_df_4 = one_year_df_4.drop_duplicates(subset = ['Material/Service No.'], keep = 'first') 
                    one_year_df_4['Lowest Spend'] = one_year_df_4['New Demand'] * one_year_df_4['Lowest Price']
                    sum_4 = one_year_df_4['Lowest Spend'].sum()
                    sum_4


                    total_spends = [int(sum_4), int(sum_3), int(sum_2), int(sum_1)]
                    y_ = ['Lowest','Last-1', 'Average', 'Last']

                    y_2 = [' ', '  ' , '   ', '    ']
                    delta = []
                    colors = []
                    
                    for index, elem in enumerate(total_spends):
                        if elem == 0:
                            elem += 0.00001
                        if index == len(total_spends)-1:
                            delta.append(' ')
                            colors.append('red')
                        else:                    
                            delta.append(str(abs(int(round(((elem - total_spends[-1])/elem)*100)))))
                            print('SPEND[-1]:', total_spends[-1], '\n\n')
                            if int(elem - total_spends[-1]) < 0:
                                colors.append('red')
                            else:
                                colors.append('green')
                    #!bug

                

                    fig = px.bar(
                                x=total_spends,
                                y= y_2,
                                color = y_,
                                color_discrete_map={                           
                                    'Last': 'rgb(144, 238, 144)',
                                    'Average': '#add8e6',
                                    'Last -1': '#fbc02d', 
                                    'Lowest': 'rgb(120, 200, 67)', 
                                    'Pricebook': '#FF7F7F',
                                },
                                orientation = 'h',
                    )

                    
                    fig.add_vline(x=total_spends[-1], line_width=2, line_dash="dash", line_color="red")
                    new_spend = total_spends[:len(total_spends)-1]
                    if max(new_spend) > total_spends[-1]:
                        fig.add_vline(x=max(new_spend), line_width=2, line_dash="dash", line_color="green")

                    pb_df = pd.read_csv(str(BASE_DIR) + "/static/pb_df_after_search_" + str(user_id) + ".csv",error_bad_lines=False, parse_dates=['PO Item Creation Date'])

                    rfp_percentage = (count/pb_df.shape[0]) * 100            
                    fig.update_layout(
                                title="",
                                xaxis_title="",
                                yaxis_title="",
                                legend_title="RFP Valuation ("+ str(count) +  ")",
                                height=470,
                                template = 'ggplot2',
                            )

                    for a, b in enumerate(y_):
                                fig.add_annotation(
                                        text= '<b>' + "{:,}".format(int(total_spends[a])) + '</b>',
                                        x= total_spends[a] -total_spends[-1]/100,
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


                    fig.update_layout(xaxis_range=[0, max(total_spends) + max(total_spends)/7],  plot_bgcolor='rgba(255, 255, 255, 0.5)', )
                    fig.update_layout(height=450, width=690,)
                    fig.update_layout(legend=dict(yanchor="top",y=1,xanchor="left",x=0.00,))

                    fig.update_xaxes(showticklabels=True)
                    fig.update_xaxes(showline=True, linewidth=1, linecolor='black')

                    fig.update_yaxes(visible=False, showticklabels=False)
                    fig.update_xaxes(visible=True, showticklabels=True,  )
                    fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)',)

                    div_1 = opy.plot(fig, auto_open=False, output_type='div')


                        #! return finded rows data in table 
                    rfp_percentage = round((count/non_pricebook_items_count) * 100,1)            
                    response = JsonResponse({            
                        'plot_div_4_rfp': div_1,
                        'rfp_percentage':rfp_percentage,
                        # 'rec_case_1':rec_case_1,
                            })
                            
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
    def visual_ajax_5_rfp(request):
        # Build the POST parameters
        if request.method == 'POST':
            try:    
                #*cheking user status
                user_response = check_user_status(request)
                user_type = user_response['user_type']
                user_id = user_response['user_id']
                
                if user_type == 'customer':
                                
                    input_min_date= request.POST.get('input_min_date')
                    input_max_date= request.POST.get('input_max_date')
                    with Session(engine) as session:
                        user_session_with_data = session.query(USER_SESSION_WITH_DATA).filter(USER_SESSION_WITH_DATA.user_id == user_id).first()
                        non_pricebook_items_count = user_session_with_data.non_pricebook_items_count

                    new_df = pd.read_csv(str(BASE_DIR) + "/static/new_df_np_" + str(user_id) + ".csv",error_bad_lines=False, parse_dates=['PO Item Creation Date'])                    
                    new_df['Material/Service No.'] = new_df['Material/Service No.'].astype('str')

                    new_df['PO Item Creation Date'] = pd.DatetimeIndex(new_df['PO Item Creation Date'])
                    new_df = new_df[(new_df['PO Item Creation Date'] >= input_min_date) & (new_df['PO Item Creation Date'] <= input_max_date)]
                    new_df['Test Spend'] = new_df['PO Item Quantity'] * new_df['Unit Price']
                    last_purchases_df = new_df.loc[new_df.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]
                    last_purchases_df['Last Price'] = last_purchases_df['Unit Price'].copy()
                    
                    temp_df = pd.merge(new_df, last_purchases_df[['Material/Service No.', 'Last Price']], how='left', on='Material/Service No.')  

                    df_all_4 = temp_df.copy()
                    # df_all_4['Demand'] = 0.0
                    # idx_list_4 = df_all_4['Material/Service No.'].value_counts().index.tolist()
                    # len(idx_list_4)
                    # i=0
                    # for item_number in idx_list_4:
                    #     temp = df_all_4[df_all_4['Material/Service No.'] == item_number]
                    #     count = len(temp.groupby(temp['PO Item Creation Date'].dt.year))
                    #     summ = temp['PO Item Quantity'].sum()
                    #     demand = summ/count
                    #     df_all_4.loc[df_all_4['Material/Service No.'] == item_number, ['Demand']] = demand
                    #     i += 1
                    # df_all_4.groupby('Material/Service No.')['PO Item Quantity'].mean().reset_index()
                    temp_df = df_all_4.groupby('Material/Service No.')['PO Item Quantity'].mean().reset_index()
                    temp_df.rename(columns={'PO Item Quantity': 'New Demand'}, inplace=True)
                    df_all_4 = pd.merge(df_all_4, temp_df,  how='left', on='Material/Service No.')

                    count = len(df_all_4['Material/Service No.'].value_counts().index.tolist())
                    # Current
                    df_all_4['Curren RFP Total Spend'] = df_all_4['New Demand'] * df_all_4['Last Price']
                    type_1_df = df_all_4.drop_duplicates(subset = ['Material/Service No.'], keep = 'first') 
                    sum_1 = type_1_df['Curren RFP Total Spend'].sum() 
                    
                    a_4 = pd.DataFrame(df_all_4.groupby('Material/Service No.')['Unit Price'].mean())
                    a_4.rename(columns={'Unit Price':'Total Average Price'}, inplace=True)
                    a_4.reset_index()
                    df_all_4 = pd.merge(df_all_4, a_4,  how='left',on='Material/Service No.')
                    df_all_4['Total Average Spend'] = df_all_4['New Demand'] * df_all_4['Total Average Price']
                    type_1_df = df_all_4.drop_duplicates(subset = ['Material/Service No.'], keep = 'first') 
                    sum_2 = type_1_df['Total Average Spend'].sum()
                    

                    only_one_time_purchased_df = df_all_4.groupby(['Material/Service No.']).filter(lambda x: len(x) == 1)[['Material/Service No.','Unit Price']]
                    only_one_time_purchased_df.rename(columns={'Unit Price': 'Second Last Price'}, inplace=True)

                    at_least_two_times_purchased_df = df_all_4.groupby(['Material/Service No.']).filter(lambda x: len(x) > 1)

                    temp_df = at_least_two_times_purchased_df.loc[at_least_two_times_purchased_df.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()][['Material/Service No.','Unit Price']]
                    at_least_two_times_purchased_df = at_least_two_times_purchased_df[~at_least_two_times_purchased_df.index.isin(temp_df.index.tolist())]

                    temp_2_df = at_least_two_times_purchased_df.loc[at_least_two_times_purchased_df.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()][['Material/Service No.','Unit Price']]
                    temp_2_df.rename(columns={'Unit Price': 'Second Last Price'}, inplace=True)
                    second_last_df = temp_2_df.append(only_one_time_purchased_df)
                    df_all_4 = pd.merge(df_all_4, second_last_df[['Material/Service No.', 'Second Last Price']], how='left', on='Material/Service No.', )

                    # temp_df.rename(columns={'Unit Price': 'Second Last Price'}, inplace=True)
                    # Last Purchasing Price
                    df_all_4['Total Last Price Spend'] = df_all_4['New Demand'] * df_all_4['Second Last Price']
                    type_1_df = df_all_4.drop_duplicates(subset = ['Material/Service No.'], keep = 'first') 
                    sum_3 = type_1_df['Total Last Price Spend'].sum()   


                
                    # Lowest Purchasing RFP
                    a_5 = pd.DataFrame(df_all_4.groupby('Material/Service No.')['Unit Price'].min())
                    a_5.rename(columns={'Unit Price':'Lowest Price'}, inplace=True)
                    a_5.reset_index(inplace=True)
                    df_all_4 = pd.merge(df_all_4, a_5,  how='left',on='Material/Service No.')
                    df_all_4['Lowest Spend'] = df_all_4['New Demand'] * df_all_4['Lowest Price']
                    type_1_df =df_all_4.drop_duplicates(subset = ['Material/Service No.'], keep = 'first') 
                    sum_4 = type_1_df['Lowest Spend'].sum()
                    sum_4           

                    total_spends = [sum_4, sum_3, sum_2, sum_1]
                    y_ = ['Lowest', 'Last-1', 'Average', 'Last']

                    y_2 = [' ', '  ' , '   ', '    ']
                    delta = []
                    colors = []
                    
                    for index, elem in enumerate(total_spends):
                        if elem == 0:
                            elem += 0.00001
                        if index == len(total_spends)-1:
                            delta.append(' ')
                            colors.append('red')
                        else:                    
                            delta.append(str(abs(int(round(((elem - total_spends[-1])/elem)*100)))))
                            if int(elem - total_spends[-1]) < 0:
                                colors.append('red')
                            else:
                                colors.append('green')
                    #!bug

                

                    fig = px.bar(
                                x=total_spends,
                                y= y_2,
                                color = y_,
                                color_discrete_map={                           
                                    'Last': 'rgb(144, 238, 144)',
                                    'Average': '#add8e6',
                                    'Last -1': '#fbc02d', 
                                    'Lowest': 'rgb(120, 200, 67)', 
                                    'Pricebook': '#FF7F7F',
                                },
                                orientation = 'h',
                    )

                    
                    fig.add_vline(x=total_spends[-1], line_width=2, line_dash="dash", line_color="red")
                    new_spend = total_spends[:len(total_spends)-1]
                    if max(new_spend) > total_spends[-1]:
                        fig.add_vline(x=max(new_spend), line_width=2, line_dash="dash", line_color="green")

                    # fig.update_yaxes(ticksuffix=' ' ) 
                    
                    pb_df = pd.read_csv(str(BASE_DIR) + "/static/pb_df_after_search_" + str(user_id) + ".csv",error_bad_lines=False, parse_dates=['PO Item Creation Date'])

                
                    rfp_percentage = (count/pb_df.shape[0]) * 100            
                    fig.update_layout(
                                title="",
                                xaxis_title="",
                                yaxis_title="",
                                legend_title="RFP Valuation ("+ str(count) +  ")",
                                height=470,
                                template = 'ggplot2',
                            )

                    for a, b in enumerate(y_):
                                fig.add_annotation(
                                        text= '<b>' + "{:,}".format(int(total_spends[a])) + '</b>',
                                        x= total_spends[a] -total_spends[-1]/100,
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


                    fig.update_layout(xaxis_range=[0, max(total_spends) + max(total_spends)/7],  plot_bgcolor='rgba(255, 255, 255, 0.5)', )
                    fig.update_layout(height=450, width=690,)
                    fig.update_layout(legend=dict(yanchor="top",y=1,xanchor="left",x=0.00,))

                    fig.update_xaxes(showticklabels=True)
                    fig.update_xaxes(showline=True, linewidth=1, linecolor='black')

                    fig.update_yaxes(visible=False, showticklabels=False)
                    fig.update_xaxes(visible=True, showticklabels=True,  )
                    fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)',)

                    div_1 = opy.plot(fig, auto_open=False, output_type='div')
                        #! return finded rows data in tableax_3 
                    rfp_percentage =round( (count/non_pricebook_items_count) * 100,1)           
                    response = JsonResponse({            
                        'plot_div_5_rfp': div_1,
                        'rfp_percentage':rfp_percentage,
                        # 'rec_case_1':rec_case_1,
                            })
                            
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
    def visual_ajax_6_rfp(request):

        # Build the POST parameters
        if request.method == 'POST':
            try:    
                 #*cheking user status
                user_response = check_user_status(request)
                user_type = user_response['user_type']
                user_id = user_response['user_id']
                
                if user_type == 'customer':
                                
                    global plot_bg
                    
                    df = pd.read_csv(str(BASE_DIR) + "/static/df_np_" + str(user_id) + ".csv",error_bad_lines=False, parse_dates=['PO Item Creation Date'])                    
                    df['Material/Service No.'] = df['Material/Service No.'].astype('str')
                    
                    input_min_date= request.POST.get('input_min_date')
                    input_max_date= request.POST.get('input_max_date')
                    
                    df['PO Item Creation Date'] = pd.DatetimeIndex(df['PO Item Creation Date'])
                    df = df[(df['PO Item Creation Date'] >= input_min_date) & (df['PO Item Creation Date'] <= input_max_date)]

                    input_min_date= request.POST.get('input_min_date')
                    input_max_date= request.POST.get('input_max_date')
                    vendor_name = request.POST.get('vendor_name').lower()

                    try:
                        df['PO Item Creation Date'] = pd.DatetimeIndex(df['PO Item Creation Date'])
                    except:
                        print('Problem  with converting to Datetime / (Try/except)')
                    
                    # df = df[(df['PO Item Creation Date'] >= input_min_date) & (df['PO Item Creation Date'] <= input_max_date)]
                    

                    if df.shape[0] > 0:

                        # New conditions
                        if 'PO Item Deletion Flag' in df.columns.tolist():
                            df = df[df['PO Item Deletion Flag'] != 'X']
                        else:
                            print("The Column 'PO Item Deletion Flag' isn't in the dataset")

                        if 'PO Status Name' in df.columns.tolist():
                            df = df[df['PO Status Name'] != 'Deleted']
                        else:
                            print("The Column 'PO Status Name' isn't in the dataset")

                        if 'Vendor Name' in df.columns.tolist():               
                            df.loc[df['Vendor Name'] == 'R&M Electrical Group MMC',   'Vendor Name'] = 'R&M Electrical Group'
                            df.loc[df['Vendor Name'] == 'R&M Electrical Group Ltd',   'Vendor Name'] = 'R&M Electrical Group'
                            df.loc[df['Vendor Name'] == 'R M Electrical Group Limited',   'Vendor Name'] = 'R&M Electrical Group'
                        else:
                            print("The Column 'Vendor Name' isn't in the dataset")

                        if 'PO Item Value (GC)' in df.columns.tolist():
                            try:
                                df['PO Item Value (GC)'] = pd.to_numeric(df['PO Item Value (GC)'], errors='coerce')
                            except:
                                print("The Column 'PO Item Value (GC)' isn't in right format")

                        else:
                            print("The Column 'PO Status Name' isn't in the dataset")


                        # get most similar vendor name
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
                            # a[(a['PO Item Creation Date'] >= input_min_date) & (a['PO Item Creation Date'] <= input_max_date)]

                            total_spend = a['PO Item Value (GC)'].sum() / 1000000
                            total_spend = str(round(total_spend,2)) + 'M'

                            b = pd.DataFrame(a.groupby(by=['Product Category'])['PO Item Value (GC)'].sum())
                            b.sort_values(by=['PO Item Value (GC)'], ascending=False, inplace=True)
                            mask = a['Product Category'].isin(b.iloc[5:].index.tolist())
                            a.loc[mask, 'Product Category'] = 'Others'

                            a['PO Item Creation Date'] = pd.DatetimeIndex(a['PO Item Creation Date'])
                            a['PO Item Value (GC)'] = a['PO Item Value (GC)'].astype('float').astype(int)
                            a['Year'] = a['PO Item Creation Date'].dt.year
                            a['Year'] = pd.to_datetime(a.Year, format='%Y')


                            c = pd.DataFrame(a.groupby(by=['Year', 'Product Category'])['PO Item Value (GC)'].sum())            
                            c['PO Item Value (GC) Text'] =  c['PO Item Value (GC)'].apply(lambda x : str(round((x/1000000), 2)) + 'M')
                            c.reset_index(inplace=True)
                            c['Year'] = pd.DatetimeIndex(c['Year'])
                            c['Year'] = c['Year'].dt.year
                            b = c[c['Product Category'] != 'Others']

                            e = pd.merge(b, a[['Product Category', 'Product Category Description']],  how='left', on='Product Category').drop_duplicates(['Product Category', 'Year'])

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

                        
                            fig2 = px.line(
                                x=a_line['Year'].tolist(),
                                y=a_line['PO Item Value (GC)'].tolist(),
                                text=a_line['PO Item Value (GC) Text'].tolist(),
                            )
                            fig2.update_traces(textposition='top center')
                            
                            fig.add_trace(fig2.data[0])

                            fig.update_layout(
                                title="",
                                xaxis_title="",
                                yaxis_title="Total Spend, $",
                                legend_title="Category names",
                                height=450,
                                width=690,
                                plot_bgcolor='rgba(255,255,255,0.5)',
                                )
                            # fig.update_xaxes(type='category',     tickformat="%Y", )

                            fig.update_layout(xaxis=dict(tickformat="%Y"))          
                            fig.update_layout(legend=dict(
                                    yanchor="top",
                                    y=1,
                                    xanchor="left",
                                    x=0.00
                            ))

                            fig.update_xaxes(showline=True, linewidth=2, linecolor='white', mirror=True) 
                            fig.update_yaxes(showline=True, linewidth=2, linecolor='white', mirror=True,   ticksuffix=' ') 

                                    
                            fig.update_xaxes(visible=True, showticklabels=True)
                            fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
                            # fig.update_yaxes(showline=True, linewidth=1, linecolor='black')
                            # fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')
                            fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')



                            div_1 = opy.plot(fig, auto_open=False, output_type='div')


                                #! return finded rows data in table 
                            response = JsonResponse({            
                                'plot_div_6_rfp': div_1,
                                    })
                                    
                            add_get_params(response)
                            return response

                    else:
                        fig = go.Figure(go.Bar(
                            x=[20],
                            y=[' '],
                            marker_color= [plot_bg],
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
                        fig.update_layout(    plot_bgcolor = plot_bg )

                        fig.update_layout(xaxis_range=[0,20],  plot_bgcolor = plot_bg,)
                        fig.update_layout(
                                height=480,
                                width=690,
                                plot_bgcolor = plot_bg,)         
                        fig.update_xaxes(visible=False, showticklabels=False)
                
                        div_1 = opy.plot(fig, auto_open=False, output_type='div')

                    div_1 = opy.plot(fig, auto_open=False, output_type='div')


                        #! return finded rows data in table 
                    response = JsonResponse({            
                        'plot_div_6_rfp': div_1,
                        'rfp_percentage': '0',
                        # 'rec_case_1':rec_case_1,
                            })
                            
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
