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
	'id:STRING,'
	'fecha:STRING,'
	'accion:STRING,'
	'idLupe:STRING,'
	'idAgente:STRING,'
	'correo:STRING,'
	'telMarcado:STRING,'
	'ultimoPedido28Dias:STRING,'
	'motivoRegreso:STRING,'
	'comentarioTipificacion:STRING,'
	'Motivo:STRING,'
	'SubMotivio:STRING,'
	'Causal:STRING,'
	'Codigo:STRING,'
	'SubCodigo:STRING,'
	'Deuda:STRING,'
	'Deuda_Mayor:STRING,'
	'Deuda_Contra:STRING,'
	'MotivoChurcn:STRING,'
	'SubMotivoChurcn:STRING,'
	'Tipo_Reactivacion:STRING,'
	'Id_Pedido:STRING,'
	'Ayuda:STRING,'
	'Descrip_Ayuda:STRING,'
	'Cupon:STRING'
	)

class formatearData(beam.DoFn):
	
	def process(self, element):
		arrayCSV = element.split(';')

		tupla= {'id': arrayCSV[0],
				'fecha': arrayCSV[1],
				'accion': arrayCSV[2],
				'idLupe': arrayCSV[3],
				'idAgente': arrayCSV[4],
				'correo': arrayCSV[5],
				'telMarcado': arrayCSV[6],
				'ultimoPedido28Dias': arrayCSV[7],
				'motivoRegreso': arrayCSV[8],
				'comentarioTipificacion': arrayCSV[9],
				'Motivo': arrayCSV[10],
				'SubMotivio': arrayCSV[11],
				'Causal': arrayCSV[12],
				'Codigo': arrayCSV[13],
				'SubCodigo': arrayCSV[14],
				'Deuda': arrayCSV[15],
				'Deuda_Mayor': arrayCSV[16],
				'Deuda_Contra': arrayCSV[17],
				'MotivoChurcn': arrayCSV[18],
				'SubMotivoChurcn': arrayCSV[19],
				'Tipo_Reactivacion': arrayCSV[20],
				'Id_Pedido': arrayCSV[21],
				'Ayuda': arrayCSV[22],
				'Descrip_Ayuda': arrayCSV[23],
				'Cupon': arrayCSV[24]
				}
		
		return [tupla]



def run(output):

	gcs_path = "gs://ct-rappi" #Definicion de la raiz del bucket
	gcs_project = "contento-bi"

	mi_runer = ("DirectRunner", "DataflowRunner")[socket.gethostname()=="contentobi"]
	pipeline =  beam.Pipeline(runner=mi_runer, argv=[
        "--project", gcs_project,
        "--staging_location", ("%s/dataflow_files/staging_location" % gcs_path),
        "--temp_location", ("%s/dataflow_files/temp" % gcs_path),
        "--output", ("%s/dataflow_files/output" % gcs_path),
        "--setup_file", "./setup.py",
        "--max_num_workers", "10",
		"--subnetwork", "https://www.googleapis.com/compute/v1/projects/contento-bi/regions/us-central1/subnetworks/contento-subnet1"
	])
	
	lines = pipeline | 'Lectura de Archivo' >> ReadFromText(output)
	transformed = (lines | 'Formatear Data' >> beam.ParDo(formatearData()))
	transformed | 'Escritura a BigQuery Rappi' >> beam.io.WriteToBigQuery(
		gcs_project + ":Rappi.flujo_react2", 
		schema=TABLE_SCHEMA, 
		create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED, 
		write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND
		)

	jobObject = pipeline.run()
	# jobID = jobObject.job_id()

	return ("El proceso de cargue a bigquery fue ejecutado con exito")



