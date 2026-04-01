# LayerTAO

✅ WSL environment with Python venv
<br> ✅ BitTensor SDK and CLI installed
<br>✅ FastAPI application with OpenAPI docs
<br>✅ Welcome and health endpoints
<br>✅ Service layer for BitTensor interactions
<br>✅ Placeholder structure for subnet integrations

## Project Structure
```
~/layertao-api/
    ├── .env.example
    ├── .gitignore
    ├── requirements.txt
    ├── ReadMe.md
    ├── run.py
    └── app/
        ├── __init__.py
        ├── main.py
        ├── config.py
        ├── dependencies.py
        ├── routers/
        │   ├── __init__.py
        │   ├── welcome.py
        │   ├── health.py
        │   ├── subnet.py        
        │   └── inference.py
        ├── services/
        │   ├── __init.py
        │   └── bittensor_service.py
        └── test/
            └── test_wallet_path_normalization.py
```

### Pre-requisites 

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-venv python3-pip git curl -y
```

### Install Rust (Required for BitTensor SDK on Linux)

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
rustc --version  # Verify installation
```

`

### Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### Requirements

```txt
bittensor>=10.2.0
bittensor-cli>=9.20.0
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
python-dotenv>=1.0.0
pydantic-settings>=2.0.0
httpx>=0.27.0
numpy>=1.21.0,<2.0.0
```

#### Install them:

```bash
pip install --upgrade pip
```

```bash
pip install -r requirements.txt
```

#### Verify installation:

```bash
btcli --version
```

```bash
python3 -m bittensor
```

#### Create BitTensor Wallet (if not already)

```bash
# Create coldkey (store mnemonic securely!)
btcli wallet new_coldkey --wallet.name my_wallet

# Create hotkey
btcli wallet new_hotkey --wallet.name my_wallet --wallet.hotkey default

# List wallets to confirm
btcli wallet list
```

- Important: Save both coldkey and hotkey mnemonics offline securely

#### Wallet Registration

```bash
btcli wallet overview --wallet-name my_wallet --network test
```

#### LayerTAO .env `WALLET_PATH`

In this project, `WALLET_PATH` should point to the wallet root dir, not the full hotkey keyfile path.

- Good: `~/.bittensor/wallets` or `~/.bittensor/wallets/my_wallet`
- Also accepted (auto-normalized): `~/.bittensor/wallets/my_wallet/hotkeys/default`

This project now normalizes inside `app/dependencies.py` / `app/services/bittensor_service.py`, so `WALLET_PATH` will work if accidentally set to a deeper `hotkeys` path.

## Run Tests
```bash
pytest
```
- Running a specific test file
```bash
pytest -q tests/test_wallet_path_normalization.py
```

### Register wallet on a subnet
```bash
btcli subnet register --netuid <subet uid> --wallet.name <wallet_name> --wallet.hotkey <path to hotkey>  --network <test/finney>
```

## Accessing the Metagraph of a subnet using uid
```bash
btcli subnets metagraph --netuid 1 --network finney
```



