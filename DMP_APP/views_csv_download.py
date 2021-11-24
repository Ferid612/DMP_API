from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from datetime import datetime
from .views_visual_1 import *


@csrf_exempt
def download_csv(request):
    '''
    downloading material searching table result 
    which user see in the material_searching.html
    '''
    
    # * cheking user status
    user_type="not_user"
    user_type = check_user_status(request)
    
    if user_type == "customer":
        
        #* get material searching result data  
        df=DMP.result_data_all
        try:
            df.drop('level_0', axis=1, inplace=True)
        except Exception as e:
            pass
        
        # * change dataframe to csv file and return whith response 
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=App_to_app_{datetime.now().strftime("%Y.%m.%d_%H.%M")}.csv'  # alter as needed
        df.to_csv(path_or_buf=response, index= False)  # with other applicable parameters
        return response
    
    else:
        df=pd.DataFrame()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=YOU_HAVE_NOT_ACCESS_{datetime.now().strftime("%Y.%m.%d_%H.%M")}.csv'  # alter as needed
        df.to_csv(path_or_buf=response, index= False)  # with other applicable parameters
        return response
        
        