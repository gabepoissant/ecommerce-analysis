import pandas as pd
import datetime as dt

# Revenue by Period (incomplete periods omitted)
def revenue_by_period(df, period='month'):
    output = df[df['Type'] != 'Cancellation'].copy()
    if period == 'month':    
        output['YearMonth'] = output['InvoiceDate'].dt.strftime('%Y-%m')
        output = output[output['YearMonth'] != '2010-12']
        output = (output[['YearMonth','TotalPrice']].groupby(['YearMonth']).sum()).reset_index()

    elif period == 'season':
        season_map = {  12: 'Winter', 1: 'Winter', 2: 'Winter',
                        3: 'Spring', 4: 'Spring', 5: 'Spring',
                        6: 'Summer', 7: 'Summer', 8: 'Summer',
                        9: 'Fall', 10: 'Fall', 11: 'Fall'}
        season_order = {'Winter': 1,'Spring': 2,'Summer': 3,'Fall': 4}
        output = output[output['InvoiceDate'] <= dt.datetime(2010, 11, 30)]        
        output['Season'] = output['InvoiceDate'].dt.month.map(season_map)
        output['SeasonOrder'] = output['Season'].map(season_order)
        
        output['SeasonYearNum'] = output['InvoiceDate'].dt.year + ((output['Season'] == 'Winter') & (output['InvoiceDate'].dt.month == 12)).astype(int)
        output = (output.groupby(['SeasonYearNum', 'SeasonOrder', 'Season'], as_index=False).agg(TotalPrice=('TotalPrice', 'sum')))
        output['SeasonYear'] = output['Season'] + '-' + output['SeasonYearNum'].astype(str)       
        output = output.sort_values(['SeasonYearNum','SeasonOrder'])
        output = output[['SeasonYear','TotalPrice']]
    else:
        raise ValueError('Incorrect Period. Try: "month","season".')
    output = output.rename(columns={'TotalPrice':'Revenue'})
    return output

# Average Order Value (incomplete periods omitted)
def aov(df, period='total'):
    output = df[df['Type'] != 'Cancellation'].copy()
    if period == 'total':
        output = output[['Invoice','TotalPrice']].groupby('Invoice').sum()
        output = pd.DataFrame({'AOV':output['TotalPrice'].mean().round(2)}, index=[0])

    elif period == 'month':   
        output = output[['Invoice','TotalPrice','InvoiceDate']].groupby(['Invoice','InvoiceDate']).sum().reset_index()
        output['YearMonth'] = output['InvoiceDate'].dt.strftime('%Y-%m')
        output = output[output['YearMonth'] != '2010-12'] 
        output = (output[['YearMonth','TotalPrice']].groupby(['YearMonth']).mean()).reset_index()

    else:
        raise ValueError('Incorrect Period. Try: "total","month".')
    output = output.rename(columns={'TotalPrice':'AOV'})
    return output

# Repeat Revenue Share
def repeat_customer_revenue(df):
    df2 = df[(df['Type'] != 'Cancellation') & (df['CustomerID'] > 0)].copy()
    total = df2['TotalPrice'].sum()
    repeat = df2[['Invoice','CustomerID']].drop_duplicates(subset='Invoice')
    repeat = repeat[repeat.duplicated(subset=['CustomerID'], keep=False)]
    repeat = repeat.drop_duplicates(subset='CustomerID')
    repeat_revenue = df2[df2['CustomerID'].isin(repeat['CustomerID'])]['TotalPrice'].sum()
    pct = repeat_revenue/total
    print('Repeat customers spent',f'£{repeat_revenue:,.0f}',', which represents', f'{pct:,.2%}','of all sales.')

# Customer concentration
def customer_concentration(df):
    df2 = df[df['Type'] != 'Cancellation'].copy()
    # calculate % of transactions with unknown customer
    transaction_count = df2.shape[0]
    no_id_count = df2[df2['CustomerID'] == 0].shape[0]
    unknown_pct = no_id_count/transaction_count
    # calculate customer concentration
    concentration = df2.copy()
    concentration = concentration[concentration['CustomerID'] != 0]
    concentration = concentration[['CustomerID','TotalPrice']].groupby(by='CustomerID').sum().sort_values(by='TotalPrice', ascending=False)
    concentration['Percentage'] = concentration['TotalPrice']/ concentration['TotalPrice'].sum()
    concentration = concentration.rename(columns = {'TotalPrice':'Revenue'}).reset_index()
    concentration['CustomerID'] = concentration['CustomerID'].astype(str)
    print('Note: ', f'{unknown_pct:.1%}', 'of transactions are excluded due to unknown customers.')
    return concentration

# Percent Returns
def return_percentage(df):
    sales = df[df['Type'] == 'Sale']
    returns = df[df['Type'] == 'Return']
    return_pct = abs(returns['TotalPrice'].sum()) / sales['TotalPrice'].sum()
    return return_pct

def product_concentration(df):
    df2 = df[df['Type'] != 'Cancellation'].copy()
    code_revenue = df2[['StockCode','TotalPrice']].groupby('StockCode').sum().sort_values('TotalPrice', ascending=False)
    code_description = df2[['StockCode','Description']].drop_duplicates(subset='StockCode')
    units_sold = df2[['StockCode','Quantity']].groupby('StockCode').sum().sort_values('Quantity', ascending=False)

    product_revenue = pd.merge(code_revenue, code_description, on='StockCode', how='outer')
    product_revenue = pd.merge(product_revenue, units_sold, on='StockCode', how='outer')
    product_revenue['Percentage'] = product_revenue['TotalPrice']/product_revenue['TotalPrice'].sum()
    product_revenue = product_revenue[['StockCode','Description','TotalPrice','Percentage','Quantity']].sort_values('TotalPrice', ascending=False).reset_index(drop=True)
    product_revenue = product_revenue.rename(columns={'TotalPrice':'Revenue'})
    return product_revenue

def return_rates(df):
    code_description = df[['StockCode','Description']].drop_duplicates(subset='StockCode')

    # Exclude cancellations
    valid_returns = df[df['Type'] != 'Cancellation'].copy()
    valid_returns = valid_returns[['CustomerID','StockCode','Quantity']].groupby(['CustomerID','StockCode']).sum()
    # If given customer has returned more of an item than they have purchased, exclude that item/customer combination 
    valid_returns = valid_returns[valid_returns['Quantity'] > 0].reset_index()
    # Create identifier for valid sales
    valid_returns['Identifier'] = valid_returns['CustomerID'].astype('str') + 'x' + valid_returns['StockCode'].astype('str')

    # Create identifier onto original data (minus cancellations) to join with valid returns
    df_valid_returns = df[df['Type'] != 'Cancellation'].copy()
    df_valid_returns['Identifier'] = df_valid_returns['CustomerID'].astype('str') + 'x' + df_valid_returns['StockCode'].astype('str')
    df_valid_returns = pd.merge(valid_returns['Identifier'], df_valid_returns,on='Identifier', how='left')

    # Group gross sales and returns by StockCode on the same table
    sales = df_valid_returns[df_valid_returns['Type'] == 'Sale' ]
    returns = df_valid_returns[df_valid_returns['Type'] == 'Return']
    grouped_sales = sales[['StockCode','Quantity']].groupby('StockCode').sum().sort_values('Quantity', ascending=False)
    grouped_returns = returns[['StockCode','Quantity']].groupby('StockCode').sum().sort_values('Quantity')
    return_rates = pd.merge(grouped_returns,grouped_sales, on='StockCode', how='outer')
    return_rates = return_rates.rename(columns={'Quantity_x':'Returns','Quantity_y':'ItemsSold'})

    # Drop items with no returns, make Returns positive
    return_rates = return_rates.dropna(subset=['Returns'])
    return_rates['Returns'] = return_rates['Returns'].abs()
    # Calculate return rate, sort by highest first
    return_rates['ReturnRate'] = return_rates['Returns']/return_rates['ItemsSold']
    return_rates = return_rates.sort_values(by='ReturnRate',ascending=False).reset_index()
    # Join with StockCode descriptions
    return_rates = pd.merge(return_rates, code_description, on='StockCode', how='left')
    return return_rates


def market_growth(df):
    df2 = df[df['Type'] != 'Cancellation'].copy()
    # Create Year-Month column
    df2['YearMonth'] = df2['InvoiceDate'].dt.to_period('M')
    # ignore last month (incomplete)
    df2 = df2[df2['YearMonth']!= '2010-12']
    # Aggregate revenue by country and month
    country_month = (df2.groupby(['Country', 'YearMonth'])['TotalPrice'].sum().reset_index())
    country_month['YearMonth'] = country_month['YearMonth'].dt.to_timestamp()
    country_month = country_month.sort_values(['Country', 'YearMonth'])
    country_month['MoM_Growth'] = (country_month.groupby('Country')['TotalPrice'].pct_change())
    country_month_trimmed = (country_month.groupby('Country').filter(lambda x: x['YearMonth'].nunique() == country_month['YearMonth'].nunique()))
    growth_summary = (country_month_trimmed.groupby('Country').agg(first_revenue=('TotalPrice', 'first'), last_revenue=('TotalPrice', 'last')))
    growth_summary['Total_Growth'] = ((growth_summary['last_revenue'] - growth_summary['first_revenue']) / growth_summary['first_revenue'])
    growth_summary = growth_summary.sort_values('Total_Growth', ascending=False)
    # Calculate number of countries excluded
    total_countries = df2['Country'].drop_duplicates().shape[0]
    full_period_countries = country_month_trimmed['Country'].drop_duplicates().shape[0]
    full_period_cnt = total_countries - full_period_countries
    full_period_pct = full_period_countries/total_countries
    print('Note:', full_period_cnt, f'({full_period_pct:.0%})', 'countries are excluded due to insufficient revenue.')
    return growth_summary

def revenue_by_country(df):
    output = df[df['Type'] != 'Cancellation'].copy()
    total_revenue = output['TotalPrice'].sum()
    output = output[['Country', 'TotalPrice']].groupby('Country').sum()
    output = output.sort_values('TotalPrice', ascending=False)
    output['Percentage'] = output['TotalPrice']/total_revenue
    output = output.rename(columns={'TotalPrice':'Revenue'})
    return output