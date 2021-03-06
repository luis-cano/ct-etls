# -*- coding: utf-8 -*-

#######################################################################################################################
#Espíritu santo de DIOS, que sean tus manos tirando este código. en el nombre de JESÚS. amén y amén
#######################################################################################################################

from flask import Blueprint
from flask import jsonify
from flask import request
from shutil import copyfile, move
from google.cloud import storage
from google.cloud import bigquery
import dataflow_pipeline.contento_tech.fanalca_agendamientos_beam as fanalca_agendamientos_beam
import cloud_storage_controller.cloud_storage_controller as gcscontroller
import os
import time
import socket
import _mssql
import datetime
import time


tof_api = Blueprint('tof_api', __name__)
fileserver_baseroute = ("//192.168.20.87", "/media")[socket.gethostname()=="contentobi"]

@tof_api.route("/tof_fanalca", methods=['GET'])
def tof_fanalca():

    import sys
    reload(sys)

    SERVER="192.168.20.63\DOKIMI"
    USER="etl_fanalca_agendamiento"
    PASSWORD="etl_fanalca_agendamiento04032020*"
    DATABASE="Fanalca_Agendamientos"
    FECHA_CARGUE = datetime.date.today()
    AHORA = FECHA_CARGUE.strftime("%Y-%m-%d")

    filename = DATABASE + str(FECHA_CARGUE) +  ".csv"
    storage_client = storage.Client()
    bucket = storage_client.get_bucket('ct-tech-tof')
    blob = bucket.blob(filename)
    client = bigquery.Client()


    try:
        blob.delete() #Eliminar del storage-----
    except: 
        print("Eliminado de storage")

    try:
        QUERY = ("delete FROM `contento-bi.Contento_Tech.Consolidado_TOF` where Fecha_Cargue = '" + AHORA + "'")
        query_job = client.query(QUERY)
        rows2 = query_job.result()
    except: 
        print("Eliminado de bigquery")


    #Nos conectamos a la BD y obtenemos los registros
    conn = _mssql.connect(server=SERVER, user=USER, password=PASSWORD, database=DATABASE)
    conn.execute_query("SELECT * FROM Fanalca_Agendamientos.dbo.Fanalca_Agendamientos where CAST(Fecha_Gestion AS DATE) = CAST(GETDATE() AS DATE)")

    cloud_storage_rows = ""
    for row in conn:
        text_row =  ""
        text_row += '' + "|" if str(row[0]).encode('utf-8') is None else str(row[0]).encode('utf-8') + "|"
        text_row += '' + "|" if row[1].encode('utf-8') is None else row[1].encode('utf-8') + "|"
        text_row += '' + "|" if row[2].encode('ascii', 'ignore').decode('ascii') is None else row[2].encode('ascii', 'ignore').decode('ascii') + "|"
        text_row += '' + "|" if str(row[3]).encode('utf-8') is None else str(row[3]).encode('utf-8') + "|"
        text_row += '' + "|" if str(row[4]).encode('utf-8') is None else str(row[4]).encode('utf-8') + "|"
        text_row += '' + "|" if str(row[5]).encode('utf-8') is None else str(row[5]).encode('utf-8') + "|"
        text_row += '' + "|" if str(row[6]).encode('utf-8') is None else str(row[6]).encode('utf-8') + "|"
        text_row += '' + "|" if str(row[7]).encode('utf-8') is None else str(row[7]).encode('utf-8') + "|"
        text_row += '' + "|" if str(row[8]).encode('utf-8') is None else str(row[8]).encode('utf-8') + "|"
        text_row += '' + "|" if str(row[9]).encode('utf-8') is None else str(row[9]).encode('utf-8') + "|"
        text_row += '' + "|" if str(row[10]).encode('utf-8') is None else str(row[10]).encode('utf-8') + "|"
        text_row += '' + "|" if str(row[11]).encode('utf-8') is None else str(row[11]).encode('utf-8') + "|"
        text_row += '' + "|" if row[12].encode('ascii', 'ignore').decode('ascii') is None else row[12].encode('ascii', 'ignore').decode('ascii') + "|"
        text_row += '' + "|" if row[14].encode('ascii', 'ignore').decode('ascii') is None else row[14].encode('ascii', 'ignore').decode('ascii') + "|"
        text_row += '' + "|" if str(row[15]).encode('utf-8') is None else str(row[15]).encode('utf-8') + "|"
        text_row += '' + "|" if str(row[16]).encode('utf-8') is None else str(row[16]).encode('utf-8') + "|"
        text_row += '' + "|" if str(row[17]).encode('utf-8') is None else str(row[17]).encode('utf-8') + "\n"

        cloud_storage_rows += text_row

    
    gcscontroller.create_file(filename, cloud_storage_rows, "ct-tech-tof")   # Revisar problema con las subcarpetas
    flowAnswer = fanalca_agendamientos_beam.run(filename)

    conn.close()
    return flowAnswer





@tof_api.route("/tof_fanalca_recov", methods=['GET'])
def tof_fanalca_recov():

    import sys
    reload(sys)

    SERVER="192.168.20.63\DOKIMI"
    USER="etl_fanalca_agendamiento"
    PASSWORD="etl_fanalca_agendamiento04032020*"
    DATABASE="Fanalca_Agendamientos"
    FECHA_CARGUE = datetime.date.today()
    AHORA = FECHA_CARGUE.strftime("%Y-%m-%d")
    mespasado = datetime.datetime.now() - datetime.timedelta(days=30)
    mespasado_d = mespasado.strftime("%Y-%m-%d")

    filename = DATABASE + str(mespasado_d) + "-" + str(FECHA_CARGUE) + ".csv"
    storage_client = storage.Client()
    bucket = storage_client.get_bucket('ct-tech-tof')
    blob = bucket.blob(filename)
    client = bigquery.Client()


    try:
        blob.delete() #Eliminar del storage-----
        print("Eliminado de storage")
    except: 
        print("No se encontró el archivo: " + filename + "En Storage")

    try:
        QUERY = ("delete FROM `contento-bi.Contento_Tech.Consolidado_TOF` where SUBSTR(Fecha_Gestion,1,10) > '" + mespasado_d + "'")
        query_job = client.query(QUERY)
        rows2 = query_job.result()
        print("Eliminado de bigquery")
    except: 
        print("No se encontraron datos para eliminar entre las fechas: " + AHORA + " y " + mespasado_d)


    #Nos conectamos a la BD y obtenemos los registros
    conn = _mssql.connect(server=SERVER, user=USER, password=PASSWORD, database=DATABASE)
    conn.execute_query("SELECT * FROM Fanalca_Agendamientos.dbo.Fanalca_Agendamientos where CAST(Fecha_Gestion AS DATE) > '" +  mespasado_d + "'")

    cloud_storage_rows = ""
    for row in conn:
        text_row =  ""
        text_row += '' + "|" if str(row[0]).encode('utf-8') is None else str(row[0]).encode('utf-8') + "|"
        text_row += '' + "|" if row[1].encode('utf-8') is None else row[1].encode('utf-8') + "|"
        text_row += '' + "|" if row[2].encode('ascii', 'ignore').decode('ascii') is None else row[2].encode('ascii', 'ignore').decode('ascii') + "|"
        text_row += '' + "|" if str(row[3]).encode('utf-8') is None else str(row[3]).encode('utf-8') + "|"
        text_row += '' + "|" if str(row[4]).encode('utf-8') is None else str(row[4]).encode('utf-8') + "|"
        text_row += '' + "|" if str(row[5]).encode('utf-8') is None else str(row[5]).encode('utf-8') + "|"
        text_row += '' + "|" if str(row[6]).encode('utf-8') is None else str(row[6]).encode('utf-8') + "|"
        text_row += '' + "|" if str(row[7]).encode('utf-8') is None else str(row[7]).encode('utf-8') + "|"
        text_row += '' + "|" if str(row[8]).encode('utf-8') is None else str(row[8]).encode('utf-8') + "|"
        text_row += '' + "|" if str(row[9]).encode('utf-8') is None else str(row[9]).encode('utf-8') + "|"
        text_row += '' + "|" if str(row[10]).encode('utf-8') is None else str(row[10]).encode('utf-8') + "|"
        text_row += '' + "|" if str(row[11]).encode('utf-8') is None else str(row[11]).encode('utf-8') + "|"
        text_row += '' + "|" if row[12].encode('ascii', 'ignore').decode('ascii') is None else row[12].encode('ascii', 'ignore').decode('ascii') + "|"
        text_row += '' + "|" if row[14].encode('ascii', 'ignore').decode('ascii') is None else row[14].encode('ascii', 'ignore').decode('ascii') + "|"
        text_row += '' + "|" if str(row[15]).encode('utf-8') is None else str(row[15]).encode('utf-8') + "|"
        text_row += '' + "|" if str(row[16]).encode('utf-8') is None else str(row[16]).encode('utf-8') + "|"
        text_row += '' + "|" if str(row[17]).encode('utf-8') is None else str(row[17]).encode('utf-8') + "\n"

        cloud_storage_rows += text_row

    gcscontroller.create_file(filename, cloud_storage_rows, "ct-tech-tof")   # Revisar problema con las subcarpetas
    flowAnswer = fanalca_agendamientos_beam.run(filename)

    conn.close()
    return flowAnswer