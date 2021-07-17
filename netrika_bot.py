from flask import jsonify

import netrika_api
from manage import *
from medsenger_api import AgentApiClient
from helpers import *
from models import *

medsenger_api = AgentApiClient(API_KEY, MAIN_HOST, AGENT_ID, API_DEBUG)


@app.route('/')
def index():
    return "Waiting for the thunder"


@app.route('/status', methods=['POST'])
@verify_json
def status(data):
    answer = {
        "is_tracking_data": True,
        "supported_scenarios": [],
        "tracked_contracts": [contract.id for contract in Contract.query.all()]
    }

    return jsonify(answer)


@app.route('/init', methods=['POST'])
@verify_json
def init(data):
    contract_id = data.get('contract_id')
    info = medsenger_api.get_patient_info(contract_id)
    patient = Patient.query.filter_by(id=info['id']).first()
    police = data.get('params', {}).get('police')

    if not police:
        abort(422)

    if not patient:
        netrika_id = netrika_api.add_patient(info['id'], info['email'], info['name'], info['birthday'], info['sex'], police)
        patient = Patient(id=info['id'], netrika_id=netrika_id, sent_documents=[])
        db.session.add(patient)

    netrika_api.create_case(info['id'], info['doctor_id'], contract_id, info['doctor_name'])

    contract = Contract(patient_id=info['id'])
    db.session.add(contract)

    return "ok"


@app.route('/remove', methods=['POST'])
@verify_json
def remove(data):
    c = Contract.query.filter_by(id=data.get('contract_id')).first()
    if c:
        db.session.delete(c)
        db.session.commit()
    return "ok"


# settings and views
@app.route('/settings', methods=['GET'])
@verify_args
def get_settings(args, form):
    return render_template('settings.html', contract=Contract.query.filter_by(id=args.get('contract_id')).first())


@app.route('/settings', methods=['POST'])
@verify_args
def set_settings(args, form):
    contract = Contract.query.filter_by(id=args.get('contract_id')).first()
    if contract:
        contract.doctor_comment = form.get('doctor_comment')
        contract.address = form.get('address')
        contract.card = form.get('card')
        db.session.commit()

    return "<strong>Спасибо, окно можно закрыть</strong><script>window.parent.postMessage('close-modal-success','*');</script>"



with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(HOST, PORT, debug=API_DEBUG)
