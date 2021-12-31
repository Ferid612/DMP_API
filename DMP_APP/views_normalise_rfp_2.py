from .views_visual_rfp_2 import *

class DMP_RFP_2_normalise(DMP_RFP_2):
    @csrf_exempt
    
    def normalise_rfp(request):
        # Build the POST parameters
        if request.method == 'POST':
            try:    
                #*cheking user status
                
                user_response = check_user_status(request)
                user_type = user_response['user_type']
                user_id = user_response['user_id']
                
                
                if user_type == 'customer':
                                
                    
                    a2a_conv = pd.read_csv(str(BASE_DIR) + '/static/a2a_conv_np_' + str(user_id) + '.csv', error_bad_lines=False)
                    
                    all_headers=DMP_RFP_2.all_headers

                    test_df = pd.DataFrame(a2a_conv)

                    test_df = test_df[test_df['UoM_label'] != 1]         
                    test_df = test_df[test_df['Unit Price'] != test_df['Converted Price']]
                    
                    json_records_all=test_df.to_json(orient='records')
                    app_selected_all_json=json.loads(json_records_all)
                    
                    if request.method =='POST':  
                            response = JsonResponse({
                                
                                        'result_app_to_app':  app_selected_all_json,
                                        'app_selected_indexes':  test_df.index.tolist(),
                                        'all_headers': all_headers,
                                        'user_input_desc': ['user_input_desc','desc_input_user','input_user_desc'],
                                })
                            add_get_params(response)
                            return response
                    else:
                        response = JsonResponse({
                                'result_data_all':  "space data",
                                'user_input_desc':"space data",
                                'all_headers':"space data",
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
    def change_data_rfp(request):
  
        # Build the POST parameters
        if request.method == 'POST':
            try:    
                
                #*cheking user status
                user_response = check_user_status(request)
                user_type = user_response['user_type']
                user_id = user_response['user_id']
                
                if user_type == 'customer':
                    approve_list = request.POST.getlist('approve_list[]')
                    remove_list = request.POST.getlist('remove_list[]')
        
        
                    #! bug in here
                    
                    app = pd.read_csv(str(BASE_DIR) + "/static/app_to_app_rfp_after_search_2_" + str(user_id) + ".csv",error_bad_lines=False, parse_dates=['PO Item Creation Date'])
                    
                    i=0
                    for index in approve_list:
                        app.loc[app.index == int(index), 'Unit Price'] = app[app.index == int(index)]['Converted Price']
                        i += 1
                    print('IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII: = ', i)
                    

                    app.to_csv(str(BASE_DIR) + "/static/app_to_app_rfp_after_search_" + str(user_id) + ".csv", index = False)
        

                    #!bug finished


                    response = JsonResponse({
                                'result_data_all':  'all',
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
    def change_data_all_rfp(request):
        # Build the POST parameters
        if request.method == 'POST':
            try:    
                
                #*cheking user status
                user_response = check_user_status(request)
                user_type = user_response['user_type']
                user_id = user_response['user_id']
                
                if user_type == 'customer':
                    

                    app = pd.read_csv(str(BASE_DIR) + "/static/app_to_app_rfp_after_search_2_" + str(user_id) + ".csv",error_bad_lines=False, parse_dates=['PO Item Creation Date'])

                    app['Unit Price'] = app['Converted Price']
                    app.to_csv(str(BASE_DIR) + "/static/app_to_app_rfp_after_search_" + str(user_id) + ".csv", index = False)

                    response = JsonResponse({
                                'result_data_all':  'all',
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

