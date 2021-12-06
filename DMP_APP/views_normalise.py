from .views_visual_1 import *

class DMP_normalise(DMP):
    @csrf_exempt
    def normalise(request):
        # Build the POST parameters
        if request.method == 'POST':
            try:
                    
                #*cheking user status
                user_type=check_user_status(request)['user_type']  
                if user_type == 'customer':
                    
                    all_dataframes_from_searching=DMP.all_dataframes_from_searching
                    all_headers=DMP.all_headers

                    test_df = pd.DataFrame(all_dataframes_from_searching['result_app_to_app'])
                    test_df['Converted Price']=round(test_df['Converted Price'],2)
                    
                    test_df = test_df[test_df['Unit Price'] != test_df['Converted Price']]
                    test_df = test_df[test_df['UoM_label'] != 1]         
                    
                    json_records_all=test_df.to_json(orient='records')
                    DMP.app_selected_all_json=json.loads(json_records_all)
                    
                    response = JsonResponse({
                            'result_data_all':  all_dataframes_from_searching['result_data_all'],
                                'result_app_to_app':  DMP.app_selected_all_json,
                                'app_selected_indexes':  test_df.index.tolist(),
                            'user_input_desc': all_dataframes_from_searching['user_input_desc'],
                            'all_headers': all_headers,
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
        if request.method =='POST':  
            # * cheking user status
            user_type="not_user"
            user_type = check_user_status(request)['user_type']
             
            if user_type == "customer":
                approve_list = request.POST.getlist('approve_list[]')
                remove_list = request.POST.getlist('remove_list[]')
                app=DMP.result_data_app_copy.copy()

                for index in approve_list:
                    app.loc[app.index == int(index), 'Unit Price'] = app[app.index == int(index)]['Converted Price']

                DMP.result_data_app=app
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
            # * cheking user status
            user_type = "not_user"
            user_type = check_user_status(request)['user_type']
            
            if user_type == "customer":
                app=DMP.result_data_app_copy.copy()
                app['Unit Price'] = app['Converted Price']
                DMP.result_data_app=app
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
                    'Answerr':  "This request is only for POST method !",
                              })
            add_get_params(response)
            return response
