from .views_visual_rfp import *

class DMP_RFP_normalise(DMP_RFP):
    @csrf_exempt
    def normalise_rfp(request):
        a2a_conv=DMP_RFP.a2a_conv
        all_headers=DMP_RFP.all_headers

        test_df = pd.DataFrame(a2a_conv)

        test_df = test_df[test_df['UoM_label'] != 1]         
        test_df = test_df[test_df['Unit Price'] != test_df['Converted Price']]
        
        json_records_all=test_df.to_json(orient='records')
        DMP_RFP.app_selected_all_json=json.loads(json_records_all)
        
        if request.method =='POST':  
                response = JsonResponse({
                       
                            'result_app_to_app':  DMP_RFP.app_selected_all_json,
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

    @csrf_exempt
    def change_data_rfp(request):
        if request.method =='POST':  
            approve_list = request.POST.getlist('approve_list[]')
            remove_list = request.POST.getlist('remove_list[]')
 
            print('approve_listttttttttttttt: ',approve_list)
            #! bug in here
            DMP_RFP.app_to_app_rfp_after_search=DMP_RFP.app_to_app_rfp_after_search_2.copy()
            i=0
            for index in approve_list:
                DMP_RFP.app_to_app_rfp_after_search.loc[ DMP_RFP.app_to_app_rfp_after_search.index == int(index), 'Unit Price'] =  DMP_RFP.app_to_app_rfp_after_search[ DMP_RFP.app_to_app_rfp_after_search.index == int(index)]['Converted Price']
                i += 1
            
            print('iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii: ', i)

            #!bug finished


            response = JsonResponse({
                        'result_data_all':  'all',
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


    @csrf_exempt
    def change_data_all_rfp(request):
        if request.method =='POST':
            rfp_name= request.POST.get('rfp_name')
            vendor_name= request.POST.get('vendor_name')
            currency= request.POST.get('currency')
            region_name= request.POST.get('region_name')



            DMP_RFP.rfp_name=rfp_name
            DMP_RFP.rfp_vendor_name=vendor_name
            DMP_RFP.rfp_currency_name=currency
            DMP_RFP.rfp_region_name=region_name

        
            DMP_RFP.app_to_app_rfp_after_search.loc[DMP_RFP.app_to_app_rfp_after_search['UoM_label'] != -1, 'Unit Price'] = DMP_RFP.app_to_app_rfp_after_search_2[DMP_RFP.app_to_app_rfp_after_search_2['UoM_label'] != -1]['Converted Price']           
          
          
            response = JsonResponse({
                        'result_data_all':  'all',
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

    @csrf_exempt
    def save_rfp_name(request):
        if request.method =='POST':
            rfp_name= request.POST.get('rfp_name')
            vendor_name= request.POST.get('vendor_name')
            currency= request.POST.get('currency')
            region_name= request.POST.get('region_name')



            DMP_RFP.rfp_name=rfp_name
            DMP_RFP.rfp_vendor_name=vendor_name
            DMP_RFP.rfp_currency_name=currency
            DMP_RFP.rfp_region_name=region_name


            response = JsonResponse({
                        'result_data_all':  'all',
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




    # ! back old value 

    @csrf_exempt
    def get_data_back_rfp(request):
        if request.method =='POST':  
            
            DMP_RFP.app_to_app_rfp_after_search==DMP_RFP.app_to_app_rfp_after_search_2

            response = JsonResponse({
                        'result_data_all':  'all',
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
