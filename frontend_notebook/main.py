from datetime import datetime
from ftplib import all_errors
from http.client import REQUEST_URI_TOO_LONG
import logging
from flask import Flask
from flask_restx import Resource, Api
from google.cloud import datastore
from google.cloud import language_v1 as language
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import NMF, LatentDirichletAllocation
import os
import io
import numpy
import six
import argparse
import json
import classifytext
import requests
import urllib
# from dash import dcc, html
# import plotly.express as px
# import pandas as pd


OUTPUT = "index.json"
RESOURCES = os.path.join(os.path.dirname(__file__), "resources")
QUERY_TEXT = """Google Home enables users to speak voice commands to interact
with services through the Home\'s intelligent personal assistant called
Google Assistant. A large number of services, both in-house and third-party,
are integrated, allowing users to listen to music, look at videos or photos,
or receive news updates entirely by voice."""
QUERY_CATEGORY = "/Computers & Electronics/Software"

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:/Users/kkgaf/Documents/DB_NLP_PROJECT/backend_api/key.json"


"""
This Flask app shows some examples of the types of requests you could build.
There is currently a GET request that will return all the data in GCP Datastore.
There is also a POST request that will analyse some given text then store the text and its sentiment in GCP Datastore.


The sentiment analysis of the text is being done by Google's NLP API. 
This API can be used to find the Sentiment, Entities, Entity-Sentiment, Syntax, and Content-classification of texts.
Find more about this API here:
https://cloud.google.com/natural-language/docs/basics
For sample code for implementation, look here (click 'Python' above the code samples):
https://cloud.google.com/natural-language/docs/how-to
Note: The analyze_text_sentiment() method below simply copies the 'Sentiment' part of the above documentation.


The database we are using is GCP Datastore (AKA Firestore in Datastore mode). 
This is a simple NoSQL Document database offering by Google:
https://cloud.google.com/datastore
You can access the database through the GCP Cloud Console (find Datastore in the side-menu)


Some ideas of things to build:
- At the moment, the code only stores the analysis of the first sentence of a given text. Modify the POST request to
 also analyse the rest of the sentences. 
- GET Request that returns a single entity based on its ID
- POST Request that will take a list of text items and give it a sentiment then store it in GCP Datastore
- DELETE Request to delete an entity from Datastore based on its ID
- Implement the other analyses that are possible with Google's NLP API


We are using Flask: https://flask.palletsprojects.com/en/2.0.x/
Flask RESTX is an extension of Flask that allows us to document the API with Swagger: https://flask-restx.readthedocs.io/en/latest/
"""

app = Flask(__name__)
api = Api(app)

parser_all = api.parser()
parser_all.add_argument("text", type=str, help="Text", location="args")
parser_all.add_argument("timestamp", type=str, help="Text", location="args")
parser_all.add_argument("title", type=str, help="Text", location="args")
parser_all.add_argument("bank", type=str, help="Text", location="args")

parser = api.parser()
parser.add_argument("text", type=str, help="Text", location="form")

#parser for GET
parser_get = api.parser()
parser_get.add_argument("text", type=int, help="Text", location="args")

@api.route("/api/text")
class Text(Resource):
    def get(self):
        """
        This GET request will return all the texts and sentiments that have been POSTed previously.
        """
        # Create a Cloud Datastore client.
        datastore_client = datastore.Client()

        # Get the datastore 'kind' which are 'Sentences'
        query = datastore_client.query(kind="Article")
        text_entities = list(query.fetch())

        # Parse the data into a dictionary format
        result = {}
        for text_entity in text_entities:
            result[str(text_entity.key.name)] = {
                "bank": str(text_entity["bank"]),
                "timestamp": str(text_entity["timestamp"]),
                "sentiment": str(text_entity["sentiment"]),
                "magnitude": str(text_entity["magnitude"]),
            }

        return result
    
    # DELETE Request to delete an entity from Datastore based on its ID
    @api.expect(parser)
    def delete(self):
        
        datastore_client = datastore.Client()
        
        #user types in the ID they want to delete
        args = parser.parse_args()
        text = args["text"]

        # Get the datastore 'kind' which are 'Sentences'
        query = datastore_client.query(kind="Article")
        text_entities = list(query.fetch())

        #if ID exists in list, get the query and delete it
        for e in text_entities:
            if e.key.name == text:
                datastore_client.delete(e.key)
                return ("Entity deleted for id: " + str(text))

        #return invalid if ID didn't delete
        return "Invlaid ID: Key not deleted"


    @api.expect(parser_all)
    def post(self):
        """
        This POST request will accept a 'text', perform sentiment analysis, store
        the result to datastore as an 'Article', and also return the result.
        """
        datastore_client = datastore.Client()
        args = parser_all.parse_args()
        text = args["text"]
        urllib.parse.unquote(text)
        current_datetime = args["timestamp"]
        title = args["title"]
        bank = args["bank"]
        # Get the sentiment score of the first sentence of the analysis (that's the [0] part)
        overall = analyze_text_sentiment_overall(text)
        result = {}

        sentiment = overall.get("sentiment score")
        magnitude = overall.get("sentiment magnitude")

        # Assign a label based on the score
        overall_sentiment = "unknown"
        if sentiment > 0:
            overall_sentiment = "positive"
        if sentiment < 0:
            overall_sentiment = "negative"
        if sentiment == 0:
            overall_sentiment = "neutral"

        # The kind for the new entity. This is so all 'Sentences' can be queried.
        kind = "Article"
        # Create a key to store into datastore
        key = datastore_client.key(kind, title)

        # Construct the new entity using the key. Set dictionary values for entity
        entity = datastore.Entity(key)
        entity["bank"] = bank
        entity["timestamp"] = current_datetime
        entity["sentiment"] = overall_sentiment
        entity["magnitude"] = magnitude

        # Save the new entity to Datastore.
        datastore_client.put(entity)

        result[str(entity.key.name)] = {
            "bank": bank,
            "timestamp": str(current_datetime),
            "sentiment": overall_sentiment,
            "magnitude": magnitude
        }

        return result

@api.route("/api/sentences")
class Sentences(Resource):
    def get(self):
        """
        This GET request will return all the texts and sentiments that have been POSTed previously.
        """
        # Create a Cloud Datastore client.
        datastore_client = datastore.Client()

        # Get the datastore 'kind' which are 'Sentences'
        query = datastore_client.query(kind="Sentences")
        text_entities = list(query.fetch())

        # Parse the data into a dictionary format
        result = {}
        for text_entity in text_entities:
            result[str(text_entity.key.name)] = {
                "bank": str(text_entity["bank"]),
                "timestamp": str(text_entity["timestamp"]),
                "sentiment": str(text_entity["sentiment"]),
                "magnitude": str(text_entity["magnitude"]),
            }

        return result
    
    # DELETE Request to delete an entity from Datastore based on its ID
    @api.expect(parser)
    def delete(self):
        
        datastore_client = datastore.Client()
        
        #user types in the ID they want to delete
        args = parser.parse_args()
        text = args["text"]

        # Get the datastore 'kind' which are 'Sentences'
        query = datastore_client.query(kind="Sentences")
        text_entities = list(query.fetch())

        #if ID exists in list, get the query and delete it
        for e in text_entities:
            if e.key.name == text:
                datastore_client.delete(e.key)
                return ("Entity deleted for id: " + str(text))

        #return invalid if ID didn't delete
        return "Invlaid ID: Key not deleted"


    @api.expect(parser_all)
    def post(self):
        """
        This POST request will accept a 'text', perform sentiment analysis, store
        the result to datastore as a 'Sentence', and also return the result.
        """
        datastore_client = datastore.Client()
        args = parser_all.parse_args()
        text = args["text"]
        current_datetime = args["timestamp"]
        title = args["title"]
        bank = args["bank"]
        # Get the sentiment score of the first sentence of the analysis (that's the [0] part)
        all_sentences = analyze_text_sentiment(text, title + " Article")
        result = {}

        for sentence in all_sentences:
            sentiment = sentence.get("sentiment score")
            magnitude = sentence.get("sentiment magnitude")
            txt = sentence.get("text")

            # Assign a label based on the score
            overall_sentiment = "unknown"
            if sentiment > 0:
                overall_sentiment = "positive"
            if sentiment < 0:
                overall_sentiment = "negative"
            if sentiment == 0:
                overall_sentiment = "neutral"

            # The kind for the new entity. This is so all 'Sentences' can be queried.
            kind = "Sentences"
            # Create a key to store into datastore
            key = datastore_client.key(kind, txt)
            #if datastore_client.get(key) != None:
            #    continue
            # If a key id is not specified then datastore will automatically generate one. For example, if we had:
            # key = datastore_client.key(kind, 'sample_task')
            # instead of the above, then 'sample_task' would be the key id used.

            # Construct the new entity using the key. Set dictionary values for entity
            entity = datastore.Entity(key)
            entity["bank"] = bank
            entity["timestamp"] = current_datetime
            entity["sentiment"] = overall_sentiment
            entity["magnitude"] = magnitude
            # Save the new entity to Datastore.
            datastore_client.put(entity)

            result[str(entity.key.name)] = {
                "bank": bank,
                "timestamp": str(current_datetime),
                "sentiment": overall_sentiment,
                "magnitude": magnitude
            }

        return result

#@api.route("/api/individual")
class Individual(Resource):
    #GET Request that returns a single entity based on its ID
    #@api.expect(parser_get)
    def get(self, text, kind):
        """
        This GET request will return a single entity based on its ID and type 
        """
        # Create a Cloud Datastore client.
        datastore_client = datastore.Client()

        # Get the datastore 'kind' which are 'Sentences'
        query = datastore_client.query(kind=kind)
        text_entities = list(query.fetch())
        
        #args = parser_get.parse_args()
        #text = args["text"]
        

        # Parse the data into a dictionary format
        result = {}
        for text_entity in text_entities:
            if text_entity.id == text:
                if kind == "Entities":
                    # formatting
                    mention = {}
                    '''for key, value in text_entity["mentions"].items():
                        subvalues = {}
                        for subkey, subvalue in value.items():
                            subvalues[subkey] = subvalue
                        submention = {}
                        submention[key] = subvalues
                        mention.update(submention)'''
                    result[str(text_entity.id)] = {
                        "entity name": str(text_entity["entity name"]),
                        "entity type": str(text_entity["entity type"]),
                        "entity salience": str(text_entity["entity salience"]),
                        "entity sentiment": str(text_entity["entity sentiment"]),
                        #"mentions": str(mention)
                    }
                elif kind == "KeyWords":
                    result[str(text_entity.id)] = {
                        "text keywords": str(text_entity["keywords"]),
                    }
                elif kind == "Classifications":
                    result[str(text_entity.id)] = {
                        "category": str(text_entity["category"]),
                        "confidence": str(text_entity["confidence"]),
                    }
            elif text_entity.key.name == text:
                if kind == "Sentences":
                    result[text_entity.key.name] = {
                        "text": str(text_entity["text"]),
                        "sentiment": str(text_entity["sentiment"]),
                    }
                elif kind == "Article":
                    result[text_entity.key.name] = {
                        #"bank": str(text_entity["bank"]),
                        #"timestamp": str(text_entity["timestamp"]),
                        "sentiment": str(text_entity["sentiment"]),
                        "magnitude": str(text_entity["magnitude"]),
                    }

        return result

    def delete(self, text, kind):
        """
        This DELETE request will delete a single entity based on its ID and type
        """
        datastore_client = datastore.Client()
        
        #text = int(text)

        query = datastore_client.query(kind=kind)
        text_entities = list(query.fetch())

        #if ID exists in list, get the query and delete it
        for e in text_entities:
            if e.id == int(text):
                datastore_client.delete(e.key)
                return ("Entity deleted for id: " + str(text))
            elif e.key.name == text:
                datastore_client.delete(e.key)
                return ("Entity deleted for id: " + str(text))

        #return invalid if ID didn't delete
        return "Invlaid ID: Key not deleted"


@api.route("/api/entity")
class EntityAnalysis(Resource):
    def get(self):
        """
        This GET request will return all the texts and sentiments that have been POSTed previously.
        """
        # Create a Cloud Datastore client.
        datastore_client = datastore.Client()

        # Get the datastore 'kind' which are 'Entities'
        query = datastore_client.query(kind="Entities")
        text_entities = list(query.fetch())

        # Parse the data into a dictionary format
        result = {}
        for text_entity in text_entities:
            mention = {}
            for key, value in text_entity["mentions"].items():
                subvalues = {}
                for subkey, subvalue in value.items():
                    subvalues[subkey] = subvalue
                submention = {}
                submention[key] = subvalues
                mention.update(submention)
            result[str(text_entity.id)] = {
                "entity name": str(text_entity["entity name"]),
                "timestamp": str(text_entity["timestamp"]),
                "entity type": str(text_entity["entity type"]),
                "entity salience": str(text_entity["entity salience"]),
                "entity sentiment": str(text_entity["entity sentiment"]),
                "mentions": str(mention)
            }

        return result
    
    # DELETE Request to delete an entity from Datastore based on its ID
    @api.expect(parser)
    def delete(self):
        
        datastore_client = datastore.Client()
        
        #user types in the ID they want to delete
        args = parser.parse_args()
        text = args["text"]
        text = int(text)

        # Get the datastore 'kind' which are 'Entities'
        query = datastore_client.query(kind="Entities")
        text_entities = list(query.fetch())

        #if ID exists in list, get the query and delete it
        for e in text_entities:
            if e.id == text:
                datastore_client.delete(e.key)
                return ("Entity deleted for id: " + str(text))

        #return invalid if ID didn't delete
        return "Invlaid ID: Key not deleted"
        
    @api.expect(parser)
    def post(self):
        """
        This POST request will accept a 'text', do entities analysis and return the results.
        """
        datastore_client = datastore.Client()

        args = parser.parse_args()
        text = args["text"]

        # Get the sentiment score of the first sentence of the analysis (that's the [0] part)
        # sentiment = analyze_text_sentiment(text)[0].get("sentiment score")
        all_sentences = analyze_text_entities(text)
        result = {}

        for sentence in all_sentences:
            name = sentence.get("entity name")
            typ = sentence.get("entity type")
            salience = sentence.get("entity salience")
            sentiment = sentence.get("entity sentiment")
            meta = sentence.get("metadata")
            mentions_list = sentence.get("mentions")

            words = {}

            if len(mentions_list):
                for ct, mention in enumerate(mentions_list):
                    words[str(ct)] = {
                        "text": mention[0],
                        "type": mention[1]
                    }

            # Assign a label based on the score
            overall_sentiment = "unknown"
            if sentiment > 0:
                overall_sentiment = "positive"
            if sentiment < 0:
                overall_sentiment = "negative"
            if sentiment == 0:
                overall_sentiment = "neutral"

            current_datetime = datetime.now()

            # The kind for the new entity. This is so all 'Entities' can be queried.
            kind = "Entities"

            # Create a key to store into datastore
            key = datastore_client.key(kind)
            # If a key id is not specified then datastore will automatically generate one. For example, if we had:
            # key = datastore_client.key(kind, 'sample_task')
            # instead of the above, then 'sample_task' would be the key id used.

            # Construct the new entity using the key. Set dictionary values for entity
            entity = datastore.Entity(key)
            entity["entity name"] = name
            entity["timestamp"] = current_datetime
            entity["entity type"] = typ.name
            entity["entity salience"] = salience
            entity["entity sentiment"] = overall_sentiment
            entity["mentions"] = words

            # Save the new entity to Datastore.
            datastore_client.put(entity)

            result[str(entity.key.id)] = {
                "entity name": name,
                "timestamp": str(current_datetime),
                "entity type": typ.name,
                "entity salience": salience,
                "entity sentiment": overall_sentiment,
                "mentions": words
            }

        return result

@api.route("/api/sentimentwebpage")
class SentimentWebpage(Resource):
    
    @api.expect(parser)
    def post(self):
        """
        This POST request will accept a 'text', analyze the sentiment analysis of the first sentence, store
        the result to datastore as a 'Sentence', and also return the result.
        """
        datastore_client = datastore.Client()

        args = parser.parse_args()
        webpageURL = args["text"]

        html_content = requests.get(webpageURL).text

        # Get the sentiment score of the first sentence of the analysis (that's the [0] part)
        # sentiment = analyze_text_sentiment(text)[0].get("sentiment score")
        all_sentences = analyze_text_sentimentWebpage(html_content)
        result = {}

        for sentence in all_sentences:
            sentiment = sentence.get("sentiment score")
            txt = sentence.get("text")

            # Assign a label based on the score
            overall_sentiment = "unknown"
            if sentiment > 0:
                overall_sentiment = "positive"
            if sentiment < 0:
                overall_sentiment = "negative"
            if sentiment == 0:
                overall_sentiment = "neutral"

            current_datetime = datetime.now()

            # The kind for the new entity. This is so all 'Sentences' can be queried.
            kind = "Sentences"

            # Create a key to store into datastore
            key = datastore_client.key(kind)

            # Construct the new entity using the key. Set dictionary values for entity
            entity = datastore.Entity(key)
            entity["text"] = txt
            entity["timestamp"] = current_datetime
            entity["sentiment"] = overall_sentiment

            # Save the new entity to Datastore.
            datastore_client.put(entity)

            result[str(entity.key.id)] = {
                "text": txt,
                "timestamp": str(current_datetime),
                "sentiment": overall_sentiment,
            }

        return result


#Classify content POST method
@api.route("/api/classificationstrings")
class ClassificationStrings(Resource):
   
    @api.expect(parser)
    def post(self):
        """
        This POST request will accept a 'text' of at least 20 words, classify the content into category labels for all sentences, assign confidence scores, store
        the result to datastore as a 'Sentence', and also return the result.
        """
        datastore_client = datastore.Client()

        args = parser.parse_args()
        text = args["text"]

        # classify the input text into a list of categories-confidence pairs
        #since the funciton returns a dictionary, we will store 'result' as a dict
        all_classifies_dict = classifytext.classify(text)
        result = {}

        for key in all_classifies_dict:
            category = key
            confidence = all_classifies_dict[key]

            current_datetime = datetime.now()

            # The kind for the new entity. This is so all 'Sentences' can be queried.
            kind = "Classifications"

            # Create a key to store into datastore
            key = datastore_client.key(kind)
            # If a key id is not specified then datastore will automatically generate one. For example, if we had:
            # key = datastore_client.key(kind, 'sample_task')
            # instead of the above, then 'sample_task' would be the key id used.

            # Construct the new entity using the key. Set dictionary values for entity
            entity = datastore.Entity(key)
            entity["category"] = category
            entity["confidence"] = confidence
            entity["timestamp"] = current_datetime

            # Save the new entity to Datastore.
            datastore_client.put(entity)

            result[str(entity.key.id)] = {
                "category": category,
                "confidence": str(confidence),
                "timestamp": str(current_datetime),
            }

        return result

#Classify content POST method with a URL input
@api.route("/api/classificationwebpage")
class ClassificationWebpage(Resource):
    @api.expect(parser_get)
    def get(self):
         """
         This GET request will return all the category labels and confidences that have been POSTed previously based on text/URL put in.
         """
         # Create a Cloud Datastore client.
         datastore_client = datastore.Client()

         # Get the datastore 'kind' which are 'Classifications'
         query = datastore_client.query(kind="Classifications")
         text_entities = list(query.fetch())

         # Parse the data into a dictionary format
         result = {}
         for text_entity in text_entities:
             result[str(text_entity.id)] = {
                "category": str(text_entity["category"]),
                "confidence": str(text_entity["confidence"]),
                "timestamp": str(text_entity["timestamp"]),
                
             }

         return result

    @api.expect(parser)
    def post(self):
        """
        This POST request will accept a URL string, classify the content into categroy labels for all sentences, assign confidence scores, store
        the result to datastore as a 'Sentence', and also return the result.
        """
        datastore_client = datastore.Client()

        #user passes in URL
        args = parser.parse_args()
        webpageURL = args["text"]


        #convert input url to html, store in variable. pass that variabel to classifyWeb function below
        html_content = requests.get(webpageURL).text
            
        # classify the input text into a list of categories-confidence pairs
        #since the funciton returns a dictionary, we will store 'result' as a dict
        all_classifies_dict = classifytext.classifyWeb(html_content)
        result = {}

        for key in all_classifies_dict:
            category = key
            confidence = all_classifies_dict[key]

            current_datetime = datetime.now()

            # The kind for the new entity. This is so all 'Sentences' can be queried.
            kind = "Classifications"

            # Create a key to store into datastore
            key = datastore_client.key(kind)
            # If a key id is not specified then datastore will automatically generate one. For example, if we had:
            # key = datastore_client.key(kind, 'sample_task')
            # instead of the above, then 'sample_task' would be the key id used.

            # Construct the new entity using the key. Set dictionary values for entity
            entity = datastore.Entity(key)
            entity["category"] = category
            entity["confidence"] = confidence
            entity["timestamp"] = current_datetime

            # Save the new entity to Datastore.
            datastore_client.put(entity)

            result[str(entity.key.id)] = {
                "category": category,
                "confidence": str(confidence),
                "timestamp": str(current_datetime),
            }

        return result
       

@app.errorhandler(500)
def server_error(e):
    logging.exception("An error occurred during a request.")
    return (
        """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(
            e
        ),
        500,
    )

def analyze_text_sentimentWebpage(text):
    """
    This is modified from the Google NLP API documentation found here:
    https://cloud.google.com/natural-language/docs/analyzing-sentiment
    It makes a call to the Google NLP API to retrieve sentiment analysis.
    """
    client = language.LanguageServiceClient()
    document = language.Document(content=text, type_=language.Document.Type.HTML)

    response = client.analyze_sentiment(request={"document": document})


    # Format the results as a dictionary
    sentiment = response.document_sentiment
    results = dict(
        text=text,
        score=f"{sentiment.score:.1%}",
        magnitude=f"{sentiment.magnitude:.1%}",
    )

    # Print the results for observation
    for k, v in results.items():
        print(f"{k:10}: {v}")

    # Get sentiment for all sentences in the document
    sentence_sentiment = []
    for sentence in response.sentences:
        item = {}
        item["text"] = sentence.text.content
        item["sentiment score"] = sentence.sentiment.score
        item["sentiment magnitude"] = sentence.sentiment.magnitude
        sentence_sentiment.append(item)

    return sentence_sentiment
    

def analyze_text_sentiment(text, title):
    """
    This is modified from the Google NLP API documentation found here:
    https://cloud.google.com/natural-language/docs/analyzing-sentiment
    It makes a call to the Google NLP API to retrieve sentiment analysis.
    """
    client = language.LanguageServiceClient()
    document = language.Document(content=text, type_=language.Document.Type.PLAIN_TEXT)

    response = client.analyze_sentiment(document=document)

    # Format the results as a dictionary
    sentiment = response.document_sentiment
    '''results = dict(
        text=title,
        score=f"{sentiment.score:.1%}",
        magnitude=f"{sentiment.magnitude:.1%}",
    )'''

    results = {}
    results["text"] = title
    results["sentiment score"] = sentiment.score
    results["sentiment magnitude"] = sentiment.magnitude

    # Print the results for observation
    for k, v in results.items():
        print(f"{k:10}: {v}")

    # Get sentiment for all sentences in the document
    sentence_sentiment = []
    sentence_sentiment.append(results)
    for sentence in response.sentences:
        item = {}
        item["text"] = sentence.text.content
        item["sentiment score"] = sentence.sentiment.score
        item["sentiment magnitude"] = sentence.sentiment.magnitude
        sentence_sentiment.append(item)

    return sentence_sentiment

def analyze_text_sentiment_overall(text):
    """
    This is modified from the Google NLP API documentation found here:
    https://cloud.google.com/natural-language/docs/analyzing-sentiment
    It makes a call to the Google NLP API to retrieve sentiment analysis.
    """
    client = language.LanguageServiceClient()
    document = language.Document(content=text, type_=language.Document.Type.PLAIN_TEXT)

    response = client.analyze_sentiment(document=document)

    # Format the results as a dictionary
    sentiment = response.document_sentiment
    '''results = dict(
        score=f"{sentiment.score:.1%}",
        magnitude=f"{sentiment.magnitude:.1%}",
    )'''

    result = {}
    result["sentiment score"] = sentiment.score
    result["sentiment magnitude"] = sentiment.magnitude

    return result


def analyze_text_entities(text):
    """
    This is modified from the Google NLP API documentation found here:
    https://cloud.google.com/natural-language/docs/analyzing-sentiment
    It makes a call to the Google NLP API to retrieve entities analysis.
    """
    client = language.LanguageServiceClient()
    document = language.Document(content=text, type_=language.Document.Type.PLAIN_TEXT)

    response = client.analyze_entities(document=document)

    # Get sentiment for all sentences in the document
    entities_analysis = []
    for entity in response.entities:
        item = {}
        item["entity name"] = entity.name
        item["entity type"] = entity.type_
        item["entity salience"] = entity.salience
        item["entity sentiment"] = entity.sentiment.score
        metadata = []
        for metadata_name, metadata_value in entity.metadata.items():
            metadata.append([metadata_name, metadata_value])
        item["metadata"] = metadata
        mentions = []
        for mention in entity.mentions:
            mentions.append([mention.text.content, language.EntityMention.Type(mention.type_).name])
        item["mentions"] = mentions
        entities_analysis.append(item)

    return entities_analysis


# Deleting stored data if necessary

def delete_all_test_data(kind):
    """Function for Deleting all the Test data"""

    ds_client = datastore.Client()
    fetch_limit = 100

    print('-- Deleting all entities --')

    entities = True
    while entities:
        query = ds_client.query(kind=kind)
        entities = list(query.fetch(limit=fetch_limit))
        for entity in entities:
            print('Deleting: {}'.format(entity))
            ds_client.delete(entity.key)

#delete_all_test_data("Sentences")

@api.route("/api/topics")
class TopicAnalyser(Resource):
    # get the topic analysis of the whole text
    def display_topics(self, model, feature_names, no_top_words):
        for topic_idx, topic in enumerate(model.components_):
            return " ".join([feature_names[i] for i in topic.argsort()[:-no_top_words - 1:-1]])

    def analyse(self, data):
        # HYPERPARAMETERS: Consider tuning
        no_features = 120
        no_topics = 5

        data = [data]

        # LDA can only use raw term counts for LDA because it is a probabilistic graphical model
        tf_vectorizer = CountVectorizer(max_df=1, min_df=1, max_features=no_features, stop_words='english')
        tf = tf_vectorizer.fit_transform(data)
        tf_feature_names = tf_vectorizer.get_feature_names()
        # Run LDA
        model = LatentDirichletAllocation(n_components=no_topics, max_iter=5, learning_method='online',
                                    learning_offset=50., random_state=0).fit(tf)

        # HYPERPARAMETER: Consider tuning
        no_top_words = 15

        topics = self.display_topics(model, tf_feature_names, no_top_words)
        return topics

    def get(self):
        """
        This GET request will return all the keywords that have been POSTed previously.
        """
        # Create a Cloud Datastore client.
        datastore_client = datastore.Client()

        # Get the datastore 'kind' which are 'KeyWords'
        query = datastore_client.query(kind="KeyWords")
        text_entities = list(query.fetch())

        # Parse the data into a dictionary format
        result = {}
        for text_entity in text_entities:
            result[str(text_entity.id)] = {
                "text keywords": str(text_entity["keywords"]),
                "timestamp": str(text_entity["timestamp"])
            }

        return result
    
    # DELETE Request to delete an entity from Datastore based on its ID
    @api.expect(parser)
    def delete(self):
        
        datastore_client = datastore.Client()
        
        #user types in the ID they want to delete
        args = parser.parse_args()
        text = args["text"]
        text = int(text)

        # Get the datastore 'kind' which are 'KeyWords'
        query = datastore_client.query(kind="KeyWords")
        text_entities = list(query.fetch())

        #if ID exists in list, get the query and delete it
        for e in text_entities:
            if e.id == text:
                datastore_client.delete(e.key)
                return ("Entity deleted for id: " + str(text))

        #return invalid if ID didn't delete
        return "Invlaid ID: Key not deleted"

    @api.expect(parser)
    def post(self):
        """
        This POST request will accept a 'text', do keywords analysis and return the results.
        """
        datastore_client = datastore.Client()

        args = parser.parse_args()
        text = args["text"]

        # Get the sentiment score of the first sentence of the analysis (that's the [0] part)
        all_sentences = self.analyse(text)

        result = {}

        current_datetime = datetime.now()

        # The kind for the new entity. This is so all 'KeyWords' can be queried.
        kind = "KeyWords"

        # Create a key to store into datastore
        key = datastore_client.key(kind)
        # If a key id is not specified then datastore will automatically generate one. For example, if we had:
        # key = datastore_client.key(kind, 'sample_task')
        # instead of the above, then 'sample_task' would be the key id used.

        # Construct the new entity using the key. Set dictionary values for entity
        entity = datastore.Entity(key)
        entity["keywords"] = all_sentences
        entity["timestamp"] = current_datetime

        # Save the new entity to Datastore.
        datastore_client.put(entity)

        result[str(entity.key.id)] = {
            "text keywords": all_sentences,
            "timestamp": str(current_datetime)
        }

        return result

@api.route("/api/clean")
class DeleteKind(Resource):
    def delete(self):
        """
        This DELETE request will delete EVERYTHING in the database. Proceed with caution.
        """
        delete_all_test_data("Text")
        delete_all_test_data("Classifications")
        delete_all_test_data("KeyWords")
        delete_all_test_data("Sentences")
        delete_all_test_data("Entities")
        delete_all_test_data("Article")

@api.route("/api/analysis")
class CompleteAnalysis(Resource):
    def get(self):
        """
        This GET request will return all the complete analyses that have been POSTed previously.
        """
        # Create a Cloud Datastore client.
        datastore_client = datastore.Client()

        # Get the datastore 'kind' which are 'Text'
        query = datastore_client.query(kind="Text")
        text_entities = list(query.fetch())

        individual = Individual()

        result = {}

        for text_entity in text_entities:
            sentiment_analysis = {}
            entity_analysis = {}
            keyword_analysis = {}
            content_analysis = {}

            for key in text_entity["sentiment analysis"]:
                print(key)
                sentiment_analysis.update(individual.get(key, "Article"))
            for key in text_entity["entity analysis"]:
                entity_analysis.update(individual.get(int(key), "Entities"))
            for key in text_entity["keyword analysis"]:
                keyword_analysis.update(individual.get(int(key), "KeyWords"))
            for key in text_entity["content analysis"]:
                content_analysis.update(individual.get(int(key), "Classifications"))
            
            print(sentiment_analysis)

            result[str(text_entity.id)] = {
                "timestamp": str(text_entity["timestamp"]),
                "title": str(text_entity["title"]),
                "bank": str(text_entity["bank"]),
                "sentiment analysis": sentiment_analysis,
                "entity analysis": entity_analysis,
                "keyword analysis": keyword_analysis,
                "content analysis": content_analysis
            }

        return result

    @api.expect(parser)
    def delete(self):
        
        datastore_client = datastore.Client()
        
        #user types in the ID they want to delete
        args = parser.parse_args()
        text = args["text"]
        #text = int(text)

        query = datastore_client.query(kind="Text")
        text_entities = list(query.fetch())

        individual = Individual()

        for text_entity in text_entities:
            if text_entity.id == int(text):
                for key in text_entity["entity analysis"]:
                    individual.delete(int(key), "Entities")
                for key in text_entity["keyword analysis"]:
                    individual.delete(int(key), "KeyWords")
                for key in text_entity["content analysis"]:
                    individual.delete(int(key), "Classifications")
            
                datastore_client.delete(text_entity.key)
                return ("Entity deleted for id: " + str(text))

            elif e.key.name == text:
                for key in text_entity["sentiment analysis"]:
                    individual.delete(key, "Article")

                datastore_client.delete(text_entity.key)
                return ("Entity deleted for id: " + str(text))
        
        #return invalid if ID didn't delete
        return "Invlaid ID: Key not deleted"

    @api.expect(parser_all)
    def post(self):
        """
        This POST request will accept a 'text', do complete analysis (content, entities, sentiment, keywords) 
        and return the results.
        """
        sentiment = Text()
        entities = EntityAnalysis()
        topic = TopicAnalyser()
        content = ClassificationStrings()

        args = parser_all.parse_args()
        current_datetime = args["timestamp"]
        title = args["title"]
        bank = args["bank"]

        sentiment_analysis = sentiment.post()
        entity_analysis = entities.post()
        topic_analysis = topic.post()
        content_analysis = content.post()

        datastore_client = datastore.Client()
        kind = "Text"
        key = datastore_client.key(kind)
        entity = datastore.Entity(key)

        entity["title"] = title
        entity["bank"] = bank
        entity["timestamp"] = current_datetime
        entity["sentiment analysis"] = list(sentiment_analysis.keys())
        entity["entity analysis"] = list(entity_analysis.keys())
        entity["keyword analysis"] = list(topic_analysis.keys())
        entity["content analysis"] = list(content_analysis.keys())

        datastore_client.put(entity)

        result = {}

        result[str(entity.key.id)] = {
            "title": title,
            "bank": bank,
            "timestamp": str(current_datetime),
            "sentiment analysis": sentiment_analysis,
            "entity analysis": entity_analysis,
            "keyword analysis": topic_analysis,
            "content analysis": content_analysis
        }

        return result


if __name__ == "__main__":
    # This is useds when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host="127.0.0.1", port=8080, debug=True)
    
    