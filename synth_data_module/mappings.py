def ethnicity(col):
    dic = {'hispanic': 'E1',
           'nonhispanic': 'E2'}
    col = col.apply(lambda x: dic.get(x, '99'))
    return col


def gender(col):
    dic = {'M': 'M',
           'F': 'F'}
    col = col.apply(lambda x: dic.get(x, 'U'))
    return col


def payer_category(df):
    govdic = {'medicare': '01',
              'medi-cal': '02',
              'medical': '02',
              # Designate dual eligible payers as medicare:
              'dual eligible': '01',
              # County Indigent Programs : '05',
              }
    privdic = {
            # Workers’ Compensation : '04',
            # Other Indigent : '07',
            }
    # If Gov owned payer identify if medicare or medical, otherwise return 06 ('OTHER Gov'). lower match for accuracy
    if df[2] in ['GOVERNMENT', ]:
        category = govdic.get(df[1].lower(), '06')
    # If Private owned, look up specific designations (to be added as necessary) otherwise return 03 = private coverage
    elif df[2] in ['PRIVATE', ]:
        category = privdic.get(df[1], '03')
    # Return Self Pay if NO_INSURANCE
    elif df[2] in ['NO_INSURANCE', ]:
        category = '08'
    else:
        category = '09'
    return category


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
    opts = ['01', '02', '03', '04', '05', '06', '07', '20', '21', '43', '50', '51', '61', '62', '63', '64', '65', '66',
            '69', '70', '81', '82', '83', '84', '85', '86', '87', '88', '89', '90', '91', '92', '93', '94', '95', '00']
    return opts
