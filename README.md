# Crop Disease Prediction & Farm Record Verification

A beginner-friendly college project combining **Machine Learning** and **Blockchain**. The ML side predicts a crop disease from a synthetic CSV dataset. The blockchain side stores a compact farm-record hash and metadata on a local Ganache network using a Solidity contract, Truffle, and Web3.py.

> **Dataset note:** `ml/dataset/crop_disease.csv` is a synthetic/demo dataset generated for this project. It is not an official agricultural dataset and should not be used for real agronomic decisions.

## Technologies
Python, Jupyter Notebook, Pandas, NumPy, Scikit-learn, Flask, HTML, CSS, JavaScript, Solidity, Truffle, Ganache, Web3.py, CSV.

## Architecture
```text
Browser / HTML-CSS-JS
        |
        v
      Flask
      /   \
     ML   Web3.py
     |       |
    CSV    Ganache
     |       |
   .pkl   FarmRecord.sol
```

## Exact project structure
```text
Crop-Disease-Blockchain/
├── frontend/
│   ├── index.html
│   ├── prediction.html
│   ├── verification.html
│   ├── result.html
│   ├── css/style.css
│   └── js/app.js
├── ml/
│   ├── dataset/crop_disease.csv
│   ├── notebooks/crop_disease_prediction.ipynb
│   ├── models/crop_disease_model.pkl
│   └── requirements.txt
├── blockchain/
│   ├── contracts/FarmRecord.sol
│   ├── migrations/1_initial_migration.js
│   ├── migrations/2_deploy_farm_record.js
│   ├── test/FarmRecord.test.js
│   ├── truffle-config.js
│   └── package.json
├── backend/app.py
├── README.md
└── .gitignore
```

## Windows installation

### 1. Python environment
From the project root in Windows CMD:
```cmd
python -m venv venv
venv\Scripts\activate
pip install -r ml\requirements.txt
```

### 2. Ganache
Install/open **Ganache Desktop** and create a local workspace. Use the RPC server shown by Ganache. The default project configuration expects:
```text
RPC URL: http://127.0.0.1:7545
Network ID: *
```
If Ganache uses another port, set `GANACHE_PORT` for Truffle and `GANACHE_URL` for Flask.

### 3. Truffle
Install Node.js, then from CMD:
```cmd
cd blockchain
npm install
npm run compile
npm run migrate
```
The migration writes the deployed contract address into Truffle's generated `build/contracts/FarmRecord.json`. That generated build directory is intentionally not part of the requested source architecture and is recreated by `truffle compile`/`migrate`.

### 4. ML model
The ZIP already contains a trained `ml/models/crop_disease_model.pkl`. To retrain it from the notebook:
```cmd
jupyter notebook
```
Open `ml/notebooks/crop_disease_prediction.ipynb` and run all cells. The notebook loads the CSV, preprocesses categorical/numeric fields, trains a Random Forest, evaluates it, demonstrates a sample prediction, and saves the model.

### 5. Flask backend
From the project root:
```cmd
venv\Scripts\activate
python backend\app.py
```
Open:
```text
http://127.0.0.1:5000/
```
Flask serves the requested frontend files directly, so a separate web server is not required.

## Optional environment configuration
No private key is hard-coded. With standard Ganache, Web3.py can send transactions from an unlocked Ganache account. Optional variables:

```cmd
set GANACHE_URL=http://127.0.0.1:7545
set GANACHE_ACCOUNT=0xYOUR_GANACHE_ACCOUNT
set CONTRACT_ADDRESS=0xDEPLOYED_CONTRACT_ADDRESS
set FLASK_PORT=5000
```
For a Ganache setup that requires signed transactions, adapt `app.py` to use a private key supplied through an environment variable; never commit the key.

## API documentation

### GET `/api/health`
Returns Flask and Ganache connection status.

### POST `/api/predict`
Example JSON:
```json
{
  "Crop":"Rice",
  "Temperature":28,
  "Humidity":80,
  "Soil_Moisture":65,
  "Rainfall":120,
  "pH":6.5
}
```
Returns prediction, confidence when supported, and status.

### POST `/api/records`
Accepts `farmerId`, `farmerName`, `crop`, `disease`, `farmInfo`, and `recordInfo`. Flask creates a deterministic SHA-256 hash, converts it to `bytes32`, and stores the compact record through Web3.py.

### GET `/api/records/<record_id>`
Reads a farm record from the Solidity contract.

### POST `/api/records/verify`
Accepts `recordId`. It reads the on-chain record and confirms that it exists; if a `recordHash` is also supplied, it compares that hash with the on-chain hash.

## Blockchain testing
With Ganache running:
```cmd
cd blockchain
npm test
```
The tests cover deployment, insertion, retrieval, event emission, verification, wrong-hash behavior, and nonexistent records.

## Complete user flow
1. Open the home page.
2. Select Disease Prediction.
3. Enter the exact six model features shown by the form.
4. Flask loads the pre-trained `.pkl` and returns a disease prediction.
5. Continue to Farm Record Verification.
6. Enter farmer/farm details.
7. Flask deterministically hashes the record.
8. Web3.py sends the record to Ganache.
9. `FarmRecord.sol` stores the record and emits `FarmRecordAdded`.
10. The transaction hash and record hash are displayed.

## No database
This project deliberately uses **no database**. CSV is the ML data source, the `.pkl` file stores the trained ML pipeline, and Ganache stores blockchain records. There is no MySQL, MongoDB, PostgreSQL, Firebase, or SQLite database.

## Troubleshooting

**Ganache not running:** Start Ganache before migration or blockchain operations.

**Wrong RPC port:** Change `GANACHE_PORT` for Truffle and `GANACHE_URL` for Flask.

**Contract not deployed:** Run `cd blockchain`, `npm run compile`, then `npm run migrate`.

**Contract address mismatch:** Set `CONTRACT_ADDRESS` to the address in `blockchain/build/contracts/FarmRecord.json`, or remove the variable so `app.py` reads the artifact.

**Missing `.pkl`:** Run the notebook from beginning to end; it writes `ml/models/crop_disease_model.pkl`.

**Python package errors:** Activate `venv` and run `pip install -r ml\requirements.txt`.

**Truffle compile errors:** Confirm Node.js/Truffle are installed and use Solidity 0.8.20-compatible Truffle.

**Web3 connection errors:** Check Ganache RPC URL, port, account availability, and that Truffle migration succeeded.

**CORS errors:** Flask-CORS is included and enabled. Prefer opening the application through `http://127.0.0.1:5000/` rather than opening HTML files with `file://`.

## Validation
The supplied source files, dataset, notebook JSON, trained model, Solidity contract, migrations, tests, Flask routes, and frontend paths are included in this archive. A full live Ganache/Truffle integration test requires a running local Ganache process; start Ganache and run the commands above before demonstration.
