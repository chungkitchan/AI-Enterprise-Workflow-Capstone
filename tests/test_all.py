import pytest, json, unittest
from starlette.testclient import TestClient
from app.main import app
from app.config import *
from app.routers.log import *

def test_01_ingestion(test_app):
    response = test_app.get("/ingest")
    assert response.status_code == 202
    assert response.json()=={"status":"ingestion initiated"}

def test_02_training(test_app):
    response = test_app.get("/model/train")
    assert response.status_code == 202
    assert response.json()=={"status":"training initiated"}

def test_03_prediction_country(test_app):
    response = test_app.get("/model/predict/?start=2019-01-13&duration=10&country=Australia")
    #json_data = json.loads(response.data)
    assert response.status_code == 200
    assert 'arima' in response.json()
    assert 'sarima' in response.json()

def test_04_prediction_total(test_app):
    response = test_app.get("/model/predict/?start=2019-01-13&duration=10")
    assert response.status_code == 200
    assert 'arima' in response.json()
    assert 'sarima' in response.json()

def test_05_log_predict():
        test_log='test-predict.csv'
        log_file = os.path.join(LOG_DIRECTORY, test_log)
        log_predict(test_log, '2019-01-01', 20, 'Australia', 1234, 1234)
        assert os.path.exists(log_file)

def test_06_log_ingest():
        test_log='test-ingest.csv'
        log_file = os.path.join(LOG_DIRECTORY, test_log)
        log_ingest(test_log, 1234, 1234)
        assert os.path.exists(log_file)

def test_07_log_train():
        test_log='test-train.csv'
        log_file = os.path.join(LOG_DIRECTORY, test_log)
        log_train(test_log,'test', 'test', 1234)
        assert os.path.exists(log_file)

def test_08_log_get(test_app):
    response = test_app.get("/logs/?type=ingest&mode=test")
    assert response.status_code == 200
    assert 'log' in response.json()