from django.urls import path
from . import views_pricebook

from .views_pricebook import DMP_pricessbook 

urlpatterns = [

    path('pricebook_table/', DMP_pricessbook.pricebook_table),
    path('pricebook_save/', DMP_pricessbook.pricebook_save),
    path('get_all_customer/', DMP_pricessbook.get_all_customer),


]
