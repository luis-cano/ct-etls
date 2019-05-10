from flask import Blueprint
from flask import jsonify
from flask import request
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
from google.cloud import datastore
from google.cloud import bigquery
from google.cloud import storage
import logging
import uuid
import json
import urllib3
import socket
import requests
import os
import dataflow_pipeline.massive as pipeline
import cloud_storage_controller.cloud_storage_controller as gcscontroller
import datetime
import time
import sys
import dataflow_pipeline.telefonia.cdr_beam as cdr_beam #[[[[[[[[[[[[[[[[[[***********************************]]]]]]]]]]]]]]]]]]

cdr_api = Blueprint('cdr_api', __name__) #[[[[[[[[[[[[[[[[[[***********************************]]]]]]]]]]]]]]]]]]


########################### DEFINICION DE VARIABLES ###########################

zona_horaria = (1, 2)[socket.gethostname()=="contentobi"]
hoy = datetime.datetime.now()
ayer = datetime.datetime.today() - datetime.timedelta(days = zona_horaria)
ano = str(hoy.year)
hour1 = "060000"
hour2 = "235959"
if len(str(ayer.day)) == 1:
    dia = "0" + str(ayer.day)
else:
    dia = str(ayer.day)

if len(str(ayer.month)) == 1:
    mes = "0"+ str(ayer.month)
else:
    mes = str(ayer.month)

GetDate1 = str(ano)+str(mes)+str(dia)+str(hour1)
GetDate2 = str(ano)+str(mes)+str(dia)+str(hour2)

fecha = str(ano)+str(mes)+str(dia)
KEY_REPORT = "cdr" #[[[[[[[[[[[[[[[[[[***********************************]]]]]]]]]]]]]]]]]]
CODE_REPORT = "cbps_cdr" #[[[[[[[[[[[[[[[[[[***********************************]]]]]]]]]]]]]]]]]]
Ruta = ("/192.168.20.87", "media")[socket.gethostname()=="contentobi"]
ext = ".csv"
ruta_completa = "/"+ Ruta +"/BI_Archivos/GOOGLE/Telefonia/"+ KEY_REPORT +"/" + fecha + ext


########################### CODIGO #####################################################################################

@cdr_api.route("/" + KEY_REPORT, methods=['GET']) #[[[[[[[[[[[[[[[[[[***********************************]]]]]]]]]]]]]]]]]]
def Ejecutar():
    
    reload(sys)
    sys.setdefaultencoding('utf8')
    storage_client = storage.Client()
    bucket = storage_client.get_bucket('ct-telefonia')
    gcs_path = 'gs://ct-telefonia'
    sub_path = KEY_REPORT + '/'
    output = gcs_path + "/" + sub_path + fecha + ext
    blob = bucket.blob(sub_path + fecha + ext)
    dateini = request.args.get('dateini')
    dateend = request.args.get('dateend')

    if dateini is None:
        dateini = GetDate1
    else:
        dateini = dateini + hour1

    if dateend is None:
        dateend = GetDate2
    else:
        dateend = dateend + hour2

    client = bigquery.Client()
    QUERY = (
        'SELECT servidor, operacion, token, ipdial_code, id_cliente, cartera FROM telefonia.parametros_ipdial')
    query_job = client.query(QUERY)
    rows = query_job.result()
    data = ""
    
    try:
        os.remove(ruta_completa) #Eliminar de aries
    except: 
        print("Eliminado de aries")
    
    try:
        blob.delete() #Eliminar del storage
    except: 
        print("Eliminado de storage")

    file = open(ruta_completa,"a")
    for row in rows:
        url = 'http://' + str(row.servidor) + '/ipdialbox/api_reports.php?token=' + row.token + '&report=' + str(CODE_REPORT) + '&date_ini=' + dateini + '&date_end=' + dateend
        datos = requests.get(url).content
        if len(requests.get(url).content) < 40:
            continue
        else:
            i = json.loads(datos)
            for rown in i:
                file.write(
                    str(rown["id_call"].encode('utf-8'))+'|'+
                    str(rown["type_call"].encode('utf-8'))+'|'+
                    str(rown["talk_time"])+'|'+
                    str(rown["id_agent"])+'|'+
                    str(rown["agent_name"].encode('utf-8'))+'|'+
                    str(rown["agent_identification"])+'|'+
                    str(rown["skill"])+'|'+
                    str(rown["date"])+'|'+
                    str(rown["hour"])+'|'+
                    str(rown["day_of_week"].encode('utf-8'))+'|'+
                    str(rown["typing_code"].encode('utf-8'))+'|'+
                    str(rown["descri_typing_code"].encode('utf-8'))+'|'+
                    str(rown["typing_code2"].encode('utf-8'))+'|'+
                    str(rown["descri_typing_code2"].encode('utf-8'))+'|'+
                    str(rown["hit"].encode('utf-8'))+'|'+
                    str(rown["telephone_destination"])+'|'+
                    str(rown["telephone_costs"])+'|'+
                    str(rown["telephone_number"])+'|'+
                    str(rown["who_hangs_up"].encode('utf-8'))+'|'+
                    str(rown["customer_identification"])+'|'+
                    str(rown["month"])+'|'+
                    str(rown["screen_recording"].encode('utf-8'))+'|'+
                    str(rown["operation"].encode('utf-8'))+'|'+
                    str(rown["ring"])+'|'+
                    str(rown["abandon"])+'|'+
                    str(row.id_cliente).encode('utf-8')+"|"+
                    str(row.cartera).encode('utf-8') + "\n")
    
    file.close()
    blob.upload_from_filename("/"+ Ruta +"/BI_Archivos/GOOGLE/Telefonia/"+ KEY_REPORT +"/" + fecha + ext)
    time.sleep(10)
    ejecutar = cdr_beam.run(output, KEY_REPORT) #[[[[[[[[[[[[[[[[[[***********************************]]]]]]]]]]]]]]]]]]    
    time.sleep(60)

    return ("Proceso de listamiento de datos: listo ..........................................................." + ejecutar)

########################################################################################################################