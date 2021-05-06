# AI Enterprise Workflow - Capstone Project Submission

Chung Kit Chan (email: chanck@sg.ibm.com) submission for the IBM AI Enterprise Workflow course on Coursera.

## Run app local

### Clone the git repo
<code>git clone https://github.com/chungkitchan/AI-Enterprise-Workflow-Capstone.git</code>

### Install the prereq
<code>pip install -r requirements.txt</code>

### Run the application
<code>uvicorn app.main:app</code>

### Test the application
<code>py.test -v</code>
To test individual test name, eg. to test prediction use:
<code>py.test -k prediction -v</code>

### Build docker image 
<code>docker build -t app .</code>

### Run docker
<code>docker run -it --rm -p 8000:8000  --name app app</code>

## Endpoint
The endpoint are documented in openapi format. It can be accessed throught the following URL:
<code>http://localhost:8000/docs</code>

## Marking Criteria
* Are there unit tests for the API?  
  Yes, see tests/test_all.py  

* Are there unit tests for the model?  
  Yes, see tests/test_all.py  

* Are there unit tests for the logging?  
  Yes, see tests/test_all.py  

* Can all of the unit tests be run with a single script and do all of the unit tests pass?  
  Yes, run <code>py.test</code>  

* Is there a mechanism to monitor performance?  
  Yes, see app/monitor.py  

* Was there an attempt to isolate the read/write unit tests from production models and logs?  
  Yes, see app/routers/log.py  

* Does the API work as expected? For example, can you get predictions for a specific country as well as for all countries combined?  
  Yes, for specific country run <code>curl -L "http://127.0.0.1:8000/model/predict?start=2019-01-20&duration=10&country=Australia"</code>  
  For all country run <code>curl -L "http://127.0.0.1:8000/model/predict?start=2019-01-20&duration=10"</code>   

* Does the data ingestion exists as a function or script to facilitate automation?  
  Yes, see app/ingestion.py  

* Were multiple models compared?  
  Yes, see notebook/compare.ipynb  

* Did the EDA investigation use visualizations?  
  Yes, see notebook/analyze.ipynb  

* Is everything containerized within a working Docker image?  
  Yes, see Dockerfile  

* Did they use a visualization to compare their model to the baseline model?   
  Yes, see notebook/compare.ipynb  
