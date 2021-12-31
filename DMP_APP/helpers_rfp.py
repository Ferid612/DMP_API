import math
import numpy as np
import pandas as pd
from fuzzywuzzy import fuzz
import datetime
import plotly.graph_objects as go
import plotly.express as px
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cluster import DBSCAN
from DMP_API.settings import BASE_DIR


CRED = '\033[91m'
CEND = '\033[0m'


def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

def preprocess_pricebook_data(pb_df, currency_ratio):
    
    all_columns = ['BP Material / \nService Master No.', 'Supplier Part No. / Reference', 'BP Long Description', 'Manufacturer Name',
                    'Manufacturer Part Number', 'BP Short Description',  'Supplier Description', 'Incoterms Key', '2021 rates', '2020 rates', 'UOM']

    columns = pb_df.columns.tolist()

    for in_column in columns:
        sim_scores = []
        for column_base in all_columns:
            score = fuzz.ratio(column_base, in_column)
            sim_scores.append(score)
        
        max_score = max(sim_scores)
        max_score_index = sim_scores.index(max_score)
        result_column = all_columns[max_score_index]

        if max_score > 80:
            pb_df.rename(columns={in_column: result_column }, inplace=True)
        else:
            print(CRED + 'The column name "' + in_column  + '" is not in base columns list'   + CEND)
                    

    #! Preprocess raw data
    pb_df = pb_df[all_columns]
    pb_df.dropna(subset=['2021 rates'], inplace=True)
    pb_df.dropna(subset=['2020 rates'], inplace=True)

    pb_df = pb_df[pb_df['2021 rates'].apply(lambda x: is_float(x))]
    pb_df = pb_df[pb_df['2020 rates'].apply(lambda x: is_float(x))]
    pb_df['2021 rates'] = pb_df['2021 rates'].astype('float')
    pb_df['2020 rates'] = pb_df['2020 rates'].astype('float')

    pb_df = pb_df[(pb_df['2021 rates'] > 0) & (pb_df['2020 rates'] > 0)]

    pb_df['Manufacturer Name'] = pb_df['Manufacturer Name'].replace(np.nan, ' ', regex=True) 
    pb_df['Manufacturer Part Number'] = pb_df['Manufacturer Part Number'].replace(np.nan, ' ', regex=True) 

    pb_df['BP Material / \nService Master No.'] = pb_df['BP Material / \nService Master No.'].astype('str')
    pb_df['BP Material / \nService Master No.'] = pb_df['BP Material / \nService Master No.'].apply(lambda x: str(x)[:-2])
    

    current_date = datetime.date.today().strftime('%Y-%m-%d')

    pb_df['PO Item Creation Date'] = '2021-08-06'
    pb_df['PO Item Creation Date'] = pd.DatetimeIndex(pb_df['PO Item Creation Date'])
    pb_df.loc[pb_df['BP Material / \nService Master No.'] == 'n', 'BP Material / \nService Master No.'] = pb_df[pb_df['BP Material / \nService Master No.'] == 'n'].index
    pb_df['BP Material / \nService Master No.'] =  pb_df['BP Material / \nService Master No.'].astype('str')
    pb_df['2021 rates'] = pb_df['2021 rates'] / currency_ratio 
    pb_df['2020 rates'] = pb_df['2020 rates'] / currency_ratio 

    return pb_df

def get_most_spent_material_indexes(new_a2a):

    temp = new_a2a.copy()
    df_agg = temp.groupby(['Material/Service No.']).agg({'PO Item Value (GC)':sum})
    res = df_agg.apply(lambda x: x.sort_values(ascending=False))
    idx = res.index.tolist()
    list_of_idxes = []
    i=0
    for index in idx:
        if temp[temp['Material/Service No.'] == index].shape[0] > 1:
            list_of_idxes.append(index)
            if i == 9:
                break
            i +=1

    return list_of_idxes

def get_a2a_df(app_to_app_rfp, app_rfp_df):
    
    new_a2a = pd.merge(app_to_app_rfp, app_rfp_df[['BP Material / \nService Master No.', '2021 rates', '2020 rates']], 
        how='left', left_on='Material/Service No.', right_on='BP Material / \nService Master No.')
    new_a2a['2021 rates'] = new_a2a['2021 rates'].astype('float')

    new_a2a['delta'] = 0.0
    new_a2a['percentage'] = 0.0
    new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax(), 'delta'] = new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['2021 rates'] - new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['Unit Price']
    new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax(), 'percentage'] = (new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['delta'] / new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['Unit Price']) * 100

    weight_df = pd.DataFrame(new_a2a.groupby('Material/Service No.')['PO Item Value (GC)'].sum())
    weight_df.rename(columns={'PO Item Value (GC)':'Item Total Spend'}, inplace=True)
    weight_df.reset_index(inplace=True)
    new_a2a = pd.merge(new_a2a, weight_df,  how='left', on='Material/Service No.')
    new_a2a['Item Weight'] = new_a2a['Item Total Spend'] / (new_a2a['PO Item Value (GC)'].sum())

    return new_a2a
                
def get_delta_and_index(total_spends):
    
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

    return delta, colors

def plot_1_1_pb(fig, result, list_of_idxs):

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

    return fig        

def plot_1_2_pb(fig, result_3, list_of_idxs):

    result_3 = result_3.sort_values('PO Item Creation Date')
    result_3['delta'] = result_3['2021 rates'] - result_3['2020 rates']
    result_3['percentage'] = (result_3['delta'] / result_3['2020 rates']) * 100
    groups = result_3.groupby("Material # + abs percentage")

    i=0
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
        delta =  round(result_3[result_3['Material/Service No.'] == row['Material/Service No.']]['percentage'].tolist()[0], 1)

        list_of_text[0] = str(delta) + '%'
        if row['Material/Service No.'] in list_of_idxs:
            fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='lines+markers+text',
                                hovertext=hover_data ,textposition='top center',
                                name=name, marker_size=10,legendgroup=name, 
                                line = dict(width=2, dash='dash', color=px.colors.qualitative.Bold[i]), marker_symbol='triangle-up'),)
        else:
            fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='lines+markers+text',
                    hovertext=hover_data ,textposition='top center',
                    name=name, marker_size=10,legendgroup=name,  visible='legendonly',
                    line = dict(width=2, dash='dash', color=px.colors.qualitative.Bold[i]), marker_symbol='triangle-up'))

        i+= 1

    return fig, result_3

def plot_1_3_pb(fig, result, list_of_idxs, today, current_date):
    
    groups = result.groupby("Material # + abs percentage")
    i=0
    for name, group in groups:
        group = group[group['PO Item Creation Date'] != current_date]
        try:
            group.reset_index(inplace=True)
        except: 
            pass
        max_date = group.loc[group['PO Item Creation Date'].idxmax()]['PO Item Creation Date']
        material_id = group.loc[group['PO Item Creation Date'].idxmax()]['Material/Service No.']
        p = group.loc[group['PO Item Creation Date'].idxmax()]['percentage']
        y1 = group.loc[group['PO Item Creation Date'].idxmax()]['PO Item Creation Date']

        try:
            y1 = pd.Timestamp(y1)
        except:
            continue
        ts1 = y1
        ts2 = today
        x1 = group.loc[group['PO Item Creation Date'].idxmax()]['Unit Price']
        temp = group.loc[group['PO Item Creation Date'] == max_date]
        if temp.shape[0] > 1:
            x1 = group.loc[group['PO Item Creation Date'] == max_date]['Unit Price'].tolist()[-1]
        x2 = group.loc[group['PO Item Creation Date'].idxmax()]['2021 rates']
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
    
    return fig

def plot_1_4_pb(fig, result_3, list_of_idxs, today, current_date):

    result_3['PO Item Creation Date'] = pd.DatetimeIndex(result_3['PO Item Creation Date'])    
    groups = result_3.groupby("Material # + abs percentage")
    i=0
    for name, group in groups:
        group.loc[group['PO Item Creation Date'].idxmax()]
        
        grup_loc = group.loc[group['PO Item Creation Date'].idxmax()]['Material/Service No.']
        # print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ grup_loc: ", grup_loc)
        # print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ grup_loc type: ", type(grup_loc))
        
        material_id =group.loc[group['PO Item Creation Date'].idxmax()]['Material/Service No.']
        y1 = group.loc[group['PO Item Creation Date'].idxmax()]['PO Item Creation Date']
        y1 = pd.Timestamp(y1)
        ts1 = y1
        ts2 = today
        x1 = group.loc[group['PO Item Creation Date'].idxmax()]['Unit Price']
        x2 = group.loc[group['PO Item Creation Date'].idxmax()]['2021 rates']
        x = (x1 + x2)/2
        result_3.loc[result_3['Material/Service No.'] == material_id, 'mid_x'] = ts1+(ts2-ts1)/2
        result_3.loc[result_3['Material/Service No.'] == material_id, 'mid_y'] = (x1 + x2)/2    



    groups = result_3.groupby("Material # + abs percentage") ##.apply(lambda x: x.sort_values('abs_percentage', ascending=False))
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
        delta =  round(result_3[result_3['Material/Service No.'] == row['Material/Service No.']]['percentage'].tolist()[0], 1)

        list_of_text[-1] = str(delta) + '%'
        if row['Material/Service No.'] in list_of_idxs:
            fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='text', hovertext=hover_data,
                    textposition='bottom center', text=list_of_text, name=name, marker_size=5, legendgroup=name,
                                    line=dict(color=px.colors.qualitative.Bold[i]),))
            fig.update_traces()
        else:
            fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='text', hovertext=hover_data,
            textposition='bottom center', text=list_of_text, name=name, marker_size=5, legendgroup=name, visible='legendonly',
                                    line=dict(color=px.colors.qualitative.Bold[i]),))
    

    return fig

def update_layout_fig_1_1(fig):
    names = set()
    fig.for_each_trace(
        lambda trace:
            trace.update(showlegend=False)
            if (trace.name in names) else names.add(trace.name))

    fig.update_layout(legend_title='Material #         Last',)

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
    fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')
    fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')

    return fig

def update_layout_fig_1_2(plot_bg_color):

    fig = go.Figure(go.Bar(
        x=[20],
        y=[' '],
        marker_color=[plot_bg_color],
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
    fig.update_layout(    plot_bgcolor=plot_bg_color )
    fig.update_layout(xaxis_range=[0,20],  plot_bgcolor=plot_bg_color,)
    fig.update_layout(
            height=450,
            width=690,
            plot_bgcolor=plot_bg_color,)         
    fig.update_xaxes(visible=False, showticklabels=False)
    fig.update_xaxes(showline=True, linewidth=1, linecolor='black')

    return fig




def plot_2_1_pb(fig, all_drop_df, sorted_list):
    
    groups = all_drop_df.groupby("Material # + percentage")
    i=0
    for name, group in groups:
        list_of_dates = []
        list_of_usd_prices = []
        text_data = []
        group.sort_values(by='PO Item Creation Date', inplace=True)
        for index, row in group.iterrows():
                index = list(sorted_list).index(abs(round(row['percentage'],2 )), )
                list_of_usd_prices.append(row['Unit Price'])
                list_of_dates.append(row['PO Item Creation Date']) 
                text_data.append('Weight: ' + str(round(row['Item Weight'],4)))
        
        if index == 0:
            fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='lines+markers+text', textposition='top center',
                            hovertext=text_data , name=name, marker_size=7,  legendrank=index, 
                                    legendgroup=name, line=dict(color=px.colors.qualitative.Dark24[i%24])))
        
        else:
            fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='lines+markers+text', textposition='top center',
                            hovertext=text_data, name=name, marker_size=7, legendrank=index, visible='legendonly',
                                    legendgroup=name,  line=dict(color=px.colors.qualitative.Dark24[i%24])))
        
        i += 1

 
    return fig

def plot_2_2_pb(fig, result_3, sorted_list):
    
    groups = result_3.groupby("Material # + percentage")
    i=0
    for name, group in groups:
        list_of_dates = []
        list_of_usd_prices = []
        list_of_text = []
        hover_data = []
        group.sort_values(by='PO Item Creation Date', inplace=True)
        
        for index, row in group.iterrows():
                index = list(sorted_list).index(abs(round(row['percentage 0'],2 )), )
                list_of_usd_prices.append(row['Unit Price'])
                list_of_dates.append(row['PO Item Creation Date']) 
                list_of_text.append(' ')
                hover_data.append('Weight: ' + str(round(row['Item Weight'], 4)))
        
        if index == 0:
            fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='lines+markers+text',
                                hovertext=hover_data ,textposition='bottom left',
                                name=name, marker_size=10, legendgroup=name, 
                                line = dict(width=2, dash='dash',  color=px.colors.qualitative.Dark24[i%24]), 
                                            legendrank=index, marker_symbol='triangle-up'),)

        else:
            fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='lines+markers+text',
                    hovertext=hover_data ,textposition='bottom left', text=list_of_text,
                    name=name, marker_size=10,legendgroup=name,  visible='legendonly',
                    line = dict(width=2, dash='dash',  color=px.colors.qualitative.Dark24[i%24]), marker_symbol='triangle-up', legendrank=index, ))
        i += 1


    return fig

def plot_2_3_pb(fig, all_drop_df, sorted_list, today, current_date):
    
    groups = all_drop_df.groupby("Material # + percentage")
    i=0
    for name, group in groups:
        group = group[group['PO Item Creation Date'] != current_date]
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
        ts2 = today
        x1 = group.loc[group['PO Item Creation Date'].idxmax()]['Unit Price']
        temp = group.loc[group['PO Item Creation Date'] == max_date]
        if temp.shape[0] > 1:
            x1 = group.loc[group['PO Item Creation Date'] == max_date]['Unit Price'].tolist()[-1]
        x2 = group.loc[group['PO Item Creation Date'].idxmax()]['2021 rates']
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


    return fig

def plot_2_4_pb(fig, result_3, sorted_list, today, current_date):

    result_3['PO Item Creation Date'] = pd.DatetimeIndex(result_3['PO Item Creation Date'])    
    groups = result_3.groupby("Material # + percentage")
    i=0
    for name, group in groups:
        group.loc[group['PO Item Creation Date'].idxmax()]
        material_id = group.loc[group['PO Item Creation Date'].idxmax()]['Material/Service No.']
        y1 = group.loc[group['PO Item Creation Date'].idxmax()]['PO Item Creation Date']
        y1 = pd.Timestamp(y1)
        ts1 = y1
        ts2 = today
        x1 = group.loc[group['PO Item Creation Date'].idxmax()]['Unit Price']
        x2 = group.loc[group['PO Item Creation Date'].idxmax()]['2021 rates']
        x = (x1 + x2)/2
        result_3.loc[result_3['Material/Service No.'] == material_id, 'mid_x'] = ts1+(ts2-ts1)/2
        result_3.loc[result_3['Material/Service No.'] == material_id, 'mid_y'] = (x1 + x2)/2
    
    groups = result_3.groupby("Material # + percentage")
    i=0
    for name, group in groups:
        list_of_dates = []
        list_of_usd_prices = []
        list_of_text = []
        hover_data = []
        group.sort_values(by='PO Item Creation Date', inplace=True)
        for index, row in group.iterrows():
                index = list(sorted_list).index(abs(round(row['percentage 0'],2 )), )
                list_of_usd_prices.append(row['mid_y'])
                list_of_dates.append(row['mid_x'])
                list_of_text.append(' ')
                hover_data.append('Weight: ' + str(round(row['Item Weight'], 4)))
        delta =  round(result_3[result_3['Material/Service No.'] == row['Material/Service No.']]['percentage'].tolist()[0], 1)

        list_of_text[0] = str(delta) + '%'
        if index == 0:
            fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='text',
                                hovertext=hover_data ,textposition='bottom left', text=list_of_text,
                                name=name, legendgroup=name, ))
        else:
            fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='text',
                    hovertext=hover_data ,textposition='bottom left', text=list_of_text,
                    name=name, legendgroup=name,  visible='legendonly', legendrank=index, ))
        i += 1


    return fig

def update_layout_fig_2_1(fig):

    fig.update_layout(legend_title='Material #         Last     RFP',             yaxis_title="Price, $",)
    
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

    return fig




def plot_3_1_pb(fig, all_increase_df, sorted_list):
    
    groups = all_increase_df.groupby("Material # + percentage")
    i=0
    for name, group in groups:
        list_of_dates = []
        list_of_usd_prices = []
        list_of_text = []
        text_data = []
        group.sort_values(by='PO Item Creation Date', inplace=True)
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
                            hovertext=text_data, name=name, marker_size=7,  legendrank=index, 
                                    legendgroup=name, line=dict(color=px.colors.qualitative.Dark24[i%24])))
        
        else:
            fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='lines+markers+text', textposition='top center',
                            hovertext=text_data, name=name, marker_size=7, legendrank=index, visible='legendonly',
                                    legendgroup=name,  line=dict(color=px.colors.qualitative.Dark24[i%24])))
        
        i += 1

    return fig

def plot_3_2_pb(fig, result_3, sorted_list):

    groups = result_3.groupby("Material # + percentage")
    i=0
    for name, group in groups:
        list_of_dates = []
        list_of_usd_prices = []
        list_of_text = []
        hover_data = []
        group.sort_values(by='PO Item Creation Date', inplace=True)
        for index, row in group.iterrows():
                index = list(sorted_list).index(abs(round(row['percentage 0'],2 )), )
                list_of_usd_prices.append(row['Unit Price'])
                list_of_dates.append(row['PO Item Creation Date']) 
                list_of_text.append(' ')
                hover_data.append('Weight: ' + str(round(row['Item Weight'], 4)))
        delta =  round(result_3[result_3['Material/Service No.'] == row['Material/Service No.']]['percentage'].tolist()[0], 1)

        list_of_text[0] = str(delta) + '%'
        if index == 0:
            fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='lines+markers+text',
                                hovertext=hover_data ,textposition='top center',
                                name=name, marker_size=10, legendgroup=name, 
                                line = dict(width=2, dash='dash',  color=px.colors.qualitative.Dark24[i%24]), 
                                            legendrank=index, marker_symbol='triangle-up'),)
        else:
            fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='lines+markers+text',
                    hovertext=hover_data ,textposition='top center', name=name, marker_size=10,legendgroup=name,  visible='legendonly',
                    line = dict(width=2, dash='dash',  color=px.colors.qualitative.Dark24[i%24]), marker_symbol='triangle-up', legendrank=index, ))
        i += 1
    
    return fig
    
def plot_3_3_pb(fig, all_increase_df, sorted_list, today, current_date):
    
    groups = all_increase_df.groupby("Material # + percentage")
    i=0
    for name, group in groups:
        group = group[group['PO Item Creation Date'] != current_date]
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
        ts2 = today
        x1 = group.loc[group['PO Item Creation Date'].idxmax()]['Unit Price']
        temp = group.loc[group['PO Item Creation Date'] == max_date]
        if temp.shape[0] > 1:
            x1 = group.loc[group['PO Item Creation Date'] == max_date]['Unit Price'].tolist()[-1]
        x2 = group.loc[group['PO Item Creation Date'].idxmax()]['2021 rates']
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
                                hovertext=hover_data ,textposition='bottom right', text=list_of_text,
                                name=name, legendgroup=name, ))
        else:
            fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='text',
                    hovertext=hover_data ,textposition='bottom right', text=list_of_text,
                    name=name, legendgroup=name,  visible='legendonly', legendrank=index, ))
        i += 1
    

    return fig

def plot_3_4_pb(fig, result_3, sorted_list, today, current_date):
    
    result_3['PO Item Creation Date'] = pd.DatetimeIndex(result_3['PO Item Creation Date'])    
    groups = result_3.groupby("Material # + percentage")
    i=0
    for name, group in groups:
        group.loc[group['PO Item Creation Date'].idxmax()]
        material_id = group.loc[group['PO Item Creation Date'].idxmax()]['Material/Service No.']
        y1 = group.loc[group['PO Item Creation Date'].idxmax()]['PO Item Creation Date']
        y1 = pd.Timestamp(y1)
        ts1 = y1
        ts2 = today
        x1 = group.loc[group['PO Item Creation Date'].idxmax()]['Unit Price']
        x2 = group.loc[group['PO Item Creation Date'].idxmax()]['2021 rates']
        x = (x1 + x2)/2
        result_3.loc[result_3['Material/Service No.'] == material_id, 'mid_x'] = ts1+(ts2-ts1)/2
        result_3.loc[result_3['Material/Service No.'] == material_id, 'mid_y'] = (x1 + x2)/2
        
    groups = result_3.groupby("Material # + percentage")
    i=0
    for name, group in groups:
        list_of_dates = []
        list_of_usd_prices = []
        list_of_text = []
        hover_data = []
        group.sort_values(by='PO Item Creation Date', inplace=True)
        for index, row in group.iterrows():
                index = list(sorted_list).index(abs(round(row['percentage 0'],2 )), )
                list_of_usd_prices.append(row['mid_y'])
                list_of_dates.append(row['mid_x']) 
                list_of_text.append(' ')
                hover_data.append('Weight: ' + str(round(row['Item Weight'], 4)))
        delta =  round(result_3[result_3['Material/Service No.'] == row['Material/Service No.']]['percentage'].tolist()[0], 1)

        list_of_text[0] = str(delta) + '%'
        if index == 0:
            fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='text',
                                hovertext=hover_data ,textposition='top left', text=list_of_text,
                                name=name, legendgroup=name, ))
        else:
            fig.add_trace(go.Scatter(x=list_of_dates, y=list_of_usd_prices, mode='text',
                    hovertext=hover_data ,textposition='top left', text=list_of_text,
                    name=name, legendgroup=name,  visible='legendonly', legendrank=index, ))
        i += 1


    return fig

def update_layout_fig_4_1(fig, y_, delta,  total_spends, colors, count):
    
    fig.add_vline(x=total_spends[-1], line_width=2, line_dash="dash", line_color="red")
    new_spend = total_spends[:len(total_spends)-1]
    if max(new_spend) > total_spends[-1]:
        fig.add_vline(x=max(new_spend), line_width=2, line_dash="dash", line_color="green")

        
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
    
    
    fig.update_layout(title="", xaxis_title="", yaxis_title="", legend_title="RFP Valuation ("+ str(count) +  ")", height=470, template = 'ggplot2', )

    fig.update_layout(xaxis_range=[0, max(total_spends) + max(total_spends)/7],  plot_bgcolor='rgba(255, 255, 255, 0.5)', )
    fig.update_layout(height=450, width=690,)
    fig.update_layout(legend=dict(yanchor="top",y=1,xanchor="left",x=0.00,))

    fig.update_xaxes(visible=True, showticklabels=True)
    fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
    fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')



    return fig

def update_layout_fig_5_1(fig, y_, delta,  total_spends, colors, count):
    fig.update_yaxes(ticksuffix=' ' ) 
    fig.update_layout(title="", xaxis_title="", yaxis_title="", legend_title="RFP Valuation (" + str(count) +")", height=470, template = 'ggplot2',  )


    for a, b in enumerate(y_):
                fig.add_annotation(text= '<b>' + "{:,}".format(int(total_spends[a])) + '</b>', x= total_spends[a] - total_spends[-1]/100, y=a, xanchor='right',
                        font=dict( family="Courier New, monospace", size=16, color="#ffffff", ), showarrow=False)
    
    for a, b in enumerate(y_):
        fig.add_annotation(text= '<b>' + b + '</b>', y=a, x=(100), xanchor='left', 
                font=dict(family="Courier New, monospace", size=16, color="#ffffff", ),  align='left', showarrow=False)

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
        fig.add_annotation(text='<b>' + str(temp) + '</b>', x=(x_ + max(total_spends)/15), y=a,
                font=dict(family="Courier New, monospace", size=16, color=colors[a], ), align="right", showarrow=False)

    fig.update_layout(xaxis_range=[0, max(total_spends) + max(total_spends)/7],  plot_bgcolor='rgba(255, 255, 255, 0.5)')
    fig.add_vline(x=total_spends[-1], line_width=2, line_dash="dash", line_color="red")
    fig.add_vline(x=max(total_spends), line_width=2, line_dash="dash", line_color="green")
    fig.update_layout(legend=dict(yanchor="top",y=1,xanchor="left",x=0.00,))
    fig.update_layout(height=450,width=690,)
    fig.update_xaxes(visible=True, showticklabels=True)
    fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
    fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')

    return fig

def update_layout_fig_5_1(fig, y_, delta,  total_spends, colors, count):
    
    fig.update_yaxes(ticksuffix=' ' ) 

    fig.update_layout(title="", xaxis_title="", yaxis_title="", legend_title="RFP Valuation (" + str(count) +")", height=470, template = 'ggplot2', )

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
        fig.add_annotation(text='<b>' + str(temp) + '</b>', x=(x_ + max(total_spends)/15), y=a, font=dict(family="Courier New, monospace", size=16, color=color, ), align="right", showarrow=False)
    fig.add_vline(x=total_spends[-1], line_width=2, line_dash="dash", line_color="red")
    fig.add_vline(x=max(total_spends), line_width=2, line_dash="dash", line_color="green")

    for a, b in enumerate(y_):
                fig.add_annotation(text= '<b>' + "{:,}".format(int(total_spends[a])) + '</b>', x= total_spends[a] - total_spends[-1]/100, y=a, xanchor='right',
                        font=dict(family="Courier New, monospace", size=16, color="#ffffff", ), showarrow=False)
    fig.update_layout(xaxis_range=[0, max(total_spends) + max(total_spends)/7])
    for a, b in enumerate(y_):
        fig.add_annotation(text= '<b>' + b + '</b>', y=a, x=(100),  xanchor='left',  font=dict(family="Courier New, monospace", size=16, color="#ffffff", ), align='left', showarrow=False)
    fig.update_layout(xaxis_range=[0, max(total_spends) + max(total_spends)/7],  plot_bgcolor='rgba(255, 255, 255, 0.5)',)
    fig.update_layout(title="", xaxis_title="", yaxis_title="", height=470, template = 'ggplot2', )

    fig.update_layout(legend=dict(yanchor="top",y=1,xanchor="left",x=0.00,))
    fig.update_layout(height=450,width=690,)
    fig.update_xaxes(visible=True, showticklabels=True)
    fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
    fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')


    return fig

def update_layout_fig_6(fig, plot_bg_color):

    fig.update_layout(title="", xaxis_title="", yaxis_title="Total Spend, $", legend_title="Category names", height=450, width=640, plot_bgcolor=plot_bg_color,)
    fig.update_xaxes(type='category',     tickformat="%Y", )
    fig.update_layout(xaxis=dict(tickformat="%Y"))          

    fig.update_layout(legend=dict( yanchor="top", y=1, xanchor="left", x=0.00))

    fig.update_yaxes(showline=True, linewidth=2, linecolor='white', mirror=True,   ticksuffix=' ') 
    fig.update_xaxes(visible=True, showticklabels=True)
    fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
    fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')

    return fig

def normalize_pricebook(app_rfp_df):

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


     
            alt_uom_df = pd.read_csv(str(BASE_DIR) + "/static/AGT alternative UOM.csv", error_bad_lines=False, dtype="unicode")
        
        
        if alt_uom_df[alt_uom_df['Material ID'] == str(material_id)].shape[0] > 0: #okay just one minute okay          
            al_un = alt_uom_df[alt_uom_df['Material ID'] == str(material_id)]['AUn'].tolist()[0]
            b_un = alt_uom_df[alt_uom_df['Material ID'] == str(material_id)]['BUn'].tolist()[0]
            counter = alt_uom_df[alt_uom_df['Material ID'] == str(material_id)]['Counter'].tolist()[0]
            denom = alt_uom_df[alt_uom_df['Material ID'] == str(material_id)]['Denom.'].tolist()[0]
            fraction = (int(counter) / int(denom))
    
            
            uom_group_list = ['PH', 'PK', 'PAC']  # holds uoms that represents group

            if app_rfp_df.iat[index, app_rfp_df.columns.get_loc('UOM_label')] != 1 and  (al_un in uom_group_list  and row['UOM'] in uom_group_list):                        
                    app_rfp_df.loc[index, '2021 rates'] = app_rfp_df.loc[index, '2021 rates'] / fraction
                    app_rfp_df.loc[index, '2020 rates'] = app_rfp_df.loc[index, '2020 rates'] / fraction
                    app_rfp_df.loc[index, 'UOM'] = b_un


    return app_rfp_df

def check_description_2(x, desc):
    return float(len(set(x).intersection(desc)) / len(set(x).union(desc)))

def find_a2a_non_pricebook(new_df):
    
    # Step - 1  (material id: yes   |   part number: yes)
    df_1 = new_df[(new_df['Material/Service No.'] != '#') & (new_df['Manufacturer Part No.'] != '#')].copy()
    new_df.loc[df_1.index.tolist(), 'Material/Service No.'] = new_df.loc[df_1.index.tolist(), 'Material/Service No.'] + ' (' + new_df.loc[df_1.index.tolist(), 'Manufacturer Part No.'] + ')'


    # Step - 2  (material id: no   |   part number: yes)
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

    
    # Step - 3  (material id: yes   |   part number: no)
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

    return new_df

def find_price_raisen_materials_pb(new_a2a):
    new_a2a['Average Price'] = new_a2a['Unit Price'].groupby(new_a2a['Material/Service No.']).transform('mean')
    new_a2a['delta'] = 0.0
    new_a2a['Increase percentage'] = 0.0
    new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax(), 'delta'] = new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['2021 rates'] - new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['Average Price']
    new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax(), 'Increase percentage'] = (new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['delta'] / new_a2a.loc[new_a2a.groupby('Material/Service No.')['PO Item Creation Date'].idxmax()]['Average Price']) * 100


    weight_df = pd.DataFrame(new_a2a.groupby('Material/Service No.')['PO Item Value (GC)'].sum())
    weight_df.rename(columns={'PO Item Value (GC)':'Item Total Spend'}, inplace=True)
    weight_df.reset_index(inplace=True)
    new_a2a = pd.merge(new_a2a, weight_df,  how='left', on='Material/Service No.')



    new_a2a['Item Weight'] = new_a2a['Item Total Spend'] / (new_a2a['PO Item Value (GC)'].sum())
    
    new_a2a['Increase percentage'] = new_a2a['Increase percentage'].apply(np.ceil)
    new_a2a['Average Price'] = round(new_a2a['Average Price'], 2)
    increase_df = new_a2a[new_a2a['Increase percentage'] > 0]
    increase_df.sort_values(by='PO Item Creation Date', inplace=True)
    unique_increase_df = increase_df.drop_duplicates(subset = ['Material/Service No.'], keep = 'last') 
    unique_increase_df['Proposed Price'] =  unique_increase_df['2021 rates'].astype('str')

    return unique_increase_df



def find_price_raisen_materials_non_pb(new_df):
    
    today = pd.to_datetime("today").normalize()
    one_year_before = today - datetime.timedelta(days=3*365)
    starting_date = one_year_before.replace(month=1, day=1)   # 2020-01-01
    one_year_before = today - datetime.timedelta(days=1*365)  # 2020-12-31
    ending_date = one_year_before.replace(month=12, day=31)
    new_df['PO Item Creation Date'] = pd.DatetimeIndex(new_df['PO Item Creation Date'])
    new_df = new_df[(new_df['PO Item Creation Date'] >= starting_date) & (new_df['PO Item Creation Date'] <= ending_date)]
    
    df_23 = new_df.groupby(['Material/Service No.']).filter(lambda x: len(x) > 1)
    df_23['PO Item Value (GC)'] = df_23['PO Item Value (GC)'].astype('float')

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
    increase_df_23['Increase percentage'] = increase_df_23['percentage'].apply(np.ceil)
    increase_df_23['From Pricebook'] = 'NO'
    
    increase_df_23['2021 rates'] = increase_df_23['Last Price']

    return increase_df_23









