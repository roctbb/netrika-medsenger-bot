import uuid

from flask import jsonify, abort, render_template, make_response

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


def init_patient(patient, contract_id, uid):
    if patient.police:
        info = medsenger_api.get_patient_info(contract_id)
        patient.netrika_id = netrika_api.add_patient(uid, info['email'], info['name'], info['birthday'], info['sex'],
                                                     patient.police)
        patient.available_documents = None


def init_case(contract_id, uid):
    info = medsenger_api.get_patient_info(contract_id)
    netrika_api.create_case(uid, info['doctor_id'], contract_id, info['doctor_name'])


@app.route('/init', methods=['POST'])
@verify_json
def init(data):
    contract_id = data.get('contract_id')
    info = medsenger_api.get_patient_info(contract_id)
    patient = Patient.query.filter_by(id=info['id']).first()
    uid = str(uuid.uuid4())

    if not patient:
        netrika_id = None
        patient = Patient(id=info['id'], netrika_id=netrika_id, sent_documents=[])
        patient.police = data.get('params', {}).get('police')
        init_patient(patient, contract_id, uid)
        db.session.add(patient)

    if patient.netrika_id:
        init_case(contract_id, uid)

    contract = Contract(id=contract_id, patient_id=info['id'])
    db.session.add(contract)
    db.session.commit()

    return "ok"


@app.route('/remove', methods=['POST'])
@verify_json
def remove(data):
    c = Contract.query.filter_by(id=data.get('contract_id')).first()
    if c:
        db.session.delete(c)
        db.session.commit()
    return "ok"


@app.route('/setup', methods=['GET'])
@verify_args
def get_setup(args, form):
    return gs(args, form)


@app.route('/setup', methods=['POST'])
@verify_args
def set_setup(args, form):
    return ss(args, form)


# settings and views
@app.route('/settings', methods=['GET'])
@verify_args
def get_settings(args, form):
    return gs(args, form)


@app.route('/settings', methods=['POST'])
@verify_args
def set_settings(args, form):
    return ss(args, form)


def gs(args, form):
    contract = Contract.query.filter_by(id=args.get('contract_id')).first()
    if not contract:
        abort(404)
    return render_template('settings.html', contract=contract, error='')


def ss(args, form):
    contract_id = args.get('contract_id')
    contract = Contract.query.filter_by(id=contract_id).first()
    uid = str(uuid.uuid4())

    if contract:
        patient = contract.patient
        patient.police = form.get('police')
        init_patient(patient, contract_id, uid)
        db.session.commit()

        if patient.netrika_id:
            init_case(contract_id, uid)
            return "<strong>Спасибо, окно можно закрыть</strong><script>window.parent.postMessage('close-modal-success','*');</script>"
        else:
            return render_template('settings.html', contract=contract, error='Проверьте правильность полиса.')
    else:
        abort(404)


@app.route('/documents', methods=['GET'])
@verify_args
def documents(args, form):
    contract_id = args.get('contract_id')
    contract = Contract.query.filter_by(id=contract_id).first()

    if contract:
        patient = contract.patient

        if patient.netrika_id:
            if patient.available_documents:
                documents = patient.available_documents
            else:
                documents = netrika_api.encounter_search(patient.netrika_id)
                patient.available_documents = documents
                db.session.commit()
            return render_template('documents.html', documents=documents)
        else:
            return render_template('documents.html', documents=[])
    else:
        abort(404)


@app.route('/documents', methods=['POST'])
@verify_args
def download(args, form):
    contract_id = args.get('contract_id')
    download = form.get('download')
    contract = Contract.query.filter_by(id=contract_id).first()

    document_id = form.get('document_id')

    if contract and contract.patient.netrika_id:
        if not download:

            documents = list(filter(lambda x: x['document_id'] == document_id, contract.patient.available_documents))

            if not documents:
                abort(404)

            document = documents[0]
            name = document['description']
            org = document['organization']
            date = document['indexed']

            answer = netrika_api.echo_document(document_id)
            if not answer:
                abort(404)

            _, _, data = answer

            print("requested document ", document_id)

            return render_template('document.html', name=name, org=org, date=date, data=str(data).lstrip("b'").rstrip("'"), contract=contract, document_id=document_id)
        else:
            answer = netrika_api.get_document(document_id)

            if not answer:
                abort(404)

            name, mime, data = answer

            print("requested document ", document_id)

            response = make_response(data)
            response.headers.set('Content-Type', mime)
            response.headers.set(
                'Content-Disposition', 'attachment', filename=name)
            return response
    else:
        abort(404)


def tasks(app):
    with app.app_context():
        patients = Patient.query.all()

        for patient in patients:
            if patient.netrika_id and patient.contracts:
                if not patient.sent_documents:
                    patient.sent_documents = []
                docs = netrika_api.encounter_search(patient.netrika_id)

                if not patient.available_documents:
                    patient.available_documents = docs

                if not patient.sent_documents:
                    patient.sent_documents = []
                    for doc in docs:
                        patient.sent_documents.append(doc.get('document_id'))
                else:
                    new_docs = filter(lambda doc: doc.get('document_id') and doc.get('document_id') not in patient.sent_documents, docs)
                    for doc in new_docs:
                        attachment = netrika_api.echo_document(doc.get('document_id'))
                        for contract in patient.contracts:
                            medsenger_api.send_message(contract_id=contract.id, text="Новый документ в региональной системе: {}".format(doc.get('description')), only_doctor=True, need_answer=False,
                                                       attachments=[attachment])
                        patient.sent_documents.append(doc.get('document_id'))
                        print("I will save doc {} to {}".format(doc.get('document_id'), patient.id))
        db.session.commit()


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(HOST, PORT, debug=API_DEBUG)
