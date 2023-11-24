from flask import Flask, jsonify, request

from src.services.api_service import APIService

app = Flask(__name__)


@app.route("/chart-data", methods=["GET"])
def get_chart_data():
    '''
    GET endpoint that provides ability to query a persistent database for
    tracked tokens over a period of time partitioned by a step size
    '''
    try:
        token_symbol = str(request.args.get("token_symbol")).upper()
        step = int(request.args.get("time_unit_in_hours"))

        # Validate request params before proceeding to service layer
        if step <= 0:
            return (
                jsonify(error="`time_unit_in_hours` must be greater than 0."),
                400,
            )
        elif not token_symbol or step is None:
            return (
                jsonify(
                    error="Both `token_symbol` and `time_unit_in_hours` query params are required."
                ),
                400,
            )

        service = APIService()
        res = service.get_data_and_convert(token_symbol, step)
        if len(res) == 0:
            return (
                jsonify(error=f"{token_symbol} is not currently tracked!"),
                404,
            )

        return jsonify(res), 200

    except ValueError:
        return (
            jsonify(error="`time_unit_in_hours` must be an integer."),
            400,
        )
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify(error="An error occurred."), 500


def start_server(debug=False):
    print("Starting the server...")
    app.run(debug=debug)
