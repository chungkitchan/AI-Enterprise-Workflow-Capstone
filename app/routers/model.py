from fastapi import APIRouter, Depends, HTTPException, Security, File, UploadFile, status, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import Optional
from ..config import *
from .log import *

import pandas as pd
import numpy as np
import json, traceback, sys, os, re, moment, pickle
from statsmodels.tsa.api import SARIMAX
from statsmodels.tsa.arima.model import ARIMA
from datetime import date, datetime
'''
from sklearn import svm
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
'''

router = APIRouter(
    prefix="/model",
    tags=["model"],
    responses={
        404: {"description": "Not found"},
        403: {"description": "Not authenticated, set your X-API-KEY headers to correct apiKey"}}
)

def train_arima(data, country=None):
    arima = ARIMA(data, order=ARIMA_ORDER)
    arima_model = arima.fit()
    if country:
        pickle_file = os.path.join(MODELS_DIRECTORY, 'arima_' + country.replace(' ','_') + '.pickle')
    else:
        pickle_file = os.path.join(MODELS_DIRECTORY, 'arima.pickle')
    with open(pickle_file,'wb') as file:
        pickle.dump(arima_model, file)
    log_train(TRAIN_LOG, 'arima', pickle_file, data.size)

def train_SARIMA_model(data, country=None):
    sarima = SARIMAX(
        data,
        order=ARIMA_ORDER,
        seasonal_order=SARIMA_SEASONAL_ORDER
    )
    sarima_model = sarima.fit()
    if country:
        pickle_file = os.path.join(MODELS_DIRECTORY, 'sarima_' + country.replace(' ','_') + '.pickle') 
    else:
        pickle_file = os.path.join(MODELS_DIRECTORY, 'sarima.pickle')
    with open(pickle_file,'wb') as file:
        pickle.dump(sarima_model, file)
    log_train(TRAIN_LOG, 'sarima', pickle_file, data.size)

def train_models():
    if not os.path.exists(MODELS_DIRECTORY):
        os.makedirs(MODELS_DIRECTORY)
    if not os.path.exists(os.path.join(INGEST_DIRECTORY,REVENUE_BY_COUNTRY)) or not os.path.exists(os.path.join(INGEST_DIRECTORY,ALL_REVENUE)):
        raise Exception("Training files do not exsists!!!")

    revenue_all = pd.read_csv(os.path.join(INGEST_DIRECTORY,ALL_REVENUE),header=0, index_col=0,parse_dates=['date'],usecols=["date", "revenue"])
    train_arima(revenue_all,country=None)
    train_SARIMA_model(revenue_all, country=None)

    revenue_country = pd.read_csv(os.path.join(INGEST_DIRECTORY,REVENUE_BY_COUNTRY),header=0, index_col=0,squeeze=True, parse_dates=['date'],usecols=["date","country","revenue"])
    countries = revenue_country['country'].unique()
    for country in countries:
        df = revenue_country[revenue_country['country']==country].reset_index()[['date','revenue']].set_index('date').resample('D').sum()
        train_arima(df, country=country)
        train_SARIMA_model(df, country=country)

async def predict(date,duration=30,country=None):
    if country:
        arima_model_path = os.path.join(MODELS_DIRECTORY,'arima_' + country.replace(' ','_') + '.pickle') 
        sarima_model_path = os.path.join(MODELS_DIRECTORY,'sarima_' + country.replace(' ','_') + '.pickle')
    else:
        arima_model_path = os.path.join(MODELS_DIRECTORY,'arima.pickle') 
        sarima_model_path = os.path.join(MODELS_DIRECTORY,'sarima.pickle')
    if not os.path.exists(arima_model_path) or not os.path.exists(sarima_model_path):
        raise Exception("Model files do not exsists!!!")
    with open(arima_model_path,'rb') as file:
        arima_model = pickle.load(file)
    with open(sarima_model_path,'rb') as file:
        sarima_model = pickle.load(file)
    #print(f"date({type(date)}): {date}, duration({type(duration)}): {duration}, country({type(country)})={country}")
    start =  moment.date(date)
    start_date = start.format("YYYY-M-D")
    end_date = start.add(day=duration).format("YYYY-M-D")
    #print(f"start_date({type(start_date)}): {start_date}, end_date({type(end_date)}): {end_date},")
    arima_result = arima_model.predict(start=start_date,end=end_date)
    sarima_result = sarima_model.predict(start=start_date,end=end_date)
    if country == None: country = 'all'
    log_predict(PREDICT_LOG, start_date, duration, country, arima_result.sum(), sarima_result.sum())
    return {'arima': {'daily': arima_result,'total': arima_result.sum()} ,
        'sarima': {'daily':sarima_result, 'total': sarima_result.sum()}}

@router.get("/train",include_in_schema=True, status_code=status.HTTP_202_ACCEPTED) 
async def train(background_tasks: BackgroundTasks):
    try:
        if not os.path.exists(os.path.join(INGEST_DIRECTORY,REVENUE_BY_COUNTRY)) or not os.path.exists(os.path.join(INGEST_DIRECTORY,ALL_REVENUE)):
            raise Exception("Training files do not exsists!!!")
        background_tasks.add_task(train_models)
        return {"status":"training initiated"}
    except:
        #traceback.print_exc()
        msg=traceback.format_exception(*sys.exc_info())
        print(msg)
        raise HTTPException(status_code=500, detail=msg)

@router.get("/predict",include_in_schema=True)
async def get_predict(start: date=Query(...), duration: int=Query(...), country: Optional[str]=Query(None)):
    try:
        result = await predict(start.strftime("%Y-%m-%d"), duration, country)
        #print(f"result: {result}")
        return result
    except:
        #traceback.print_exc()
        msg=traceback.format_exception(*sys.exc_info())
        print(msg)
        raise HTTPException(status_code=500, detail=msg)