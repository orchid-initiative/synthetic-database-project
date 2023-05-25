def ethnicity(col):
    dic = {'hispanic':'E1',
            'nonhispanic': 'E2'}
    col = col.apply(lambda x: dic.get(x, '99'))
    return col

def gender(col):
    dic = {'M': 'M',
            'F': 'F'}
    col = col.apply(lambda x: dic.get(x, 'U'))
    return col 

def race(col):
    dic = {'native': 'R1',
            'asian': 'R2',
            'black': 'R3',
            'hawaiian': 'R4',
            'white': 'R5',
            'other': 'R9'}
    col = col.apply(lambda x: dic.get(x, '99'))
    return col

def disposition():
    l = ['01','02','03','04','05','06','07','20','21','43','50','51','61','62','63','64',
            '65','66','69','70','81','82','83','84','85','86','87','88','89','90','91',
            '92','93','94','95','00']
    return l