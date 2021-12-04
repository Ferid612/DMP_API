from .views_visual_1 import *
from .views_visual_rfp import *

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
from .worker import *
import plotly.graph_objects as go
import plotly.express as px
import re
import urllib
import requests
from datetime import date
from .search_alg_parallel import *
from .helpers import *
import warnings
warnings.filterwarnings('ignore')
from functools import reduce


class DMP_Region(DMP_RFP):
    @csrf_exempt
    def test_function(request):
        response=JsonResponse({"Data":"data"})
        add_get_params(response)
        
        return response


    #!!!   region data
    app_to_app_region=[]
    pb_df=[]
    app_region_df=[]
    weight_df=[]
    new_a2a=[]
    region_1=[]
    region_2=[]
    df_1=[]
    temp_dash=[]
    a2a_conv=[]
    total_items_region=0
    benchmark_perscent_region=0
    uploaded_region_file=[]
    region_name=[]
    region_vendor_name=[]
    region_currency_name=[]
    min_date=""
    max_date=""
    categories_region=[]
    df_full=[]


    result_df=[]
    list_of_regions=[]

    all_headers=["PO No.","PO Item No.","Incoterms Name", "Material/Service No.","Vendor Name","PO Item Description","Manufacturer Name",
                "Manufacturer Part No.","Long Description","PO Item Creation Date","PO Item Value (GC)","PO Item Value (GC) Unit", "PO Item Quantity Unit", "Unit Price","Converted Price", "score","path",
                "desc","index","desc_words_short", "desc_words_long"]


    @csrf_exempt
    def search_region_new(request):
        
        pb_df=DMP_Region.uploaded_region_file
        a2a = pd.read_csv(r'C:\Users\OMEN 30L AD\Desktop\DMP\Data\A2A_28_08_2021.csv',  error_bad_lines=False, dtype="unicode", parse_dates=['PO Item Creation Date'])
        DMP_Region.a2a=a2a

        
        response=JsonResponse({"display_converted_uom_region":232})
        add_get_params(response)
        
        return response




    @csrf_exempt
    def search_region(request):
        #************ region searching section start**********************#!****
    
        # df_full= pd.read_csv('C:\\Users\\DRL-Team\\Desktop\DMP\\files\\df_all_regions.csv',error_bad_lines=False, dtype="unicode",parse_dates=['PO Item Creation Date'])
        df_full = pd.read_csv(r'C:\Users\OMEN 30L AD\Desktop\DMP\Data\full_data.csv', parse_dates=['PO Item Creation Date'], dtype="unicode")
        min_date = df_full.loc[df_full['PO Item Creation Date'].idxmin()]['PO Item Creation Date'].strftime('%Y-%m-%d')
        max_date = df_full.loc[df_full['PO Item Creation Date'].idxmax()]['PO Item Creation Date'].strftime('%Y-%m-%d')

        DMP_Region.min_date = min_date
        DMP_Region.max_date = max_date
        DMP_Region.df_full=df_full

        a2a=DMP_Region.a2a
        intersect = reduce(np.intersect1d, a2a.groupby('Region')['Material/Service No.'].apply(list))
        result_df = a2a.loc[a2a['Material/Service No.'].isin(intersect), :].copy()
        result_df['PO Item Quantity'] = result_df['PO Item Quantity'].astype('float')
        result_df['Unit Price'] = result_df['Unit Price'].astype('float')
        result_df['PO Item Value (GC)'] = result_df['PO Item Value (GC)'].astype('float')
        
        DMP_Region.result_df=result_df
        DMP_Region.a2a=a2a

        list_of_regions = result_df['Region'].value_counts().index.tolist()
        list_of_regions = list_of_regions[::-1]
        list_of_regions.remove('AGT')
        list_of_regions.append('AGT')

        DMP_Region.list_of_regions=list_of_regions




        DMP_Region.plot_bg='rgba(171, 248, 190, 0.8)'

        response=JsonResponse({
            "data":"name is succeess",
        })
        add_get_params(response)
        return response

    #************ region searching section end************************   
    @csrf_exempt 
    def upload_file(request): 
        # Build the POST parameters
        if request.method == 'POST':
            try:
                for index, file_ts in enumerate(request.FILES.getlist('input_files')):
                    try:
                    
                        csv_file_name=file_ts.name            
                        region_file=pd.read_csv(file_ts.file)

                        DMP_Region.uploaded_region_file=region_file

                    except Exception as e:
                        print("exc", e)
                        continue


            except:
                print("Not successfully", file_ts.name)       
            response = JsonResponse({'Answer': "Sorry this method running only POST method. Thanks from DRL", })
            add_get_params(response)
            return response
        else:
            response = JsonResponse({'Answer': "Sorry this method running only POST method. Thanks from DRL", })
            
            add_get_params(response)
            return response

    #*****************************region Visualization SECTION************************************************************

    @csrf_exempt
    def get_filter_data_region(request):

        if request.method =='POST':          

            response = JsonResponse({                                    
                    
                    # 'apple_to_apple_count':DMP_Region.apple_to_apple_count,
                    'regions_region':["AGT","TRN"],
                    'vendor_names':  ["SOLAR"],
                    'categories': DMP_Region.categories_region,
                    'region_name':DMP_Region.region_name,
                    'vendor_name':DMP_Region.region_vendor_name,
                    'currency':DMP_Region.region_currency_name,

                    'benchmark_perscent_region':DMP_Region.benchmark_perscent_region_after_search,
                    'total_items_region':DMP_Region.total_items_region_after_search
                })
                
            add_get_params(response)
            return response

    @csrf_exempt
    def get_dates(request):
        if request.method =='POST':
            # all_apple_to_apple 
            #! return finded rows data in table 
            response = JsonResponse({
                 'min_date':DMP_Region.min_date,
                 'max_date':DMP_Region.max_date,
                 })
            add_get_params(response)
            return response
 

    @csrf_exempt
    def visual_ajax_1_region(request):
        if request.method =='POST':

            result_df=DMP_Region.result_df
            list_of_regions=DMP_Region.list_of_regions
            result_agt_df = result_df[result_df['Region'] == 'AGT']
            avg_result_df = result_df.copy()
            a2a=DMP_Region.a2a

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
            y_2 = [' ', '  ' , '   ']
            for index, elem in enumerate(total_spends):
                if index == len(total_spends)-1:
                    delta.append(' ')
                    colors.append('red')
                else:
                    delta.append(str(abs(int(elem - total_spends[-1]))))
                    if int(elem - total_spends[-1]) < 0:
                        colors.append('red')
                    else:
                        colors.append('green')

            fig = px.bar(
                        x=total_spends,
                        y= y_2,
                        color = y_,
                        orientation = 'h',
            )
            count = len(result_df['Material/Service No.'].unique().tolist() )
            rfp_percentage = (count/len(a2a['Material/Service No.'].unique().tolist())) * 100


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
                                x= total_spends[a]-total_spends[-1]/7,
                                y=a,
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
                        temp = abs(int(b))
                    elif len(b) != 0:
                        color = '#006400'
                        temp = abs(int(b))

                    if total_spends[a] > total_spends[-1]:
                        x_ = max(total_spends)
                    else:
                        x_ = total_spends[-1]
                if a != len(delta)-1:
                    temp =  "{:,}".format(int(temp))
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
            # fig.add_vline(x=total_spends[-1], line_width=2, line_dash="dash", line_color="red")
            # fig.add_vline(x=max(total_spends), line_width=2, line_dash="dash", line_color="green")


            fig.add_vline(x=total_spends[-1], line_width=2, line_dash="dash", line_color="red")
            new_spend = total_spends[:len(total_spends)-1]
            if max(new_spend) > total_spends[-1]:
                fig.add_vline(x=max(new_spend), line_width=2, line_dash="dash", line_color="green")
            
            fig.update_layout(
                        height=450,
                        width=690,
                        plot_bgcolor=DMP_Region.plot_bg,) 

            
            div_1 = opy.plot(fig, auto_open=False, output_type='div')

        
            #! return finded rows data in table 
            response = JsonResponse({            
                'plot_div_1_region': div_1,
                'top_10_spend_weight':222,

                    })
                    
            add_get_params(response)
            print("ajax_1_region_succcessfull")


            return response
            
        else:
            response = JsonResponse({            
                    'plot_div_1_region': "Data is not for this filters.",                    
                        })
                        
            add_get_params(response)
            
            print("ajax_1_region_not_succcessfull")
            return response




    @csrf_exempt
    def visual_ajax_2_region(request):
        if request.method =='POST':


            result_df=DMP_Region.result_df
            list_of_regions=DMP_Region.list_of_regions


            result_agt_df = result_df[result_df['Region'] == 'AGT']
            avg_result_df = result_df.copy()
            a2a=DMP_Region.a2a

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
            y_2 = [' ', '  ' , '   ']
            for index, elem in enumerate(total_spends):
                if index == len(total_spends)-1:
                    delta.append(' ')
                    colors.append('red')
                else:
                    delta.append(str(abs(int(elem - total_spends[-1]))))
                    if int(elem - total_spends[-1]) < 0:
                        colors.append('red')
                    else:
                        colors.append('green')

            fig = px.bar(
                        x=total_spends,
                        y= y_2,
                        color = y_,
                        orientation = 'h',
            )
            count = len(result_df['Material/Service No.'].unique().tolist() )
            rfp_percentage = (count/len(a2a['Material/Service No.'].unique().tolist())) * 100


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
                                x= total_spends[a]-total_spends[-1]/7,
                                y=a,
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
                        temp = abs(int(b))
                    elif len(b) != 0:
                        color = '#006400'
                        temp = abs(int(b))

                    if total_spends[a] > total_spends[-1]:
                        x_ = max(total_spends)
                    else:
                        x_ = total_spends[-1]
                if a != len(delta)-1:
                    temp =  "{:,}".format(int(temp))
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
            # fig.add_vline(x=total_spends[-1], line_width=2, line_dash="dash", line_color="red")
            # fig.add_vline(x=max(total_spends), line_width=2, line_dash="dash", line_color="green")


            fig.add_vline(x=total_spends[-1], line_width=2, line_dash="dash", line_color="red")
            new_spend = total_spends[:len(total_spends)-1]
            if max(new_spend) > total_spends[-1]:
                fig.add_vline(x=max(new_spend), line_width=2, line_dash="dash", line_color="green")
            
            fig.update_layout(
                        height=450,
                        width=690,
                        plot_bgcolor=DMP_Region.plot_bg,) 

            
            div_1 = opy.plot(fig, auto_open=False, output_type='div')

        
            #! return finded rows data in table 
            response = JsonResponse({            
                'plot_div_2_region': div_1,
                'top_10_spend_weight':222,

                    })
                    
            add_get_params(response)
            print("ajax_2_region_succcessfull")


            return response
            
        else:
            response = JsonResponse({            
                    'plot_div_2_region': "Data is not for this filters.",                    
                        })
                        
            add_get_params(response)
            
            print("ajax_2_region_not_succcessfull")
            return response

    @csrf_exempt
    def visual_ajax_3_region(request):
        if request.method =='POST':

            a2a=DMP_Region.a2a
            list_of_regions=DMP_Region.list_of_regions
            max_val = 0
            max_region = ''
            for region in list_of_regions:
                print(region)
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
                    
                    if item_number == '10007916':
                        print('Material ID: ', item_number,' and Region: ', region, ' and average price: ', average_price, )
                        
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
                    delta.append(str(abs(int(elem - total_spends[-1]))))
                    if int(elem - total_spends[-1]) < 0:
                        colors.append('red')
                    else:
                        colors.append('green')

            fig = px.bar(
                        x=total_spends,
                        y= y_2,
                        color = y_,
                        orientation = 'h',
            )
            count = len(result_df['Material/Service No.'].unique().tolist() )
            rfp_percentage = (count/len(a2a['Material/Service No.'].unique().tolist())) * 100

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
                                x= total_spends[a]-total_spends[-1]/7,
                                y=a,
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
                        temp = abs(int(b))
                    elif len(b) != 0:
                        color = '#006400'
                        temp = abs(int(b))

                    if total_spends[a] > total_spends[-1]:
                        x_ = max(total_spends)
                    else:
                        x_ = total_spends[-1]
                if a != len(delta)-1:
                    temp =  "{:,}".format(int(temp))
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
            # fig.add_vline(x=total_spends[-1], line_width=2, line_dash="dash", line_color="red")
            # fig.add_vline(x=max(total_spends), line_width=2, line_dash="dash", line_color="green")


            fig.add_vline(x=total_spends[-1], line_width=2, line_dash="dash", line_color="red")
            new_spend = total_spends[:len(total_spends)-1]
            if max(new_spend) > total_spends[-1]:
                fig.add_vline(x=max(new_spend), line_width=2, line_dash="dash", line_color="green")
            # fig.show()







            
            
            fig.update_layout(
                        height=450,
                        width=690,
                        plot_bgcolor=DMP_Region.plot_bg,) 

            
            div_1 = opy.plot(fig, auto_open=False, output_type='div')

        
            #! return finded rows data in table 
            response = JsonResponse({            
                'plot_div_3_region': div_1,
                'top_10_spend_weight':333,

                    })
                    
            add_get_params(response)
            print("ajax_3_region_succcessfull")


            return response
            
        else:
            response = JsonResponse({            
                    'plot_div_3_region': "Data is not for this filters.",                    
                        })
                        
            add_get_params(response)
            
            print("ajax_3_region_not_succcessfull")
            return response
    @csrf_exempt
    def visual_ajax_4_region(request):
        if request.method =='POST':


            result_df=DMP_Region.result_df
            list_of_regions=DMP_Region.list_of_regions


            result_agt_df = result_df[result_df['Region'] == 'AGT']
            avg_result_df = result_df.copy()
            a2a=DMP_Region.a2a

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
            y_2 = [' ', '  ' , '   ']
            for index, elem in enumerate(total_spends):
                if index == len(total_spends)-1:
                    delta.append(' ')
                    colors.append('red')
                else:
                    delta.append(str(abs(int(elem - total_spends[-1]))))
                    if int(elem - total_spends[-1]) < 0:
                        colors.append('red')
                    else:
                        colors.append('green')

            fig = px.bar(
                        x=total_spends,
                        y= y_2,
                        color = y_,
                        orientation = 'h',
            )
            count = len(result_df['Material/Service No.'].unique().tolist() )
            rfp_percentage = (count/len(a2a['Material/Service No.'].unique().tolist())) * 100

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
                                x= total_spends[a]-total_spends[-1]/7,
                                y=a,
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
                        temp = abs(int(b))
                    elif len(b) != 0:
                        color = '#006400'
                        temp = abs(int(b))

                    if total_spends[a] > total_spends[-1]:
                        x_ = max(total_spends)
                    else:
                        x_ = total_spends[-1]
                if a != len(delta)-1:
                    temp =  "{:,}".format(int(temp))
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
            # fig.add_vline(x=total_spends[-1], line_width=2, line_dash="dash", line_color="red")
            # fig.add_vline(x=max(total_spends), line_width=2, line_dash="dash", line_color="green")


            fig.add_vline(x=total_spends[-1], line_width=2, line_dash="dash", line_color="red")
            new_spend = total_spends[:len(total_spends)-1]
            if max(new_spend) > total_spends[-1]:
                fig.add_vline(x=max(new_spend), line_width=2, line_dash="dash", line_color="green")
            
            fig.update_layout(
                        height=450,
                        width=690,
                        plot_bgcolor=DMP_Region.plot_bg,) 

            
            div_1 = opy.plot(fig, auto_open=False, output_type='div')

        
            #! return finded rows data in table 
            response = JsonResponse({            
                'plot_div_1_region': div_1,
                'top_10_spend_weight':222,

                    })
                    
            add_get_params(response)
            print("ajax_1_region_succcessfull")


            return response
            
        else:
            response = JsonResponse({            
                    'plot_div_1_region': "Data is not for this filters.",                    
                        })
                        
            add_get_params(response)
            
            print("ajax_1_region_not_succcessfull")
            return response

    @csrf_exempt
    def visual_ajax_5_region(request):
        if request.method =='POST':

            list_of_regions=DMP_Region.list_of_regions
            last_result_df=DMP_Region.result_df
            result_df=DMP_Region.result_df
            a2a=DMP_Region.a2a

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
            y_2 = [' ', '  ' , '   ']
            for index, elem in enumerate(total_spends):
                if index == len(total_spends)-1:
                    delta.append(' ')
                    colors.append('red')
                else:
                    delta.append(str(abs(int(elem - total_spends[-1]))))
                    if int(elem - total_spends[-1]) < 0:
                        colors.append('red')
                    else:
                        colors.append('green')

            fig = px.bar(
                        x=total_spends,
                        y= y_2,
                        color = y_,
                        orientation = 'h',
            )
            count = len(result_df['Material/Service No.'].unique().tolist() )
            rfp_percentage = (count/len(a2a['Material/Service No.'].unique().tolist())) * 100

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
                                x= total_spends[a]-total_spends[-1]/7,
                                y=a,
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
                        temp = abs(int(b))
                    elif len(b) != 0:
                        color = '#006400'
                        temp = abs(int(b))

                    if total_spends[a] > total_spends[-1]:
                        x_ = max(total_spends)
                    else:
                        x_ = total_spends[-1]
                        
                if a != len(delta)-1:
                    temp =  "{:,}".format(int(temp))
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
            # fig.add_vline(x=total_spends[-1], line_width=2, line_dash="dash", line_color="red")
            # fig.add_vline(x=max(total_spends), line_width=2, line_dash="dash", line_color="green")
            fig.update_layout(plot_bgcolor='rgba(171, 248, 190, 0.8)')


            fig.add_vline(x=total_spends[-1], line_width=2, line_dash="dash", line_color="red")
            new_spend = total_spends[:len(total_spends)-1]
            if max(new_spend) > total_spends[-1]:
                fig.add_vline(x=max(new_spend), line_width=2, line_dash="dash", line_color="green")
            # fig.show()
            fig.update_layout(
                        height=450,
                        width=690,
                        plot_bgcolor=DMP_Region.plot_bg,) 

            
            div_1 = opy.plot(fig, auto_open=False, output_type='div')

        
            #! return finded rows data in table 
            response = JsonResponse({            
                'plot_div_2_region': div_1,
                'top_10_spend_weight':222,

                    })
                    
            add_get_params(response)
            print("ajax_2_region_succcessfull")


            return response
            
        else:
            response = JsonResponse({            
                    'plot_div_2_region': "Data is not for this filters.",                    
                        })
                        
            add_get_params(response)
            
            print("ajax_2_region_not_succcessfull")
            return response

    @csrf_exempt
    def visual_ajax_6_region(request):
        if request.method =='POST':

            a2a=DMP_Region.a2a
            list_of_regions=DMP_Region.list_of_regions
            last_result_df=DMP_Region.result_df



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
                    delta.append(str(abs(int(elem - total_spends[-1]))))
                    if int(elem - total_spends[-1]) < 0:
                        colors.append('red')
                    else:
                        colors.append('green')

            fig = px.bar(
                        x=total_spends,
                        y= y_2,
                        color = y_,
                        orientation = 'h',
            )
            count = len(result_df['Material/Service No.'].unique().tolist() )
            rfp_percentage = (count/len(a2a['Material/Service No.'].unique().tolist())) * 100

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
                                x= total_spends[a]-total_spends[-1]/7,
                                y=a,
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
                        temp = abs(int(b))
                    elif len(b) != 0:
                        color = '#006400'
                        temp = abs(int(b))

                    if total_spends[a] > total_spends[-1]:
                        x_ = max(total_spends)
                    else:
                        x_ = total_spends[-1]
                        
                if a != len(delta)-1:
                    temp =  "{:,}".format(int(temp))
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
            # fig.add_vline(x=total_spends[-1], line_width=2, line_dash="dash", line_color="red")
            # fig.add_vline(x=max(total_spends), line_width=2, line_dash="dash", line_color="green")


            fig.add_vline(x=total_spends[-1], line_width=2, line_dash="dash", line_color="red")
            new_spend = total_spends[:len(total_spends)-1]
            if max(new_spend) > total_spends[-1]:
                fig.add_vline(x=max(new_spend), line_width=2, line_dash="dash", line_color="green")


            
            fig.update_layout(
                        height=450,
                        width=690,
                        plot_bgcolor=DMP_Region.plot_bg,) 

            
            div_1 = opy.plot(fig, auto_open=False, output_type='div')

        
            #! return finded rows data in table 
            response = JsonResponse({            
                'plot_div_3_region': div_1,
                'top_10_spend_weight':333,

                    })
                    
            add_get_params(response)
            print("ajax_3_region_succcessfull")


            return response
            
        else:
            response = JsonResponse({            
                    'plot_div_3_region': "Data is not for this filters.",                    
                        })
                        
            add_get_params(response)
            
            print("ajax_3_region_not_succcessfull")
            return response