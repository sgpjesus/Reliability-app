"""
The extractor module holds the extractor methods, i.e. methods for extracting data from various sources, like Excel, txt,
and so on.
"""

import os
import pandas as pd
import sys
import numpy as np


def parser(file_path, cols_expected_table, integer_cols, client_id):
    """
    Data parser from various files. At the moment the only supported formats are XLSX, or TXT. The main idea is that it
    reads a data file looking for the column names which must be inside that file. The user has to specify which columns
    are to be considered as integers and the client_id.
    :param file_path:
    :param cols_expected_table:
    :param integer_cols:
    :param client_id:
    :return:
    """
    cols_expected = cols_expected_table.values

    extension = os.path.splitext(file_path)[-1]

    if extension == '.xlsx':
        print('parsing data...')
        parsed_data = pd.read_excel(file_path,
                                    sheetname='Sheet1',
                                    # skiprows=9
                                    )

    elif extension == '.txt':
        print('parsing data...')

        success = False

        for i in range(100):  # it could be any reasonable number for a header file with not content.
            print('')
            try:
                parsed_data = pd.read_csv(file_path, sep=r"|", encoding='ISO-8859-1', skiprows=i,
                                          parse_dates=True, infer_datetime_format=True, decimal=b'.', thousands=',',
                                          #                                        nrows=i+50
                                          )
                raw_data_cols = parsed_data.columns

                print('Skiping {} rows has returned data.'.format(i))

                if len(raw_data_cols) <= 5:  # again, find a reasonable number for columns
                    print('Data only contains {} columns.'.format(len(raw_data_cols)))
                    pass
                else:
                    parsed_data = parsed_data.loc[
                        (parsed_data.isnull().sum(axis=1) <= 2).values]  # remove rows full of NANs

                    for col in raw_data_cols:
                        if parsed_data[col].dtype == 'object':

                            # - strip all extra white spaces from cells:
                            try:
                                parsed_data[col] = [x.strip() if type(x) == str else x for x in parsed_data[col].values]
                                #print(parsed_data.shape)

                            except:
                                print('.')  # just a debugging assistant
                                pass

                            try:
                                parsed_data[col] = pd.to_datetime(parsed_data[col])

                            except:
                                pass

                    # print(parsed_data.count())
                    parsed_data = parsed_data.loc[:, parsed_data.count() > 1]
                    print(parsed_data.shape)

                    parsed_data.columns = parsed_data.columns.map(lambda x: x.strip())

                    print('Final data\'s header has {} rows, {} events, and {} columns.'.format(i,
                                                                                                len(parsed_data),
                                                                                                len(parsed_data.columns)
                                                                                                ))
                    success = True
                    break
            except:
                e = sys.exc_info()
                print('Skiping {} rows did not return any data table.'.format(i))
                print('Reason: {}'.format(e))

    else:
        raise ValueError('Invalid extension.')

    dict_header = dict()
    dict_header['cols_i'] = None
    for i in parsed_data.iterrows():

        if np.all([col in i[1].index for col in cols_expected]) or np.all(
                [col in i[1].values for col in cols_expected]):
            dict_header['col_names'] = i[1].index if len([c for c in i[1].index if 'Unnamed' in c]) < 1 else i[1].values
            dict_header['n_rows'] = i[0]
            #         print('- - - - - - - - - -')
            print('found all columns required!!')
            dict_header['cols_i'] = np.where([col in cols_expected for col in dict_header['col_names']])[0]
            break
        else:
            print('it did not find all the columns required!!')

    # print(dict_header)
    # parsed_data = parsed_data.iloc[i_keep,dict_header['cols_i']].dropna(how='all').copy()
    parsed_data = parsed_data.iloc[dict_header['n_rows'] + 1:, dict_header['cols_i']].dropna(how='all').copy()

    i_keep = (parsed_data.count(axis=1) > 2)
    parsed_data = parsed_data[i_keep]
    parsed_data.columns = dict_header['col_names'][dict_header['cols_i']]

    # parsed_data.columns = list(cols_expected_table.index)
    parsed_data.columns = [cols_expected_table.index[cols_expected_table.values == c][0] for c in parsed_data.columns]

    for col in integer_cols:
        if parsed_data[col].dtype == object:
            parsed_data[col] = parsed_data[col].replace({'[+\-!*_,]': ''}, regex=True)

    parsed_data['clientid'] = client_id
    parsed_data['wo_type_nano'] = '-'

    print('parsing is complete.')

    return parsed_data