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
import dataflow_pipeline.telefonia.skill_detail_beam as skill_detail_beam #[[[[[[[[[[[[[[[[[[***********************************]]]]]]]]]]]]]]]]]]
import sys

skill_detail_api = Blueprint('skill_detail_api', __name__) #[[[[[[[[[[[[[[[[[[***********************************]]]]]]]]]]]]]]]]]]


########################### DEFINICION DE VARIABLES ###########################

zona_horaria = (1, 2)[socket.gethostname()=="contentobi"]
hoy = datetime.datetime.now()
ayer = datetime.datetime.today() - datetime.timedelta(days = zona_horaria)
ano = str(hoy.year)
hour1 = "000000"
hour2 = "235959"
if len(str(hoy.day)) == 1:
    dia = "0" + str(hoy.day)
else:
    dia = str(hoy.day)

if len(str(hoy.month)) == 1:
    mes = "0"+ str(hoy.month)
else:
    mes = str(hoy.month)

GetDate1 = str(ano)+str(mes)+str(dia)+str(hour1)
GetDate2 = str(ano)+str(mes)+str(dia)+str(hour2)

fecha = str(ano)+str(mes)+str(dia)
KEY_REPORT = "skill_detail" #[[[[[[[[[[[[[[[[[[***********************************]]]]]]]]]]]]]]]]]]
CODE_REPORT = "skill_detail" #[[[[[[[[[[[[[[[[[[***********************************]]]]]]]]]]]]]]]]]]
Ruta = ("/192.168.20.87", "media")[socket.gethostname()=="contentobi"]
ext = ".csv"
ruta_completa = "/"+ Ruta +"/BI_Archivos/GOOGLE/Telefonia/"+ KEY_REPORT +"/" + fecha + ext


########################### CODIGO #####################################################################################

@skill_detail_api.route("/" + KEY_REPORT, methods=['GET']) #[[[[[[[[[[[[[[[[[[***********************************]]]]]]]]]]]]]]]]]]
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
        'SELECT servidor, operacion, token, ipdial_code, id_cliente, cartera FROM telefonia.parametros_ipdial') #WHERE ipdial_code = "intcob-unisabaneta"
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

    try:
        QUERY2 = ('delete FROM `contento-bi.telefonia.skill_detail` where replace(substr(date,0,10),"-","") = ' + '"' + dateini[0:8] + '"')
        query_job = client.query(QUERY2)
        rows2 = query_job.result()
    except: 
        print("Eliminado de bigquery")

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
                    rown["operation"]+"|"+
                    rown["id_call"]+"|"+
                    rown["type_call"]+"|"+
                    str(rown["date"])+"|"+
                    str(rown["id_agent"])+"|"+
                    rown["name_agent"]+"|"+
                    str(rown["skill"])+"|"+
                    str(rown["wait_time"])+"|"+
                    str(rown["calls_ans_10"])+"|"+
                    str(rown["calls_ans_20"])+"|"+
                    str(rown["calls_ans_30"])+"|"+
                    str(rown["calls_ans_40"])+"|"+
                    str(rown["calls_ans_50"])+"|"+
                    rown["skill_result"]+"|"+
                    str(rown["ani"])+"|"+
                    str(rown["dnis"])+"|"+
                    str(row.id_cliente).encode('utf-8') + "|" +
                    row.cartera.encode('utf-8') + "\n")
    
    file.close()
    blob.upload_from_filename(ruta_completa)
    time.sleep(10)
    ejecutar = skill_detail_beam.run(output, KEY_REPORT) #[[[[[[[[[[[[[[[[[[***********************************]]]]]]]]]]]]]]]]]]    
    time.sleep(60)

    return("El proceso " + KEY_REPORT + ". Fue Cargado Exitosamente en la fecha: " + fecha)
########################################################################################################################