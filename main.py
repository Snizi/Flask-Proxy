from flask import Flask, request, render_template, redirect, url_for, session
import requests
from bs4 import BeautifulSoup
import re

class CensoredWords:


    def __init__(self, keywords):
        self.CENSORED_WORD = "[palavra censurada]"
        self.censored_words = keywords
        

    def replace_words(self, text):
        for word in self.censored_words:
            text = re.sub(r'\b' + word + r'\b', self.CENSORED_WORD, text, flags=re.IGNORECASE)
        return text

class ProxyHandler:
    @staticmethod
    def handle_proxy(site, session_age):
        try:
            response = requests.get(site)
            soup = BeautifulSoup(response.text, 'html.parser')

            for a_tag in soup.find_all('a', href=True):
                if a_tag['href'].startswith('/'):
                    a_tag['href'] = f"http://localhost:3000/proxy/{site}{a_tag['href']}"
                elif a_tag['href']:
                    a_tag['href'] = f"http://localhost:3000/proxy/{a_tag['href']}"

            if session_age and int(session_age) < 18:
                with open('keywords.txt', 'r') as file:
                    keywords = file.read().splitlines()

                censored_words = CensoredWords(keywords)
                for tag in soup.find_all(['p', 'a', 'header', 'footer', 'nav', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'], string=True):
                    tag.string = censored_words.replace_words(tag.get_text())
            return str(soup)
        except requests.exceptions.RequestException as e:
            return str(e)

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

@app.route('/')
def index():
    if not session.get('age'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['age'] = request.form['age']
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('age', None)
    return redirect(url_for('index'))

@app.route('/proxy', methods=['GET', 'POST'])
def proxy():
    if request.method == 'POST':
        site = request.form.get('site', '')
        if site:
            return redirect(url_for('show_proxy', site=site))
    return redirect(url_for('index'))

@app.route('/proxy/<path:site>')
def show_proxy(site):
    session_age = session.get('age')
    return ProxyHandler.handle_proxy(site, session_age)

if __name__ == '__main__':
    app.run(host='localhost', port=3000)
