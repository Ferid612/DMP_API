from django.urls import path
from .views_visual_1 import DMP
from .views_normalise import DMP_normalise
from . import views_sign_in
from . import custom_logic


from . import views_csv_download
urlpatterns = [
    path('upload_file_historical/',DMP.upload_file_historical),
    path('check_file_historical/',DMP.check_file_historical),
    path('check_token_time_call/',custom_logic.check_token_time_call),
    path('check_user_status/',custom_logic.check_user_status),
    path('contact_us/',custom_logic.contact_us),
    
    path('upload_sql_table/',custom_logic.upload_sql_table),
    
    
    
    
    path('normalise/',DMP_normalise.normalise),
    path('change_data/',DMP_normalise.change_data),
    path('change_data_all/',DMP_normalise.change_data_all),


    path('download_csv/',views_csv_download.download_csv),


    path('search/',DMP.searching),
    path('get_filter_data/',DMP.get_filter_data),
    path('visual_ajax_1_2_3/',DMP.visual_ajax_1_2_3),
    path('visual_ajax_4/',DMP.visual_ajax_4),
    path('visual_ajax_5_7/',DMP.visual_ajax_5_7),
    path('visual_ajax_6/',DMP.visual_ajax_6),



    
    path('login/', custom_logic.login),
    path('register_user/', views_sign_in.register_user),

    
]
