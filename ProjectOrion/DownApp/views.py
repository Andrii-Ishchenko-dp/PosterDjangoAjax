from django.shortcuts import render
import os
import tempfile
import xlwt
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import hashlib
import requests
from django.http import HttpResponse, HttpResponseNotFound
import time


app_id = 2659
app_key = '7776c65da87f8e3856d6befb30f1d46b'
access_token = '578064:4602865fe26394f496eb17b40a03f60b'

# пуш проекта с мака

@csrf_exempt
def index(request):
    otvet = request.GET.get('posterToken')
    access_token = '578064:4602865fe26394f496eb17b40a03f60b'
    con= {}

    if otvet != None:
        auth = {
            'application_id': app_id,
            'application_secret': app_key,
            'code': otvet,
            'verify': hashlib.md5((str(app_id) + ':' + app_key + ':' + str(otvet)).encode('utf-8')).hexdigest()
        }

        data = requests.post('https://joinposter.com/api/v2/auth/manage', data=auth).json()
        data = dict(data)

        # global access_token
        access_token = data['access_token']

        con['access'] = data['access_token']

        #url_params = request.GET.copy() #блок котрий відповідає за додавання токену до URL
        #url_params['access_token'] = access_token
        # response = request.path + '?' + url_params.urlencode()

        print('Токен доступа при авторизации: ', access_token)
        # client_data = {
        #     'access_token': data['access_token'],
        #     'account_number': data['account_number']
        # }
        # database.child("accaunt").child('{}'.format(data['account_number'])).set(client_data)

    response = render(request, 'DownApp/index.html', context=con)

    return response


@csrf_exempt
def export_data(request):

    if (request.method == 'POST'):

        if request.POST.get('type_of_down') == '1':
            token = request.POST.get('access_tok')
            print('token при вигрузці товарів по акції: ', token)
            cheks = []
            count_cheks = 0
            data_start = request.POST.get('field1')
            data_end = request.POST.get('field2')

            inkl = '-'
            data_start_new = str(data_start).translate(str.maketrans('', '', inkl))
            data_end_new = str(data_end).translate(str.maketrans('', '', inkl))

            url_dash = 'https://joinposter.com/api/dash.getTransactions?token={}' \
                       '&dateFrom={}' \
                       '&dateTo={}'

            res_chek = requests.get(url_dash.format(token, data_start_new, data_end_new)).json()
            print(res_chek['response'])

            if len(res_chek['response']) < 1:
                print('Выгрузка пустого файла')
                wb = xlwt.Workbook()
                ws = wb.add_sheet('Нет продаж')
                ws.write(0, 0, 'Нет продаж в указанный период времени')

                with tempfile.NamedTemporaryFile(delete=False, suffix='.xls') as temp_file:
                    wb.save(temp_file.name)
                    filename = os.path.basename(temp_file.name)

                data = {'filename': filename}
                return JsonResponse(data)

            else:
                for l in res_chek['response']:
                    countofstor = {
                        'id': res_chek['response'][count_cheks]['transaction_id'],
                        'date_close_date': res_chek['response'][count_cheks]['date_close_date']
                    }
                    count_cheks += 1
                    cheks.append(countofstor)  # Получил список чеков в указанный период времени

                dish = []
                activ_prom = []

                for i in range(len(cheks)):
                    count_dish = 0

                    url_tovari = 'https://joinposter.com/api/dash.getTransactionsProducts?token={}' \
                                 '&transactions_id={}'
                    res_dish = requests.get(url_tovari.format(token, cheks[i]['id'])).json()
                    # dish.append(cheks[i]['date_close_date'])# добавляю дату перед позициями по акции
                    for o in res_dish['response']:
                        dic_dish = {
                            'prod_name': res_dish['response'][count_dish]['product_name'],
                            'num': res_dish['response'][count_dish]['num'],
                            'payed_sum': res_dish['response'][count_dish]['payed_sum'],
                            'product_sum': res_dish['response'][count_dish]['product_sum'],
                            'promotion_id': res_dish['response'][count_dish]['promotion_id']
                        }
                        if dic_dish['promotion_id'] != 0:
                            dish.append(
                                dic_dish)  # Получил список блюд с указанных чеков, на которые распространялась акция
                            if activ_prom.count(dic_dish['promotion_id']) == 0:
                                activ_prom.append(dic_dish['promotion_id'])
                        count_dish += 1

                print('список блюд на которые распространялась акция: ', dish)
                if len(dish)<1:
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Нет продаж')

                    ws.write(0, 0, 'Нет продаж акции в указанный период времени')

                    with tempfile.NamedTemporaryFile(delete=False, suffix='.xls') as temp_file:
                        wb.save(temp_file.name)
                        filename = os.path.basename(temp_file.name)

                    data = {'filename': filename}
                    return JsonResponse(data)

                prom = []
                count_prom = 0
                url_prom = 'https://joinposter.com/api/clients.getPromotions?token={}'
                res_prom = requests.get(url_prom.format(token)).json()
                for p in res_prom['response']:
                    dic_prom = {
                        'promotion_id': res_prom['response'][count_prom]['promotion_id'],
                        'name': res_prom['response'][count_prom]['name']
                    }
                    prom.append(dic_prom)
                    count_prom += 1

                # создал отдельный список акций, которые были задействованы в этом периоде времени
                print('активние акции в этот период времени: ', prom)
                wb = xlwt.Workbook()
                activ_prom_with_name = []

                for t in range(len(prom)):
                    if int(prom[t]['promotion_id']) in activ_prom:
                        activ_prom_with_name.append(prom[t])

                for r in range(len(activ_prom_with_name)):
                    ws = wb.add_sheet(activ_prom_with_name[r]['name'])
                    ws.write(0, 0, 'Название')
                    ws.write(0, 1, 'Количество')
                    ws.write(0, 2, 'Цена без акции')
                    ws.write(0, 3, 'Цена с акцией')
                    ws.write(0, 4, 'Скидка')
                    y = 1
                    for b in dish:
                        x = 0
                        if b['promotion_id'] == int(activ_prom_with_name[r]['promotion_id']):
                            ws.write(y, x, b['prod_name'])
                            x += 1
                            ws.write(y, x, float(b['num']))
                            x += 1
                            ws.write(y, x, float(b['product_sum']))
                            x += 1
                            ws.write(y, x, float(b['payed_sum']))
                            x += 1
                            ws.write(y, x, xlwt.Formula("C{}-D{}".format(y + 1, y + 1)))
                            y += 1


            with tempfile.NamedTemporaryFile(delete=False, suffix='.xls') as temp_file:
                wb.save(temp_file.name)
                filename = os.path.basename(temp_file.name)

            data = {'filename': filename}
            return JsonResponse(data)


        elif request.POST.get('type_of_down') == '2':
            access_token = request.POST.get('access_tok')
            print('Код доступа при выгрузке остатков: ', access_token)
            storage = []  # склады в заведении, id, название

            url_stor = 'https://joinposter.com/api/storage.getStorages?token={}'
            res_stor = requests.get(url_stor.format(access_token)).json()
            print('количество складов: ', res_stor)

            if len(res_stor['response']) < 1:
                print('Выгрузка пустого файла')
                wb = xlwt.Workbook()
                ws = wb.add_sheet('Нет складов')
                ws.write(0, 0, 'Нет складов')

                with tempfile.NamedTemporaryFile(delete=False, suffix='.xls') as temp_file:
                    wb.save(temp_file.name)
                    filename = os.path.basename(temp_file.name)

                data = {'filename': filename}
                return JsonResponse(data)

            else:
                inkl = '-'
                token = access_token
                data_start_get = request.POST.get('field1')
                data_start = str(data_start_get).translate(str.maketrans('', '', inkl))
                data_start_origin = data_start
                data_end_get = request.POST.get('field2')
                data_end = str(data_end_get).translate(str.maketrans('', '', inkl))
                data_end_origin = data_end

                storage = []  # склады в заведении, id, название
                count_stor = 0

                url_stor = 'https://joinposter.com/api/storage.getStorages?token={}'
                res_stor = requests.get(url_stor.format(token)).json()

                for l in res_stor['response']:
                    countofstor = {
                        'id': res_stor['response'][count_stor]['storage_id'],
                        'name': res_stor['response'][count_stor]['storage_name']
                    }
                    count_stor += 1
                    storage.append(countofstor)

                storage.append({
                    'id': '0',
                    'name': 'Все склады'
                })

                wb = xlwt.Workbook()

                url_zvit_za_ruhom = 'https://joinposter.com/api/storage.getReportMovement?' \
                                    'token={}&' \
                                    'dateFrom={}&' \
                                    'dateTo={}&' \
                                    'storage_id={}&' \
                                    'type=0'
                nomer_stroki = 0
                time_start_req = time.time()
                for i in storage:  # прохожусь по складам в заведении
                    spisok_name = []  # список с уникальными названиями ингредиентов и товаров

                    data_start = data_start_origin  # возвращаю датам значения по умолчанию
                    data_end = data_end_origin  # возвращаю датам значения по умолчанию
                    time_to_list_start = time.time()
                    ws = wb.add_sheet(i['name'])
                    ws.write(0, 0, 'Название:')
                    kolichestvo_dnei = int(data_end_origin) - int(data_start_origin)
                    for q in range(kolichestvo_dnei + 1):
                        ws.write(0, q + 1, int(data_start_origin) + q)
                    while data_start <= data_end:  # по датам
                        spisok = []  # список с полученной инфой по складу
                        zvit_za_ruhom = requests.get(
                            url_zvit_za_ruhom.format(token, data_start, data_end, i['id'])).json()
                        spisok += zvit_za_ruhom['response']
                        for o in spisok:

                            if o['ingredient_name'] not in spisok_name:
                                spisok_name.append(o['ingredient_name'])
                                ws.write(int(spisok_name.index(o['ingredient_name'])) + 1, 0, o['ingredient_name'])

                            ws.write(int(spisok_name.index(o['ingredient_name'])) + 1,
                                     int(data_start) - int(data_start_origin) + 1,
                                     o['start'])
                            if data_start == data_end:
                                continue
                            ws.write(int(spisok_name.index(o['ingredient_name'])) + 1,
                                     int(data_end_origin) - int(data_start) + 1,
                                     o['end'])

                        data_start = str(int(data_start) + 1)  # сокращаю период запроса на день вперёд
                        data_end = str(int(data_end) - 1)  # сокращаю период запроса на день назад
                    time_to_get_req = time.time() - time_to_list_start
                    print('Время на заполнение получение всех запросов по одному складу: ', time_to_get_req)

                time_final = time.time() - time_start_req
                print('Общее время выполнения запроса: ', time_final)

                with tempfile.NamedTemporaryFile(delete=False, suffix='.xls') as temp_file:
                    wb.save(temp_file.name)
                    filename = os.path.basename(temp_file.name)

                data = {'filename': filename}
                return JsonResponse(data)


@csrf_exempt
def download_file(request, filename):
    file_path = os.path.join(tempfile.gettempdir(), filename)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename=' + filename
            return response
    else:
        return HttpResponse('В указанный период нет данных. Перезайдите в приложение и выберете другой временной промежуток.', status=404)

