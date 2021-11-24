from django.core.mail import send_mail


def update_layout_fig_1_3(fig, plot_bg_color):
    fig.update_layout(xaxis_title="",)
    fig.update_layout( height=450, width=640,xaxis_title="",  yaxis_title="Price",plot_bgcolor=plot_bg_color,)
    fig.update_layout(legend=dict(yanchor="top",y=1,xanchor="left",x=0.00,))
    fig.update_yaxes( showline=True, linewidth=2, linecolor='white', mirror=True, showgrid=True, gridwidth=0.1, gridcolor='white', tickprefix='$', ticksuffix=' ') 


    fig.update_xaxes(visible=True, showticklabels=True)
    fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
    fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')
    fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')

    return fig

def update_layout_fig_2(fig, max_val, plot_bg_color):
    fig.update_xaxes(type='category',     tickformat="%Y", )
    fig.update_traces(marker_line_width=0, xperiodalignment="start")
    fig.update_layout(title="", xaxis_title="", yaxis_title="Total Spend, $", legend_title="Vendor names", height=450, width=640, plot_bgcolor=plot_bg_color,)

    # Essential!!!!!!!!!!!!!!!!!
    fig.update_layout(xaxis=dict(tickformat="%Y"))
    fig.update_layout(legend=dict(yanchor="top", y=1, xanchor="left", x=0.00 ))
    fig.update_yaxes( showline=True, linewidth=2, linecolor='white', mirror=True,  ticksuffix=' ') 
    fig.update_layout(yaxis_range=[0, 1.15*max_val])
    
    fig.update_xaxes(visible=True, showticklabels=True)
    fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
    fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')
    fig.update_layout(yaxis_range=[0, 1.15*max_val])

    return fig

def update_layout_fig_4(fig, spend, delta, y_, y_2, colors, plot_bg_color):

    new_spend = spend[:len(spend)-1]
    fig.add_vline(x=spend[-1], line_width=2, line_dash="dash", line_color="red")
    if max(new_spend) > spend[-1]:
        fig.add_vline(x=max(new_spend), line_width=2, line_dash="dash", line_color="green")

    for a, b in enumerate(delta):
        temp = ''
        if b != ' ':
            if len(b) > 0  and float(b) < 0 :
                temp = abs(float(b))
            elif len(b) != 0:
                temp = abs(float(b))

            if spend[a] > spend[-1]:
                x_ = max(spend)
            else:
                x_ = spend[-1]
        if a != len(delta)-1:
            temp = str(int(temp)) + '%' 
        fig.add_annotation(   
                text='<b>' + str(temp) +  '</b>',
                x = x_ + max(spend)/100,
                xanchor='left', 
                y=a,
                font=dict(
                    family="Courier New, monospace",
                    size=16,
                    color=colors[a],
                ),
                
                align="right",
    showarrow=False)

    for a, b in enumerate(y_):
        fig.add_annotation(
            text= '<b>' + "{:,}".format(int(spend[a])) + '</b>',
            x= spend[a] - spend[-1]/100,
            y=a,
            xanchor='right',
            font=dict(
                family="Courier New, monospace",
                size=16,
                color="#ffffff",
            ),
    showarrow=False)


    for a, b in enumerate(y_2):
        fig.add_annotation(
                text= '<b>' + b + '</b>',
                y=a,
                x=0,
                xanchor='left', 
                font=dict(
                    family="Courier New, monospace",
                    size=12,
                    color="#ffffff",
                    ),
                align='left',
    showarrow=False)


    fig.update_layout(
                title="",
                xaxis_title="",
                yaxis_title="",
                legend_title="Calculation criteria",
                width=680,
                height=450,
                plot_bgcolor=plot_bg_color,
                )

    fig.update_layout(legend=dict(
        yanchor="top",
        y=1,
        xanchor="left",
        x=0.00
    ))
    fig.update_layout(xaxis_range=[0, max(spend) + max(spend)/7.5])
                
    fig.update_xaxes(visible=True, showticklabels=True)
    fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
    fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')


    return fig

def recommendation_alg(prospoed_price_rec, lowest_purchase_price_rec, last_purchase_price_rec, average_purchase_price_rec, item_quantity, vendor_name, min_ven_name, min_ven_val, flag):

    
    savings = round((last_purchase_price_rec - prospoed_price_rec)*item_quantity, 2)
    best_savings = round((last_purchase_price_rec - min_ven_val)*item_quantity, 2)
    
    message_recomandation = ""
    if prospoed_price_rec < lowest_purchase_price_rec:
        if vendor_name == min_ven_name and flag == 1:
            message_recomandation='Price is lower than the lowest purchase price and is the best price among the proposed prices, hence recommended to accept. Savings for the next purchase batch is $' + str(savings)
        
        elif vendor_name == min_ven_name and flag == 0:
            message_recomandation='Price is lower than the lowest purchase price, hence recommended to accept. Savings for the next purchase batch is $' + str(savings)
        
        else:
            message_recomandation='Price is lower than the lowest purchase price, hence recommended to accept. Savings for the next purchase batch is $' + str(savings) + '. But vendor ' + str(min_ven_name) + ' proposed the best price: $' + str(round(min_ven_val, 2)) + ' among the proposed prices. Savings for the next purchase batch can be $' + str(best_savings) + ', if you accept offer from ' + min_ven_name + '.'


    elif prospoed_price_rec < last_purchase_price_rec and prospoed_price_rec < average_purchase_price_rec:
    
        
        if vendor_name == min_ven_name and flag == 1:
            message_recomandation='Price is lower than last and average purchase price and is the best price among the proposed prices, hence recommended to accept. Savings for the next purchase batch is $' + str(savings)
        
        elif vendor_name == min_ven_name and flag == 0:
            message_recomandation='Price is lower than last and average purchase price, hence recommended to accept. Savings for the next purchase batch is $' + str(savings) + '.'

        else:
            message_recomandation='Price is lower than the lowest purchase price, hence recommended to accept. Savings for the next purchase batch is $' + str(savings) + '. But vendor ' + str(min_ven_name) + ' proposed the best price: $' + str(round(min_ven_val, 2)) + ' among the proposed prices. Savings for the next purchase batch can be $' + str(best_savings) + ', if you accept offer from ' + min_ven_name + '.'
        

    elif prospoed_price_rec < last_purchase_price_rec and prospoed_price_rec > average_purchase_price_rec:
        lower_percentage = round((last_purchase_price_rec - prospoed_price_rec) / last_purchase_price_rec , 2) * 100
        higher_percentage = round((prospoed_price_rec - average_purchase_price_rec) / average_purchase_price_rec, 2) * 1000
        if lower_percentage > higher_percentage:
    
            if vendor_name == min_ven_name and flag == 1:
                message_recomandation= "Price is lower than last purchase " +  str(round(lower_percentage))  + "% and higher than average purchase price " +  str(round(higher_percentage))  + "%, and also is the best price among the proposed prices, hence recommended to accept. Savings for the next purchase batch is $" + str(savings)
            
            elif vendor_name == min_ven_name and flag == 0:
                message_recomandation="Price is lower than last purchase " +  str(round(lower_percentage))  + "% and higher than average purchase price " +  str(round(higher_percentage))  + "%, hence recommended to accept. Savings for the next purchase batch is $" + str(savings)
                
            else:
                message_recomandation = 'Price is lower than last purchase ' +  str(round(lower_percentage))  + '% and higher than average purchase price ' +  str(round(higher_percentage))  + '%,  hence recommended to accept. Savings for the next purchase batch is $' + str(savings) + '. But vendor ' + str(min_ven_name) + ' proposed the best price: $' + str(round(min_ven_val, 2)) + ' among the proposed prices. Savings for the next purchase batch can be $' + str(best_savings) + ', if you accept offer from ' + min_ven_name + '.'
            
        
    elif prospoed_price_rec > last_purchase_price_rec and prospoed_price_rec < average_purchase_price_rec:
        higher_percentage = round((prospoed_price_rec - last_purchase_price_rec) / last_purchase_price_rec , 2) * 100
        lower_percentage = round((average_purchase_price_rec - prospoed_price_rec) / average_purchase_price_rec, 2) * 100
        if lower_percentage > higher_percentage:
            
            if vendor_name == min_ven_name and flag == 1:
                message_recomandation='Price is lower than average purchase ' +  str(round(higher_percentage))   + ' and higher than last purchase price ' +  str(round(lower_percentage))  + '%, and is the best price among the proposed prices, hence recommended to accept. Savings for the next purchase batch is $' + str(savings)
            
            elif vendor_name == min_ven_name and flag == 0:
                message_recomandation='Price is lower than average purchase ' +  str(round(higher_percentage))   + ' and higher than last purchase price ' +  str(round(lower_percentage))  + '%, hence recommended to accept. Savings for the next purchase batch is $' +  + str(savings)
            
            else:
                message_recomandation='Price is lower than average purchase ' +  str(round(higher_percentage))   + ' and higher than last purchase price ' +  str(round(lower_percentage))  + '%, hence recommended to accept. Savings for the next purchase batch is $' + str(savings) + '. But vendor ' + str(min_ven_name) + ' proposed the best price: $' + str(round(min_ven_val, 2)) + ' among the proposed prices. Savings for the next purchase batch can be $' + str(best_savings) + ', if you accept offer from ' + min_ven_name + '.'



    return message_recomandation

def negotiation_alg(proposed_price_rec, lowest_purchase_price_rec, last_purchase_price_rec, average_purchase_price_rec, input_vendor_1):
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
    
    elif proposed_price_rec > last_purchase_price_rec and proposed_price_rec < average_purchase_price_rec:
        higher_percentage = ((proposed_price_rec - last_purchase_price_rec) / last_purchase_price_rec ) * 100
        lower_percentage = ((average_purchase_price_rec - proposed_price_rec) / average_purchase_price_rec) * 100
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
    
def find_colors_for_vlines(spend):

    delta = []
    colors = []
    for index, elem in enumerate(spend):
        if elem == 0:
            elem += 0.00001
        if index == len(spend)-1:
            delta.append(' ')
            colors.append('red')
        else:
            delta.append(str(abs(int(round(((elem - spend[-1])/elem)*100)))))
            if int(elem - spend[-1]) < 0:
                colors.append('red')
            else:
                colors.append('green')

    return delta, colors

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

def update_layout_fig_5_7(fig, plot_bg_color):
    fig.update_layout(yaxis_title="Price, $", xaxis_title="", plot_bgcolor=plot_bg_color,)
    fig.update_layout(legend=dict( yanchor="top", y=1, xanchor="left", x=0.00, ), height=200, )

    fig.update_layout(height=490,width=640,)
    fig.update_yaxes(showline=True, linewidth=2, linecolor='white', mirror=True,   ticksuffix=' ') 

    fig.update_xaxes(visible=True, showticklabels=True)
    fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
    fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')
    fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='rgb(230, 230, 230)')

    return fig
