import sys
from flask import Flask, request, abort
import requests 
import config
import json
import logging
from spotifyapp import findAndPlaySong
from termcolor import colored

cli = sys.modules['flask.cli']
cli.show_server_banner = lambda *x: None


bearer_token=config.API_CONFIG['TOKEN']
headers = {
    'Authorization': 'Bearer {}'.format(bearer_token),
    'Content-Type': 'application/json',
}
api_url = 'https://api.up.com.au'
public_port = 8080


def get_publicip():
    publicip = requests.get('https://api.ipify.org').text
    print('Public IP : {}'.format(publicip))
    return publicip

def delete_webhooks():
    # Get a list of existing webhooks
    response = requests.get('{}/api/v1/webhooks'.format(api_url), headers=headers)
    response_json = json.loads(response.text)

    # For each webhook, delete it
    for i, val in enumerate(response_json['data']): 
        webhook_id, webhook_desc = val['id'], val['attributes']['description']
        print('Deleting webhook id:{} "{}"'.format(webhook_id, webhook_desc))
        requests.delete('{}/api/v1/webhooks/{}'.format(api_url, webhook_id), headers=headers)

def create_webhook():
    # Payload
    public_ip = get_publicip()
    url = '{}:{}'.format(public_ip, public_port)
    post_data = '{"data": { "attributes": { "url": "http://' + url +'", "description": "Callback webhook to handle transactions" } } }'
    response = requests.post('{}/api/v1/webhooks'.format(api_url), headers=headers, data=post_data)
    print ('Creating webhook - response {}'.format(response))

def test_song_request(trx_msg):
    search_prefix='🎵'
    if (trx_msg.startswith(search_prefix)):
        songRequest=trx_msg.replace(search_prefix, '')
        print('Request to find and play {}'.format(songRequest))
        findAndPlaySong(songRequest=songRequest)


def get_trx(trx_id):
    response = requests.get('{}/api/v1/transactions/{}'.format(api_url, trx_id), headers=headers)
    response_json = json.loads(response.text)
    trx_msg = response_json['data']['attributes']['message']
    trx_amt = response_json['data']['attributes']['amount']['value']

    print('>> Transaction ID:{} Msg:{} of amount ${}'.format(trx_id, trx_msg, trx_amt))
    test_song_request(trx_msg)
    print()

delete_webhooks()
create_webhook()

app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    # print("webhook")
    if request.method == 'POST':
        request_json = request.json
        # print('>> JSON {}'.format(request_json))
        trx_id = request_json['data']['relationships']['transaction']['data']['id']
        get_trx(trx_id)
        sys.stdout.flush()

        return '', 200
    else:
        abort(400)

if __name__ == '__main__':
    app.run( host="0.0.0.0", port=public_port)
