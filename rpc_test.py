import requests
import json

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)


def main():
    url = "http://localhost:9030"

    # Example echo method
    payload = {
        "method": "SetPWMServo",
        "params": [1, 1500, 1000],
        "jsonrpc": "2.0",
        "id": 1011,
    }
    response = requests.post(url, json=payload).json()

    print(response)


if __name__ == "__main__":
    main()
