from django.urls import path
from .views_visual_rfp_2 import *
from .views_normalise_rfp_2 import *
urlpatterns = [

    path('non_pricebook_search/',DMP_RFP_2.non_pricebook_search),

    # path('search_rfp/',DMP_RFP_2.search_rfp),
    # path('search_rfp_new/',DMP_RFP_2.search_rfp_new),
    # path('upload_file/',DMP_RFP_2.upload_file),
    

    # path('get_dates/',DMP_RFP_2.get_dates),
    # path('get_filter_data_rfp/',DMP_RFP_2.get_filter_data_rfp),
    
    path('visual_ajax_1_rfp/',DMP_RFP_2.visual_ajax_1_rfp),
    path('visual_ajax_2_rfp/',DMP_RFP_2.visual_ajax_2_rfp),
    path('visual_ajax_3_rfp/',DMP_RFP_2.visual_ajax_3_rfp),
    path('visual_ajax_4_rfp/',DMP_RFP_2.visual_ajax_4_rfp),
    path('visual_ajax_5_rfp/',DMP_RFP_2.visual_ajax_5_rfp),
    path('visual_ajax_6_rfp/',DMP_RFP_2.visual_ajax_6_rfp),
    # path('visual_ajax_7_rfp/',DMP_RFP_2.visual_ajax_7_rfp),
    # # path('visual_ajax_8_rfp/',DMP_RFP_2.visual_ajax_8_rfp),



    # path('visual_ajax_1_region/',DMP_RFP_2.visual_ajax_1_region),
    # path('visual_ajax_2_region/',DMP_RFP_2.visual_ajax_2_region),
    # path('visual_ajax_3_region/',DMP_RFP_2.visual_ajax_3_region),
    # path('visual_ajax_4_region/',DMP_RFP_2.visual_ajax_4_region),
    # path('visual_ajax_5_region/',DMP_RFP_2.visual_ajax_5_region),
    # path('visual_ajax_6_region/',DMP_RFP_2.visual_ajax_6_region),




    # path('normalise_rfp/',DMP_RFP_2_normalise.normalise_rfp),
    # path('change_data_rfp/',DMP_RFP_2_normalise.change_data_rfp),
    # path('change_data_all_rfp/',DMP_RFP_2_normalise.change_data_all_rfp),
    # path('save_rfp_name/',DMP_RFP_2_normalise.save_rfp_name),


]
