from django.urls import path
from .views_visual_rfp import *
from .views_normalise_rfp import *
urlpatterns = [
    
    path('upload_file_historical/',DMP_RFP.upload_file_historical),
    path('search_rfp/',DMP_RFP.search_rfp),
    path('search_rfp_new/',DMP_RFP.search_rfp_new),
    path('upload_file/',DMP_RFP.upload_file),
    

    path('get_dates/',DMP_RFP.get_dates),
    path('get_dates_rfp/',DMP_RFP.get_dates_rfp),
    path('get_filter_data_rfp/',DMP_RFP.get_filter_data_rfp),
    
    path('get_discount/',DMP_RFP.get_discount),
    path('pricebook_save/', DMP_RFP.pricebook_save),

    
    path('visual_ajax_1_rfp/',DMP_RFP.visual_ajax_1_rfp),
    path('visual_ajax_2_rfp/',DMP_RFP.visual_ajax_2_rfp),
    path('visual_ajax_3_rfp/',DMP_RFP.visual_ajax_3_rfp),
    path('visual_ajax_4_rfp/',DMP_RFP.visual_ajax_4_rfp),
    path('visual_ajax_5_rfp/',DMP_RFP.visual_ajax_5_rfp),
    path('visual_ajax_6_rfp/',DMP_RFP.visual_ajax_6_rfp),
    path('visual_ajax_7_rfp/',DMP_RFP.visual_ajax_7_rfp),
   
    # path('visual_ajax_8_rfp/',DMP_RFP.visual_ajax_8_rfp),



    path('visual_ajax_1_region/',DMP_RFP.visual_ajax_1_region),
    path('visual_ajax_2_region/',DMP_RFP.visual_ajax_2_region),
    path('visual_ajax_3_region/',DMP_RFP.visual_ajax_3_region),
    path('visual_ajax_4_region/',DMP_RFP.visual_ajax_4_region),
    path('visual_ajax_5_region/',DMP_RFP.visual_ajax_5_region),
    path('visual_ajax_6_region/',DMP_RFP.visual_ajax_6_region),




    path('normalise_rfp/',DMP_RFP_normalise.normalise_rfp),
    path('change_data_rfp/',DMP_RFP_normalise.change_data_rfp),
    path('change_data_all_rfp/',DMP_RFP_normalise.change_data_all_rfp),
    path('get_data_back_rfp/',DMP_RFP_normalise.get_data_back_rfp),

    path('save_rfp_name/',DMP_RFP_normalise.save_rfp_name),


 
    path('visual_ajax_recommendation_rfp/',DMP_RFP.recommendation),
    path('display_recommendation/',DMP_RFP.display_recommendation),



]
