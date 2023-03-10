import os.path
import re
import urllib3
from urllib.parse import quote
import requests
from PyQt5 import QtCore
from lxml import etree
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QSlider, QTableWidget, \
    QHeaderView, QAbstractItemView, QTableWidgetItem, QMenu
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl, QTimer
from PyQt5.QtGui import QIcon, QImage, QPixmap
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer

from constants.window_constant import MUSIC_SEARCH_TABLE_COLUMN, ROOT_DIR
from window_func.notify_handler import NotificationWindow


class SearchMusicPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.search_result_musics = []
        self.music_name_list = []
        self.play_index = -1
        self.play_volume = 50
        self.timer = QTimer()
        self.timer.start(1000)
        self.player = QMediaPlayer()
        self.playing = False
        self.setup_ui()
        self.setup_link_event()

    def setup_link_event(self):
        self.search_btn.clicked.connect(self.search_music)
        self.timer.timeout.connect(self.timeout_process)
        self.play_duration.sliderMoved.connect(self.music_time_adjust)
        self.play_duration.sliderReleased.connect(self.music_time_adjust_over)
        self.play_duration.sliderPressed.connect(self.slider_play_press)

    def setup_ui(self):
        self.global_layout = QVBoxLayout()
        self.setup_search_top()
        top_widget = QWidget()
        top_widget.setLayout(self.top_layout)
        self.setup_search_result()
        self.bottom_widget = QWidget()
        self.bottom_widget.setLayout(self.bottom_layout)
        self.setup_search_footer()
        self.foot_widget = QWidget()
        self.foot_widget.setLayout(self.foot_layout)
        self.global_layout.addWidget(top_widget)
        self.global_layout.addWidget(self.bottom_widget)
        self.global_layout.addWidget(self.foot_widget)
        self.setLayout(self.global_layout)
        if self.search_result_musics == []:
            self.bottom_widget.hide()
            self.foot_widget.hide()

    def setup_search_footer(self):
        self.foot_layout = QHBoxLayout()
        self.previous_btn = QPushButton("?????????")
        self.play_btn = QPushButton("??????")
        self.next_btn = QPushButton("?????????")
        self.play_duration = QSlider(Qt.Horizontal)
        self.play_duration.setMinimum(0)
        self.play_duration.setMaximum(1000)

        self.volumn_splider = QSlider(Qt.Horizontal)
        self.volumn_splider.setMinimum(0)
        self.volumn_splider.setMaximum(100)
        self.volumn_splider.setValue(self.play_volume)

        self.foot_layout.addWidget(self.previous_btn)
        self.foot_layout.addWidget(self.play_btn)
        self.foot_layout.addWidget(self.next_btn)
        self.foot_layout.addWidget(self.play_duration)
        self.foot_layout.addWidget(self.volumn_splider)

        self.play_btn.clicked.connect(self.music_state)
        self.previous_btn.clicked.connect(self.play_previous_music)
        self.next_btn.clicked.connect(self.play_next_music)
        self.volumn_splider.valueChanged.connect(self.music_volume_change)

    def setup_search_top(self):
        self.top_layout = QHBoxLayout()
        self.top_layout.setAlignment(Qt.AlignCenter)
        self.search_key_edit = QLineEdit()
        self.search_key_edit.setAlignment(Qt.AlignCenter)
        self.search_key_edit.setPlaceholderText("??????????????????/????????????")
        self.search_key_edit.setText("?????????")
        self.search_key_edit.setFixedWidth(600)
        self.search_key_edit.setFocus()
        self.search_key_edit.setClearButtonEnabled(True)
        self.search_key_edit.setStyleSheet(
            'color: rgb(180, 180, 180); font: 16px "????????????";')
        self.search_btn = QPushButton(
            QIcon("static/icon/book_search_btn.png"), "??????")
        self.search_btn.setStyleSheet(
            'color: rgb(180, 180, 180); font: 16px "????????????";')
        self.search_btn.setFixedWidth(100)
        self.top_layout.addWidget(self.search_key_edit)
        self.top_layout.addWidget(self.search_btn)

    def setup_search_result(self):
        self.bottom_layout = QHBoxLayout()

        left_layout = QVBoxLayout()
        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setFixedHeight(500)

        self.img_label.setScaledContents(True)
        # ??????label????????????
        self.img_label.setPixmap(QPixmap(""))

        left_layout.addWidget(self.img_label)
        # ?????????????????????
        right_layout = QHBoxLayout()
        self.music_table = QTableWidget()
        self.music_table.setColumnCount(len(MUSIC_SEARCH_TABLE_COLUMN))
        self.music_table.verticalHeader().setVisible(False)
        self.music_table.setHorizontalHeaderLabels(MUSIC_SEARCH_TABLE_COLUMN)
        self.music_table.setShowGrid(False)
        self.music_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.music_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.music_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.music_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.music_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.music_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.music_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.music_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.music_table.customContextMenuRequested[QtCore.QPoint].connect(self.right_click_menu)

        self.music_table.itemClicked.connect(self.play_choice_music)
        right_layout.addWidget(self.music_table)

        self.left_widget = QWidget()
        self.left_widget.setLayout(left_layout)
        self.right_widget = QWidget()
        self.right_widget.setLayout(right_layout)

        self.bottom_layout.addWidget(self.left_widget)
        self.bottom_layout.addWidget(self.right_widget)

    def insert_musics(self, music_dict):
        if music_dict:
            self.bottom_widget.show()
            self.foot_widget.show()
            self.search_result_musics.append(music_dict)
            self.music_name_list.append(music_dict.get("music_name"))
            count = self.music_table.rowCount()
            self.music_table.insertRow(self.music_table.rowCount())
            # ??????
            index_cell_item = QTableWidgetItem(str(count + 1))
            index_cell_item.setTextAlignment(Qt.AlignCenter)
            self.music_table.setItem(count, 0, index_cell_item)
            # ????????????
            title_cell_item = QTableWidgetItem(str(music_dict.get("music_name")))
            title_cell_item.setTextAlignment(Qt.AlignCenter)
            self.music_table.setItem(count, 1, title_cell_item)
            # ??????
            author_cell_item = QTableWidgetItem(str(music_dict.get("singer_name")))
            author_cell_item.setTextAlignment(Qt.AlignCenter)
            self.music_table.setItem(count, 2, author_cell_item)
            # ??????
            update_chapter_cell_item = QTableWidgetItem(str(music_dict.get("music_type")))
            update_chapter_cell_item.setTextAlignment(Qt.AlignCenter)
            self.music_table.setItem(count, 3, update_chapter_cell_item)
            # ??????
            from_cell_item = QTableWidgetItem(str(music_dict.get("music_song_quality")))
            from_cell_item.setTextAlignment(Qt.AlignCenter)
            self.music_table.setItem(count, 4, from_cell_item)

    def search_music(self):
        music_key = self.search_key_edit.text()
        if music_key:
            self.music_name_list.clear()
            self.search_result_musics.clear()
            self.music_table.setRowCount(0)
            self.search_result_musics.clear()
            self.play_index = -1
            search_thread = SearchMusic(music_key)
            search_thread.search_result_pyqtSignal_trigger.connect(self.insert_musics)
            search_thread.start()
            search_thread.exec()

    def play_choice_music(self, item):
        self.play_index = item.row()
        target = self.search_result_musics[self.play_index]
        self.music_play(target)

    def music_play(self, music_detail: dict):
        try:
            self.play_duration.setValue(0)
            self.img_resp = requests.get(music_detail["photo_url"])
            self.img = QImage.fromData(self.img_resp.content)
            self.img_label.setPixmap(QPixmap.fromImage(self.img))
            self.player.setMedia(QMediaContent(QUrl(music_detail["music_url"])))
            self.playing = True
            self.player.play()
        except Exception as e:
            NotificationWindow.error(self, "??????", "??????{}????????????".format(music_detail["music_name"]))

    def play_previous_music(self):
        if self.play_index > 0:
            self.play_index -= 1
            target = self.search_result_musics[self.play_index]
            self.music_play(target)
        else:
            self.play_index = 0
            self.play_duration.setValue(0)

    def play_next_music(self):
        if self.play_index < len(self.search_result_musics) - 1:
            self.play_index += 1
            target = self.search_result_musics[self.play_index]
            self.music_play(target)
        else:
            self.play_index = 0
            self.play_duration.setValue(0)

    def music_state(self):
        if self.playing:
            self.play_btn.setText("??????")
            self.player.pause()
            self.playing = False
        else:
            self.play_btn.setText("??????")
            self.player.play()
            self.playing = True

    def music_volume_change(self):
        self.play_volume = self.volumn_splider.value()
        self.player.setVolume(self.play_volume)

    def timeout_process(self):
        if self.playing:
            old_time = self.play_duration.value()
            self.play_duration.setValue(old_time + 1)
            music_total_time = self.player.duration()
            self.play_duration.setRange(0, int(music_total_time / 1000) + 1)
            # ???????????????????????????????????????????????????
            if old_time == int(music_total_time / 1000):
                self.play_next_music()

    def music_time_adjust(self):
        self.player.pause()
        self.player.setPosition(self.play_duration.value() * 1000)

    def music_time_adjust_over(self):
        self.timer.start(1000)
        self.player.play()

    def slider_play_press(self):
        self.timer.stop()

    def right_click_menu(self, pos):
        pop_menu = QMenu()
        delete_item = pop_menu.addAction("??????")
        action = pop_menu.exec_(self.music_table.mapToGlobal(pos))
        if action == delete_item:
            row_index = self.music_table.currentRow()
            download_music_detail = self.search_result_musics[row_index]
            download_thread = DownloadThread(download_music_detail)
            download_thread.downloadSignalTrigger.connect(self.notify_download_state)
            download_thread.start()
            download_thread.exec()

    def notify_download_state(self, download_info: dict):
        state = download_info["state"]
        music_name = download_info["music_name"]
        if state:
            NotificationWindow.success(self, "??????", "?????????{}?????????".format(music_name))
        else:
            NotificationWindow.error(self, "??????", "?????????{}?????????".format(music_name))


class SearchMusic(QThread):
    search_result_pyqtSignal_trigger = pyqtSignal(dict)

    def __init__(self, music_key, page=1):
        super(SearchMusic, self).__init__()
        self.headers = {
            # "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            # "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36",
            "referer": "https://www.hifini.com",
        }

        self.base_url = "https://www.hifini.com/"
        self.search_music_url = "https://www.hifini.com/search-{}-{}.htm"
        self.music_key = music_key
        self.page = page

    def run(self):
        quota_target = quote(self.music_key).replace("%", "_")
        url = self.search_music_url.format(quota_target, self.page)
        urllib3.disable_warnings()
        res = requests.post(url, headers=self.headers, verify=False)
        if res.status_code != 200:
            return []
        else:
            e = etree.HTML(res.text)
            music_name = e.xpath('//div[@class="media-body"]/div/a/text()')
            music_next_url = e.xpath('//div[@class="media-body"]/div/a/@href')
            if all([music_name, music_next_url]):
                for next_url in music_next_url:
                    self.get_detail_music(self.base_url + next_url)

    def get_detail_music(self, url):
        result = {}
        res = requests.get(url)
        e = etree.HTML(res.text)
        aplayer = e.xpath('//div[@class="aplayer"]')
        if not aplayer:
            return result
        else:
            strr2 = res.text
            music_url = re.findall(" url: '(.*?)',", strr2, re.S)
            if not music_url:
                return result
            music_name = re.findall(" title: '(.*?)',", strr2, re.S)
            if not music_name:
                return result
            photo_url = re.findall(" pic: '(.*?)'", strr2, re.S)
            if not photo_url:
                return result
            singer_name = re.findall(" author:'(.*?)',", strr2, re.S)
            if not singer_name:
                return result
            # ??????
            music_lyrics = e.xpath(
                '//*[@id="body"]/div/div/div[1]/div[1]/div/div[2]/p/text()')[:-1]
            # ??????????????????
            music_type = e.xpath(
                '//*[@id="body"]/div/div/div[1]/ol/li[2]/a/text()')
            # ??????
            music_sound_quality = e.xpath(
                '//*[@id="body"]/div/div/div[1]/div[1]/div/div[1]/div/h4/text()')[0].replace("\t", "")
            target_chat_index = music_sound_quality.index("[")
            music_detail = {
                "music_url": self.base_url + music_url[0],
                "music_type": music_type[0],
                "music_song_quality": music_sound_quality[target_chat_index + 1:-1],
                "music_lyrics": music_lyrics,
                "music_name": music_name[0],
                "photo_url": photo_url[0],
                "big_photo_url": photo_url[0],
                "singer_name": singer_name[0],
            }
            self.search_result_pyqtSignal_trigger.emit(music_detail)


class DownloadThread(QThread):
    downloadSignalTrigger = pyqtSignal(dict)

    def __init__(self, music_detail):
        super(DownloadThread, self).__init__()
        self.music_detail = music_detail

    def run(self):
        # ????????????url
        download_url = self.music_detail["music_url"]
        music_name = self.music_detail["music_name"]
        music_auther = self.music_detail["singer_name"]
        music_resp = requests.get(download_url)
        transmit_dict = {
            "music_name": music_name,
        }
        save_path = os.path.join(ROOT_DIR, "download", "{}".format(music_auther))
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        try:
            with open(os.path.join(save_path, "{}.mp3".format(music_name)), "wb") as fp:
                fp.write(music_resp.content)
            transmit_dict.update({"state": True})
            self.downloadSignalTrigger.emit(transmit_dict)
        except Exception:
            transmit_dict.update({"state": False})
            self.downloadSignalTrigger.emit(transmit_dict)
