from django.urls import path
from .views_visual_1 import *
from .views_normalise import *
from . import views_sign_in
from . import custom_logic


from . import views_csv_download
urlpatterns = [
    path('upload_file_historical/',DMP.upload_file_historical),
    path('check_file_historical/',DMP.check_file_historical),
    
    
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

    path('save_app_to_app_in_search/',DMP.save_app_to_app_in_search),

    path('login/', custom_logic.login),
    path('register_user/', views_sign_in.register_user),

    
]
