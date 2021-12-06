from django.urls import path
from .views_visual_region import *
from .views_normalise_region import *
urlpatterns = [

  
    path('search_region/',DMP_Region.search_region),
    path('search_region_new/',DMP_Region.search_region_new),
    path('upload_file/',DMP_Region.upload_file),
    

    path('get_dates/',DMP_Region.get_dates),
    path('get_filter_data_region/',DMP_Region.get_filter_data_region),
    
    # path('visual_ajax_1_region/',DMP_Region.visual_ajax_1_region),
    path('visual_ajax_2_region/',DMP_Region.visual_ajax_2_region),
    path('visual_ajax_3_region/',DMP_Region.visual_ajax_3_region),
    # path('visual_ajax_4_region/',DMP_Region.visual_ajax_4_region),
    path('visual_ajax_5_region/',DMP_Region.visual_ajax_5_region),
    path('visual_ajax_6_region/',DMP_Region.visual_ajax_6_region),
    # path('visual_ajax_7_region/',DMP_Region.visual_ajax_7_region),
    # path('visual_ajax_8_region/',DMP_Region.visual_ajax_8_region),


    path('normalise_region/',DMP_Region_normalise.normalise_region),
    path('change_data_region/',DMP_Region_normalise.change_data_region),
    path('change_data_all_region/',DMP_Region_normalise.change_data_all_region),
    path('save_region_name/',DMP_Region_normalise.save_region_name),


]
