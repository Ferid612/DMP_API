from .views_visual_rfp_2 import *

class DMP_RFP_2_normalise(DMP_RFP_2):
    @csrf_exempt
    def normalise_rfp(request):
        a2a_conv=DMP_RFP_2.a2a_conv
        all_headers=DMP_RFP_2.all_headers

        test_df = pd.DataFrame(a2a_conv)

        test_df = test_df[test_df['UoM_label'] != 1]         
        test_df = test_df[test_df['Unit Price'] != test_df['Converted Price']]
        
        json_records_all=test_df.to_json(orient='records')
        DMP_RFP_2.app_selected_all_json=json.loads(json_records_all)
        
        if request.method =='POST':  
                response = JsonResponse({
                       
                            'result_app_to_app':  DMP_RFP_2.app_selected_all_json,
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
 
 
            #! bug in here
            app=DMP_RFP_2.app_to_app_rfp_after_search
            i=0
            for index in approve_list:
                app.loc[app.index == int(index), 'Unit Price'] = app[app.index == int(index)]['Converted Price']
                i += 1
            print('IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII: = ', i)
            
            DMP_RFP_2.app_to_app_rfp_after_search=app
 

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



            DMP_RFP_2.rfp_name=rfp_name
            DMP_RFP_2.rfp_vendor_name=vendor_name
            DMP_RFP_2.rfp_currency_name=currency
            DMP_RFP_2.rfp_region_name=region_name

            DMP_RFP_2.app_to_app_rfp_after_search['Unit Price'] = DMP_RFP_2.app_to_app_rfp_after_search['Converted Price']

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


            DMP_RFP_2.rfp_name=rfp_name
            DMP_RFP_2.rfp_vendor_name=vendor_name
            DMP_RFP_2.rfp_currency_name=currency
            DMP_RFP_2.rfp_region_name=region_name

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