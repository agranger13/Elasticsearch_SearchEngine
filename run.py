from flask import (Flask, request, make_response, render_template, jsonify, redirect, url_for)
from elasticsearch import Elasticsearch, helpers
import requests
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap
from wtforms import StringField, SubmitField, SelectMultipleField, DateField, SelectField
from wtforms.validators import DataRequired

app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = 'secret_key'
Bootstrap(app)

@app.route("/")
def hello():
    return "Running"


@app.route("/home")
def home():
    return render_template("content.html")

@app.route("/test", methods=['GET', 'POST'])
def test():
    print("test target")
    return render_template("content.html")

@app.route("/load", methods=['GET', 'POST'])
def load():
    es = ES_Data()
    searchform = SearchForm()
    message = ""
    if request.method == 'POST':
        search_input = searchform.search.data
        category_input = searchform.category.data
        premier_cours_input = searchform.start_date.data
        dernier_cours_input = searchform.end_date.data

        print(search_input)
        # result_search = es.search(search_input, category_input, premier_cours_input, dernier_cours_input)
        result_data,mean_hours = es.search(search_input, category_input, premier_cours_input, dernier_cours_input)
        # mean_hours = round(result_search["aggregations"]["mean_hours"]["value"], 2)
        response = make_response(render_template("table.html", searchform=searchform, data=result_data, mean_hours=mean_hours))
        return response
    else :
        # result_get = es.get_all()
        result_data,mean_hours = es.get_all()
        # result_data = result_get["hits"]["hits"]
        # mean_hours = round(result_get["aggregations"]["mean_hours"]["value"],2)
        response = make_response(render_template("table.html", searchform=searchform, data=result_data, mean_hours=mean_hours))
        return response

class ES_Data:

    def __init__(self):
        self.es = Elasticsearch(
            [
                'http://localhost:9200/'
            ],
            timeout=100
        )

    def get_all(self):
        es_query = {
          "aggs": {
            "mean_hours": {
              "avg": {
                "field": "nb_heure"
              }
            }
          }
        }
        es_result = self.es.search(index="projet_matiere", body=es_query, size=1000)
        mean=round(es_result["aggregations"]["mean_hours"]["value"],2) if es_result["aggregations"]["mean_hours"]["value"] is not None else "No result"

        return es_result["hits"]["hits"], mean

    def search(self, search_input, category_input, premier_cours_input, dernier_cours_input):
        should_match=0
        if len(search_input)>0 : should_match+=1

        if (premier_cours_input is not None) :
            should_match+=1
        else :
            premier_cours_input="0"

        if (dernier_cours_input is not None) :
            should_match+=1
        else :
            dernier_cours_input="0"

        if (category_input!="Toutes") :
            should_match+=1
        else :
            if(should_match==0):
                return self.get_all()

        print(should_match)

        es_query = {
          "query":{
            "bool":{
              "minimum_should_match": should_match,
              "should": [
                {
                  "match": {"matiere": search_input}
                },
                {
                  "match": {"description": search_input}
                },
                {
                  "match": {"categorie": category_input}
                },
                {
                  "match": {"premier_cours": premier_cours_input}
                },
                {
                  "match": {"dernier_cours": dernier_cours_input}
                }
              ]
            }
          },
          "aggs": {
            "mean_hours": {
              "avg": {
                "field": "nb_heure"
              }
            }
          }
        }
        es_result = self.es.search(index="projet_matiere", body=es_query, size=1000)
        mean=round(es_result["aggregations"]["mean_hours"]["value"],2) if es_result["aggregations"]["mean_hours"]["value"] is not None else "No result"

        return es_result["hits"]["hits"], mean

class SearchForm(FlaskForm):
    search=StringField('Texte', render_kw={"placeholder": "Search..."})
    category=SelectField(u'Catégories', choices=[('Toutes'), ('Mathématiques'), ('IA'), ('Développement')])
    start_date = DateField('Premier Cours', format='%Y-%m-%d', render_kw={"placeholder": "YYYY-MM-dd"})
    end_date = DateField('dernier_cours', format='%Y-%m-%d', render_kw={"placeholder": "YYYY-MM-dd"})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000)
