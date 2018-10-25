import sys, os
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, uic
from PyQt5.QtCore import QThread, pyqtSlot, pyqtSignal, QRect
from PyQt5.QtGui import QPixmap, QImage, QMovie
import re, datetime
import pytube,urllib
from lib.Youscrapy_Layout import Ui_MainWindow
from pytube import YouTube

#1)Log폴더 없는 경우 해결 V
#2) YouTube정규식 적용
#3)옳바르지 않는 동영상 주소 체크 V
#4)다운로드 경로 저장해놓기 V

#실행 파일 경로 불러오기.
fp = os.path.dirname(os.path.abspath(__file__))

class Main(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.initSignal()
        self.initDeactivate()
        self.loadPath()

        self.showStatusMsg('Hello Youscrapy!!!')
        self.check = 0
        ###더미 데이터
        #self.textEdit_URL.setText('https://www.youtube.com/watch?v=5HSy4PiUEDw')

    #시그널 초기화
    def initSignal(self) :
        #self.btn_Preview.clicked.connect(self.preview_Youtube)
        self.youtube_info = YouTube_Info()
        self.youtube_info.info_signal.connect(self.setInfo)
        self.youtube_down = YouTube_Down()
        self.youtube_down.down_signal.connect(self.setProgress)

    #스테이터스바 메시지 출력
    def showStatusMsg(self, msg) :
        self.statusbar.showMessage(msg)

    def initDeactivate(self) :
        self.combo_Stream.setEnabled(False)
        self.btn_Path.setEnabled(False)
        self.btn_Download.setEnabled(False)

    def initActivate(self) :
        self.combo_Stream.setEnabled(True)
        self.btn_Path.setEnabled(True)
        self.btn_Download.setEnabled(True)


    # YouTube_Info클래스에서 불러온 데이터 세팅.
    def setInfo(self, title, thumbnail, stream, check) :
        if not check == 1 :
            self.label_thumbnail.setPixmap(QPixmap(fp + "/resource/YouTube.jpg"))
            self.append_Log_Msg('YouTube Receive Failed...')
            self.errorPopup('url')
            return None

        self.label_title.setText(title)

        image = QImage()
        image.loadFromData(thumbnail)
        rect = QRect(0,12,120,66)
        image = image.copy(rect)
        self.label_thumbnail.setPixmap(QPixmap(image))

        self.setComboStream(stream)

        self.append_Log_Msg("YouTube Received!!!")
        self.showStatusMsg(title)

    #화질 불러오기.
    def setComboStream(self,stream) :
        self.combo_Stream.clear()
        print(stream)
        for q in stream :
            # print(q.resolution) # res로 불러오면 안되는데, 버그인듯?
            tmp_list, str_list = [], []
            tmp_list.append(str(q.mime_type or ''))
            tmp_list.append(str(q.resolution or ''))
            tmp_list.append(str(q.fps or ''))
            tmp_list.append(str(q.abr or ''))

            str_list = [x for x in tmp_list if x != '']

            self.combo_Stream.addItem(','.join(str_list))

    #프로그래스바 설정.
    def setProgress(self, value):
        self.progressBar.setValue(value)
        print(value)
        if value >= 100 and self.check == 0:
            self.check += 1
            self.append_Log_Msg('Download Complete!!!')

    #로그 메시지 출력 및 저장
    def append_Log_Msg(self, msg) :
        now = datetime.datetime.now()
        appDatetime = now.strftime('%Y-%m-%d %H:%M:%S')
        logDatetime = now.strftime('%Y-%m-%d')

        #프로그램 로그에 출력
        app_msg = msg
        log_msg = '(' + appDatetime + ') - ' + msg
        self.plainTextEdit.appendPlainText(app_msg) #insertPlainText는 줄을 바꾸지 않음

        #app_msg를 활동 로그에 저장
        #1)Log폴더 없는 경우 해결
        if not os.path.isdir(fp+'/log') :
            os.mkdir(fp+'/log')
        with open(fp+'/log/{}'.format(logDatetime), 'a') as f:
            f.write(app_msg+'\n')

    #에러팝업창.
    def errorPopup(self, msg) :
        if msg == 'url' :
            QMessageBox.about(self,'URL 주소 오류', '정확한 YouTube 동영상 주소를 입력해주세요.')
            self.showStatusMsg('URL Error!!!')
        elif msg == 'path':
            QMessageBox.about(self,'다운로드 경로 오류', '정확한 다운로드 경로를 입력해주세요.')
            self.showStatusMsg('Path Error!!!')
        else :
            QMessageBox.about(self,'오류', '무언가 오류...')
            self.showStatusMsg('Error!!!')

    #다운로드 경로 선택.
    def selectDownPath(self) :
        #경로 선택
        fpath = QFileDialog.getExistingDirectory(self)
        self.label_Path.setText(fpath)


    #프리뷰 버튼 클릭
    @pyqtSlot()
    def on_btn_Preview_clicked(self) :
        #url 입력받고 정규식으로 체크
        #2) YouTube정규식 적용
        url = self.textEdit_URL.text().strip()
        v = re.compile("^https://www.youtube.com/?")
        self.check = 0

        #옳바른 주소를 입력했을 경우.
        if v.match(url) is not None :
            self.initActivate()
            self.append_Log_Msg(url)
            self.showStatusMsg(url + ' - Loading...')

            movie = QMovie(fp+"/resource/loading.gif")
            self.label_thumbnail.setMovie(movie)
            movie.start()

            self.youtube_info.yt_url = self.textEdit_URL.text()
            self.youtube_info.start()


        #잘못된 주소를 입력했을 경우.
        else:
            self.errorPopup('url')
            self.textEdit_URL.setFocus(True)

    #경로 버튼 클릭
    @pyqtSlot()
    def on_btn_Path_clicked(self) :
        #4)다운로드 경로 저장해놓기
        self.selectDownPath()

    #다운로드 버튼 클릭.
    @pyqtSlot()
    def on_btn_Download_clicked(self) :
        #print('Download Button Click')
        path = self.label_Path.text().strip()
        #print(path)
        if not os.path.isdir(path) :
            self.errorPopup('path')
            return None

        self.append_Log_Msg("Download initializing....")
        self.savePath(str(path))
        self.youtube_down.yt_url = self.textEdit_URL.text()
        self.youtube_down.yt_path = self.label_Path.text()
        self.youtube_down.yt_stream = self.combo_Stream.currentIndex()
        self.youtube_down.start()

    #추후 실행했을 때를 위한, 저장 경로 기억하기.
    def savePath(self,path) :
        if not os.path.isdir(fp+'/log') :
            os.mkdir(fp+'/log')
        if not(path == '' or path is None) :
            with open(fp+'/log/pathLog', 'w') as f:
                f.write(path)

    #추후 실행시, 저장경로 불러오기
    def loadPath(self) :
        try:
            with open(fp+'/log/pathLog', 'r') as f:
                self.label_Path.setText(f.readline())
        except Exception as e:
            self.label_Path.setText('다운로드 경로')


#---------- YouTube Info ----------#
#유튜브 정보 불러오는 쓰래드.
class YouTube_Info(QThread) :
    info_signal = QtCore.pyqtSignal(str, bytes, list, int)

    def __init__(self) :
        super(YouTube_Info,self).__init__()
        self.yt_url = ""
        self.yt_title = ""
        self.yt_thumbnail = ""
        self.yt_stream = ""

    @pyqtSlot(str, bytes, list, int)
    def run(self) :
        print('run')
        #3)옳바르지 않는 동영상 주소 체크
        try:
            print('try')
            self.get_Info(self.yt_url)
            yttitle = self.yt_title
            ytthumbnail = self.yt_thumbnail
            ytstream = self.yt_stream
            ytcheck = 1
            self.info_signal.emit(yttitle, ytthumbnail, ytstream, ytcheck)
        except:
            yttitle = self.yt_title
            ytthumbnail = self.yt_thumbnail
            ytstream = self.yt_stream
            ytcheck = 0
            self.info_signal.emit(yttitle, ytthumbnail, ytstream, ytcheck)
            print("YouTube_Info - Error!!!")

    def get_Info(self, url):
        video_info = YouTube(url)
        self.yt_title = video_info.title
        thumbnail = video_info.thumbnail_url
        self.yt_thumbnail = urllib.request.urlopen(thumbnail).read()
        self.yt_stream = video_info.streams.all()
        print(self.yt_stream)


#---------- YouTube Down ----------#
#유튜브 다운 받는 쓰래드.
class YouTube_Down(QThread) :
    down_signal = QtCore.pyqtSignal(float)

    def __init__(self):
        super(YouTube_Down, self).__init__()
        self.yt_url = ""
        self.yt_path = ""
        self.yt_stream = ""

    @pyqtSlot(str)
    def run(self):
        self.download(self.yt_url,self.yt_path, self.yt_stream)

    def download(self, url, path, stream):
        video = YouTube(url)
        video_streams = video.streams.all()
        print('video.register_on_complete_callback')
        video.register_on_progress_callback(self.progress_Bar)
        try:
            print('self.video')
            print(url, path, stream)
            video_streams[stream].download(path)
        except:
            print("YouTube_Down - Error")

    def progress_Bar(self, stream, chunk, file_handle, bytes_remaining):
        p = round(file_handle.tell() / (file_handle.tell() + bytes_remaining) * 100, 1)
        self.down_signal.emit(p)



if __name__ == "__main__" :
    app = QApplication(sys.argv)
    youscrapy_main = Main()
    youscrapy_main.show()
    app.exec_()
