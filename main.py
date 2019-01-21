from __future__ import print_function, absolute_import

from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
from google.cloud import datastore
from google.cloud import bigquery
import logging
import uuid
import json
import urllib3
import requests
import os
import dataflow_pipeline.massive as pipeline
import cloud_storage_controller.cloud_storage_controller as gcscontroller

from procesos.bancolombia import bancolombia_api
from procesos.avon import avon_api
from procesos.negociadores import negociadores_api
from procesos.leonisa import leonisa_api
from procesos.Telefonia.login_logout import login_logout_api
from procesos.Telefonia.csat import csat_api
from procesos.Telefonia.agent_status import agent_status_api
from procesos.Telefonia.cdr import cdr_api
from procesos.bancolombia_castigada import bancolombia_castigada_api

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'OAuth2Credential.json'

app = Flask(__name__, static_url_path='/')
CORS(app)

app.register_blueprint(bancolombia_api, url_prefix='/bancolombia')
app.register_blueprint(avon_api, url_prefix='/avon')
app.register_blueprint(login_logout_api, url_prefix='/telefonia')
app.register_blueprint(csat_api, url_prefix='/telefonia')
app.register_blueprint(agent_status_api, url_prefix='/telefonia')
app.register_blueprint(cdr_api, url_prefix='/telefonia')
app.register_blueprint(negociadores_api, url_prefix='/negociadores')
app.register_blueprint(leonisa_api, url_prefix='/leonisa')
app.register_blueprint(bancolombia_castigada_api, url_prefix='/bancolombia_castigada')

@app.route("/", methods=['GET', 'POST'])
def raiz():

    response = {}
    response["code"] = 200
    response["description"] = "Usa los Endpoints de cada servicio de acuerdo a la documentacion"

    return jsonify(response), 200

@app.route("/balance", methods=['GET', 'POST'])
def start_dataflow():

    #Obtenemos los parametros
    filename = request.args.get('filename', default = '', type = str)

    if filename == '':
        response = {}
        response["code"] = 400
        response["description"] = "El valor del fichero en cloud storage (filename) es obligatorio"
        return jsonify(response), 400

    try:
        pipeline.run(filename)

        response = {}
        response["code"] = 200
        response["description"] = "Proceso iniciado correctamente, la sincronizacion terminara en unos momentos"
        response["input"] = filename

        return jsonify(response), 200
    except Exception as e:
        logging.exception(e)
        
        response = {}
        response["code"] = 500
        response["description"] = "Error: <pre>{}</pre>".format(e)

        return jsonify(response), 500

@app.errorhandler(500)
def server_error(e):
    logging.exception('Un error a ocurrido durante la ejecucion')
    return """
    Un error a ocurrido durante la ejecucion: <pre>{}</pre>
    Visualiza los logs para tener una trama completa.
    """.format(e), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
