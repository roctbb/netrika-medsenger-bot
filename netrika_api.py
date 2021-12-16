import base64
from datetime import datetime

import requests
from config import *


def add_patient(patient_id, email, name, birthday, sex, policy):
    d, m, Y = birthday.split('.')
    data = {
        "command": "add_patient",
        "params": {
            "birthdate": "{}-{}-{}".format(Y, m, d),
            "name": name,
            "patient_id": patient_id,
            "email": email,
            "sex": sex,
            "snils": policy
        }
    }

    print("Send to {}: {}".format(NETRIKA_HOST, data))

    try:
        answer = requests.post(NETRIKA_HOST, json=data)
        print(answer.text)

        if answer.json().get('status') != 'ok':
            return None

        return answer.json().get('data', {}).get("patient_netrika_id")
    except Exception as e:
        print(e)
        return None


def create_case(patient_id, doctor_id, contract_id, doctor_name):
    data = {
        "command": "create_case",
        "params": {
            "open_date": datetime.now().strftime('%Y-%m-%d'),
            "doctor_name": doctor_name,
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "contract_id": contract_id
        }
    }

    print("Send to {}: {}".format(NETRIKA_HOST, data))

    try:
        answer = requests.post(NETRIKA_HOST, json=data)
        print(answer.text)

        if answer.json().get('status') != 'ok':
            return None

        return True
    except Exception as e:
        print(e)
        return None


def encounter_search(patient_netrika_id):
    data = {
        "command": "encounter_search",
        "params": {
            "patient_netrika_id": patient_netrika_id
        }
    }

    print("Send to {}: {}".format(NETRIKA_HOST, data))

    try:
        answer = requests.post(NETRIKA_HOST, json=data)
        print(answer.text)

        if answer.json().get('status') != 'ok':
            return None

        return answer.json().get('data')
    except Exception as e:
        print(e)
        return None


def echo_document(document_id):
    data = {
        "command": "echo_document",
        "params": {
            "document_id": document_id
        }
    }

    print("Send to {}: {}".format(NETRIKA_HOST, data))
    answer = requests.post(NETRIKA_HOST, json=data)
    try:
        print(answer.headers)
        return ["document.pdf", answer.headers.get('Content-Type'), base64.b64encode(answer.content)]
    except Exception as e:
        print(e)
        return None
