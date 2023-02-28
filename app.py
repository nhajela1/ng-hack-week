from flask import Flask, request, render_template, url_for
import sqlite3
import pandas as pd

app = Flask(__name__)



def get_df():
    conn = sqlite3.connect('database.sqlite')
    df = pd.read_sql_query("SELECT name, description, site FROM companies LIMIT 5", conn)
    conn.close()
    final_string = ""
    for index, row in df.iterrows():
        string_output = f"\n{row['name']}\n{'-' * 100}\n{row['description']}\n{'-' * 100}\n{row['site']}\n{'-' * 100}\n"
        final_string += string_output
    return final_string

dataframe = get_df()

@app.route('/', methods =['GET', 'POST'])
def retrieve_ans():
    if request.method == 'POST':
        industry_name = request.form.get('area')
        product_name = request.form.get('product')

        return render_template('index.html', product_name = dataframe)

    else:
        return render_template('index.html')
    
def home():
    return  render_template('index.html')
if __name__ == "__main__":
    app.run(debug=True)
