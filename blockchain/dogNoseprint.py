import dlib
import os
from imutils import face_utils
import numpy as np
import matplotlib.pyplot as plt
import cv2 as cv
import cv2
from sklearn.cluster import KMeans
import math
import imghdr
import time
'''사진속의 개의 얼굴을 박스로 찾아내고 해당 박스내에서 다시 개의 코의 부분만을 찾아내는 함수.'''
class noseprintshot(object):
    def find_dog_nose(img_path, size=None, debug=False ):
        img_name=img_path.strip("./templates/"".jpg")
        input_image = cv.imread(img_path)
        input_image = cv.cvtColor(input_image, cv.COLOR_BGR2RGB)
        detector= dlib.cnn_face_detection_model_v1('./studydata/dogHeadDetector.dat')
        predictor = dlib.shape_predictor('./studydata/landmarkDetector.dat')
        image = input_image.copy() # 가져온 이미지를 복사하여 가져온 이미지 대신 복사 이미지를 수정
        if size:
            image = imutils.resize(image, width=size) # 만약 입력된 사이즈가 존재하면, 입력된 사이즈대로 영상 크기를 지정.
        gray_image = cv.cvtColor(image, cv.COLOR_BGR2GRAY) # 입력된 영상을 Gray(HxWx1(Intensity))형태로 변환
        dets = detector(gray_image, 1) # 해당 이미지를 가져온 개 얼굴 인식 모델을 사용해서 개 얼굴 탐지 및 탐지된 얼굴 수를 입력.
        print('Found {} faces.'.format(len(dets))) # 입력된 영상에서 찾은 개의 얼굴의 갯수를 표시
        k = 0

        for (i, det) in enumerate(dets): # 감지된 얼굴 박스들의 수만큼 루프를 돌며 순서대로 박스 표시 
            nosearea = input_image.copy() # 출력될 코 영역 사진
            k=k+1
            # 코의 SUBPLOT을 표시하기위한 인덱스 값
            # 얼굴 영역의 얼굴 랜드마크를 결정한 다음 얼굴 랜드마크(x, y) 좌표를 NumPy Array로 변환합니다.
            shape = predictor(image, det.rect) # 각 개의 얼굴의 부분()
            shape = face_utils.shape_to_np(shape)
            print(shape)
            # dlib의 사각형을 OpenCV bounding box로 변환(x, y, w, h)
            (x, y, w, h) = face_utils.rect_to_bb(det.rect) 
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(image, "Face #{}".format(i + 1), (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            # 감지된 얼굴 박스 위에 얼굴 #번호 텍스트를 입력
            if debug:
                # 얼굴 랜드마크에 포인트를 그립니다.
                for (i, (x, y)) in enumerate(shape):# 해당 얼굴 박스에서 얼굴의 각 부분을 감지한 부분들의 수(총 6개)만큼 
                                                     # 루프를 돌며 표시.
                    cv2.circle(image, (x, y), int(image.shape[1]/250), (0, 0, 255), -1)
                    # 각 랜드마크 지점(얼굴의 상위 3지점, 두 눈, 코 총 6개의 점)에 표시
                    if (i == 5): # 왼쪽 눈일때, 왼쪽 눈의 좌표값을 저장하고 해당 지점이 왼쪽 눈임을 텍스트로 표시
                        eyel_x,eyel_y = x,y
                        cv2.putText(image, "Left eyes", (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
                    if (i == 2):# 오른쪽 눈일때, 오른쪽 눈의 좌표값을 저장하고 해당 지점이 오른쪽 눈임을 텍스트로 표시
                        eyer_x,eyer_y = x,y
                        cv2.putText(image, "Right eyes", (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
                    if (i == 3):# 코의 중심 좌표값을 저장하고 해당 지점이 코의 중심임을 텍스트로 표시
                        nose_x,nose_y = x,y
                        cv2.putText(image, "NoseDetect", (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
                    # cv2.putText(image, str(i + 1), (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.2, (255, 255, 255), 1)
            length_cut1=math.sqrt(abs(eyel_x - nose_x)**2+abs(eyel_y - nose_y)**2) 
            length_cut1= round(length_cut1) # 인덱스로 영역을 분할할 것이므로 반올림해준다.
            length_cut2=math.sqrt(abs(eyer_x - nose_x)**2+abs(eyer_y - nose_y)**2)
            length_cut2= round(length_cut2) # 인덱스로 영역을 분할할 것이므로 반올림해준다.
            if (length_cut1 >length_cut2):
                length_cut=round(length_cut1/3)
                # 긴 쪽으로 하는데, 이것은 각도에 따라 눈과 코의 거리가 짧아져 코의 전반적인 부분이 짤릴수 있으므로.
                # 먼저 왼쪽 눈과 코의 중심거리가 더 길다면 왼쪽 눈과 코의 중심거리를 CUT길이로 지정.
            else:
                length_cut=round(length_cut2/3)
                # 만약 왼쪽 눈고 코의 중심거리가 오른쪽 눈과의 거리보다 짧다면 오른쪽 눈과의 거리를 CUT 길이로 지정
            nosearea=nosearea[nose_y-length_cut:nose_y+length_cut,nose_x-length_cut:nose_x+length_cut]
            # 코 영역 추출 [코의 중심에서 각 눈에서 코의 중심까지의 거리/2만큼 W,H를 지정]

            nosearea_nocolor=cv.cvtColor(nosearea, cv2.COLOR_BGR2GRAY)
            # 코 영역을 BGR TO GRAY 컨버져
            cv2.imwrite('./dognosedict/nosearea_dog{0}_{1}.jpg'.format(k,img_name), nosearea_nocolor)
            # 해당 코 영역을 GRAY채널로 JPG 저장
            dst = cv.normalize(nosearea_nocolor, None, 0, 255, cv.NORM_MINMAX)
            # 해당 GRAY 채널로 만든 코 영역을 스트레칭하여, 명암비를 확실히 함.
            cv2.imwrite('./dognosedict/nosearea_dog{0}_{1}.jpg'.format(k,img_name), dst)
            # 스트레칭한 GRAY채널 코 영역 JPG 저장
            nosearea_nocolor=cv.imread('./dognosedict/nosearea_dog{0}_{1}.jpg'.format(k,img_name))
            # 저장한 GRAY채널 코 영역을 읽어옴
            noseimg_st=cv.imread('./dognosedict/nosearea_dog{0}_{1}.jpg'.format(k,img_name))
            # 저장한 스트레칭한 GRAY채널 코 영역을 읽어옴
            nosearea_nocolor = cv.resize(nosearea_nocolor, (1280, 720), interpolation=cv.INTER_LANCZOS4)
            noseimg_st = cv.resize(noseimg_st, (1280, 720), interpolation=cv.INTER_LANCZOS4)
            # 눈으로 보기 좋게 1280*720비율로 RESIZE, 보간은 가장 퀄리티가 좋은 64픽셀을 이용하는 Lanczos 보간법이용

            # 스트레칭한 이미지의 바이너리 이미지 생성
            plt.subplot(1, len(dets), k) 
            plt.imshow(nosearea_nocolor)
            plt.title('NoseArea Not contrast stretching')
            plt.xticks([]), plt.yticks([])
            plt.show()
            plt.imshow(noseimg_st)
            plt.title('NoseArea contrast stretching')
            plt.xticks([]), plt.yticks([])
            plt.show()
        if (len(dets)>1):
            print('we can only One your pet NosePrint. Check your background.\n')
        return './dognosedict/nosearea_dog{0}_{1}.jpg'.format(k,img_name)
    def noseprint_SIFT(input_noseimg): 
        # SIFT 알고리즘을 활용해 특징점들을 추출하는 함수
        # 출력: KEYPOINT = 특징점 DESCRIPTOR = 각 특징점에 대한 128개 벡터
        gray = cv2.imread(input_noseimg)
        # SIFT 추출기 생성
        sift = cv.xfeatures2d.SIFT_create()
        # 키 포인트 검출과 서술자 계산
        keypoints, descriptor = sift.detectAndCompute(gray, None)
        return (keypoints, descriptor)
    def matcher_twoimage_knn(kp1,desc1,kp2,desc2,img1,img2,rate=0.75,type_algori ="SIFT"):
        # BFMatcher 생성, L2 거리, 상호 체크 ---③
        # 매칭 결과를 거리기준 오름차순으로 정렬 ---③
        if type == "SIFT":
            bf = cv2.BFMatcher(cv2.NORM_L1) 
        elif type == "SURF":
            bf = cv2.BFMatcher(cv2.NORM_L2) 
        elif type == "ORB":
            bf = cv2.BFMatcher(cv2.NORM_HAMMING)
        else :
            bf = cv2.BFMatcher(cv2.NORM_L1)

        matches = bf.knnMatch(desc1,desc2, k=2)
        # Brute-Force 매칭기 생성.입력 이미지 descriptor 하고 대상 이미지 descriptor를 하나하나 비교.


        # 매칭기의 매칭 기준 알고리즘을 knnMatch로 설정(대상 이미지 desciptor의 하나에서 가장 근접한 k=2개의 이웃한 입력 이미지 
        # descriptor들을 찾아내 반환한다.)
        good = []
        # 반환된 descriptor중 반환된 각 하나의 대상 descriptor에 대한 입력 descriptor들의 거리가 인접할때, 즉 더 정확한 descrpitor들만 
        # 찾아내 반환함. 반환시 최근접한 이웃 descriptor부터 출력됨.

        for i,pair in enumerate(matches):
            try:
                m,n = pair
                if m.distance < rate*n.distance: # 첫번째 이웃의 거리가 두번째 이웃거리의 3/4보다 가까운 경우만, 첫번째 descriptor를 추가
                    good.append([m]) # 해당 descriptor를 좋다고 판단하고 추가
            except ValueError:
                pass
        img3 = cv2.drawMatchesKnn(img1,kp1,img2,kp2,good,None,flags=2) 
        # 찾은 좋은 매칭들만 그림에 표시
        plt.imshow(img3),plt.show()
        # 표시한 그림 나타내기
        print('{0} match in {1} '.format(len(good),len(matches)))
        # 찾은 좋은 매칭점 : 전체 찾은 매칭점
        print("Match ? {0}".format(0.25<=(len(good)/len(matches))))
        return 0.25<=(len(good)/len(matches))
        # 만약 좋은 매칭점들이 전체 찾은 매칭점과의 비율이 0.33(about 1/3)보다 클때, 해당 두개의 그림이 같다고 판단.