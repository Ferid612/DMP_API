from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .custom_logic import *
from .models import *

import json
import pandas as pd


class DMP_pricessbook:
    pricebook_table=[]

    @csrf_exempt
    def get_all_customer(request):
        # Build the POST parameters
        if request.method == 'POST':
            try:    
                #*cheking user status
                user_type=check_user_status(request)['user_type']  
                if user_type == 'supplier':
                    # get supplier data for getting customers which supplier have connection with it
                    input_user_name = request.POST.get('input_user_name')
                    input_token = request.POST.get('input_token')
                    
                    #get supplier id    
                    with Session(engine) as session:
                    
                        user_table_query= (
                            session.query(
                                DMP_USERS.user_id,USER_SESSION.user_token,DMP_USERS.supplier_id)
                            .select_from(DMP_USERS)\
                            .join(USER_SESSION, USER_SESSION.user_id==DMP_USERS.user_id)
                            .filter(DMP_USERS.user_name==input_user_name)
                            .order_by(DMP_USERS.user_name))   
                        
                        user_table_dict = serializer(user_table_query)
                        supplier_id=user_table_dict[0]['supplier_id']
                        
                        # get customers which have connection supplier
                        customer_query = session.query(Customer.customer_name).select_from(Customer)\
                        .join(SupplierCustomerConnection, Customer.customer_id== SupplierCustomerConnection.customer_id)\
                        .filter(SupplierCustomerConnection.supplier_id==supplier_id)\
                        .distinct()
                    
                    
                        # get pricebooks which it is's supplier
                        pricebook_query = session.query(Customer.customer_name,Pricebook.pricebook_name,Pricebook.pricebook_location).select_from(Customer)\
                        .join(PricebookConnection, Customer.customer_id== PricebookConnection.customer_id)\
                        .join(Pricebook,Pricebook.pricebook_id==PricebookConnection.pricebook_id)\
                        .filter(PricebookConnection.supplier_id==supplier_id)\
                        .distinct()
                    
                    customer_name_list = pd.DataFrame(serializer(customer_query))['customer_name'].to_json(orient='records')
                    pricebook_table = pd.DataFrame(serializer(pricebook_query)).to_json(orient='records')
                    
                    print(customer_name_list)
                    print(pricebook_table)
  
  
                    response = JsonResponse({
                            'customer_list':customer_name_list,
                            'pricebook_table':  pricebook_table,
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
    def pricebook_table(request):
        # Build the POST parameters
        if request.method == 'POST':
            try:    
                #*cheking user status
                user_type=check_user_status(request)['user_type']  
                if user_type == 'supplier':
                                    
                    pricebook_name=request.POST.get('pricebook_name')
                    print("pricebook_name: ",pricebook_name)
                
                    pricebook_table = pd.read_csv(str(BASE_DIR) + "/static/pricebooks/"+pricebook_name+".csv",error_bad_lines=False, dtype="unicode",  index_col=False)
                    # pricebook_table = pd.read_csv(r'C:\Users\OMEN 30L AD\Desktop\DMP\Data\4410014947_price_book.csv',error_bad_lines=False, dtype="unicode",  index_col=False)

                    try:
                        del pricebook_table['index']
                    except:
                        pass


                    try:
                        pricebook_table.reset_index(inplace=True)
                        pricebook_table['index'] = pricebook_table.index
                        pricebook_table.rename(columns={'2021 rates':'Proposed Price'},inplace=True)
                        pricebook_table.rename(columns={'2020 rates':'Last Price'},inplace=True)

                    except Exception as e:
                        print("error: " , e)
                        pass

                    DMP_pricessbook.pricebook_table=pricebook_table


                    pricebook_columns=pricebook_table.columns.tolist()
                    json_records_app=pricebook_table.to_json(orient='records')
                    pricebook_table=json.loads(json_records_app)

                    # pricebook_columns=pricebook_columns.reset_index().to_json(orient='records')

                    response = JsonResponse({
                                'pricebook_columns': pricebook_columns,
                                'pricebook_table':  pricebook_table,
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
    def pricebook_save(request):
        # Build the POST parameters
        if request.method == 'POST':
            try:    
                #*cheking user status
                user_type=check_user_status(request)['user_type']  
                if user_type == 'supplier':
                                    
                    dict = json.loads(request.POST.get('key1'))
                    pricebook_table=DMP_pricessbook.pricebook_table
                    dict_df= pd.DataFrame(dict.items(), columns=['index', 'Proposed Price'])
                    try:
                        
                        dict_df['index']=dict_df['index'].astype('str')
                        
                        pricebook_table['index']=pricebook_table['index'].astype('str')
                        
                        
                        if 'Proposed Price' in pricebook_table.columns.tolist():
                            del pricebook_table['Proposed Price']   
                    except Exception as e:
                        print("error: ",e)

                    
                    try:
                        pricebook_table = pd.merge(pricebook_table, dict_df, how='left',on="index")
                        del pricebook_table['index']


                    except:
                        print("error: ", e )
                
                    pricebook_table.rename(columns={'Proposed Price':'2021 rates'},inplace=True)
                    pricebook_table.to_csv(str(BASE_DIR) + "/static/4410014947_price_book.csv",index=False)

                    print("dict", pricebook_table)    
                    response = JsonResponse({
                                'pricebook_columns':"pricebook_columns",
                            'pricebook_table':  "pricebook_table",
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
