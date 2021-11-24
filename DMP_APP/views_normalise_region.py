from .views_visual_region import *

class DMP_Region_normalise(DMP_Region):
    @csrf_exempt
    def normalise_region(request):
        a2a_conv=DMP_Region.a2a_conv
        all_headers=DMP_Region.all_headers

        test_df = pd.DataFrame(a2a_conv)

        test_df = test_df[test_df['UoM_label'] != 1]         
        test_df = test_df[test_df['Unit Price'] != test_df['Converted Price']]
        
        json_records_all=test_df.to_json(orient='records')
        DMP_Region.app_selected_all_json=json.loads(json_records_all)
        
        if request.method =='POST':  
                response = JsonResponse({
                       
                            'result_app_to_app':  DMP_Region.app_selected_all_json,
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
    def change_data_region(request):
        if request.method =='POST':  
            approve_list = request.POST.getlist('approve_list[]')
            remove_list = request.POST.getlist('remove_list[]')
 
 
            #! bug in here
            app=DMP_Region.app_to_app_region_after_search
            i=0
            for index in approve_list:
                app.loc[app.index == int(index), 'Unit Price'] = app[app.index == int(index)]['Converted Price']
                i += 1
            print('IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII: = ', i)
            
            DMP_Region.app_to_app_region_after_search=app
 

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
    def change_data_all_region(request):
        if request.method =='POST':
            region_name= request.POST.get('region_name')
            vendor_name= request.POST.get('vendor_name')
            currency= request.POST.get('currency')


            DMP_Region.region_name=region_name
            DMP_Region.region_vendor_name=vendor_name
            DMP_Region.region_currency_name=currency

            DMP_Region.app_to_app_region_after_search['Unit Price'] = DMP_Region.app_to_app_region_after_search['Converted Price']

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
    def save_region_name(request):
        if request.method =='POST':
            region_name= request.POST.get('region_name')
            vendor_name= request.POST.get('vendor_name')
            currency= request.POST.get('currency')


            DMP_Region.region_name=region_name
            DMP_Region.region_vendor_name=vendor_name
            DMP_Region.region_currency_name=currency

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