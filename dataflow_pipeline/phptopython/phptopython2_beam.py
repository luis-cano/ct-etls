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


now = datetime.datetime.now()


TABLE_SCHEMA = (
	'fecha_de_contacto:STRING,'
	'id_contento:STRING,'
	'id_lupe:STRING,'
	'causal:STRING,'
	'email:STRING,'
	'motivo_cliente_activo:STRING,'
	'sub_motivo_cliente_activo:STRING,'
	'motivo_cliente_no_activo:STRING,'
	'sub_motivo_cliente_no_activo:STRING,'
	'orden:STRING,'
	'forma_de_reactivacion:STRING,'
	'cupon:STRING,'
	'deuda:STRING,'
	'monto_deuda:STRING,'
	'flujo:STRING,'
	'usuario:STRING'
)

class formatearData(beam.DoFn):
	
	def process(self, element):
		arrayCSV = element.split(';')

		tupla= {
				'fecha_de_contacto': arrayCSV[0],
				'id_contento': arrayCSV[1],
				'id_lupe': arrayCSV[2],
				'causal': arrayCSV[3],
				'email': arrayCSV[4],
				'motivo_cliente_activo': arrayCSV[5],
				'sub_motivo_cliente_activo': arrayCSV[6],
				'motivo_cliente_no_activo': arrayCSV[7],
				'sub_motivo_cliente_no_activo': arrayCSV[8],
				'orden': arrayCSV[9],
				'forma_de_reactivacion': arrayCSV[10],
				'cupon': arrayCSV[11],
				'deuda': arrayCSV[12],
				'monto_deuda': arrayCSV[13],
				'flujo': arrayCSV[14],
				'usuario': arrayCSV[15]
				}
		
		return [tupla]



def run(archivo):

	gcs_path = "gs://ct-bridge" #Definicion de la raiz del bucket
	gcs_project = "contento-bi"

	mi_runer = ("DirectRunner", "DataflowRunner")[socket.gethostname()=="contentobi"]
	pipeline =  beam.Pipeline(runner=mi_runer, argv=[
        "--project", gcs_project,
        "--staging_location", ("%s/dataflow_files/staging_location" % gcs_path),
        "--temp_location", ("%s/dataflow_files/temp" % gcs_path),
        "--output", ("%s/dataflow_files/output" % gcs_path),
        "--setup_file", "./setup.py",
        "--max_num_workers", "25",
		"--subnetwork", "https://www.googleapis.com/compute/v1/projects/contento-bi/regions/us-central1/subnetworks/contento-subnet1"
	])
	
	lines = pipeline | 'Lectura de Archivo phpToPython' >> ReadFromText(archivo, skip_header_lines=1)
	transformed = (lines | 'Formatear Data phpToPython' >> beam.ParDo(formatearData()))
	transformed | 'Escritura a BigQuery phpToPython' >> beam.io.WriteToBigQuery(
		gcs_project + ":Rappi.flujo_react", 
		schema=TABLE_SCHEMA, 
		create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED, 
		write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND
		)

	jobObject = pipeline.run()
	# jobID = jobObject.job_id()

	return ("El proceso de cargue a bigquery fue ejecutado con exito")



