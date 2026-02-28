import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd

def apply_style():
    plt.rcParams['figure.dpi'] = 150
    sns.set_theme(context='paper',font='Ebrima',rc={'axes.titleweight':'bold','axes.facecolor':'#EAEAF2', 'figure.facecolor':"#EAEAF2"})   
    
    plt.rcParams['figure.figsize'] = (12, 6)
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['axes.labelsize'] = 12
    plt.rcParams['xtick.labelsize'] = 10
    plt.rcParams['ytick.labelsize'] = 10

def line_chart(df, x_col, y_col, xlabel, ylabel, title):
    sns.lineplot(df,x=x_col,y=y_col, marker='o')
    plt.ticklabel_format(style='plain', axis='y')
    plt.ylim(0, None)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(f"{title}.png", bbox_inches='tight')
    plt.show()

def plot_bar(df, x_col, y_col, title, xlabel, ylabel, units='%'):   
    ax = sns.barplot(x=x_col, y=y_col, hue=x_col, data=df, palette='crest')
    for p in ax.patches:
        width = p.get_width()
        height = p.get_height()
        x, y = p.get_xy() 
        if units == '£':
            ax.annotate(f'£{height:,.0f}', (x + width/2, y + height), ha='center', va='bottom',fontsize=7)
        elif units == '%':
            ax.annotate(f'{height:,.1%}', (x + width/2, y + height), ha='center', va='bottom',fontsize=7)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(f"{title}.png", bbox_inches='tight')
    plt.show()

def plot_hbar(df, x_col, y_col, title, xlabel, ylabel, units='%'):  
    ax = sns.barplot(x=x_col,y=y_col,hue=y_col,data=df,palette='crest',dodge=False)
    for p in ax.patches:
        width = p.get_width()
        y = p.get_y() + p.get_height() / 2
        if units == '£':
            ax.annotate(f'£{width:,.0f}',xy=(width, y),xytext=(2, 0),textcoords='offset points',ha='left',va='center',fontsize=7)
        elif units == '%':
            ax.annotate(f'{width:,.1%}',xy=(width, y),xytext=(4, 0),textcoords='offset points',ha='left',va='center',fontsize=7)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(f"{title}.png", bbox_inches='tight')
    plt.show()    
