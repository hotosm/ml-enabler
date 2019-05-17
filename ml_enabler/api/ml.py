from flask_restful import Resource


class StatusCheckAPI(Resource):

    def get(self):
        return {'hello': 'world'}, 200
