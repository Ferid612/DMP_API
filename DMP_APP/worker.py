import pandas as pd

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