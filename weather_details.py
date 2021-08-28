from flask import Flask, render_template,request,redirect
import sqlite3 as sql
import requests
import json
import os
from datetime import datetime
import redis

app=Flask(__name__)
rdb=redis.Redis(host='127.0.0.1',port=6379,db=0)

@app.before_first_request
def before():
    database='weatherreport.db'
    with sql.connect(database) as conn:
        Cursor=conn.cursor()
        query='''CREATE TABLE IF NOT EXISTS weather
                (sno INTEGER PRIMARY KEY AUTOINCREMENT, city_name text[20])'''
        Cursor.execute(query)
        conn.commit()


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/getdata',methods=['GET','POST'])
def getdata():
    if(request.method=='POST'):
        data=dict(request.form)
        values=list(data.values())
        with sql.connect('weatherreport.db') as conn:
            cursor=conn.cursor()
            query='INSERT INTO weather(city_name) values(?)'
            cursor.execute(query,values)
            conn.commit()
    return redirect('/display')
    
    
@app.route('/display')
def display():
    with sql.connect('weatherreport.db') as conn:
        cursor=conn.cursor()
        # now fetch data from buyerdetails table
        query="select * from weather"
        cursor.execute(query)
        data=cursor.fetchall()
        city_name=data[0][1]
        API_key=os.environ['WEATHER_API_TOKEN']
        kelvin_degree_tf=-273.15
        api_endpoint=rf'https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={API_key}'
        response=requests.get(api_endpoint)
        if response.ok:
            data=response.json()
            temperature_K=data['main']['temp']
            temp1=data['main']['temp_max']
            temp2=data['main']['temp_min']
            w=data['wind']['speed']
            wind=(w*3.6)
            wind=str(round(wind))
            wind=wind+'km/h'
            e = datetime.now()
            time=e.strftime("%I:%M %p")
            date=e.strftime("%a %b %d")
            temperature_dC=temperature_K+kelvin_degree_tf
            temp_max=temp1+kelvin_degree_tf
            temp_max=round(temp_max*100)/100
            temp_min=temp2+kelvin_degree_tf
            temp_min=round(temp_min*100)/100
            temperature_dC=round(temperature_dC*100)/100
            query="delete from weather"
            cursor.execute(query) 
            conn.commit() 
            
            return render_template('display.html',temperature=temperature_dC,temp_max=temp_max,temp_min=temp_min,
            wind=wind,date=date,time=time,d=data)  


@app.route('/dayforecast/<string:s>')
def dayforecast(s):
        if s in rdb:
            print('from cache')
            data=(rdb.get(s)).decode()
            l=json.loads(data)
            d=l['list']
                
        else:
            city_name=s
            print(city_name)
            units='metric'
            API_key=os.environ['WEATHER_API_TOKEN']
            api_endpoint=rf'https://api.openweathermap.org/data/2.5/forecast?q={city_name}&appid={API_key}&units={units}'
            print('from api')
            response=requests.get(api_endpoint)
            data=response.json()
            rdb.set(city_name,json.dumps(data))
            d=data['list']
            
        return render_template('dayforecast.html',data=d)  


app.run(debug=True)