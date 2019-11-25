from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.core.files.storage import default_storage

import pandas as pd
import os
import numpy as np
import requests
import openpyxl
import csv

#from django.http import HttpResponse, HttpResponseRedirect
#from .models import TodoItem

#def myView(request):
#    return HttpResponse('HELLO …………….. test!')

#def myView(request):
#    all_todo_items = TodoItem.objects.all()
#    return render(request, 'toenter.html',
#                 {'all_items': all_todo_items})
#
#def addTodo(request):
#    new_item = TodoItem(content = request.POST['content'])
#    new_item.save()
#    return HttpResponseRedirect('/sampsite/')
#
#def deleteTodo(request, todo_id):
#    item_to_delete = TodoItem.objects.get(id=todo_id)
#    item_to_delete.delete()
#    return HttpResponseRedirect('/sampsite/')
#def myView(request):
#    return render(request, 'toenter.html')
def Index(request):
    return render(request, 'sampsite/index.html', {"dt_html": []})

#def Capping(df, threshold):
#    while (df.weight > float(threshold)).any():
#        largest = float(df.weight.nlargest(1)) 
#        df['weight_1'] = 0
#        df.loc[df.weight == float(threshold), 'weight_1'] = float(threshold)
#        # df['weight_1'][df.weight == threshold] = threshold
#        num = len(df[df.weight == largest]) 
#        df.loc[df.weight == largest, 'weight_1'] = float(threshold)
#        # df['weight_1'][df.weight == largest] = threshold
#        dist = (largest - float(threshold))*num
#        total = df.weight[(df.weight_1 == 0)].sum()
#        df.loc[df.weight_1 == 0, 'weight_1'] = df.weight + dist*(df.weight/total)
#        # df['weight_1'][df.weight_1 == 0] = df.weight + dist*(df.weight/total)
#        del df['weight']
#        df.rename(columns={'weight_1': 'weight'}, inplace=True)
#    return df

def Capping(df, threshold):
    while (df.weight > float(threshold)).any():
        largest = float(df.weight.nlargest(1)) 
        df['weight_1'] = 0
        df.loc[df.weight == float(threshold), 'weight_1'] = float(threshold)
        # df['weight_1'][df.weight == threshold] = threshold
        num = len(df[df.weight == largest]) 
        df.loc[df.weight == largest, 'weight_1'] = float(threshold)
        # df['weight_1'][df.weight == largest] = threshold
        dist = (largest - float(threshold))*num
        total = df.weight[(df.weight_1 == 0)].sum()
        df.loc[df.weight_1 == 0, 'weight_1'] = df.weight + dist*(df.weight/total)
        # df['weight_1'][df.weight_1 == 0] = df.weight + dist*(df.weight/total)
        del df['weight']
        df.rename(columns={'weight_1': 'weight'}, inplace=True)
    return df

def astrip(astring):
    bs = astring.strip("\r\n")
    return bs.replace("\r\n", "")

def Upload(request):
    dt_html = {}
    error_dict = {}
    file_path = ""
    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        #the other parameter
        threshold = request.POST['threshold']
#        myfile = pd.read_csv('sample weighting file.csv')
        if threshold:
            pd.set_option("display.precision", 16)
            pd.set_option('colheader_justify', 'center') 
            mydf = []
            for line in myfile:
                mydf.append(line.decode('utf-8').split(','))
            tmp = pd.DataFrame(mydf)
            tmp[tmp.columns[-1]] = tmp[tmp.columns[-1]].apply(astrip)
            header = tmp.iloc[0]
            tmp = tmp[1:] #cut the first row/header off
            # Rename the dataframe's column values with the header variable
            tmp.columns = header
            print("check")
            print(tmp.head())
            tmp[tmp.columns[-1]] = tmp[tmp.columns[-1]].astype(float)
            print(tmp.dtypes)
         
            #url of the uploaded file
            fs = FileSystemStorage()
            filename = fs.save(myfile.name, myfile)
            uploaded_file_url = fs.url(filename)
    
     
            udates = tmp.Date.unique()
            tb = pd.DataFrame()
            
            for day in udates:
              print(day)
              dfile = tmp[tmp.Date == day]
              Capping(dfile, threshold)
              tb = tb.append(dfile)
              print(tb)
    
    #        tb.to_excel(os.path.join("static/files", request.FILES['myfile'].name))
            dt_html = tb.to_html(index=True,classes="mystyle")    
    
            file_path = os.path.join("static/files/", "weighted_file.csv")
            print(file_path)
            with open(file_path,'w') as outputfile:
                writer = csv.writer(outputfile)
                writer.writerow(['Date','float_mkt', 'sedol','weight'])
                l = tb.values.tolist()
                for row in l:
                    writer.writerow(row)
                    outputfile.flush()            
            
        else:
            dt_html = {}
            error_dict['file_error']="Please Upload File!"
            error_dict['threshold_error'] = "Please Add Threshold!"
    elif request.method == 'POST':
        error_dict = {}
        error_dict['threshold_error'] = ""
        threshold = request.POST['threshold']
        if not threshold:
            error_dict['threshold_error'] = "Please Add Threshold!"
        error_dict['file_error']="Please Upload File!"        
        
    return render(request, 'sampsite/index.html', {"dt_html":dt_html, "error_dict": error_dict, "file_path":file_path})

def Prime(df):
    if (df[df['cumsum'] > 0.475]['weight'] > 0.05).any():
        print("aggregated 5% more than 47.5%, prime it")
        largest = float(df[df['cumsum'] > 0.475]['weight'].nlargest(1))
        indexv = np.where(df.weight == largest)[0][0]
        delta = 0.475 - df.iloc[:indexv]['weight'].sum()
        if largest >= delta >= 0.045:
            df['weight_1'] = 0.00
            #df['weight_1'][df.index.isin(range(indexv))] = df['weight']
            #df.iloc[:indexv, ]['weight_1'] = df.iloc[:indexv, ]['weight']
            df['weight_1'][df.index.isin(range(indexv))] = df['weight']
            df['weight_1'][df.weight == largest] = delta
            dist = largest - delta
            total = df.weight[(df.weight_1 == 0)].sum()
            df['weight_1'][df.weight_1 == 0] = df.weight + dist*(df.weight/total)
            #df.weight.sum()
            del df['weight']
            df.rename(columns={'weight_1': 'weight'}, inplace=True) 
            df['cumsum'] = df.weight.cumsum()
        else:
            pass
    else:
        pass
    return df
            

def Rule50(df):
    while (df[df['cumsum'] > 0.475]['weight'] > 0.05).any():
        print("aggregated 5% more than 45%, cap it")
        largest = float(df[df['cumsum'] > 0.475]['weight'].nlargest(1))
        #indexv = df[df.weight == largest].index
        #indexv = df.loc[df.weight == largest].index.values
        #indexv = int(indexv)
        indexv = np.where(df.weight == largest)[0][0]
        #type(indexv)
        #indexv = int(indexv)
        df['weight_1'] = 0.00
        df['weight_1'][df.index.isin(range(indexv))] = df['weight']
        #df.loc[0:indexv]['weight_1'] = df['weight']
        df['weight_1'][df.weight == largest] = 0.045
        dist = largest - 0.045
        total = df.weight[(df.weight_1 == 0)].sum()
        df['weight_1'][df.weight_1 == 0] = df.weight + dist*(df.weight/total)
        #df.weight.sum()
        del df['weight']
        df.rename(columns={'weight_1': 'weight'}, inplace=True) 
        df['cumsum'] = df.weight.cumsum()
        return Rule50(df) 
            

def Seq50(df, i):
    while i < len(df)-1:
        print(i)
        if df['weight'].iloc[i+1] <= df['weight'].iloc[i]:
            pass
           
        else:
            df['weight_1'] = 0.00
            df['weight_1'].iloc[:i+1] = df['weight']
            df['weight_1'].iloc[i+1] = df.iloc[i]['weight']
            dist = df.iloc[i+1]['weight'] - df.iloc[i]['weight']
            total = df.weight[(df.weight_1 == 0)].sum()
            df['weight_1'][df.weight_1 == 0] = df.weight + dist*(df.weight/total)
            del df['weight']
            df.rename(columns={'weight_1': 'weight'}, inplace=True) 
        i += 1
    return df

def Petcare(request):
    dt_html = {}
    error_dict = {}
    file_path = ""
    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        pd.set_option("display.precision", 16)
        pd.set_option('colheader_justify', 'center') 

        mydf = []
        for line in myfile:
            mydf.append(line.decode('utf-8').split(','))
        tmp = pd.DataFrame(mydf)
        
        tmp[tmp.columns[-1]] = tmp[tmp.columns[-1]].apply(astrip)
        header = tmp.iloc[0]
        tmp = tmp[1:] #cut the first row/header off
        tmp.columns = header
        
#        print("check")
#        print(tmp.head())
        tmp[tmp.columns[-1]] = tmp[tmp.columns[-1]].astype(float)
#        print(tmp.dtypes)
     
        #url of the uploaded file
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)

        #special capping
        pure = tmp[tmp['Tier'] == 'Tier 1']
        npure = tmp[tmp['Tier'] == 'Tier 2']
        
        pure['weight'] = pure.weight * 0.825
        npure['weight'] = npure.weight * 0.175
        
        pure = pure.sort_values('weight', ascending=False).reset_index()
        npure = npure.sort_values('weight', ascending=False).reset_index()
        
        #step1 capping at 10% or 4..5% respectively
        threshold = 0.10
        Capping(pure, threshold)
        pure['cumsum'] = pure.weight.cumsum()
        
        threshold = 0.045
        Capping(npure, threshold)
        npure['cumsum'] = npure.weight.cumsum()
        
        #prime
        pureprime = Prime(pure)
            
        #Rule50
        Rule50(pureprime)
        
        #Seq50
        pureseq = Seq50(pureprime, 0)
        
        #cobble together
        pureseq.head()
        npure.head()
        
        finaldf = pureseq.append(npure)
        print(finaldf)

#        tb.to_excel(os.path.join("static/files", request.FILES['myfile'].name))
        dt_html = finaldf.to_html(index=True,classes="mystyle")    

        file_path = os.path.join("static/files/", "petcare_weighted_file.csv")
        print(file_path)
        with open(file_path,'w') as outputfile:
            writer = csv.writer(outputfile)
            writer.writerow(finaldf.columns)
            l = finaldf.values.tolist()
            for row in l:
                writer.writerow(row)
                outputfile.flush()            
            
    else:
        dt_html = {}
        error_dict['file_error']="Please Upload File!"

    return render(request, 'sampsite/index.html', {"dt_html":dt_html, "error_dict": error_dict, "file_path":file_path})
    