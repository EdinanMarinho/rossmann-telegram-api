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

# Webhook localhost                                                                                                                       
#https://api.telegram.org/bot7694499169:AAHUk3YGF-pOq6TephY18BLysH-SZv-PMaM/setWebhook?url=https://21dbdad3aaa68a.lhr.life

# Webhook Render
#https://api.telegram.org/bot7694499169:AAHUk3YGF-pOq6TephY18BLysH-SZv-PMaM/setWebhook?url=https://rossmann-telegram-edinan-marinho.onrender.com

#Message
#https://api.telegram.org/bot7694499169:AAHUk3YGF-pOq6TephY18BLysH-SZv-PMaM/sendMessage?chat_id=895518040&text=Olá Edinan, eu estou bem, obrigado!

def send_message( chat_id, text ):
    url = 'https://api.telegram.org/bot{}/'.format( TOKEN )
    url = url + 'sendMessage?chat_id={}'.format( chat_id )
    
    # API request using POST method 
    r = requests.post( url, json={'text': text} )
    print( 'Status Code {}'.format( r.status_code ) )
    
    return None
      
def load_dataset( store_id ):

    # loading  dataset
    # df10 = pd.read_csv( '/home/dimarinho/repos/Data_Science_em_Producao/datasets/test.csv' )
    # df_store_raw = pd.read_csv( '/home/dimarinho/repos/Data_Science_em_Producao/datasets/store.csv' )

    # # # loading  dataset
    df10 = pd.read_csv( 'datasets/test.csv', low_memory=False )
    df_store_raw = pd.read_csv( 'datasets/store.csv', low_memory=False )

    # merge test dataset + store (com as mesmas features usadas para fazer as predicoes)
    df_test = pd.merge( df10, df_store_raw, how='left', on='Store' )

    # escolha uma loja 
    df_test = df_test[df_test['Store'] == store_id ]
    
    if not df_test.empty:
        # somente as lojas que estao abertas
        df_test = df_test[df_test['Open'] != 0]
        # lojas sem dados faltantes na coluna 'Open'
        df_test = df_test[ ~df_test['Open'].isnull() ]
        # retira a coluna 'Id' 
        df_test = df_test.drop( 'Id', axis=1 )
    
        # converte o DataFrame em json para o envio via API
        data = json.dumps( df_test.to_dict( orient='records' ) )
    
    else:
        data = 'error'
        
    return data

def predict( data ):
    # Chamada para a API
    url = 'https://api-rossmann-edinan-marinho.onrender.com/rossmann/predict'
    # indica para a API o tipo de requisicao que estamos fazendo
    header = {'Content-type': 'application/json' }
    data = data

    # requisicao
    r = requests.post( url, data=data, headers=header )
    print( 'Status Code {}'.format( r.status_code ) )
    
    # cria um objeto DataFrame a partir da lista de dicionarios
    d1 = pd.DataFrame( r.json(encoding='utf-8'), columns=r.json()[0].keys() )
    
    return d1

def parse_message( message ):
    chat_id = message['message']['chat']['id']
    store_id = message['message']['text']
    
    store_id = store_id.replace( '/', '' )
    
    try:
        store_id = int( store_id )
        
    except ValueError:
        store_id = 'error'
        
    return chat_id, store_id

# API initialize
app = Flask( __name__ )

@app.route( '/', methods=['GET', 'POST'] )
def index():
    if request.method == 'POST':
        message = request.get_json()
        chat_id, store_id = parse_message( message )
        
        if store_id != 'error':
            # loading data
            data = load_dataset( store_id )
            
            if data != 'error':
                # prediction
                d1 = predict( data )

                # Calculation
                # DataFrame que contem a soma das previsoes de vendas por loja
                d2 = d1[['store','prediction']].groupby('store').sum().reset_index()
                
                msg = 'Loja número {} venderá ${:,.2f} nas próximas 6 semanas'.format(
                        d2['store'].values[0], d2['prediction'].values[0] )
               
                send_message( chat_id, msg )
                return Response( 'Ok', status=200 )
            
            else: 
                send_message( chat_id, 'Loja não disponível' )
                return Response( 'Ok', status=200 )
        
        else:
            send_message( chat_id, 'ID Loja Errado' )
            return Response( 'Ok', status=200 ) 
        
    else:
        return '<h1> Rossmann Telegram BOT </h1>'
    
    
if __name__ == '__main__':
    port = os.environ.get( 'PORT', 5000 )
    app.run( host='0.0.0.0', port=port, debug=True )
