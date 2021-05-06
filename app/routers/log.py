from fastapi import APIRouter, Depends, HTTPException, Security, File, UploadFile, status, BackgroundTasks, Query, Response
from pydantic import BaseModel, Field
from typing import Optional
import csv, uuid, os, traceback, sys
from datetime import datetime
from ..config import *
import pandas as pd

router = APIRouter(
    prefix="/logs",
    tags=["logs"],
    responses={
        404: {"description": "Not found"},
        403: {"description": "Not authenticated, set your X-API-KEY headers to correct apiKey"}}
)

def write_log(log_name, log_data, log_header):
    full_log_name = os.path.join(LOG_DIRECTORY,log_name)
    if not os.path.exists(LOG_DIRECTORY):
        os.makedirs(LOG_DIRECTORY)
    if not os.path.exists(full_log_name):
        do_write_header = True
    else:
        do_write_header = False
    #print(f"log name: {full_log_name}, do_write_header: {do_write_header}, log_data: {log_data}")
    with open(full_log_name, 'a+', newline='') as csvfile:
        writer = csv.writer(csvfile)
        if do_write_header: writer.writerow(log_header)
        writer.writerow(log_data)

def log_train(log_name, model, name, size):
    now = datetime.now()
    id = str(uuid.uuid4())
    log = [id, now, model, name, size]
    headers = ['id', 'datetime', 'model', 'name', 'size']
    write_log(log_name, log, headers)

def log_ingest(log_name, country_size, total_size):
    now = datetime.now()
    id = str(uuid.uuid4())
    log = [id, now, country_size, total_size]
    headers = ['id', 'datetime', 'countries size', 'total size']
    write_log(log_name, log, headers)

def log_predict(log_name, start, duration, country, arima_result, sarima_result):
    now = datetime.now()
    id = str(uuid.uuid4())
    log = [id, now, start, duration, country, arima_result, sarima_result]
    headers = ['id', 'datetime', 'query start', 'query duration','query country', 'arima prediction', 'sarima prediction']
    write_log(log_name, log, headers)
    
@router.get("/",include_in_schema=True)
async def get_logs(response: Response, type: str=Query(...), mode: str=Query(...)):
    try:
        if type == "ingest" and (mode=='prod' or mode=='test'):
            if mode=="test": logs_name = 'test-ingest.csv'
            else: logs_name = INGEST_LOG
        elif type == "train" and (mode=='prod' or mode=='test'):
            if mode=="test": logs_name = 'test-train.csv'
            else: logs_name = TRAIN_LOG
        elif type == "predict" and (mode=='prod' or mode=='test'):
            if mode=="test": logs_name = 'test-predict.csv'
            else: logs_name = PREDICT_LOG
        else:
            response.status_code = 400
            return {"error":"type must be either: ingest, train or predict and mode must be either: prod or test"}
        #print(f"get_logs(), type: {type}, mode: {mode}, logs_name: {logs_name}")
        logs = pd.read_csv(os.path.join(LOG_DIRECTORY, logs_name)).to_dict(orient='records')
        #print(f"get_logs(): logs: {logs}")
        return { 'log': logs}
    except:
        #traceback.print_exc()
        msg=traceback.format_exception(*sys.exc_info())
        print(msg)
        raise HTTPException(status_code=500, detail=msg)