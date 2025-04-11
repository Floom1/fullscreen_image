import sys
import os
import random
import configparser
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer, QEvent, QByteArray
from smb.SMBConnection import SMBConnection
import io



class FullScreenWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.allow_close = False
        self.initUI()


    def initUI(self):
        self.setWindowTitle("Full Screen App")
        self.showFullScreen()

        self.setWindowFlags(
            Qt.Window |
            Qt.CustomizeWindowHint |
            Qt.WindowStaysOnTopHint
        )

        # Чтение конфигурации
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.interval = int(config['Settings']['interval'])
        self.folder_path = config['Settings']['folder_path']
        self.login = config['Settings'].get('login', '')
        self.password = config['Settings'].get('password', '')

        # Проверка, сетевая ли папка
        self.is_network_folder = self.folder_path.startswith('\\\\')

        # Получение списка изображений
        if self.is_network_folder:
            images = self.get_network_images()
        else:
            images = self.get_local_images()

        if not images:
            print("Нет изображений в папке")
            sys.exit(1)

        # Выбор случайного изображения
        random_image = random.choice(images)
        if self.is_network_folder:
            image_data = self.download_network_image(random_image)
            if image_data is None:
                print("Не удалось загрузить изображение")
                sys.exit(1)
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
        else:
            image_path = os.path.join(self.folder_path, random_image)
            pixmap = QPixmap(image_path)

        if pixmap.isNull():
            print(f"Не удалось загрузить изображение")
            sys.exit(1)

        # Отображение изображения
        label = QLabel(self)
        label.setPixmap(pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(label)

        # Настройка таймера для закрытия
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.on_timeout)
        self.timer.start(self.interval * 1000)
        print(f"Таймер запущен на {self.interval} секунд")


    def get_local_images(self):
        """Получение списка изображений из локальной папки"""
        try:
            return [f for f in os.listdir(self.folder_path) if f.endswith('.jpg')]
        except Exception as e:
            print(f"Ошибка доступа к локальной папке: {e}")
            return []


    def get_network_images(self):
        """Получение списка изображений из сетевой папки"""
        server_name = self.folder_path.split('\\')[2]
        share_name = self.folder_path.split('\\')[3]
        client_name = "MyPC"

        conn = SMBConnection(self.login, self.password, client_name, server_name, use_ntlm_v2=True)
        try:
            conn.connect(server_name, 139)
            files = conn.listPath(share_name, "/")
            images = [f.filename for f in files if f.filename.endswith('.jpg')]
            return images
        except Exception as e:
            print(f"Ошибка подключения к сетевой папке: {e}")
            return []
        finally:
            conn.close()


    def download_network_image(self, image_name):
        """Загрузка изображения из сетевой папки в память"""
        server_name = self.folder_path.split('\\')[2]
        share_name = self.folder_path.split('\\')[3]
        client_name = "MyPC"

        # Список портов для попыток: сначала более новый - 445, затем для старых систем - 139
        ports = [445, 139]

        for port in ports:
            conn = SMBConnection(self.login, self.password, client_name, server_name, use_ntlm_v2=True)
            try:
                conn.connect(server_name, port)
                # Загружаем изображение в память
                image_data = io.BytesIO()
                conn.retrieveFile(share_name, f"/{image_name}", image_data)
                image_data.seek(0)  # Возвращаемся к началу потока
                print(f"Изображение {image_name} загружено в память с порта {port}")
                return image_data.getvalue()  # Возвращаем байты
            except Exception as e:
                print(f"Ошибка при подключении к порту {port}: {e}")
            finally:
                conn.close()

        print(f"Не удалось загрузить изображение {image_name}")
        return None


    def on_timeout(self):
        print("Таймер сработал, закрываем окно")
        self.allow_close = True
        self.close()
        QApplication.instance().quit()


    def closeEvent(self, event):
        if not self.allow_close:
            event.ignore()
        else:
            print("Закрываем окно")
            event.accept()


    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.windowState() & Qt.WindowMinimized:
                print("Попытка свернуть окно, восстанавливаем")
                self.setWindowState(Qt.WindowMaximized)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FullScreenWindow()
    window.show()
    sys.exit(app.exec_())