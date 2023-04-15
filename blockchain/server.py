#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from flask import Flask, request, jsonify
from flask import send_file
from flask_restful import Resource, Api, reqparse, abort
import json
import os
from time import time
from textwrap import dedent
from uuid import uuid4
import cv2
import random
import numpy as np
# Our blockchain.py API
from blockchain import Blockchain
from dogNoseprint import noseprintshot 
import apscheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
import socket
import requests
from Cryptodome.PublicKey import RSA
from Cryptodome.Hash import SHA256
from Cryptodome.Signature import PKCS1_v1_5
from transaction import Transaction
# 다수의 노드에서의 프로세스를 처리하기 위한 signal 라이브러리
import signal
# /transactions/new : to create a new transaction to a block
# /mine : to tell our server to mine a new block.
# /chain : to return the full Blockchain.
# /nodes/register : to accept a list of new nodes in the form of URLs
# /nodes/resolve : to implement our Consensus Algorithm
blockchain = Blockchain() # 블록체인 생성
# 자신의 외부 ip주소를 플라스크 웹서버로 실행하기 위해 받는 변수
app = Flask(__name__)
# Universial Unique Identifier
app.config['UPLOAD_FOLDER'] = './teamplates'
# 플라스크 서버에서 받는 임시파일은 해당 디렉토리에 저장되도록 설정함
node_identifier = str(uuid4()).replace('-','')
count = 0
state = 0 # 트랜잭션이 있는지 확인하는 상태 변수
# 트랜잭션들을 마이닝하여 실제 체인에 블록으로 등록시키는 마이닝 트랜잭션
# 어떠한 트랜잭션의 발생시 반드시 실행되도록 설정.
@app.route('/mine/transaction', methods=['GET'])
def mine():
    # 노드의 마이닝을 접근된 시간에 따른 순차적인 마이닝을 수행하기 위해 불러오는 변수 
    global state
    # 현재 마이닝 요청으로 접근된 시각을 해당 지역변수에 저장.
    # 블록체인에 마지막에 넣어진 블록.
    print(len(blockchain.current_transactions))
    checkmychain = blockchain.resolve_conflicts()
    # 자신의 노드가 최신 노드인지 먼저 확인한 뒤 진행합니다.
    # Warning! input transaction Double
    # blockchain.current_transactions.append(check)
    # Warning! input transaction Double
    transactions_all = blockchain.current_transactions
    print((blockchain.current_transactions))
    # 블록에 트랜잭션을 등록하기 전에
    for i in range(len(transactions_all)):
        try:
            checktransaction = transactions_all[i]
            # 블록에 트랜잭션을 등록하기 전에 블록으로 등록할 트랜잭션들을 검사한다.
        except: 
            break
        try:
            transactiontype = (checktransaction['transactioncode'])[0:4]
            # 트랜잭션의 종류를 판별하는 앞의 4자리 코드 비트로 중복되어 검사해야할 키와 값들을 각각 확인한다.
        except:
            return 'No transactioncode have. Can not mine', 400
        if transactiontype == "0001":
            # 만약 트랜잭션 유형이 분양 거래였을 경우, 우리가 확인해야할 키와 값은 판매자, 강아지 정보이다.
            TROKAY=blockchain.search_transaction('seller',checktransaction['seller'],'dog_info',checktransaction['dog_info'])
            # 판매자와 강아지 정보를 통해 중복되는 다른 분양 정보가 있는지 확인한다.(Double Attatk check)
            if TROKAY != None:
                # 만약 이미 블록에 동일한 트랜잭션이 존재할 시,
                blockchain.current_transactions.remove(checktransaction)
                # 트랜잭션 큐에서 해당 중복되는 트랜잭션을 제거한다.
            checktransaction = {
                'seller' :  checktransaction['seller'],# 판매자
                'dog_info' :  checktransaction['dog_info'] # 강아지 정보 
            }
            # 이제 트랜잭션 큐를 검사할때 이다. 트랜잭션 큐에 등록된 트랜잭션들은 모두 하나의 블록에 등록된다.
            # 그러기때문에 처리시 이중 분양과 같은 블록이 마이닝 될 수 있다. 이를 해결하기 위해서는 트랜잭션 큐를 확인하고 
            # 먼저 등록된 트랜잭션만 처리해준다.
            checkpara = blockchain.check_attack_double_simple(checktransaction)
            # 해당 함수는 위에서 입력한 트랜잭션의 내용을 포함하는 트랜잭션들을 리스트로 추출해준다.
            if checkpara != None:
                # checkpara가 None이라면 중복되는 요소가 없다는 것이고 아니라면 있다는 것
                for a in range(1,len(checkpara)):
                    blockchain.current_transactions.remove(checkpara[-a])
        elif transactiontype == "0010":
        # 만약 트랜잭션 타입이 분양취소였을경우(분양계약 취소)
            # 만약 트랜잭션 유형이 분양 거래였을 경우, 우리가 확인해야할 키와 값은 구매자, 강아지 정보이다.
            TROKAY=blockchain.search_transaction('buyer',checktransaction['buyer'],'dog_info',checktransaction['dog_info'])
            # 판매자와 강아지 정보를 통해 분양 정보가 있는지 확인한다.(Double Attatk check)
            if TROKAY == None:
                # 만약 이미 블록에 동일한 트랜잭션이 존재할 시,
                blockchain.current_transactions.remove(checktransaction)
                # 트랜잭션 큐에서 해당 중복되는 트랜잭션을 제거한다.
            checktransaction = {
                'buyer' :  checktransaction['buyer'],# 판매자
                'dog_info' :  checktransaction['dog_info'] # 강아지 정보 
            }
            # 이제 트랜잭션 큐를 검사할때 이다. 트랜잭션 큐에 등록된 트랜잭션들은 모두 하나의 블록에 등록된다.
            # 그러기때문에 처리시 이중 분양과 같은 블록이 마이닝 될 수 있다. 이를 해결하기 위해서는 트랜잭션 큐를 확인하고 
            # 먼저 등록된 트랜잭션만 처리해준다.
            checkpara = blockchain.check_attack_double_simple(checktransaction)
            # 해당 함수는 위에서 입력한 트랜잭션의 내용을 포함하는 트랜잭션들을 리스트로 추출해준다.
            if checkpara != None:
                # checkpara가 None이라면 중복되는 요소가 없다는 것이고 아니라면 있다는 것
                for a in range(1,len(checkpara)):
                    blockchain.current_transactions.remove(checkpara[-a])
        elif transactiontype == "0100":
            # 만약 트랜잭션 유형이 id가입인 경우, 확인해야할 키와 값은 id,pw이다
            # 만약 트랜잭션 유형이 분양 거래였을 경우, 우리가 확인해야할 키와 값은 판매자, 강아지 정보이다.
            TROKAY=blockchain.search_transaction('emailid',checktransaction['emailid'],'transactioncode',checktransaction['transactioncode'])
            # 판매자와 강아지 정보를 통해 중복되는 다른 분양 정보가 있는지 확인한다.(Double Attatk check)
            if TROKAY != None:
                # 만약 이미 블록에 동일한 트랜잭션이 존재할 시,
                blockchain.current_transactions.remove(checktransaction)
            checktransaction = {
                'emailid' :  checktransaction['emailid'],# 아이디
                'transactioncode' :  checktransaction['transactioncode'] # 트랜잭션 코드 
            }
            # 이제 트랜잭션 큐를 검사할때 이다. 트랜잭션 큐에 등록된 트랜잭션들은 모두 하나의 블록에 등록된다.
            # 그러기때문에 처리시 이중 분양과 같은 블록이 마이닝 될 수 있다. 이를 해결하기 위해서는 트랜잭션 큐를 확인하고 
            # 먼저 등록된 트랜잭션만 처리해준다.
            checkpara = blockchain.check_attack_double_simple(checktransaction)
            # 해당 함수는 위에서 입력한 트랜잭션의 내용을 포함하는 트랜잭션들을 리스트로 추출해준다.
            if checkpara != None:
                # checkpara가 None이라면 중복되는 요소가 없다는 것이고 아니라면 있다는 것
                for a in range(1,len(checkpara)):
                    blockchain.current_transactions.remove(checkpara[-a])
    if len(blockchain.current_transactions) == 0:
        # 현재의 트랜잭션 리스트의 길이가 0이다(즉, 들어있는 트랜잭션이 없다는 것)
        state = 0
        # state는 0으로 바꿔준다.
    if state == 0:
        return 'missing values', 400
    else:
        last_block= blockchain.last_block
        # 마지막 마이닝 요청의 POW증명에 대한 값
        last_proof= last_block['proof']
        # 마지막 블록의 증명 값
        # 블록 마이닝을 완료했다면 클라이언트에게도 등록이 완료되었다는 응답 메세지를 전송
        # 오직 트랜잭션이 있을때만 블록을 생성
        proof= blockchain.pow(last_proof)
        # 마지막 블록의 증명 값으로 실제 POW를 만족하여 마이닝할수 있는지 확인.
        previous_hash= blockchain.hash(last_block) 
        # 블록 체인의 마지막 블록의 해쉬값
        block= blockchain.new_block(proof, previous_hash)
        # 새로운 블록을 자신의 블록 체인에 블록 업데이트 한다.
        response = {
        'message': 'new block found',
        'index': block['index'],
        'timestamp':block['timestamp'],
        'transaction': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']
        }
        updateallnode=blockchain.request_update_chain()
        # 모든 노드들을 자신이 방금 업데이트한 블록체인으로 업데이트시킴
        state = 0
        # 트랜잭션을 마이닝했으므로 남아있는 트랜잭션은 없게 된다. 따라서 state는 0이다.
        return jsonify(response) , 201

# 레트로핏에서 데이터를 받아 해당 데이터를 파일로 ./templates/디렉터리에 저장하는 함수
# 사용자의 관리자 코드, 이름, email 아이디와 비밀번호를 받고 아이디를 블록으로 등록시키는 함수
@app.route('/transactions/new/id', methods = ['POST'])
def new_transaction_registerid():
    global state
    values=request.get_json()
    ori_index = blockchain.last_block['index']
    required=["idcode","idname","emailid", "idpw","transactioncode"]
    if not all(k in values for k in required):
        return 'missing values', 400    
    index = blockchain.new_transaction_registerid(values["idcode"],values["idname"],values["emailid"],values["idpw"],values["transactioncode"])
    if ori_index == index:
        return 'Not upload TR', 400
    response = {'message': 'Transaction will be added to Block {%s}' %index}
    state = 1
    return jsonify(response), 201

# 가입자가 가입 성립시 기록되는 트랙잭션
# 분양시 성립되는 거래를 기록하는 트랜잭션
@app.route('/transactions/new/transaction', methods = ['POST']) 
def new_transaction_transaction():
    values= request.get_json()
    ori_index = blockchain.last_block['index']
    required = ['buyer', 'seller', 'dog_info', 'price','transactioncode']
    global state
    if not all(k in values for k in required):
        return 'missing values 1', 400
    index = blockchain.new_transaction_transaction(values['buyer'], values['seller'], values['dog_info'], values['price'],values['transactioncode'])
    if ori_index == index:
        return 'Not upload TR', 400
    response = { 'message':'Check Seller Sign {%s}' %index}
    state = 1
    return jsonify(response), 201

# 펫 정보 입력란에서 해당 개의 정보를 입력하여 새로운 개의 정보를 입력하는 트랜잭션
# 사진 파일과 json형식의 입력 양식을 따로 받아서 이를 처리함
@app.route('/transactions/new/dog', methods = ['POST'])
def new_transaction_dog():
    ori_index = blockchain.last_block['index']
    try:
        file = request.files['file']
    except:
        return 'missing values', 400
    print(request.form['jsondata'])
    # 받은 요청에서 파일형식의 파일은 파일로 저장
    values = json.loads(request.form['jsondata'])
    print(values)
    print(type(values))
    # 입력받은 값중 jsondata라는 데이터를 json형식으로 읽어들임
    required = ['dog_info','owner','transactioncode']
    if not all(k in values for k in required):
        return 'missing values in json', 400
    # 만약 요청받은 json정보에 위의 키중 하나라도 없다면 위의 에러가 메세지로 출력되어 응답으로 보내진다.
    dog_info_dict = values['dog_info']
    # 요청받은 정보중 강아지 정보에 대한 딕셔너리를 조회한다.
    required = ['ownerid','owner','name','sex','species']
    # 요청받은 강아지 정보 딕셔너리에 필요한 정보가 다 들어가 있는지 확인한다.
    if not all(k in dog_info_dict for k in required):
        return 'missing values in dog_info_dict', 400
    # 딕셔너리에 해당 키에 대한 값이 존재한지를 확인한다.
    file.save('./templates/' +  file.filename)
    # 이미지처리를 위해 임시 디렉토리에 파일을 저장
    img_nose=noseprintshot.find_dog_nose("./templates/"+file.filename,debug=True)
    # 임시 디렉토리에 저장된 해당 강아지 파일로 강아지의 코부분을 특정지어 추출
    os.remove('./templates/' +  file.filename)
    # 받았던 강아지 이미지 파일 삭제
    KEY1,DES1=noseprintshot.noseprint_SIFT(img_nose)
    # 이미지에 대한 특이점과 그 특이점에 대한 디스크립터 
    dog_nose_check = {
            'species':dog_info_dict['species'],
            'sex':dog_info_dict['sex']
    }
    check_dog_duplicate=blockchain.dog_info_search(dog_nose_check,values['transactioncode'])
    # 종, 성별이 같은 강아지로 범주를 줄여 해당 강아지의 비문 정보와 동일한 강아지 정보가 있는지를 조회한다.
    for i in range(1,len(check_dog_duplicate)+1):
        # 입력한 강아지의 종,성별과 같은 강아지들을 조회
        transaction = check_dog_duplicate[-i]
        # 각각의 트랜잭션을 조회하며 해당 트랜잭션에 기록된 강아지와 같은지 검사한다.
        img2=transaction['dog_info'].get('imgnosepath')
        key2_dict=transaction['dog_info'].get('imagekey')
        key2 = []
        for kp_dict in key2_dict:
            kp = cv2.KeyPoint(x=kp_dict['pt'][0], y=kp_dict['pt'][1], _size=kp_dict['size'], _angle=kp_dict['angle'], _response=kp_dict['response'], _octave=kp_dict['octave'], _class_id=kp_dict['class_id'])
            key2.append(kp)
        des2_serialize=transaction['dog_info'].get('imagedes')
        des2 = np.array(des2_serialize)
        # 비교할 강아지에 대한 이미지, 이미지의 키와디스크립터에 대한 정보를 추출한다.
        # 비교할 강아지에 대한 사진을 받는다.
        check=matcher_twoimage_knn(key1,des1,key2,des2,img_nose,img2)
        # 각 강아지의 정보를 비교하며 같으면 True 다르면 False 
        if check == True:
            response = {'message': 'Duplication Info'}
            return jsonify(response), 201
    img_nose_path = os.path.abspath(img_nose)
    # 생성한 코 이미지에 대한 절대 경로를 저장
    dog_info = blockchain.get_dog_information(dog_info_dict["ownerid"],dog_info_dict["owner"],dog_info_dict["name"],dog_info_dict["sex"], dog_info_dict["species"],img_nose_path,KEY1,DES1)
    global state
    index= blockchain.new_registration_dog(dog_info_dict["ownerid"],dog_info,values['transactioncode'])
    if ori_index == index:
        return 'Not upload TR', 400
    response = {'message': 'SAVE OKAY'}
    state = 1
    return jsonify(response), 201

# 개의 이미지를 입력하여 해당 개의 정보를 받아오는 트랜잭션
@app.route('/get/dog_info', methods = ['POST'])
def get_dog_info():
    values=request.get_json()
    required=['owner','sex', 'species', 'url', 'img_hash']
    index= blockchain.get_dog_information(values["owner"],values['sex'], values['species'], values['url'], values['img_hash'])
    response = {'message': 'Transaction will be added to Block {%s}' %index}
    return jsonify(response), 201

# 전체 블록체인의 블록들과 그 길이를 가져오는 트랜잭션
@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain' : blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

# 로그인을 확안하는 함수. 아이디와 비밀번호를 받고 해당 아이디와 
@app.route('/chain/loginsearch', methods = ['POST'])
def login_id():
    values=request.get_json()
    required=['emailid','idpw']
    # 이메일 아이디를 요청으로 입력받음.
    transaction=blockchain.search_transaction('emailid',values['emailid'],'idpw',values['idpw'])
    # 이메일 아이디와 비밀번호로 트랜잭션을 조회한다.
    if transaction:
        response = {'message': 'LoginOK' }
        return jsonify(response), 201
    else:
        response = {'message': 'LoginNOOK' }
        return jsonify(response), 201
    return "Error: Please supply a valid list of nodes", 400

# 사용자가 로그인시에 아이디,비밀번호를 입력받아 체인의 트랜잭션에서 해당 정보를 조회하여 메세지를 전송하는 함수
@app.route('/chain/idsearch', methods = ['POST'])
def search_id():
    values=request.get_json()
    required=['emailid']
    # 이메일 아이디를 요청으로 입력받음.
    transaction=blockchain.search_transaction('emailid',values['emailid'])
    if transaction:
        response = {'message': 'NoCan' }
        return jsonify(response), 201
    else:
        response = {'message': 'Can' }
        return jsonify(response), 201
    return "Error: Please supply a valid list of nodes", 400

# IP노드를 블록체인 네트워크에 가입시키는 함수
@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None: # Bad Request 400
        return "Error: Please supply a valid list of nodes", 400
    # 풀노드로 네트워크안에 있는 노드들 확인
    for node in nodes:
        # 노드들안에 있는 
        blockchain.register_node(node)
    # 노드
    response = {
        'message' : 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201

# 마이닝시 해당 트랜잭션을 블록에 올릴것인지 합의를 거친뒤 그 결과를 반환하는 트랜잭션
@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    # 해당 체인이 유효한지 검사하여 유효하면 해당 체인으로 블록 체인의 체인을 업데이트
    replaced = blockchain.resolve_conflicts() # True False return
    # 해당 함수를 호출하므로써 호출한 노드는 최신 체인으로 업데이트되거나 
    # 혹은 자신이 최신 체인이였을 경우, 나의 노드가 최신 체인임을 확인 가능.
    # 만약 체인이 유효하다면 합의가 완료->해당 체인을 새로운 블록 체인의 체인으로 등록
    if replaced:
        response = {
            'message' : 'Our chain was replaced',
            'new_chain' : blockchain.chain
        }
    # 만약 체인이 유효하지 않다면 기존의 체인을 그대로 유지한다.
    else:
        response = {
            'message' : 'Our chain is authoritative',
            'chain' : blockchain.chain
        }
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug = True)


# In[ ]:




