import os, json, pickle, hashlib
from pathlib import Path
from datetime import datetime, timezone

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from web3 import Web3

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
MODEL_PATH = BASE_DIR / "ml" / "models" / "crop_disease_model.pkl"
ARTIFACT_PATH = BASE_DIR / "blockchain" / "build" / "contracts" / "FarmRecord.json"

app = Flask(__name__)
CORS(app)

GANACHE_URL = os.getenv("GANACHE_URL", "http://127.0.0.1:7545")
GANACHE_ACCOUNT = os.getenv("GANACHE_ACCOUNT", "")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS", "")

_model = None
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
_contract = None

def load_model():
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model not found: {MODEL_PATH}. Run the notebook first.")
        with open(MODEL_PATH, "rb") as f:
            _model = pickle.load(f)
    return _model

def load_contract():
    global _contract
    if _contract is not None:
        return _contract
    if not ARTIFACT_PATH.exists():
        raise FileNotFoundError("Truffle artifact missing. Run 'truffle compile' and 'truffle migrate --network development' first.")
    artifact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    address = CONTRACT_ADDRESS
    if not address:
        networks = artifact.get("networks", {})
        if networks:
            # Select the latest deployment entry in the artifact.
            address = list(networks.values())[-1].get("address", "")
    if not address:
        raise RuntimeError("Contract address is unavailable. Set CONTRACT_ADDRESS or deploy with Truffle.")
    if not w3.is_connected():
        raise ConnectionError(f"Cannot connect to Ganache at {GANACHE_URL}")
    _contract = w3.eth.contract(address=Web3.to_checksum_address(address), abi=artifact["abi"])
    return _contract

def get_account():
    if not w3.is_connected():
        raise ConnectionError(f"Cannot connect to Ganache at {GANACHE_URL}")
    account = GANACHE_ACCOUNT or (w3.eth.accounts[0] if w3.eth.accounts else "")
    if not account:
        raise RuntimeError("No Ganache account available. Set GANACHE_ACCOUNT.")
    return Web3.to_checksum_address(account)

def canonical_record(data):
    clean = {k: str(data.get(k, "")).strip() for k in ["farmerId","farmerName","crop","disease","farmInfo","recordInfo"]}
    return json.dumps(clean, sort_keys=True, separators=(",", ":"))

def make_hash(data):
    return hashlib.sha256(canonical_record(data).encode("utf-8")).hexdigest()

@app.get("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.get("/frontend/<path:path>")
def frontend(path):
    return send_from_directory(FRONTEND_DIR, path)

@app.get("/api/health")
def health():
    connected = bool(w3.is_connected())
    return jsonify({"status":"ok", "ganacheConnected":connected, "contractArtifact":ARTIFACT_PATH.exists()})

@app.post("/api/predict")
def predict():
    try:
        data = request.get_json(force=True) or {}
        required = ["Crop","Temperature","Humidity","Soil_Moisture","Rainfall","pH"]
        missing = [x for x in required if x not in data or data[x] in (None, "")]
        if missing:
            return jsonify({"error":f"Missing fields: {', '.join(missing)}"}), 400
        model = load_model()
        import pandas as pd
        row = pd.DataFrame([{k: data[k] for k in required}])
        row[required[1:]] = row[required[1:]].apply(pd.to_numeric, errors="raise")
        prediction = str(model.predict(row)[0])
        confidence = None
        if hasattr(model, "predict_proba"):
            confidence = float(max(model.predict_proba(row)[0]))
        return jsonify({"prediction":prediction,"confidence":confidence,"status":"success"})
    except Exception as exc:
        return jsonify({"error":str(exc)}), 500

@app.post("/api/records")
def add_record():
    try:
        data = request.get_json(force=True) or {}
        required = ["farmerId","farmerName","crop","disease","farmInfo","recordInfo"]
        missing = [x for x in required if not str(data.get(x, "")).strip()]
        if missing:
            return jsonify({"error":f"Missing fields: {', '.join(missing)}"}), 400
        contract = load_contract(); account = get_account()
        record_hash_hex = make_hash(data)
        record_hash = Web3.to_bytes(hexstr="0x"+record_hash_hex)
        # Record ID is deterministic from the canonical record, so duplicate data maps to the same ID.
        record_id = "REC-" + record_hash_hex[:20]
        tx = contract.functions.addRecord(record_id, data["farmerId"], data["farmerName"], data["crop"], data["disease"], data["farmInfo"], data["recordInfo"], record_hash).transact({"from":account})
        receipt = w3.eth.wait_for_transaction_receipt(tx)
        return jsonify({"recordId":record_id,"recordHash":"0x"+record_hash_hex,"transactionHash":receipt.transactionHash.hex(),"blockNumber":receipt.blockNumber,"status":"confirmed","timestamp":datetime.now(timezone.utc).isoformat()})
    except Exception as exc:
        return jsonify({"error":str(exc)}), 500

@app.get("/api/records/<record_id>")
def get_record(record_id):
    try:
        record = load_contract().functions.getRecord(record_id).call()
        return jsonify({"recordId":record[0],"farmerId":record[1],"farmerName":record[2],"crop":record[3],"disease":record[4],"farmInfo":record[5],"recordInfo":record[6],"recordHash":Web3.to_hex(record[7]),"timestamp":record[8],"creator":record[9]})
    except Exception as exc:
        return jsonify({"error":str(exc)}), 404

@app.post("/api/records/verify")
def verify_record():
    try:
        data = request.get_json(force=True) or {}
        record_id = str(data.get("recordId", "")).strip()
        if not record_id:
            return jsonify({"error":"recordId is required"}), 400
        contract = load_contract()
        onchain = contract.functions.getRecord(record_id).call()
        verified = True
        if "recordHash" in data:
            supplied = data["recordHash"]
            verified = Web3.to_hex(onchain[7]).lower() == str(supplied).lower()
        return jsonify({"verified":verified,"recordHash":Web3.to_hex(onchain[7]),"recordId":record_id,"status":"verified" if verified else "mismatch"})
    except Exception as exc:
        return jsonify({"verified":False,"error":str(exc)}), 404

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("FLASK_PORT", "5000")), debug=True)
