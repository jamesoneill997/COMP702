from flask import Flask, request, jsonify, make_response
from flask_restful import Resource, Api
from data import Data

app = Flask("oddsgenie-api")
api = Api(app)

class ResultsHandler(Resource):
    def get(self):
        try:
            http_code = 200
            response = Data().get_results()
        except Exception as e:
            print(e)
            http_code = 500
            response = {
                "code": http_code,
                "status": "error",
                "error": "Something went wrong", 
            }
        return make_response(jsonify(response), http_code)
        
class RaceCardsHandler(Resource):
    def get(self):
        try:
            http_code = 200
            response = Data().get_racecards()
        except Exception as e:
            print(e)
            http_code = 500
            response = {
                "code": http_code,
                "status": "error",
                "error": "Something went wrong", 
            }
        return make_response(jsonify(response), http_code)
    
api.add_resource(ResultsHandler, '/api/v1/results')
api.add_resource(RaceCardsHandler, '/api/v1/racecards')
if __name__ == '__main__':
    app.run(debug=True)