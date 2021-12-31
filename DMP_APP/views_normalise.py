from .views_visual_1 import *

class DMP_normalise(DMP):
    @csrf_exempt
    def normalise(request):
        # Build the POST parameters
        if request.method == 'POST':
            try:
                    
                 #*cheking user status
                user_response = check_user_status(request)
                user_type = user_response['user_type']
                user_id = user_response['user_id']
                
                if user_type == 'customer':
                    
                    with Session(engine) as session:
                        user_session_with_data = session.query(USER_SESSION_WITH_DATA).filter(USER_SESSION_WITH_DATA.user_id==user_id).first()
    
                        test_df = pd.json_normalize(json.loads(user_session_with_data.result_data_app_copy))
                        result_data_all = pd.json_normalize( json.loads( user_session_with_data.result_data_all))                              
                        user_input_desc = user_session_with_data.user_input_desc     
                        all_headers = user_session_with_data.all_headers

                    print("user_id: ", user_id)
                    print("All_headers: ", all_headers)
                  
                    test_df['Converted Price'] = round(test_df['Converted Price'],2)
                    test_df = test_df[test_df['Unit Price'] != test_df['Converted Price']]
                    test_df = test_df[test_df['UoM_label'] != 1]         
                    json_records_all = test_df.to_json(orient='records')
                    app_selected_all_json = json.loads(json_records_all)
                    
                    response = JsonResponse({
                            'all_headers': all_headers,

                            'user_input_desc': user_input_desc,

                            'result_data_all':  result_data_all.to_json(orient='records'),
                            
                            'result_app_to_app':  app_selected_all_json,
                            
                            'app_selected_indexes':  test_df.index.tolist(),
                            
                            
                    
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
    def change_data(request):
        """
        this function for changing(normalize)  apple to apple data one by one 
        """

        if request.method =='POST':  
            #*cheking user status
            user_response = check_user_status(request)
            user_type = user_response['user_type']
            user_id = user_response['user_id']
            
            if user_type == "customer":
                # get all changing data as approve_list
                approve_list = request.POST.getlist('approve_list[]')


                with Session(engine) as session:
                    #  get user data with user session 
                    
                    user_session_with_data = session.query(USER_SESSION_WITH_DATA).filter(USER_SESSION_WITH_DATA.user_id == user_id).first()
                    
                       
                    result_data_app_copy_json = json.loads(user_session_with_data.result_data_app_copy)
                  
                    #get app_to_app data copy  which it is never changed   
                    app = pd.json_normalize(result_data_app_copy_json)
                    # app['PO Item Creation Date'] = pd.DatetimeIndex(app['PO Item Creation Date'])
                  
                    # changing unit price to new converted price one by one at copies data
                    for index in approve_list:
                        app.loc[app.index == int(index), 'Unit Price'] = app[app.index == int(index)]['Converted Price']


                    # assign copies data to working data
                    user_session_with_data.result_data_app = app.to_json(orient='records')
                    session.commit()
               

                response = JsonResponse({
                            'result_data_all':  'all',
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
            response = JsonResponse({
                    'result_data_all':  "",
                    })
            add_get_params(response)
            return response


    @csrf_exempt
    def change_data_all(request):
        if request.method =='POST':  
            #*cheking user status
            user_response = check_user_status(request)
            user_type = user_response['user_type']
            user_id = user_response['user_id']            
            if user_type == "customer":
                
                with Session(engine) as session:
                    #  get user data with user session 

                    user_session_with_data = session.query(USER_SESSION_WITH_DATA).filter(USER_SESSION_WITH_DATA.user_id== user_id).first()
                    
                       
                    result_data_app_copy_json = json.loads(user_session_with_data.result_data_app_copy)
                  
                    #get app_to_app data copy  which it is never changed   
                    app = pd.json_normalize(result_data_app_copy_json)
                    
                    
                    # app['PO Item Creation Date'] = pd.DatetimeIndex(app['PO Item Creation Date'])
                    app['Unit Price'] = app['Converted Price']
                  

                    # assign copies data to working data
                    user_session_with_data.result_data_app = app.to_json(orient='records')
                    session.commit()
                    
                response = JsonResponse({
                            'Answer':  'All Unit Price ssuccessfully replaced to Converted Price in app to app',
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
            response = JsonResponse({
                    'Answerr':  "This request is only for POST method !",
                              })
            add_get_params(response)
            return response
