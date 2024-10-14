import os
import requests
import json
import pandas as pd

from flask import Flask, request, Response


# Token do Bot no Telegram
TOKEN = os.environ.get('TOKEN')

## Info sobre o Bot
#https://api.telegram.org/bot7694499169:AAHUk3YGF-pOq6TephY18BLysH-SZv-PMaM/getMe

## get update
#https://api.telegram.org/bot7694499169:AAHUk3YGF-pOq6TephY18BLysH-SZv-PMaM/getUpdates

# Webhook                                                                                                                        
#https://api.telegram.org/bot7694499169:AAHUk3YGF-pOq6TephY18BLysH-SZv-PMaM/setWebhook?url=https://3098219175b4bb.lhr.life

# Webhook Renderi
#https://api.telegram.org/bot7694499169:AAHUk3YGF-pOq6TephY18BLysH-SZv-PMaM/setWebhook?url=https://telegram-bot-rossmann-b1ht.onrender.com/rossmann/predict

#Message
#https://api.telegram.org/bot7694499169:AAHUk3YGF-pOq6TephY18BLysH-SZv-PMaM/sendMessage?chat_id=895518040&text=Olá Edinan, eu estou bem, obrigado!

def send_message(chat_id, text):
    # send message
    url = 'https://api.telegram.org/bot{}/'.format( TOKEN )
    url = url + 'sendMessage?chat_id={}'.format( chat_id )

    r = requests.post( url, json={'text': text} )
    print('Status code {}'.format( r.status_code ) )

    return None


def load_dataset(store_id):
    df10 = pd.read_csv('test.csv', low_memory=False )
    df_store_raw = pd.read_csv('store.csv', low_memory=False)

    # merge test dataset + store (contendo as mesmas features usadas para fazer as predicoes)
    df_test = pd.merge( df10, df_store_raw, how='left', on='Store' )

    # escolher store para predicao
    df_test = df_test[df_test['Store'] == store_id ]

    if not df_test.empty:

        # remover dias fechados
        df_test = df_test[df_test['Open'] != 0]
        df_test = df_test[~df_test['Open'].isnull()]    
        df_test = df_test.drop( 'Id', axis=1 )

        # Convertendo DataFrame em JSON
        data = json.dumps( df_test.to_dict( orient='records' ))
    
    else:
        data = 'error'

    return data

def predict( data ):
    # API Call
    url = 'https://telegram-bot-rossmann-b1ht.onrender.com/rossmann/predict' 
    header = {'Content-type': 'application/json'}
    data = data
    
    # requisicao
    r = requests.post( url, data = data,headers = header )
    print( 'Status Code {}'.format( r.status_code ) )

    # cria um objeto DataFrame a partir da lista de dicionarios
    d1 = pd.DataFrame( r.json(), columns=r.json()[0].keys() )

    return d1

def parse_message( message ):
    chat_id = message['message']['chat']['id']
    store_id = message['message']['text']
    
    store_id = store_id.replace( '/', '')
    
    try:
        store_id = int( store_id )
    except ValueError:
        store_id = 'error'

    return chat_id, store_id

# API initialize
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'] )
def index():
    if request.method == 'POST':
        message = request.get_json()
        
        chat_id, store_id = parse_message(message)

        if store_id != 'error':
            # loading data
            data = load_dataset( store_id )
            
            if data != 'error':
                # prediction
                d1 = predict( data )
            
                # calculation
                d2 = d1[['store', 'prediction']].groupby('store').sum().reset_index()

                # send message
                msg = 'Loja número {} venderá R$ {:,.2f} nas próximas 6 semanas'.format(
                        d2['store'].values[0],
                        d2['prediction'].values[0] )          
                
                send_message( chat_id, msg )
                return Response( 'OK', status=200 )  
            
            else:
                send_message( chat_id, f'Não existe esse {} código de loja'.format(d2['store'].values[0]) )
                return Response( 'OK', status=200)

        else:
            send_message( chat_id, 'Número da Loja está Errado')
            return Response( 'OK', status=200 ) 


    else:
        return '<h1> Rossmann Telegram BOT </h1>'
    

if __name__ == '__main__':
    port = os.environ.get( 'PORT', 5000 )
    app.run( host='0.0.0.0', port=port , debug=True )

