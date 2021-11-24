from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .custom_logic import *
import json
import pandas as pd


class DMP_pricessbook:
    pricebook_table=[]

    @csrf_exempt
    def pricebook_table(request):
        pricebook_name=request.POST.get('pricebook_name')
        print("pricebook_name: ",pricebook_name)
        if user=="Farid":
            pricebook_table = pd.read_csv('C:\\Users\\DRL-Team\\Desktop\\DMP\\files\\4410014947_price_book.csv',error_bad_lines=False, dtype="unicode",  index_col=False)
        else:
            pricebook_table = pd.read_csv(r'C:\Users\OMEN 30L AD\Desktop\DMP\Data\4410014947_price_book.csv',error_bad_lines=False, dtype="unicode",  index_col=False)
    

        # pricebook_table = pd.read_csv(r'C:\Users\OMEN 30L AD\Desktop\DMP\Data\4410014947_price_book.csv',error_bad_lines=False, dtype="unicode",  index_col=False)

        try:
            del pricebook_table['index']
        except:
            pass


        try:
            pricebook_table.reset_index(inplace=True)
            pricebook_table['index'] = pricebook_table.index
            pricebook_table.rename(columns={'2021 rates':'Proposed Price'},inplace=True)
            pricebook_table.rename(columns={'2020 rates':'Last Price'},inplace=True)

        except Exception as e:
            print("error: " , e)
            pass

        DMP_pricessbook.pricebook_table=pricebook_table

    




        pricebook_columns=pricebook_table.columns.tolist()
        json_records_app=pricebook_table.to_json(orient='records')
        pricebook_table=json.loads(json_records_app)

        # pricebook_columns=pricebook_columns.reset_index().to_json(orient='records')

        response = JsonResponse({
                        'pricebook_columns':pricebook_columns,
                    'pricebook_table':  pricebook_table,
            })
        add_get_params(response)
        return response

    @csrf_exempt
    def pricebook_save(request):
        dict = json.loads(request.POST.get('key1'))
        pricebook_table=DMP_pricessbook.pricebook_table
        dict_df= pd.DataFrame(dict.items(), columns=['index', 'Proposed Price'])
        try:
            
            dict_df['index']=dict_df['index'].astype('str')
            
            pricebook_table['index']=pricebook_table['index'].astype('str')
            
            
            if 'Proposed Price' in pricebook_table.columns.tolist():
                del pricebook_table['Proposed Price']   
        except Exception as e:
            print("error: ",e)

        
        try:
            pricebook_table = pd.merge(pricebook_table, dict_df, how='left',on="index")
            del pricebook_table['index']


        except:
            print("error: ", e )
       
        pricebook_table.rename(columns={'Proposed Price':'2021 rates'},inplace=True)
        if user == "Farid":

            pricebook_table.to_csv(r'C:\Users\DRL-Team\Desktop\DMP\files\4410014947_price_book.csv',index=False)
        else:
            pricebook_table.to_csv(r'C:\Users\OMEN 30L AD\Desktop\DMP\4410014947_price_book_2.csv',index=False)

        print("dict", pricebook_table)    
        response = JsonResponse({
                    'pricebook_columns':"pricebook_columns",
                'pricebook_table':  "pricebook_table",
        })
        add_get_params(response)
        return response