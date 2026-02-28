import pandas as pd
from IPython.display import display

def load_raw(path):
    loaded_dataset = pd.read_excel(path)
    return loaded_dataset

def date_range(df):
    start_date = df['InvoiceDate'].min().strftime('%B %d, %Y')
    end_date = df['InvoiceDate'].max().strftime('%B %d, %Y')
    return print('The dataset captures',start_date,'through',end_date,'.')

def data_info(df):
    print('=' * 80)
    print('Dataset Overview')
    print('=' * 80)
    print('Shape')
    print(f' Columns:   {df.shape[1]}')
    print(f' Rows:      {df.shape[0]}')
    print('-' * 80)
    print('\n First 5 rows:')
    display(df.head())
    print('-' * 80)
    print('\n Data Types and Non-Null Values: \n')
    df.info(memory_usage=False)
    print('\n')
    print('-' * 80)
    print('\n Unique Values:')
    display(df.nunique())
    print('-' * 80)
    print('\n Statistical Summary:')
    display(df.describe())
    print('-' * 80)
    print("\n Missing Values Analysis\n")
    display(pd.DataFrame(df.isna().sum(), columns=['Missing']))
    print('Rows Where Price = £0:', df[df['Price'] == 0].shape[0])
    return 

def repair_transactions(df):
    repaired = df.copy()
    # Create dictionary of {Missing Description StockCode : Most common non-null description found for that code}    
    repaired_descriptions = {}
    missing_desc = (repaired[repaired['Description'].isna()]).drop_duplicates(subset=['StockCode'])
    for code in missing_desc['StockCode']: 
        descs = (repaired.loc[repaired['StockCode'] == code, 'Description'].dropna())  
        if not descs.empty:
            repaired_descriptions[code] = descs.value_counts().idxmax()
    repaired['Description'] = repaired['Description'].fillna(repaired['StockCode'].map(repaired_descriptions))
    print('Repaired Descriptions:               ', df['Description'].isna().sum() - repaired['Description'].isna().sum())
    # Repeat same structure for price
    repaired_prices = {}
    missing_price = (repaired[repaired['Price'] == 0]).drop_duplicates(subset='StockCode')
    for code in missing_price['StockCode']:
        price = (repaired.loc[repaired['StockCode'] == code, 'Price'].dropna())
        if not price.empty:
            repaired_prices[code] = price.value_counts().idxmax()
    repaired['Price'] = repaired['Price'].mask(repaired['Price'] == 0,repaired['StockCode'].map(repaired_prices))
    print('Repaired Prices:                     ', df[df['Price'] == 0].shape[0] - repaired[repaired['Price'] == 0].shape[0])
    # Reassign missing customer IDs to 0:
    missing_id_count = repaired['Customer ID'].isna().sum()
    repaired.loc[(repaired['Customer ID'].isna()),'Customer ID'] = 0 
    print('Missing customer IDs reassigned to 0:', missing_id_count)
    return repaired

def unusual_stock_codes(df):
    df2 = df.copy()
    unusual_stock_codes = ['POST','D','DOT','M','C2','BANK CHARGES','TEST001','TEST002','PADS','m','S','B','ADJUST2','AMAZONFEE','ADJUST']
    # Define net and gross for unusual subset vs total
    df2['Net'] = df2['Quantity']*df2['Price']
    df2['Gross'] = (df2['Quantity'].abs())*df2['Price']
    df_unusual = df2[df2['StockCode'].isin(unusual_stock_codes)]
    unusual_net = df_unusual['Net'].sum()
    unusual_gross = df_unusual['Gross'].sum()
    total_net = df2['Net'].sum()
    total_gross = df2['Gross'].sum()
    print('Unusual StockCodes:',unusual_stock_codes)
    print('Net Value of unusual transactions:       ', f'£{unusual_net:,.2f},   ' ,((unusual_net/total_net)*100).round(2),'% of total.')
    print('Gross Value of unusual transactions:     ', f'£{unusual_gross:,.2f},     ' , ((unusual_gross/total_gross)*100).round(2),'% of total.')
    return 

def clean_transactions(df):
    cleaned = df.copy()
    # Drop Rows with Null Description 
    before = len(cleaned)
    cleaned = cleaned[~(cleaned['Description'].isna())]
    print('Null description rows dropped:       ', before - len(cleaned))
    # Drop Rows with price = 0
    before = len(cleaned)
    cleaned = cleaned[~(cleaned['Price'] == 0)]
    print('Missing price rows dropped:          ', before - len(cleaned))
    # Manually define list of codes that should be deleted
    before = len(cleaned)
    codes_to_drop = ['POST','D','DOT','M','C2','BANK CHARGES','TEST001','TEST002','PADS','m','S','B','ADJUST2','AMAZONFEE','ADJUST']
    cleaned = cleaned[~cleaned['StockCode'].isin(codes_to_drop)]
    print('Unusual StockCode rows dropped:      ',before - len(cleaned))
    # Set data type of Customer ID from float to int
    cleaned = cleaned.copy()
    cleaned['Customer ID'] = cleaned['Customer ID'].astype('Int64')
    # Rename 'Price' to 'UnitPrice'
    cleaned = cleaned.rename(columns={'Customer ID':'CustomerID','Price':'UnitPrice'})
    return cleaned

def add_features(df):
    columns_before = df.columns.tolist()
    # Date and time
    featured = df.copy()
    featured['Weekday'] = featured['InvoiceDate'].dt.strftime('%a')
    featured['Year'] = featured['InvoiceDate'].dt.year
    featured['Month'] = featured['InvoiceDate'].dt.month
    featured['Day'] = featured['InvoiceDate'].dt.day
    featured['Time'] = featured['InvoiceDate'].dt.time
    # Define new column 'TotalPrice' as 'Quantity' * 'UnitPrice'
    featured['TotalPrice'] = featured['Quantity'] * featured['UnitPrice']
    # Label Sales
    featured.loc[featured['Quantity'] > 0, 'Type'] = 'Sale'
    print('Transactions labeled "Sales:"        ', len(featured[featured['Type'] == 'Sale']))
    # Label Cancellations
    featured.loc[featured['Invoice'].astype(str).str.startswith('C'), 'Type'] = 'Cancellation'
    print('Transactions labeled "Cancellation:" ', len(featured[featured['Type'] == 'Cancellation']))
    # Label Returns
    featured.loc[(featured['Type'] != 'Cancellation') & (featured['Type'] != 'Sale'), 'Type'] = 'Return'
    print('Transactions labeled "Return:"       ', len(featured[featured['Type'] == 'Return']))
    featured = featured[['Invoice','Type','InvoiceDate','Weekday','Year','Month','Day','Time','CustomerID','Country','StockCode','Description','Quantity','UnitPrice','TotalPrice']]
    print('Columns Added:')
    print('     ',list(set(featured.columns.tolist()) - set(columns_before)))
    featured = featured.reset_index(drop=True)
    return featured

