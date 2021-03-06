# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
import logging
import re
import json
import requests
import uuid
import time
import os
import socket
import argparse
import uuid
import datetime
import apache_beam as beam
from apache_beam.io import ReadFromText
from apache_beam.io import WriteToText
from apache_beam.io.filesystems import FileSystems
from apache_beam.metrics import Metrics
from apache_beam.metrics.metric import MetricsFilter
from apache_beam import pvalue
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions

####################### PARAMETROS DE LA TABLA EN BQ ##########################

TABLE_SCHEMA = (
			'idkey:STRING,'
			'Fecha_Cargue:STRING,'
			'Id_Gestion:STRING,'
			'Id_Cod_Gestion:STRING,'
			'Nombre_Codigo:STRING,'
			# 'Observacion:STRING,'
			'Fecha_Gestion:STRING,'
			'Usuario_gestion:STRING,'
			'Documento:STRING,'
			'Num_Obligacion:STRING,'
			'Id_Campana:STRING,'
			'Nombre_Campana:STRING'
)

class formatearData(beam.DoFn):
	
	def process(self, element):
		arrayCSV = element.split('|')

		tupla= {
				'idkey': str(uuid.uuid4()),
				'Fecha_Cargue': datetime.datetime.today().strftime('%Y-%m-%d'),
				'Id_Gestion': arrayCSV[0],
				'Id_Cod_Gestion': arrayCSV[1],
				'Nombre_Codigo': arrayCSV[2],
				# 'Observacion': arrayCSV[3],
				'Fecha_Gestion': arrayCSV[3],
				'Usuario_gestion': arrayCSV[4],
				'Documento': arrayCSV[5],
				'Num_Obligacion': arrayCSV[6],
				'Id_Campana': arrayCSV[7],
				'Nombre_Campana': arrayCSV[8]

				}
		
		return [tupla]

############################ CODIGO DE EJECUCION ###################################
def run(filename):

	gcs_path = 'gs://ct-tech-tof/bancolombiaSAC' #Definicion de la raiz del bucket
	gcs_project = "contento-bi"
	FECHA_CARGUE = str(datetime.date.today())

	mi_runner = ("DirectRunner", "DataflowRunner")[socket.gethostname()=="contentobi"]
	pipeline =  beam.Pipeline(runner=mi_runner, argv=[
        "--project", gcs_project,
        "--staging_location", ("%s/dataflow_files/staging_location" % gcs_path),
        "--temp_location", ("%s/dataflow_files/temp" % gcs_path),
        "--output", ("%s/dataflow_files/output" % gcs_path),
        "--setup_file", "./setup.py",
        "--max_num_workers", "15",
		"--subnetwork", "https://www.googleapis.com/compute/v1/projects/contento-bi/regions/us-central1/subnetworks/contento-subnet1"
    ])

	lines = pipeline | 'BANCOSAC_TECH Lectura de Archivo' >> ReadFromText(gcs_path + '/' + filename)
	transformed = (lines | 'BANCOSAC_TECH Formatear Data' >> beam.ParDo(formatearData()))
	# transformed | 'Escribir en Archivo' >> WriteToText(gcs_path + "/" + "REWORK",file_name_suffix='.csv',shard_name_template='')

	transformed | 'BANCOSAC_TECH Escritura a BigQuery Bridge' >> beam.io.WriteToBigQuery(
		gcs_project + ":Contento_Tech.Gestiones_BancoSAC", 
		schema=TABLE_SCHEMA, 
		create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED, 
		write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND)

	jobObject = pipeline.run()
	return ("R!")


################################################################################