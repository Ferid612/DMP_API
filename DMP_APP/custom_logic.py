from django.views.decorators.csrf import csrf_exempt
from .models import DMP_USERS,USER_SESSION, USER_SESSION_WITH_DATA
from django.http import JsonResponse
from DMP_API.settings import engine, BASE_DIR
from sqlalchemy.orm import Session
import  secrets
import traceback
import logging
import pandas as pd
user="Farid"
# user="Javidan"
import time
import schedule
from django.core.mail import send_mail
import os
print("i am working*****************************************************************4444")


def check_token_time():
    print("Cheking user session time...")

            
    with Session(engine) as session:
        user_session = session.query(USER_SESSION)

        for user in user_session:
            timeout = int(user.timeout)
            timeout -= 60
            user.timeout= timeout
            user_id = user.user_id
            
            print("user_id: " , user_id)
            print("user_time: " , timeout)
            
            
            
            if timeout < 0:
                user_session_with_data = session.query(USER_SESSION_WITH_DATA).filter(USER_SESSION_WITH_DATA.user_id == user_id)
                

                
                user_session_with_data.first().categories_in_result=""

                
                try:
                    os.remove(str(BASE_DIR) + "/static/all_dataframe_" + str(user_id) + ".csv")
                    # os.remove(str(BASE_DIR) + "/static/uploaded_historical_data_" + str(user_id) + ".csv")
                    os.remove(str(BASE_DIR) + "/static/df_org_" + str(user_id) + ".csv")
                except Exception as e:
                    pass
                               
                                
                new_token=secrets.token_hex(64)
                user.user_token= new_token
                user_session_with_data.first().user_token= new_token
                
                
                user.timeout= 1200
        session.commit()
        
        
  
flag_for_job = 1
@csrf_exempt 
def check_token_time_call(request):
    try:
        global flag_for_job
        if flag_for_job == 1:
            print("i call check_token_time")
            schedule.every(60).seconds.do(check_token_time)
            flag_for_job = 2
            while True:
                schedule.run_pending()
                time.sleep(1) 
        else:
            response = JsonResponse({      
            'answer':"cheking was started"
            })
            add_get_params(response)
            return response
            
    except Exception as e:
        my_traceback = traceback.format_exc()
        logging.error(my_traceback)
        print('\33[91m my_traceback_612', my_traceback,'\33[0m')
        response = JsonResponse({'error_text':str(e),
                                    'error_text_2':my_traceback
                                    })
        response.status_code = 505
        add_get_params(response)
        return response 

@csrf_exempt
def contact_us(request):
    try:
        full_name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        phone = request.POST.get('phone')
        print("Contact: ", full_name)
        print("Contact: ", email)
        print("Contact: ", message)
        print("Contact: ", phone)
        send_mail(
            "Contack-Us from: "+ full_name , #subject
            "User Email: "+'email'+" Request for discount: "+'message',    #message
            email, #from email
            ["hebibliferid20@gmail.com", "cavidan5889@gmail.com","dmp.bestrack@gmail.com", "prodigitrack.dmp@gmail.com"],  
            html_message=message)
    except Exception as e:
        print("mail sending error: ", e)
    response = JsonResponse({      
    'user_type':"user_type"
    })
    add_get_params(response)
    print("\033[92m Send mail SUCCESSFULLY" '\033[0m')
    return response


@csrf_exempt
def upload_sql_table(request):
    if request.method == 'POST':
        try:    
            
            #*cheking user status
            user_type=check_user_status(request)['user_type']  
            if user_type == 'customer' or user_type == 'supplier':
                user_type = "not_user"
                file_name = 'user_session_with_data_2'
                
                try:
                    input_user_name = request.POST.get('input_user_name')
                    input_token = request.POST.get('input_token')
                    
                    print("\033[92m input_user_name: " , input_user_name)
                    print("input_token: " , input_token, '\033[0m')
                    
                    # creat SQL TABLE With pandas dataframe
                    
                    with Session(engine) as session:
                        df = pd.read_csv(str(BASE_DIR) + '/static/data-1640345600058.csv')
                        df.to_sql(file_name, engine, if_exists='replace', index=False)



                except Exception as e:
                    my_traceback = traceback.format_exc()
                    logging.error(my_traceback)
                    print('\33[91m my_traceback_612', my_traceback,'\33[0m')
                    response = JsonResponse({'error_text':str(e),
                                                'error_text_2':my_traceback
                                                })
                    response.status_code = 505
                    add_get_params(response)
                    response['user_type'] = user_type
                    return response 

                try:            
                    with engine.connect() as con:
                        # query_1='ALTER TABLE '+file_name.lower()+ ' ALTER COLUMN '+file_name.lower() +'_ID SET NOT NULL;'            
                        query_2='ALTER TABLE '+file_name.lower()+ ' ADD PRIMARY KEY (user_id);'
                        # con.execute(query_1)  
                        con.execute(query_2)
                except Exception as e:
                    print("\033[93m eerror in primari key: ",e)



                response = JsonResponse({      
                'user_type':user_type
                })
                add_get_params(response)
                response['user_type'] = user_type
                
                
                print("\033[92m Uploaded to SQL DATABASE SUCCESSFULLY" '\033[0m')
                return response

            else:
                response = JsonResponse({'Answer': "You have have not access to this query.", })
                response.status_code=501
                add_get_params(response)
                return response
        except Exception as e:
            my_traceback = traceback.format_exc()
            logging.error(my_traceback)
            response = JsonResponse({'error_text':str(e),
                                        'error_text_2':my_traceback
                                        })
            response.status_code = 505
            
            add_get_params(response)
            return response 
    else:
        response = JsonResponse({'Answer': "Sorry this method running only POST method. Thanks from DRL", })
        add_get_params(response)
        return response


@csrf_exempt
def check_user_status(request):
    user_type = "not_user"
    user_id = -5
    try:
        input_user_name = request.POST.get('input_user_name')
        input_token = request.POST.get('input_token')
        
        print("\033[92m input_user_name: " , input_user_name)
        print("input_token: " , input_token, '\033[0m')
  
        with Session(engine) as session:
        
            sql_table= (
                session.query(
                    DMP_USERS.user_name,DMP_USERS.first_name,DMP_USERS.last_name,DMP_USERS.user_mail,
                    DMP_USERS.user_password,DMP_USERS.user_type,DMP_USERS.user_id,USER_SESSION.user_token)
                .select_from(DMP_USERS).join(USER_SESSION, USER_SESSION.user_id==DMP_USERS.user_id)
                .filter(DMP_USERS.user_name==input_user_name)
                .order_by(DMP_USERS.user_name))   
        
        
            sql_table = serializer(sql_table)
            
            user_token = sql_table[0]['user_token']
            if user_token == input_token:
                user_name = sql_table[0]['user_name']
                first_name = sql_table[0]['first_name']
                last_name = sql_table[0]['last_name']
                user_mail = sql_table[0]['user_mail']
                user_id = sql_table[0]['user_id']
                user_type = sql_table[0]['user_type']
            else:
                user_type="not_user"

        with Session(engine) as session:
            user_session = session.query(USER_SESSION)
            for user in user_session:
                if str(user.user_id) == str(user_id):
                    user.timeout = 1200
                    
            session.commit()
   
    except Exception as e:
        my_traceback = traceback.format_exc()
        logging.error(my_traceback)
        print('\33[91m my_traceback_612', my_traceback,'\33[0m')
        response = JsonResponse({'error_text':str(e),
                                    'error_text_2':my_traceback
                                    })
        response.status_code = 505
        add_get_params(response)
        response['user_type'] = user_type
        response['user_id'] = user_id
        
        return response 
    
    if user_type != "not_user":
        response = JsonResponse({      
            'user_name': user_name,
            'first_name': first_name,
            'last_name': last_name,
            'user_mail': user_mail,
            'user_id':user_id,
            'user_type':user_type
            })
    else:
            response = JsonResponse({      
            'user_name': "Unknown",
            'first_name': "Unknown",
            'last_name': "Unknown",
            'user_mail': "Unknown@gmail.com",
            'user_id':"Unknown_id",
            'user_type':user_type
            })
    
    add_get_params(response)
    response['user_type'] = user_type
    response['user_id'] = user_id
    
    return response
            
            
            
@csrf_exempt
def login(request):
    if request.method == 'POST':
        user_type = ""  
        user_mail = ""
        user_name = ""
        input_user_name = request.POST.get('input_user_name')
        input_password = request.POST.get('input_password')
        with Session(engine) as session:
            sql_table= (
                session.query(
                    DMP_USERS.user_name,DMP_USERS.user_mail, DMP_USERS.first_name,DMP_USERS.last_name,
                    DMP_USERS.user_password,DMP_USERS.user_type,DMP_USERS.user_id,USER_SESSION.user_token)
                .select_from(DMP_USERS).join(USER_SESSION, USER_SESSION.user_id==DMP_USERS.user_id)
                .filter(DMP_USERS.user_name==input_user_name)
                .order_by(DMP_USERS.user_name))   
            
            sql_table = serializer(sql_table)
            
            try:
                user_password = sql_table[0]['user_password']
        
                if user_password == input_password:
                    
                    user_name = sql_table[0]['user_name']
                    first_name = sql_table[0]['first_name']
                    last_name = sql_table[0]['last_name']
                    user_mail = sql_table[0]['user_mail']
                    user_id = sql_table[0]['user_id']
                    user_type = sql_table[0]['user_type']
                    
                else:
                    user_type = "not_user"
                            
            
            except Exception as e: 
                user_type = "not_user"
               

        if(user_type != 'not_user'):
            with Session(engine) as session:
                user_id = (session.query(DMP_USERS.user_id).select_from(DMP_USERS).filter(DMP_USERS.user_name==input_user_name))
                user_id = serializer(user_id)
                user_id = user_id[0]['user_id']
                
                new_token=secrets.token_hex(64)
                session.query(USER_SESSION).\
                    filter(USER_SESSION.user_id == user_id).\
                    update({'user_token': new_token})

                session.query(USER_SESSION_WITH_DATA).\
                    filter(USER_SESSION_WITH_DATA.user_id == user_id).\
                    update({'user_token': new_token})
                session.commit()
           
           

            response = JsonResponse({   
                'user_name': user_name,
                'first_name': first_name,
                'last_name': last_name,
                'user_mail': user_mail,
                'user_id':user_id,
                'user_type':user_type,
                'user_token':new_token,
                    })
            add_get_params(response)
            return response
        else:
            response = JsonResponse({'error_text':"You have not access"})
            response.status_code = 501
            add_get_params(response)
            return response 
    else:
        response = JsonResponse({'error_text':"This function working only with for POST methods"})
        response.status_code = 501
        add_get_params(response)
        return response





import json
from django.utils.html import escape


def escape_dict(data):
    if isinstance(data, list):
        for x, l in enumerate(data):
            if isinstance(l, dict) or isinstance(l, list):
                escape_dict(l)
            else:
                if l is not None:
                    data[x] = escape(l)

    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict) or isinstance(v, list):
                escape_dict(v)
            else:
                if v is not None:
                    data[k] = escape(v)
        return data


def escape_list(data):
    return list(map(lambda item: escape(item), data))


def input_json_sanitizer(request, parameter):
    if request.method == "GET":
        data = json.loads(request.GET.get(parameter))
    elif request.method == "POST":
        data = json.loads(request.POST.get(parameter))

    if isinstance(data, list):
        return escape_list(data)
    if isinstance(data, dict):
        return escape_dict(data)


def input_get_list_sanitizer(request, parameter):
    if request.method == "GET":
        data_list = request.GET.getlist(parameter)
    elif request.method == "POST":
        data_list = request.POST.getlist(parameter)

    return escape_list(data_list)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def serializer(rows) -> list:
    "Return all rows from a cursor as a dict"
    return [dict(row) for row in rows]


def single_table_serializer(model):
    exceptions = ['registry', 'classes', 'prepare', 'metadata']
    result = []
    for item in model:
        fields = {}
        for field in [dir_item for dir_item in dir(item) if not dir_item.startswith("_") and "collection" not in dir_item and dir_item not in exceptions]:
            data = item.__getattribute__(field)
            if field == 'well':
                try:
                    data = item.__getattribute__(field).well_name
                except AttributeError:
                    pass
            fields[field] = data
        result.append(fields)
    return result


def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def get_parametrization_marks(count: int) -> str:
    return " ".join(["?," if i != count else "?" for i in range(1, count + 1)])


def get_parametrization_values(data: dict) -> tuple:
    values = []
    for value in data.values():
        for item in value:
            values.append(item)
    return tuple(values)


def add_get_params(resp):
    resp["Access-Control-Allow-Origin"] = "*"
    resp["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS, PUT"
    resp["Access-Control-Allow-Headers"] = "X-Requested-With, Content-Type"


def filename_content_search(data, input_data):
    # Will be filled with data
    data_to_response = []

    # Main logic
    if input_data['FileName'] and not input_data['KeyWords']:
        if "and" in input_data['FileName']:
            file_names = input_data['FileName'].split('and')
            for row in data:
                if all(file_name.replace(' ', '') in row['report_name'].lower() for file_name in file_names):
                    data_to_response.append(row)
        elif "or" in input_data['FileName']:
            file_names = input_data['FileName'].split('or')
            for row in data:
                if any(file_name.replace(' ', '') in row['report_name'].lower() for file_name in file_names):
                    data_to_response.append(row)
        else:
            for row in data:
                if input_data['FileName'] in row['report_name'].lower():
                    data_to_response.append(row)

    elif not input_data['FileName'] and input_data['KeyWords']:
        if "and" in input_data['KeyWords']:
            key_words = input_data['KeyWords'].split('and')
            for row in data:
                try:
                    if all(key_word.replace(' ', '') in row['report_content'] for key_word in key_words):
                        data_to_response.append(row)
                except TypeError:
                    continue
        elif "or" in input_data['KeyWords']:
            key_words = input_data['KeyWords'].split('or')
            for row in data:
                try:
                    if any(key_word.replace(' ', '') in row['report_content'] for key_word in key_words):
                        data_to_response.append(row)
                except TypeError:
                    continue
        else:
            for row in data:
                try:
                    if input_data['KeyWords'] in row['report_content']:
                        data_to_response.append(row)
                except TypeError:
                    continue

    elif input_data['FileName'] and input_data['KeyWords']:
        if "and" in input_data['FileName'] and "and" in input_data['KeyWords']:
            file_names = input_data['FileName'].split('and')
            key_words = input_data['KeyWords'].split('and')
            for row in data:
                try:
                    if all(file_name.replace(' ', '') in row['report_name'].lower() for file_name in
                           file_names) and all(key_word.replace(' ', '') in row['report_content'] for key_word in key_words):
                        data_to_response.append(row)
                except TypeError:
                    continue
        elif "or" in input_data['FileName'] and "or" in input_data['KeyWords']:
            file_names = input_data['FileName'].split('or')
            key_words = input_data['KeyWords'].split('or')
            for row in data:
                try:
                    if any(file_name.replace(' ', '') in row['report_name'].lower() for file_name in
                           file_names) and any(key_word.replace(' ', '') in row['report_content'] for key_word in key_words):
                        data_to_response.append(row)
                except TypeError:
                    continue
        elif "or" in input_data['FileName'] and "and" in input_data['KeyWords']:
            file_names = input_data['FileName'].split('or')
            key_words = input_data['KeyWords'].split('and')
            for row in data:
                try:
                    if any(file_name.replace(' ', '') in row['report_name'].lower() for file_name in
                           file_names) and all(key_word.replace(' ', '') in row['report_content'] for key_word in key_words):
                        data_to_response.append(row)
                except TypeError:
                    continue
        elif "and" in input_data['FileName'] and "or" in input_data['KeyWords']:
            file_names = input_data['FileName'].split('and')
            key_words = input_data['KeyWords'].split('or')
            for row in data:
                try:
                    if all(file_name.replace(' ', '') in row['report_name'].lower() for file_name in
                           file_names) and any(key_word.replace(' ', '') in row['report_content'] for key_word in key_words):
                        data_to_response.append(row)
                except TypeError:
                    continue
        elif "and" in input_data['FileName'] and not ("or" in input_data['KeyWords'] or "and" in input_data['KeyWords']):
            file_names = input_data['FileName'].split('and')
            for row in data:
                try:
                    if all(file_name.replace(' ', '') in row['report_name'].lower() for file_name in file_names) and input_data['KeyWords'] in row['report_content']:
                        data_to_response.append(row)
                except TypeError:
                    continue
        elif "or" in input_data['FileName'] and not ("or" in input_data['KeyWords'] or "and" in input_data['KeyWords']):
            file_names = input_data['FileName'].split('or')
            for row in data:
                try:
                    if any(file_name.replace(' ', '') in row['report_name'].lower() for file_name in file_names) and input_data['KeyWords'] in row['report_content']:
                        data_to_response.append(row)
                except TypeError:
                    continue
        elif "and" in input_data['KeyWords'] and not ("or" in input_data['FileName'] or "or" in input_data['FileName']):
            key_words = input_data['KeyWords'].split('and')
            for row in data:
                try:
                    if input_data['FileName'] in row['report_name'].lower() and all(key_word.replace(' ', '') in row['report_content'] for key_word in key_words):
                        data_to_response.append(row)
                except TypeError:
                    continue
        elif "or" in input_data['KeyWords'] and not ("or" in input_data['FileName'] or "or" in input_data['FileName']):
            key_words = input_data['KeyWords'].split('or')
            for row in data:
                try:
                    if input_data['FileName'] in row['report_name'].lower() and any(key_word.replace(' ', '') in row['report_content'] for key_word in key_words):
                        data_to_response.append(row)
                except TypeError:
                    continue
        else:
            for row in data:
                try:
                    if input_data['FileName'] in row['report_name'].lower() and input_data['KeyWords'] in row['report_content']:
                        data_to_response.append(row)
                except TypeError:
                    continue

    return data_to_response
