from django.urls import path
from .views_visual_rfp_2 import DMP_RFP_2
# from .views_normalise_rfp_2 import *
urlpatterns = [

    path('non_pricebook_search/',DMP_RFP_2.non_pricebook_search),
    
    path('visual_ajax_1_rfp/',DMP_RFP_2.visual_ajax_1_rfp),
    path('visual_ajax_2_rfp/',DMP_RFP_2.visual_ajax_2_rfp),
    path('visual_ajax_3_rfp/',DMP_RFP_2.visual_ajax_3_rfp),
    path('visual_ajax_4_rfp/',DMP_RFP_2.visual_ajax_4_rfp),
    path('visual_ajax_5_rfp/',DMP_RFP_2.visual_ajax_5_rfp),
    path('visual_ajax_6_rfp/',DMP_RFP_2.visual_ajax_6_rfp),

]
