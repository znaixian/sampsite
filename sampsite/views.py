from django.shortcuts import render
import pandas as pd
import os
import numpy as np
import requests
import openpyxl


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
    return render(request, 'sampsite/index.html', {"data_list": []})

def Capping(df, threshold):
    while (df.weight > threshold).any():
        largest = float(df.weight.nlargest(1)) 
        df['weight_1'] = 0
        df.loc[df.weight == threshold, 'weight_1'] = threshold
        # df['weight_1'][df.weight == threshold] = threshold
        num = len(df[df.weight == largest]) 
        df.loc[df.weight == largest, 'weight_1'] = threshold
        # df['weight_1'][df.weight == largest] = threshold
        dist = (largest - threshold)*num
        total = df.weight[(df.weight_1 == 0)].sum()
        df.loc[df.weight_1 == 0, 'weight_1'] = df.weight + dist*(df.weight/total)
        # df['weight_1'][df.weight_1 == 0] = df.weight + dist*(df.weight/total)
        del df['weight']
        df.rename(columns={'weight_1': 'weight'}, inplace=True)
    return df

def Upload(request):
    excel_data_list = []
    error_dict = {}
    file_path = ""
    if request.method == 'POST' and request.FILES:
        f = request.FILES['input_data']
        t = request.POST['threshold']
        if t:
            pd.set_option("display.precision", 16)
            wb = openpyxl.load_workbook(f)
            worksheet = wb["Sheet1"]

            excel_data = list()
            for row in worksheet.iter_rows():
                row_data = list()
                for cell in row:
                    row_data.append(str(cell.value))
                excel_data.append(row_data)
            excel_data_list = []
            for data in excel_data[1:]:
                excel_data_dict = {}
                excel_data_dict["sedol"] = data[0]
                excel_data_dict["float_market_cap"] = data[1]
                excel_data_dict["weight"] = float(data[2])*100 if data[2] != 'None' else 0
                excel_data_list.append(excel_data_dict)

            df = pd.DataFrame(excel_data_list)
            result = Capping(df, float(t))
            df_list = df.to_dict('records')
            for exist_data in excel_data_list:
                for df_data in df_list:
                    if df_data['sedol'] == exist_data['sedol']:
                        exist_data['capped_weight'] = df_data['weight']
            # Create Excel File
            wr = openpyxl.Workbook() 
            sheet = wr.active

            sheet['A1'] = "SEDOL"
            sheet['B1'] = "FloatMarketCap($Mil, USD)"
            sheet['C1'] = "Weight"
            sheet['D1'] = "CappedWeight"
            for count, data in enumerate(excel_data_list):
                sheet['A'+str(count+2)] = data['sedol']
                sheet['B'+str(count+2)] = data['float_market_cap']
                sheet['C'+str(count+2)] = data['weight']
                sheet['D'+str(count+2)] = data['capped_weight']
            wr.save(os.path.join("static/files", request.FILES['input_data'].name))
            file_path = os.path.join("static/files/", request.FILES['input_data'].name)
            print(file_path)
        else:
            excel_data_list = []
            error_dict['file_error']="Please Upload File!"
            error_dict['threshold_error'] = "Please Add Threshold!"
    elif request.method == 'POST':
        error_dict = {}
        error_dict['threshold_error'] = ""
        t = request.POST['threshold']
        if not t:
            error_dict['threshold_error'] = "Please Add Threshold!"
        error_dict['file_error']="Please Upload File!"

    return render(request, 'weighting/index.html', {"data_list":excel_data_list, "error_dict": error_dict, "file_path":file_path})