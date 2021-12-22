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
    user_type = check_user_status(request)['user_type']
    
    if user_type == "customer":
        
        #* get material searching result data 
        
        with Session(engine) as session:
            input_token = request.POST.get('input_token')
            user_session = session.query(USER_SESSION).filter(USER_SESSION.user_token==input_token).first()
            result_data_all_json = json.loads(user_session.result_data_all)
            result_data_all = pd.json_normalize(result_data_all_json)
      
        df = result_data_all
        try:
            df.drop('level_0', axis=1, inplace=True)
        except Exception as e:
            pass
        
        # * change dataframe to csv file and return whith response 
        response = HttpResponse(content_type='text/csv')
        # response['Content-Disposition'] = f'attachment; filename=App_to_app_{datetime.now().strftime("%Y.%m.%d_%H.%M")}.csv'  # alter as needed
        response['Content-Disposition'] = f'attachment; filename=App_to_app.csv'  # alter as needed
        
        df.to_csv(path_or_buf=response, index= False)  # with other applicable parameters
        return response
    
    else:
        df=pd.DataFrame()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=YOU_HAVE_NOT_ACCESS.csv'  # alter as needed
        df.to_csv(path_or_buf=response, index= False)  # with other applicable parameters
        return response
        
        