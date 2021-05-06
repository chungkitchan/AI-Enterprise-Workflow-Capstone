from fastapi import APIRouter, Depends, HTTPException, Security, File, UploadFile, status, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional
from ..config import *
from .log import *
import pandas as pd
import numpy as np
import json, traceback, sys, os, re

router = APIRouter(
    prefix="/ingest",
    tags=["ingest"],
    responses={
        404: {"description": "Not found"},
        403: {"description": "Not authenticated, set your X-API-KEY headers to correct apiKey"}}
)

def fetch_data(data_dir):
    """
    laod all json formatted files into a dataframe
    """
    ## input testing
    if not os.path.isdir(data_dir):
        raise Exception("specified data dir does not exist")
    if not len(os.listdir(data_dir)) > 0:
        raise Exception("specified data dir does not contain any files")

    file_list = [os.path.join(data_dir,f) for f in os.listdir(data_dir) if re.search("\.json",f)]
    correct_columns = ['country', 'customer_id', 'day', 'invoice', 'month',
                       'price', 'stream_id', 'times_viewed', 'year']

    ## read data into a temp structure
    all_months = {}
    for file_name in file_list:
        df = pd.read_json(file_name)
        all_months[os.path.split(file_name)[-1]] = df

    ## ensure the data are formatted with correct columns
    for f,df in all_months.items():
        cols = set(df.columns.tolist())
        if 'StreamID' in cols:
             df.rename(columns={'StreamID':'stream_id'},inplace=True)
        if 'TimesViewed' in cols:
            df.rename(columns={'TimesViewed':'times_viewed'},inplace=True)
        if 'total_price' in cols:
            df.rename(columns={'total_price':'price'},inplace=True)

        cols = df.columns.tolist()
        if sorted(cols) != correct_columns:
            raise Exception("columns name could not be matched to correct cols")

    ## concat all of the data
    df = pd.concat(list(all_months.values()),sort=True)
    years,months,days = df['year'].values,df['month'].values,df['day'].values 
    dates = ["{}-{}-{}".format(years[i],str(months[i]).zfill(2),str(days[i]).zfill(2)) for i in range(df.shape[0])]
    df['invoice_date'] = np.array(dates,dtype='datetime64[D]')
    df['invoice'] = [re.sub("\D+","",i) for i in df['invoice'].values]
    
    ## sort by date and reset the index
    df.sort_values(by='invoice_date',inplace=True)
    df.reset_index(drop=True,inplace=True)
    df = df[df["price"]>0]
    create_summary(df)

def create_summary(df):
    column_names={
        "price sum": "revenue",
        "invoice_date":"date",
        "invoice count":"purchases",
        "invoice nunique": "unique_invoices",
        "stream_id nunique": "unique_streams",
        "times_viewed sum": "total_views"
    }
    revenue_all = df.groupby(['invoice_date']).agg({"price":["sum"],"invoice":["count","nunique"],"stream_id":["nunique"],"times_viewed":["sum"]})
    revenue_country = df.groupby(['invoice_date','country']).agg({"price":["sum"],"invoice":["count","nunique"],"stream_id":["nunique"],"times_viewed":["sum"]})
    revenue_all.columns = [' '.join(col).strip() for col in revenue_all.columns.values]
    revenue_country.columns = [' '.join(col).strip() for col in revenue_country.columns.values]
    revenue_all.reset_index(inplace=True)
    revenue_country.reset_index(inplace=True)
    revenue_all.rename(columns=column_names, inplace=True)
    revenue_country.rename(columns=column_names, inplace=True)
    revenue_all.to_csv(os.path.join(INGEST_DIRECTORY,ALL_REVENUE))
    revenue_country.to_csv(os.path.join(INGEST_DIRECTORY,REVENUE_BY_COUNTRY))
    #df.to_csv(os.path.join(INGEST_DIRECTORY,ALL_TRAINING_DATA))
    log_ingest(INGEST_LOG, revenue_country.size, revenue_all.size)

@router.get("/",include_in_schema=True, status_code=status.HTTP_202_ACCEPTED) 
async def ingest(background_tasks: BackgroundTasks):
    try:
        if not os.path.exists(INGEST_DIRECTORY):
            os.makedirs(INGEST_DIRECTORY)
        if not os.path.exists(TRAIN_DIRECTORY):
            raise Exception("Training data directory not exsists!!!")
        background_tasks.add_task(fetch_data, TRAIN_DIRECTORY)
        return {"status":"ingestion initiated"}
    except:
        #traceback.print_exc()
        msg=traceback.format_exception(*sys.exc_info())
        print(msg)
        raise HTTPException(status_code=500, detail=msg)