# Find Companies Explore Possibilities

## NG Hack Week - Team 6

This project is a essentially a tool to search for a list of vendors that sell products related to the entered query by the user. It uses the Tfidf similarity algorithm to take in the search query, breaks it down and searches through a huge database of companies and their descriptions to match the vendors with the query to get the most accurate companies. 

The company database has been web scraped from https://disfold.com/sectors-industries/ from the technology category. The names of the companies, their description and their website are scraped from a web scraper built in python using beautifulsoup. This data is being stored and managed using SQL connected to Python using the sqlite3 module. After scraping, this data is being used by the similarity algorithm to calculate and return the top companies based on the search query. Finally, these matches are displayed on the website in the same, name - description - url format. 

## Getting Started

1) Import the code from github to your local machine.
2) Install dependencies in your machine which include but are not limited to: nltk, pandas, numpy, bs4, requests, sklearn, re, flask
3) run the app.py python file
4) click the generated link in the terminal on your browser

