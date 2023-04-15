import hashlib
import json
from time import time
from time import sleep
import numpy as np
import urllib.parse
import requests
from dogNoseprint import noseprintshot
from merkleTree import get_merkle_root
import random
import cv2
from collections import Counter
from dataclasses import dataclass, asdict, astuple
from Cryptodome.PublicKey import RSA
from Cryptodome.Hash import SHA256
from Cryptodome.Signature import PKCS1_v1_5
from AESCipher import AESCipher
####### block generation & its principle
class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        self.new_block(previous_hash='1', proof=100)
    def new_block(self, proof, previous_hash=None):
        if previous_hash ==None:
            previous_hash = self.hash(self.chain[-1])
        block = {
            'index' : len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash,
            'merkle_root': get_merkle_root(self.current_transactions)
        }
        self.current_transactions = []
        self.chain.append(block)
        return block
    
    # 트랜잭션 키와 값을 받아서 해당 트랜잭션을 출력하는 함수(키는 두개를 받을수 있고, 두개를 받을 경우 각각의 입력값이 
    # 등록된 값과 동일해야 트랜잭션을 반환. 아님 None을 반환한다.)
    def search_transaction(self,insertkey,insertvalues,insertkey2=None,insertvalues2=None):
        for i in range(1,len(self.chain)+1):
            # block들의 transaction을 조회
            block=self.chain[-i]
            transaction=block['transactions']
            for n in range(len(transaction)):
                try :
                    value01=transaction[n][insertkey]
                except:
                    continue
                if value01 == insertvalues:
                    if insertkey2 == None:
                        return transaction[n]
                    else:
                        try:
                            if transaction[n][insertkey2] == insertvalues2:
                                return transaction[n]
                            else:
                                continue
                        except:
                            continue
        return None
    # 해당 key에 대한 values가 존재하면 해당 모든 트랜잭션들을 리스트형태로 출력.
    def search_transaction_all(self,insertkey,insertvalues,insertkey2=None,insertvalues2=None):
        transaction_list = []
        checkkey1=insertkey
        checkvalue1=insertvalues
        # 트랜잭션의 모음으로 동적 리스트를 생성
        for i in range(1,len(self.chain)+1):
            # block들의 transaction을 조회
            block=self.chain[-i]
            transaction=block['transactions']
            for n in range(len(transaction)):
                try:
                    value01=transaction[n][insertkey]
                except:
                    continue
                if value01 == insertvalues:
                    if insertkey2 == None:
                        transaction_list.append(transaction[n])

                        # insertkey2가 None으로 오직 하나의 키로 찾는 경우 insertkey에 입력한 값이 맞으면 해당 트랜잭션을 
                        # 리스트에 추가
                    else:
                        try:
                            if transaction[n][insertkey2] == insertvalues2:
                                transaction_list.append(transaction[n])
                                # 두 개의 키로 찾는 경우 insertkey02에 입력한 값이 맞는것까지 확인하여 해당 트랜잭션을 추가
                            else :
                                continue
                        except:
                            continue
            return transaction_list
            
    # 해당 key에 대한 values가 존재하면 해당 트랜잭션들을 출력. 
    
    # Double Spending, 여기서는 이중 트랜잭션 생성 관련 문제를 해결하기 위한 함수
    def check_attack_double_standing(self,checktransactions):
        updatemychain=self.resolve_conflicts()
        # 자신의 체인을 최신 체인으로 업데이트한다.
        transactionlist =[]
        # 빈 트랜잭션 리스트를 생성
        for i, (key, value) in enumerate(checktransactions.items()):
            # 입력받은 트랜잭션 검증을 위한 키와 그에 해당되는 값을 순차대로 출력한다.
            transactionlist.extend(self.search_transaction_all(key,value))
            # 키와 값에 해당 되는 값들을 출력한다.
            for d in range(0,len(self.current_transactions)):
                print(self.current_transactions[d])
                # 키와 값이 중복되는 트랜잭션을 트랜잭션 큐안에서 찾는다.
                if value==self.current_transactions[d][key]:
                    # 입력된 키에 대한 값이 존재하면  
                    transactionlist.append(self.current_transactions[d])
                    # 트랜잭션리스트에 추가한다.
            if len(transactionlist) < 1:
                return True
            # 중복된 트랜잭션이 없는것이므로 True를 반환
        b_count = []# 각 원소의 등장 횟수를 카운팅할 리스트
        b_tr = [] # 실제 카운팅 리스트 인덱스에 맞춰 넣어지는 트랜잭션 리스트
        for a in range(len(transactionlist)):
            if b_tr.count(transactionlist[a]) >= 1:
                b_count[b_tr.index(transactionlist[a])] += 1
            else :
                b_count.insert(a,1)
                b_tr.insert(a,transactionlist[a])
        new_b = [] # 중복 원소만 넣을 리스트
        for b in range(len(b_tr)):
            if b_count[b] >= len(checktransactions): # n회 이상 등장한 원소로도 변경 가능
                new_b.append(b_tr[b])
        if len(new_b) == 0:
            return True
        else:
            return False
            # 어떠한 트랜잭션도 중복되지 않을 때, True를 반환한다.   
    def check_attack_double_simple(self,checktransactions):
        updatemychain=self.resolve_conflicts()
        # 자신의 체인을 최신 체인으로 업데이트한다.
        transactionlist =[]
        # 빈 트랜잭션 리스트를 생성
        for i, (key, value) in enumerate(checktransactions.items()):
            # 입력받은 트랜잭션 검증을 위한 키와 그에 해당되는 값을 순차대로 출력한다.
            transactionlist.extend(self.search_transaction_all(key,value))
            # 키와 값에 해당 되는 값들을 출력한다.
            for d in range(0,len(self.current_transactions)):
                print(self.current_transactions[d])
                # 키와 값이 중복되는 트랜잭션을 트랜잭션 큐안에서 찾는다.
                if value==self.current_transactions[d][key]:
                    # 입력된 키에 대한 값이 존재하면  
                    transactionlist.append(self.current_transactions[d])
                    # 트랜잭션리스트에 추가한다.
            if len(transactionlist) < 1:
                return None
        b_count = []# 각 원소의 등장 횟수를 카운팅할 리스트
        b_tr = [] # 실제 카운팅 리스트 인덱스에 맞춰 넣어지는 트랜잭션 리스트
        for a in range(len(transactionlist)):
            if b_tr.count(transactionlist[a]) >= 1:
                b_count[b_tr.index(transactionlist[a])] += 1
            else :
                b_count.insert(a,1)
                b_tr.insert(a,transactionlist[a])
        new_b = [] # 확인할려는 조건을 만족하는 중복 트랜잭션만 넣을 리스트
        for b in range(len(b_tr)):
            if b_count[b] >= len(checktransactions): # n회 이상 등장한 원소로도 변경 가능
                new_b.append(b_tr[b])
        if len(new_b) == 0:
            return None
        else:
            return new_b
            # 어떠한 트랜잭션도 중복되지 않을 때, True를 반환한다. 
        # 사용자가 해당 서비스를 이용한 분양시, 그 거래에 대한 트랜잭션
    def new_transaction_transaction(self, buyer, seller, dog_info, price, transactioncode):
        checktransaction = {
            'seller' :  seller,# 판매자
            'dog_info' :  dog_info # 강아지 정보 
        }
        sleep(random.randrange(1, 3))
        # 1~10사이의 sleep시간을 가진다.이는 랜덤하게 시간을 두고 검증하여 이중 트랜잭션 공격을 감지하기 위함이다.
        checkpara = self.check_attack_double_standing(checktransaction)
        # Double Spending Attack 을 검증한다
        if checkpara:
            createtransaction = {
            'buyer':buyer,
            'seller':seller,
            'dog_info':dog_info,
            'price': price,
            'transactioncode':transactioncode,
            'owner':None,
            'idcode':None,
            'idname':None,
            'emailid':None,
            'idpw':None,
            'img_hash':None,
            'hash_transaction_id':None
            }
            # 만약 검증하여 해당 값이 True로 반환된 경우
            self.current_transactions.append(createtransaction)
            # 해당 트랜잭션을 트랜잭션 큐에 등록한다.
            # 만약 어떠한 중복된 트랜잭션도 발견되지않았다면 
            return self.last_block['index']+1
        else :
            # 만약 검증에 실패한 경우, 공격이 들어온것으로 감지한다.
            return self.last_block['index']
            # 검증에 실패하였기 때문에 해당 트랜잭션은 무시된다.
   
    # 사용자가 서비스 가입시 사용자의 id와 비밀번호를 네트워크에 등록하는 함수
    def new_transaction_registerid(self,idcode,idname,emailid ,idpw,transactioncode,okaykey=False,setkey=None): 
        checktransaction = {
            'emailid' :  emailid,# 이메일 아이디
            'transactioncode' : transactioncode # 트랜잭션 코드
        }
        sleep(random.uniform(1, 3))
        # 1~10사이의 sleep시간을 가진다.이는 랜덤하게 시간을 두고 검증하여 이중 트랜잭션 공격을 감지하기 위함이다.
        checkpara = self.check_attack_double_standing(checktransaction)
        # Double Spending Attack 을 검증한다
        if checkpara:
            createtransaction = {
            'buyer':None,
            'seller':None,
            'dog_info':None,
            'price': None,
            'transactioncode':transactioncode,
            'owner':None,
            'idcode':idcode,
            'idname':idname,
            'emailid':emailid,
            'idpw':idpw,
            'img_hash':None,
            'hash_transaction_id':None
            }
            # 만약 검증하여 해당 값이 True로 반환된 경우
            self.current_transactions.append(createtransaction)
            # 해당 트랜잭션을 트랜잭션 큐에 등록한다.
            # 만약 어떠한 중복된 트랜잭션도 발견되지않았다면 
            return self.last_block['index']+1
        else :
            # 만약 검증에 실패한 경우, 공격이 들어온것으로 감지한다.
            return self.last_block['index']
        
    # 개의 정보로 저장하기 위한 함수 
    def get_dog_information(self,email_id, owner,name, sex, species,imgnosepath,key1,des1):
        keypoints_dict = []
        for kp in key1:
            kp_dict = {
            'pt': (kp.pt[0], kp.pt[1]),
            'size': kp.size,
            'angle': kp.angle,
            'response': kp.response,
            'octave': kp.octave,
            'class_id': kp.class_id
        }
        keypoints_dict.append(kp_dict)
        # 키포인트는 json으로 직렬화하기 위해서는 다음과 같이 딕셔너리로 변환해줄 필요가 있다.
        dog_info = {
        'ownerid':email_id,#이메일 아이디(로그인 정보를 담고있는 범용DB와 연결되는 칼럼)
        'owner':owner, # 소유자 이름
        'name':name, # 강아지 이름
        'sex' : sex, # 강아지 성별
        'species': species, # 강아지 종
        'imgnosepath': imgnosepath, # 이미지가 저장된 절대 경로,
        'imagekey': keypoints_dict, # 이미지에 대한 특이점 key정보(리스트)
        'imagedes': des1.tolist() #  특이점 key정보에 대한 key descriptor(어레이)
        }
        # 입력한 강아지 정보가 실제 체인에서 중복되는 정보가 있는지 확인

        # 해당 강아지 정보에 대한 중복성을 검사
        
        # GET으로 넘겨주는 정보 출력
        print('%s' %email_id) 
        print('%s' %owner)
        print('%s' %sex)
        print('%s' %species)
        return dog_info
        # 개 정보 등록 함수         
    def dog_info_search(self,search_col,transactioncode):
        result_list = []
        append_tr = None
        checktransaction = {
            'transactioncode' : transactioncode# 강아지 정보
            # 강아지 분양 정보(대기,분양)
        }
        checkpara = self.check_attack_double_simple(checktransaction)
        # 트랜잭션 코드가 강아지 정보 입력인 트랜잭션들을 리스트로 추출한다.
        if checkpara:
            for i in range(1,len(checkpara)):
                append_tr = None
                checktr=checkpara[-i]
                for key,value in search_col.items():
                    if checktr.get(key) != value:
                        append_tr = None
                        break
                    else:
                        append_tr = checktr
                if append_tr != None:
                    result_list.append(append_tr)
        return result_list
                
    def new_registration_dog (self, owner, dog_info,transactioncode):
        checktransaction = {
            'owner' :  owner,# 소유자 아이디
            'dog_info' :  dog_info, # 강아지 정보
            'transactioncode' : transactioncode# 트랜잭션 코드
            # 강아지 정보 등록
        }
        sleep(random.uniform(1, 3))
        # 1~10사이의 sleep시간을 가진다.이는 랜덤하게 시간을 두고 검증하여 이중 트랜잭션 공격을 감지하기 위함이다.
        checkpara = self.check_attack_double_standing(checktransaction)
        if checkpara:
            createtransaction = {
            'buyer':None,
            'seller':None,
            'dog_info':dog_info,
            'price': None,
            'transactioncode':transactioncode,
            'owner':owner,
            'idcode':None,
            'idname':None,
            'emailid':None,
            'idpw':None,
            'img_hash':None,
            'hash_transaction_id':None
            }
            # 만약 검증하여 해당 값이 True로 반환된 경우
            self.current_transactions.append(createtransaction)
            # 해당 트랜잭션을 트랜잭션 큐에 등록한다.
            # 만약 어떠한 중복된 트랜잭션도 발견되지않았다면 
            return self.last_block['index'] + 1
        else:
            return self.last_block['index']
    
    # 해당 노드를 블록 체인 서버에 등록(풀노드)
    def register_node(self, address):
        parsed_url = urllib.parse.urlparse(address)
        # 가입 노드에 대한 
        self.nodes.add(parsed_url.netloc) # netloc attribute! network lockation
    # 유효한 체인인지 검사하는 함수.
    def valid_chain(self,chain):
        # 큐로 생각하여 가장 처음에 넣어진 체인의 블록은 체인의 맨 처음에 위치함.
        # 현재 블록(last_block)의 해쉬값과 다음 블록의 이전 해쉬값(previous_hash)값을 비교하여 해당 체인이 유효한지
        # 검사.
        last_block = chain[0]
        # 맨 처음에 제네시스 블록의 해시값과 이전 블록에서의 해시값을 비교하는 작업으로 시작됨으로 체인의 제네시스 블록을 
        # 해시값을 비교할 마지막 블록으로 설정
        current_index = 1
        # 해당 체인의 길이만큼 순차대로 검사.
        while current_index < len(chain):
            # 순차대로 체인의 블록
            block = chain[current_index]
            print('%s' % last_block)
            print('%s' % block)
            print("\n---------\n")
            # check that the hash of the block is correct(해당 블록의 이전 해쉬값과 실제 업데이트되있는 마지막 블록의 
            # 해쉬값을 비교) 만약 맞지 않을 경우, 해당 체인은 유효하지 않음.
            if block['previous_hash'] != self.hash(last_block):
                return False
            # 현재 블록을 마지막 블록으로 바꾸고 다음 블록의 이전 해쉬값과 비교하며 검사
            last_block = block
            # 현재 체인의 인덱스를 1 높임.
            current_index += 1
        return True

    def request_update_chain(self):
        # 마이닝 이후 반드시 실행되는 함수. 마이닝을 하여 블록을 블록체인에 넣어둔 노드를 기준으로 모든 노드들을 
        # 자신이 추가한 블록까지 업데이트하는 함수
        neighbours = self.nodes
        # 해당 블록체인 네트워크에 등록된 다른 노드들
        for node in neighbours:
            tmp_url = 'http://' + str(node) + '/nodes/resolved'
            # 다른 노드들을 업데이트하도록 설정합니다.
            response = requests.get(tmp_url)
            if response.status_code == 200:
                # 다른 노드들이 자신의 체인으로 업데이트되었는지에 대한 응답을 받습니다.
                print("response : "+response.json()['message'])
                # 각 노드들에 대한 메세지를 응답받아 그것을 출력하는 명령어
        print("All node update my chain")
        # 모든 노드들이 업데이트되었다는 것을 출력하는 명령어
        return True
    
    def resolve_conflicts(self):
        # 블록 생성후 체인에 블록을 넣고나서 해당 노드에서의 체인이 유효한지를 검사하고 
        # 각 노드들의 체인을 검사하여 해당 노드의 체인의 길이가 더 길고, 유효한 체인이 검증되면
        neighbours = self.nodes
        # 해당 블록체인 네트워크에 등록된 다른 노드들
        new_chain = None
        # 업데이트될 체인
        # 처음에는 나의 체인이 제일 최신 체인으로 생각하여 None으로 초기화
        max_length = len(self.chain) 
        # Our chain length 
        for node in neighbours:
            # 각 다른 노드들의 체인을 비교해가며 다른 노드의 체인의 길이가 더 길고,
            # 그 노드의 체인이 유효하다면 해당 노드의 체인으로 업데이트한뒤, 응답으로 True를 return
            tmp_url = 'http://' + str(node) + '/chain'
            # 다른 노드들을 순차적으로 server파일에 있는 함수를 호출하여 해당 노드의 체인을 검사 것이며, 
            # 체인을 응답받는 url
            response = requests.get(tmp_url)
            # 해당 노드의 체인의 길이를 응답받음.
            if response.status_code == 200:
                # 응답이 정상적으로 수행되었을 시, 조건문 진입
                length = response.json()['length']
                # 응답받은 json형식의 출력에서 해당 노드의 체인 길이를 length 지역 변수에 할당.
                chain = response.json()['chain']
                # 응답받은 json형식의 출력에서 해당 노드의 체인을 지역 변수에 할당
                if length > max_length and self.valid_chain(chain):
                    # 만약 검사하는 노드의 체인 길이가 가장 최신의 체인이여서 해당 체인의 길이가 함수를 수행하는 노드의 
                    # 체인 길이보다 길어진 경우, 그리고 해당 노드의 체인이 유효한 경우
                    max_length = length
                    # 가장 긴 길이를 해당 길이로 업데이트함.
                    new_chain = chain
                    # 해당 체인으로 업데이트할 체인에 할당.
                    continue
                    # new_chain이 바뀌었다면 다시 반복문으로 돌아감.
            if new_chain:
                # 최종적으로 나의 체인의 길이가 가장 긴 최신 체인을 new_chain에 할당한 경우
                self.chain = new_chain
                # new_chain의 체인을 나의 체인으로 업데이트함.
                return True
                # 해당 체인으로 대체되었으므로 True를 반환.
            return False
            # 만약 나의 체인이 가장 최신이였어서 new_chain이 None으로 남게된 경우
            # 나의 체인은 가장 최신의 체인으로 인증된 것이므로 False를 반환.

    # directly access from class, share! not individual instance use it
    @staticmethod
    # 위의 staticmethod는 blockchain이라는 클래스 밖의 전역에서도 해당 함수를 사용할 수 있도록 정의하기위해서 
    # 사용한 것이다.
    def hash(block):
        block_serialized = str(block)
        # json.dumps로 block이라는 딕셔너리 객체를 정렬하고나서 encode()로 하여금 문자열로 인코딩을 한다.
        return hashlib.sha256(block_serialized.encode()).hexdigest()
        # sha256 : 단방향 암호화 해시함수, 64자리(256bit) 암호화 문자열로 출력해준다.
    @property
    # 데코레이션 property : 해당 데코레이션의 함수는 자동으로 set과 get의 속성을 부여받는 객체가 된다.
    # 즉, 어떤 값을 출력할 때는 get함수, 어떤 값을 입력할 때는 set함수가 사용된다.
    def last_block(self):
        # 마지막 블록에 대한 객체 생성
        return self.chain[-1]
        # 체인의 마지막으로 넣어진 블록을 출력.
    def pow(self, last_proof):
        # 블록을 마이닝할 노드는 반드시 해당 노드가 마이닝할 능력이 됨을 증명해야한다. 
        # 즉, 이에 대한 증명방식이 필요한데 이중하나가 pow(작업증명방식)이다.
        # pow(작업증명방식)은 마이닝을 요청후 해당 마이닝 노드에서 임의의 값들로 컴퓨터 자원을 이용하여 
        # 해당 블록 체인 네트워크에서 문제내는 어떠한 해시값을 추리할때, 해당 해시값을 맞추면
        # 해당 노드가 블록을 생성할 수 있다는 것을 증명했다는것으로 생각하여 해당 노드는 pow을 통과
        # 마이닝할 수 있게되는 것이다.
        proof = 0
        # 여기서 proof는 논스로 pow과정중엣 pow를 만족시키기 위해 계속 값이 올라간다. 
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof
    @staticmethod
    def valid_proof(last_proof, proof):
        # 고정된 블록의 해시 입력값 + 논스값을 입력하여 pow증명을 해내가는 과정의 함수
        guess = str(last_proof + proof).encode()
        # pow을 하는 노드는 먼저 블록의 해시 입력값 + 논스값을 문자열로 인코딩한다.
        guess_hash = hashlib.sha256(guess).hexdigest()
        # 위에서 인코딩한 문자열 값을 sha256해시함수에 입력값으로 입력하여 64자리 문자열을 입력받고 다시 hexdigest로
        # 해당 64자리 문자열을 16진수로 변환하여 추측pow값을 추출한다.
        return guess_hash[:4] == "0000" 
    # 추측한 64자리가 만약 마지막 4자리가 0000이 되었을때,  