from flask import Flask, request, render_template, url_for
import sqlite3
import pandas as pd
import disfold as dis

app = Flask(__name__)
length = 5
names = []
descriptions = []
sites = []

@app.route('/', methods =['GET', 'POST'])
def retrieve_ans():
    if request.method == 'POST':
        product_name = request.form.get('product')
        df = dis.final_similarity_scores(5, product_name) 
        names = list(df['name'])
        descriptions = list(df['description'])
        sites = list(df['site'])
        length = len(df.index)
        
        return render_template('index.html', length = length, names = names, descriptions = descriptions, sites = sites)

    else:
        return render_template('index.html', length = 0, names = [], descriptions = [], sites = [])
    
def home():
    return  render_template('index.html', length = 0, names = names, descriptions = descriptions, sites = sites)
if __name__ == "__main__":
    app.run(debug=True)
