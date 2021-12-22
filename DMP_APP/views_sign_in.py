from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import numpy as np
import pandas as pd
import json
from django.core.mail import send_mail
from .helpers import *
from .custom_logic import *


@csrf_exempt
def register_user(request):
    if request.method =='POST':

        # * cheking user status
        # user_type="not_user"
        # user_type = check_user_status(request)['user_type']
            first_name = request.POST.get('first_name')
            last_name= request.POST.get('last_name')
            company_name = request.POST.get('company_name')
            mail_address = request.POST.get('mail_address')
            phone_number = request.POST.get('phone_number')
            message_to_us = request.POST.get('message_to_us')

            html_message ="<p> Request user register: <br/> first_name: "+first_name+ "<br/> last_name: "+last_name+ "<br/> company_name: "+company_name+"<br/> mail_address: "+mail_address+ "<br/> phone_number: "+phone_number+"<br/> message_to_us: "+message_to_us +"</p>"

            try:
                full_name = 'DMP BESTRACK'
                email = 'dmp.bestrack@gmail.com'
                message = 'I am here ' + ' ' + "new_message"
                time='time'

                #send_mail
                send_mail(
            "From: "+ full_name, #subject
            "User Email: "+email+"\n Request for discount: "+message,    #message
            email, #from email
            ["hebibliferid20@gmail.com","cavidan5889@gmail.com","dmp.prodigitrack@gmail.com", ""],     html_message=html_message)
            except Exception as e:
                print("mail sending error: ", e)


            print(first_name,last_name,company_name,mail_address,phone_number,message_to_us)
        
            response = JsonResponse({"response":"succesfully"})
            add_get_params(response)
            return response
            
    else:
        response = JsonResponse({'this_post': "DMP save app to app in search",})    
        add_get_params(response)
        return response