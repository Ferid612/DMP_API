from django.views.decorators.csrf import csrf_exempt
from .models import DMP_USERS,USER_SESSION
from django.http import JsonResponse
from DMP_API.settings import engine, BASE_DIR
from sqlalchemy.orm import Session
import  secrets


user="Farid"
# user="Javidan"

@csrf_exempt
def check_user_status(request):
    user_type = "not_user"
    
    try:
        input_user_name = request.POST.get('input_user_name')
        input_token = request.POST.get('input_token')

       
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
                    
    except Exception as e:
        user_type="not_user"
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
