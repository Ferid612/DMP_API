import math
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from fuzzywuzzy import fuzz
from .custom_logic import *
from . import views_visual_1
from django.views.decorators.csrf import csrf_exempt
from DMP_API.settings import BASE_DIR
import warnings
warnings.filterwarnings('ignore')

def get_required_columns():
    
    required_column_names = ["PO No.","PO Item No.","Incoterms Name", "Material/Service No.","PO Item Description", "Manufacturer Name", "Vendor Name", 
              "Manufacturer Part No.", "Long Description","PO Item Creation Date","PO Item Quantity", "PO Item Quantity Unit", "PO Item Value (GC)",
              "PO Item Value (GC) Unit",  "Product Category", "Product Category Description", "PO Status Name"]

    return required_column_names

def calc_distance(x1, y1, a, b, c):
    d = abs((a * x1 + b * y1 + c)) / (math.sqrt(a * a + b * b))
    return d

def find_best_k(K, Sum_of_squared_distances):
    max_val_idx = len(K) - 1
    # print('max_val: ', max_val_idx)
    # print('len(Sum_of_squared_distances): ', len(Sum_of_squared_distances))
    # print('Sum_of_squared_distances: ', Sum_of_squared_distances)
    # print('Your value is: ', Sum_of_squared_distances[max_val_idx])

    if max_val_idx > len(Sum_of_squared_distances) -1:
        max_val_idx = len(Sum_of_squared_distances) -1 
    a = Sum_of_squared_distances[0] - Sum_of_squared_distances[max_val_idx]
    b = K[max_val_idx] - K[0]
    c1 = K[0] * Sum_of_squared_distances[max_val_idx]
    c2 = K[max_val_idx] * Sum_of_squared_distances[0]
    c = c1 - c2
    
    distance_of_points_from_line = []
    for k in range(max_val_idx):
        distance_of_points_from_line.append(calc_distance(K[k], Sum_of_squared_distances[k], a,b, c))
    if len(distance_of_points_from_line) == 0:
        return 2

    return distance_of_points_from_line.index(max(distance_of_points_from_line))+1

def find_best_k_2(K, Sum_of_squared_distances):
    return 8

def big_cluster(result):
    cls_df_ = pd.DataFrame(result.groupby('Material/Service No.')['Unit Price'].mean())
    cls_df_.rename(columns={'Unit Price':'Average Price'}, inplace=True)
    cls_df_.reset_index(inplace=True)
    cls_df_['y_axis'] = 100
    cls_df = cls_df_.values
    
    Sum_of_squared_distances = []
    K = range(1,10)
    for num_clusters in K :
        kmeans = KMeans(n_clusters=num_clusters)
        kmeans.fit(cls_df)
        Sum_of_squared_distances.append(kmeans.inertia_)
        
    number_of_clusters =  find_best_k_2(K, Sum_of_squared_distances)
    if number_of_clusters > num_clusters:
         number_of_clusters = num_clusters 
    kmeans = KMeans(n_clusters=number_of_clusters)
    kmeans.fit(cls_df[:,1:])
    cls_df_['cluster'] = kmeans.labels_
    
    gb = cls_df_.groupby('cluster')
    key,grp = max(gb,key=lambda x: x[1].shape)
    idxs = grp['Material/Service No.'].tolist()
    return idxs
    # return  result['Material/Service No.'].value_counts().index.tolist()[1:2]
    
def check_description(desc, df, threshold, path, list_of_sources):
    a = pd.DataFrame(columns = df.columns)
    s1 = set(desc.replace(':',' ').replace(': ',' ').replace(',',' ').replace(', ',' ').replace(';',' ').replace('; ',' ').replace('-',' ').split())
    for index_i, row in enumerate(df[['PO Item Description', 'Long Description']].values):
        s2_small = set(row[0].replace(':',' ').replace(': ',' ').replace(',',' ').replace(', ',' ').replace(';',' ').replace('; ',' ').replace('-',' ').split())
        score_small = float(len(s1.intersection(s2_small)) / len(s1.union(s2_small)))
        
        s2_long = set(row[1].replace(':',' ').replace(': ',' ').replace(',',' ').replace(', ',' ').replace(';',' ').replace('; ',' ').replace('-',' ').split())
        score_long = float(len(s1.intersection(s2_long)) / len(s1.union(s2_long)))
        flag = 's'

        if score_small >= score_long:
            df.iat[index_i, df.columns.get_loc('score')] = score_small
        else:
            df.iat[index_i, df.columns.get_loc('score')] = score_long
            flag = 'l'
            
            
        if df.iat[index_i, df.columns.get_loc('score')] > threshold:
            df.iat[index_i, df.columns.get_loc('path')] = path
            df.iat[index_i, df.columns.get_loc('desc')] = str(flag)
            a = a.append(df.iloc[index_i])
            if path not in list_of_sources:
                
                list_of_sources[path] = list_of_general_sources[path]
    return a

def check_in_desc(aa, df, word):
    
    mask_s = df['desc_words_short'].apply(lambda x: word in x)
    a = df.loc[mask_s]

    mask_l = df['desc_words_long'].apply(lambda x: word in x)
    b = df.loc[mask_l]

    aa = aa.append(a)
    aa = aa.append(b)

    aa.loc[a.index.tolist(), 'desc'] = 's'
    aa.loc[b.index.tolist(), 'desc'] = 'l'
    
    return aa

def check_description_similarity(desc, df, threshold, path, list_of_sources):        
        desc_short_in = set(desc.replace(':',' ').replace(': ',' ').replace(',',' ').replace(', ',' ').replace(';',' ').replace('; ',' ').replace('-',' ').split())
        df['score_1'] = df['desc_words_short'].apply(lambda x: check_description_2(x, desc_short_in))
        df['score_2'] = df['desc_words_long'].apply(lambda x: check_description_2(x, desc_short_in))
        df['score'] = np.where(df['score_1'] > df['score_2'], df['score_1'], df['score_2'])
        df['flag'] = np.where(df['score_1'] > df['score_2'], 's', 'l')
        del df['score_1']
        del df['score_2']

        c = df[df['score'] > threshold]
        c['path'] = path 
        list_of_sources[path] = list_of_general_sources[path]

        return c

def check_description_2(x, desc):
    return float(len(set(x).intersection(desc)) / len(set(x).union(desc)))

def has_numbers(inputString):
    return any(char.isdigit() for char in inputString)

def generic_desc_sim(x, desc):
    return not has_numbers(set(desc).difference(set(x)))

def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False
types_of_UoM = { 'Weight': {'KG': 1, 'LO': 0.015, 'BAL': 217.72, 'LB':0.45},
                'Area':   {'M2': 1, 'JO': 1.6},
                'Length': {'M': 1, 'FT': 0.3048, 'LN': 1, 'LS': 1, 'IN': 0.0254, 'KM': 1000, 'ROL': 1, 'FOT': 0.3048},
                'Volume': {'L': 1, 'DR': 208.2, 'GAL': 3.79, 'M3': 1000, 'PL': 1, 'ML': 0.001, 'BTL': 0.75} }

list_of_general_sources = { '[1.1.1]': "Material/Services numbers and Manufacture part numbers match      (apple to apple)",
                            '[1.1.2]': "Material/Services numbers match but Manufacture part numbers don't match",
                            '[1.1.3]': "Material/Services numbers match but Manufacture part numbers don't match",
                            '[1.2.2]': "Material/Services numbers don't match but Material/Services numbers matches with Manufacture part number",
                            '[1.2.1.3]': "Material/Services numbers is in description and Manufacture part numbers match       (apple to apple)"  ,
                            '[1.2.1.4]': "Material/Services numbers is in description but Manufacture part numbers don't match",
                            '[1.2.1.5]': "Material/Services numbers is in description but Manufacture part numbers don't match",
                            '[1.3.2]': "Item numbers and manufacturer names match and similarity for description is more than fifty percent",
                            '[2.1.1]': "Manufacture part numbers and manufacture names match  (apple to apple)",
                            '[2.1.2]': "Manufacture part numbers match but manufacture names don't match",
                            '[2.1.3]': "Description base after fetching",
                            '[2.3.1]': "Manufacture part numbers don't match but Manufacture part numbers matches with Material/Services numbers",
                            '[2.4.1]': "Manufacture part number is in description",
                            '[3.1]': "Manufacture names match",
                            '[3.3.1]': "Manufacture name matches with Vendor name",
                            '[3.4.1]': "Manufacture name is in description",
                            '[4]': "Only descriptions are similar"
                            }
#! Data structureSection     
content={'success': True,
    'terms': 'https://currencylayer.com/terms',
    'privacy': 'https://currencylayer.com/privacy',
    'timestamp': 1626177124,
    'source': 'USD',
    'quotes': {'USDAED': 3.672995,
    'USDAFN': 81.061681,
    'USDALL': 103.347521,
    'USDAMD': 498.463046,
    'USDANG': 1.795788,
    'USDAOA': 643.062031,
    'USDARS': 96.10031,
    'USDAUD': 1.337835,
    'USDAWG': 1.8,
    'USDAZN': 1.69479,
    'USDBAM': 1.65166,
    'USDBBD': 2.019913,
    'USDBDT': 84.840815,
    'USDBGN': 1.64957,
    'USDBHD': 0.376895,
    'USDBIF': 1981.657884,
    'USDBMD': 1,
    'USDBND': 1.35252,
    'USDBOB': 6.897885,
    'USDBRL': 5.170898,
    'USDBSD': 1.000456,
    'USDBTC': 3.0264676e-05,
    'USDBTN': 74.502939,
    'USDBWP': 11.030013,
    'USDBYN': 2.567643,
    'USDBYR': 19600,
    'USDBZD': 2.016535,
    'USDCAD': 1.248375,
    'USDCDF': 2004.000651,
    'USDCHF': 0.916804,
    'USDCLF': 0.026943,
    'USDCLP': 743.430111,
    'USDCNY': 6.467395,
    'USDCOP': 3823.723146,
    'USDCRC': 619.257533,
    'USDCUC': 1,
    'USDCUP': 26.5,
    'USDCVE': 93.11664,
    'USDCZK': 21.665011,
    'USDDJF': 178.100932,
    'USDDKK': 6.28345,
    'USDDOP': 57.074213,
    'USDDZD': 134.524976,
    'USDEGP': 15.716602,
    'USDERN': 15.0035,
    'USDETB': 44.006469,
    'USDEUR': 0.844795,
    'USDFJD': 2.072597,
    'USDFKP': 0.721683,
    'USDGBP': 0.722255,
    'USDGEL': 3.144998,
    'USDGGP': 0.721683,
    'USDGHS': 5.917528,
    'USDGIP': 0.721683,
    'USDGMD': 51.149575,
    'USDGNF': 9821.645724,
    'USDGTQ': 7.75326,
    'USDGYD': 209.304486,
    'USDHKD': 7.76523,
    'USDHNL': 23.831239,
    'USDHRK': 6.330902,
    'USDHTG': 94.769288,
    'USDHUF': 301.379595,
    'USDIDR': 14479,
    'USDILS': 3.28031,
    'USDIMP': 0.721683,
    'USDINR': 74.533198,
    'USDIQD': 1459.616944,
    'USDIRR': 42104.999544,
    'USDISK': 123.770156,
    'USDJEP': 0.721683,
    'USDJMD': 152.06391,
    'USDJOD': 0.708996,
    'USDJPY': 110.2435,
    'USDKES': 108.000308,
    'USDKGS': 84.735704,
    'USDKHR': 4071.747061,
    'USDKMF': 415.449628,
    'USDKPW': 899.999894,
    'USDKRW': 1145.595004,
    'USDKWD': 0.30076,
    'USDKYD': 0.833671,
    'USDKZT': 427.729361,
    'USDLAK': 9497.027429,
    'USDLBP': 1512.633428,
    'USDLKR': 199.584262,
    'USDLRD': 171.550155,
    'USDLSL': 14.410057,
    'USDLTL': 2.95274,
    'USDLVL': 0.60489,
    'USDLYD': 4.512313,
    'USDMAD': 8.939333,
    'USDMDL': 18.052628,
    'USDMGA': 3775.317525,
    'USDMKD': 52.041109,
    'USDMMK': 1646.695041,
    'USDMNT': 2847.409137,
    'USDMOP': 8.00179,
    'USDMRO': 356.999828,
    'USDMUR': 42.502642,
    'USDMVR': 15.430201,
    'USDMWK': 810.322085,
    'USDMXN': 19.90989,
    'USDMYR': 4.192035,
    'USDMZN': 63.549919,
    'USDNAD': 14.409853,
    'USDNGN': 411.919901,
    'USDNIO': 34.939535,
    'USDNOK': 8.702031,
    'USDNPR': 119.20433,
    'USDNZD': 1.433675,
    'USDOMR': 0.384483,
    'USDPAB': 1.000372,
    'USDPEN': 3.966525,
    'USDPGK': 3.512701,
    'USDPHP': 50.022962,
    'USDPKR': 159.717437,
    'USDPLN': 3.86005,
    'USDPYG': 6824.246723,
    'USDQAR': 3.640979,
    'USDRON': 4.162701,
    'USDRSD': 99.277125,
    'USDRUB': 74.174704,
    'USDRWF': 1006.94163,
    'USDSAR': 3.750805,
    'USDSBD': 8.04185,
    'USDSCR': 13.965452,
    'USDSDG': 447.498384,
    'USDSEK': 8.60645,
    'USDSGD': 1.35225,
    'USDSHP': 0.721683,
    'USDSLL': 10250.000459,
    'USDSOS': 584.999906,
    'USDSRD': 21.113503,
    'USDSTD': 20536.048064,
    'USDSVC': 8.75304,
    'USDSYP': 1257.607232,
    'USDSZL': 14.580631,
    'USDTHB': 32.629737,
    'USDTJS': 11.409776,
    'USDTMT': 3.51,
    'USDTND': 2.785002,
    'USDTOP': 2.254599,
    'USDTRY': 8.592302,
    'USDTTD': 6.794183,
    'USDTWD': 27.995498,
    'USDTZS': 2319.982016,
    'USDUAH': 27.340562,
    'USDUGX': 3541.497771,
    'USDUSD': 1,
    'USDUYU': 44.058235,
    'USDUZS': 10653.585664,
    'USDVEF': 213830222338.07285,
    'USDVND': 23012.5,
    'USDVUV': 109.559402,
    'USDWST': 2.541762,
    'USDXAF': 553.942879,
    'USDXAG': 0.038301,
    'USDXAU': 0.000553,
    'USDXCD': 2.70255,
    'USDXDR': 0.702186,
    'USDXOF': 553.942879,
    'USDXPF': 101.050152,
    'USDYER': 250.297378,
    'USDZAR': 14.58803,
    'USDZMK': 9001.197529,
    'USDZMW': 22.679283,
    'USDZWL': 321.999928}}

def get_curency_data():
    return content['quotes']

def parallel_uom(material_id, identifier):
    if user == "Farid":
        if identifier == 1:
            a2a = pd.read_csv(str(BASE_DIR) + "\\static\\A2A_28_08_2021.csv")
        elif identifier == 2:
            a2a = pd.read_csv(str(BASE_DIR) + "\\static\\new_df_a2a.csv")
    else:
        if identifier == 1:
            a2a = pd.read_csv(r'C:\Users\HP\Desktop\DMP\DMP GIT\Data\A2A_28_08_2021.csv')
        elif identifier == 2:
            a2a = pd.read_csv(r'C:\Users\HP\Desktop\DMP\DMP GIT\Data\new_df_a2a.csv')
    
    a2a['PO Item Creation Date'] = pd.DatetimeIndex(a2a['PO Item Creation Date'])
    a2a = a2a[a2a['PO Item Creation Date'] >= '2018-01-01']

    try:
        del a2a['Unnamed: 0']
    except: 
        pass

    a2a_conv = pd.DataFrame(columns=a2a.columns,)
    temp_df = a2a.loc[a2a['Material/Service No.'] == material_id]
    
    temp_df = normalize(temp_df)
    
    return temp_df

def update_unit_price(in_data, index, desc_word_list, values_contains):
    flag = 0
    for word in desc_word_list:
        for value in values_contains:
            if value.lower() in word.lower() or word.lower().endswith('/pac') or word.lower().endswith('/pa') or word.lower().endswith('/p') :
                newstr = ''.join((ch if ch in '0123456789.-e' else ' ') for ch in word)
                listOfNumbers = [float(i) for i in newstr.split() if is_float(i)]

                if len(listOfNumbers) > 1:
                    try:
                        newstr =  word.lower()[word.lower().find(value.lower()):word.lower().find(value.lower())+len(value) + 5]
                        listOfNumbers = [float(i) for i in newstr.split() if is_float(i)]
                        if len(listOfNumbers) == 0:
                            listOfNumbers = re.findall(r'\d+', newstr)

                        if len(listOfNumbers) == 0:
                            newstr =  word.lower()[word.lower().find(value.lower())-5:word.lower().find(value.lower())]
                            listOfNumbers = [float(i) for i in newstr.split() if is_float(i)]
                            if len(listOfNumbers) == 0:
                                listOfNumbers = re.findall(r'\d+', newstr)

                    except:
                        continue
                if len(listOfNumbers) != 1:
                    continue
                each_count = listOfNumbers[0]
                # print('each count: ', each_count, '\n')
                in_data.iat[index, in_data.columns.get_loc('Unit Price')] /= float(each_count)
                in_data.iat[index, in_data.columns.get_loc('Converted Price')] /= float(each_count)
                in_data.iat[index, in_data.columns.get_loc('PO Item Quantity Unit')] = 'EA'
                in_data.iat[index, in_data.columns.get_loc('UoM_label')] = 1
                flag = 1
                break
        if flag == 1:
            break

    return in_data, flag

def normalize_1(in_data, types_of_UoM):

    i = 0
    for index, row in in_data.iterrows():
        for key in types_of_UoM:
            a = types_of_UoM[key]
            if  row['PO Item Quantity Unit'] in a.keys():
                print('YYYYYYYY')
                in_data.iat[i, in_data.columns.get_loc('Unit Price')] /= a[row['PO Item Quantity Unit']]
                in_data.iat[i, in_data.columns.get_loc('PO Item Quantity Unit')] = next(iter(a))
        i += 1
    
    return in_data

def normalization_based_alternative_uom(in_data):
    if user == 'Farid':
        alt_uom_df = pd.read_csv(str(BASE_DIR) + "\\static\\1.csv", error_bad_lines=False, dtype="unicode")
    else:
        alt_uom_df = pd.read_csv(str(BASE_DIR) + "\\static\\AGT alternative UOM.csv", error_bad_lines=False, dtype="unicode")

    alt_uom_df.loc[alt_uom_df['AUn'] == 'PAC', 'AUn'] = 'PH'
    for material_id in in_data['Material/Service No.'].unique().tolist(): 
        if alt_uom_df[alt_uom_df['Material ID'] == str(material_id)].shape[0] > 0:
            
            al_un = alt_uom_df[alt_uom_df['Material ID'] == str(material_id)]['AUn'].tolist()[0]
            b_un = alt_uom_df[alt_uom_df['Material ID'] == str(material_id)]['BUn'].tolist()[0]
            counter = alt_uom_df[alt_uom_df['Material ID'] == str(material_id)]['Counter'].tolist()[0]
            denom = alt_uom_df[alt_uom_df['Material ID'] == str(material_id)]['Denom.'].tolist()[0]
            fraction = (int(counter) / int(denom))
            
            
            in_data.loc[(in_data['Material/Service No.'] == material_id) & (in_data['UoM_label'] != 1) & (in_data['PO Item Quantity Unit'] == al_un), 'Unit Price'] = in_data[(in_data['Material/Service No.'] == material_id) & (in_data['UoM_label'] != 1) & (in_data['PO Item Quantity Unit'] == al_un)]['Unit Price'] / fraction            
            in_data.loc[(in_data['Material/Service No.'] == material_id) & (in_data['UoM_label'] != 1) & (in_data['PO Item Quantity Unit'] == al_un), 'Converted Price'] = in_data[(in_data['Material/Service No.'] == material_id) & (in_data['UoM_label'] != 1) & (in_data['PO Item Quantity Unit'] == al_un)]['Converted Price'] / fraction            
            in_data.loc[(in_data['Material/Service No.'] == material_id) & (in_data['UoM_label'] != 1) & (in_data['PO Item Quantity Unit'] == al_un), 'PO Item Quantity Unit'] = b_un
            in_data.loc[(in_data['Material/Service No.'] == material_id) & (in_data['UoM_label'] != 1) & (in_data['PO Item Quantity Unit'] == al_un), 'UoM_label'] = 1

    return in_data    

def get_inertias_and_K(x):
    Sum_of_squared_distances = []
    K = range(1,10)
    if len(x) < 10:
        K = range(1, len(x))

    for num_clusters in K :
        kmeans = KMeans(n_clusters=num_clusters)
        kmeans.fit(x.reshape(-1,1))  
        Sum_of_squared_distances.append(kmeans.inertia_)

    return K, Sum_of_squared_distances

def relabel_clusters(in_data):
    labels = in_data['Label'].value_counts().index.tolist()
    do_loop = True
    while do_loop == True:
        flag = 0
        test_df = in_data.groupby('Label')['Converted Price'].mean().to_frame()
        test_df.reset_index(inplace=True)
        test_df.rename(columns={'Converted Price': 'Average Price'}, inplace=True)
        min_label = test_df[test_df['Average Price'] == test_df['Average Price'].min()]['Label'].tolist()[0]
        min_average_price = test_df[test_df['Label'] == min_label]['Average Price'].tolist()[0]
        for label in labels:
            unit_prices = in_data[in_data['Label'] == label]['Converted Price'].tolist()
            for i in range(len(unit_prices)-1):
                for j in range(i+1, len(unit_prices)):
                    if abs(unit_prices[j] - unit_prices[i]) > min_average_price*2:
                        print('YYYYYY')
                        flag = 1
                        break
                if flag == 1:
                    break
            if flag == 0:   
                do_loop = False
                break

            if flag == 1:
                K, Sum_of_squared_distances = get_inertias_and_K(np.array(unit_prices))
                best_K =  find_best_k(K, Sum_of_squared_distances)
                kmeans = KMeans(n_clusters = best_K)
            
                kmeans.fit(np.array(unit_prices).reshape(-1,1))          
                in_data.loc[in_data['Label'] == label, 'Label'] = kmeans.labels_ + in_data[in_data['Label'] != 0]['Label'].max() + 1

            break
    
    return in_data, min_label

def update_converted_price(in_data, min_label):
    indices = in_data[in_data['Label'] == min_label].index.tolist()
    in_data.loc[indices, 'PO Item Quantity Unit'] = 'EA'

    list_of_labels = in_data['Label'].unique().tolist()
    list_of_labels

    a = set(list_of_labels) - set([min_label])
    a = list(a)

    m_1 = in_data[in_data['Label'] == min_label]['Converted Price'].mean()

    for i in a:
        test = in_data[in_data['Label'] == i]
        m_2 = test['Converted Price'].mean()
        frac, each_count = math.modf(m_2/m_1)
        if frac > 0.75:
            each_count += 1


        in_data.loc[test[test['UoM_label'] != 1].index.tolist(), 'Converted Price'] /= each_count
        in_data.loc[test[test['UoM_label'] != 1].index.tolist(), 'PO Item Quantity Unit'] = 'EA'

    return in_data

def normalize(in_data):
   
    in_data['Converted Price'] = in_data['Unit Price']
    in_data.reset_index(inplace=True, drop=True)

    in_data = normalize_1(in_data, types_of_UoM)
        

    in_data['Converted Price'] = in_data['Unit Price']
    in_data.reset_index(inplace=True, drop=True)

    if in_data.shape[0] > 0:
        values_contains = ['pack of', '/pack', 'pk of', '/pk', 'pkt of', '/pkt', 'per pack', 'drum of', '/ft']
        values_ends = ['/pac', '/pa', '/p']
        in_data['UoM_label'] = 0

        for index, row in in_data.iterrows():
            short_desc = row['PO Item Description'].split(',')
            long_desc = row['Long Description'][:40].split(',') 
        
            if row['PO Item Quantity Unit'] in ['EA', 'PH', 'BOX', 'PK']:
                flag = 0
                desc_word_list  = short_desc            
                in_data, flag = update_unit_price(in_data, index, desc_word_list, values_contains)
                    
                if flag == 0:                      
                    if fuzz.partial_ratio(short_desc, long_desc) >= 50:
                        desc_word_list  = row['Long Description'].split(',')
                        in_data, flag = update_unit_price(in_data, index, desc_word_list, values_contains)

        material_id = in_data['Material/Service No.'].unique().tolist()[0]
        if str(material_id) == '382515':
            print('BEFOREeeeeeeeeeeeeeeeeeeee :  ', in_data.loc[(in_data['Material/Service No.'] == material_id) & (in_data['UoM_label'] != 1)]['Unit Price'])
        
        in_data = normalization_based_alternative_uom(in_data)
                        
        if str(material_id) == '382515':
            print('AFTERrrrrrrrrrrrrrrrrrrrrr :  ', in_data.loc[(in_data['Material/Service No.'] == material_id) & (in_data['UoM_label'] != 1)]['Unit Price'])



        if in_data.shape[0] > 1:
            x = in_data['Converted Price'].values
            K, Sum_of_squared_distances = get_inertias_and_K(x)
            best_K =  find_best_k(K, Sum_of_squared_distances)
            
            kmeans = KMeans(n_clusters = best_K)
            kmeans.fit(x.reshape(-1,1))  
            in_data['Label'] = kmeans.labels_
            
            in_data, min_label = relabel_clusters(in_data)
            in_data = update_converted_price(in_data, min_label)
        
        in_data['Converted Price'] =round(in_data['Converted Price'],2)
        in_data['Unit Price'] =round(in_data['Unit Price'],2) 
        
    else:
        in_data['Converted Price'] = in_data['Unit Price']
        in_data['UoM_label'] = 0
        in_data['Label'] = -1
        
    return in_data      

def append_as_a2a(a2a, path):
    a2a['score'] = 0.9
    a2a['path'] = path
    a2a['desc'] = 'm_p'
    return a2a

@csrf_exempt
def upload_file_helpers(request): 
    try:
        for index, file_ts in enumerate(request.FILES.getlist('input_files')):
            try:
                csv_file_name=file_ts.name            
                rfp_file=pd.read_csv(file_ts.file, error_bad_lines=False,  dtype={'PO Item Quantity': 'float64', 'PO Item Value (GC)': 'float64',})

            except Exception as e:
                continue
    except:
        print("Not successfully", "file_ts.name")    
    return rfp_file

@csrf_exempt
def get_dates(request): 
    if request.method =='POST':
        input_min_date= request.POST.get('input_min_date')
        input_max_date= request.POST.get('input_max_date')

    return input_min_date, input_max_date

    
def preprocess_search_data(df, input_region):
    
    df=df[df['Region']==input_region]

    df = df[df['PO Item Deletion Flag'] != 'X']
    df = df[(df['PO Status Name'] != 'Deleted') & (df['PO Status Name'] != 'Held')]

    df['PO Item Description'] = df['PO Item Description'].replace(np.nan, ' ', regex=True)    
    df['Long Description'] = df['Long Description'].replace(np.nan, ' ', regex=True)    

    df = df[get_required_columns()]
    df['PO Item Value (GC)'].apply(lambda x : "{:,}".format(x))
    
    df['score'] = -1.0
    df['path'] = ''
    df['desc'] = ''
    list_of_sources = {}

    df['desc_words_short'] = [short_desc.replace(':',' ').replace(': ',' ').replace(',',' ').replace(', ',' ').replace(';',' ').replace('; ',' ').replace('-',' ').split() for short_desc in df['PO Item Description'].values]
    df['desc_words_long'] = [long_desc.replace(':',' ').replace(': ',' ').replace(',',' ').replace(', ',' ').replace(';',' ').replace('; ',' ').replace('-',' ').split() for long_desc in df['Long Description'].values]
    
    df['Manufacturer Part No.'] = df['Manufacturer Part No.'].str.replace(' ', '')
    df['Manufacturer Name'] = df['Manufacturer Name'].str.replace(' ', '')

    return df


    









