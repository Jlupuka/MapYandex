import sys
import requests
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPixmap
from YandexMapAPI import YandexUI

SCREEN_SIZE = [600, 450]


class MyApp(QWidget, YandexUI):
    def __init__(self, ll: str) -> None:
        super().__init__()
        self.setupUi(self)
        self.imageContent = None
        self.urlGeoCode = 'http://geocode-maps.yandex.ru/1.x/'
        self.urlStaticMap = 'http://static-maps.yandex.ru/1.x/'
        self.paramsGeoCode = {
            'apikey': '40d1649f-0493-4b70-98ba-98533de7710b',
            'format': 'json'
        }
        self.lParams = {'Спутник': 'sat', 'Схема': 'map', 'Гибрид': 'sat,skl'}
        self.paramsStaticMap = {
            'l': self.lParams['Схема'],
            'll': ll if ll else '4,20',
            'z': 16
        }
        self.ll = ll
        self.pixmap = QPixmap()
        self.initUI()

    def initUI(self) -> None:
        self.setWindowTitle('YandexMapAPI')
        self.checkBox.stateChanged.connect(self.checkbox_state_changed)
        self.satellite.toggled.connect(self.check_radio_buttons)
        self.hybrid.toggled.connect(self.check_radio_buttons)
        self.circuit.toggled.connect(self.check_radio_buttons)
        self.checkBox_2.clicked.connect(self.search_button)
        self.search.clicked.connect(self.search_button)
        self.clear.clicked.connect(self.clear_search)
        self.loadImage(self.ll)

    def loadImage(self, findPlace: str = None) -> None:
        self.imageContent = self.getImage(findPlace)
        self.pixmap.loadFromData(self.imageContent)
        self.image.setPixmap(self.pixmap)

    def getCoordinate(self, findPlace: str) -> tuple[str, str, str | None]:
        if findPlace == ',':
            findPlace = self.ll
        self.paramsGeoCode['geocode'] = findPlace
        response = requests.get(self.urlGeoCode, params=self.paramsGeoCode)
        responseJson = response.json()
        featureMember = responseJson['response']['GeoObjectCollection']['featureMember']
        position = featureMember[0]['GeoObject']['Point']['pos']
        metaData = featureMember[0]['GeoObject']['metaDataProperty']['GeocoderMetaData']
        postal_code = None
        if metaData.get('Address', {}).get('postal_code'):
            postal_code = metaData['Address']['postal_code']
        return position.replace(' ', ','), metaData['text'], postal_code

    def getImage(self, findPlace: str = None) -> None | bytes:
        if findPlace:
            coord, name, postal_code = self.getCoordinate(findPlace)
            self.paramsStaticMap['ll'] = coord
            self.editTextLine(postal_code=postal_code, name=name)
        response = requests.get(self.urlStaticMap, params=self.paramsStaticMap)
        if not response:
            print("Ошибка выполнения запроса:")
            print(response.url)
            print("Http статус:", response.status_code, "(", response.reason, ")")
            sys.exit(1)

        return response.content

    def keyPressEvent(self, event) -> None:
        ll = self.paramsStaticMap['ll'].split(',')
        if event.key() == Qt.Key_PageUp:
            self.paramsStaticMap['z'] = z + 1 if (z := self.paramsStaticMap['z']) < 17 else z
        elif event.key() == Qt.Key_PageDown:
            self.paramsStaticMap['z'] = z - 1 if (z := self.paramsStaticMap['z']) > 1 else z
        elif event.key() == Qt.Key_A:
            if (res := (float(ll[0]) - abs((self.paramsStaticMap['z'] - 18) * 0.1))) > 0:
                self.paramsStaticMap['ll'] = f"{res},{ll[1]}"
        elif event.key() == Qt.Key_D:
            if (res := (float(ll[0]) + abs((self.paramsStaticMap['z'] - 18) * 0.1))) < 180:
                self.paramsStaticMap['ll'] = f"{res},{ll[1]}"
        elif event.key() == Qt.Key_W:
            if (res := (float(ll[1]) + abs((self.paramsStaticMap['z'] - 18) * 0.1))) < 180:
                self.paramsStaticMap['ll'] = f"{ll[0]},{res}"
        elif event.key() == Qt.Key_S:
            if (res := (float(ll[1]) - abs((self.paramsStaticMap['z'] - 18) * 0.1))) > 0:
                self.paramsStaticMap['ll'] = f"{ll[0]},{res}"
        print(self.paramsStaticMap['z'])
        self.loadImage()

    def checkbox_state_changed(self, state) -> None:
        if state == 2:
            self.coordX.setEnabled(True)
            self.coordY.setEnabled(True)
            self.address.setEnabled(False)
        else:
            self.coordX.setEnabled(False)
            self.coordY.setEnabled(False)
            self.address.setEnabled(True)

    def check_radio_buttons(self) -> None:
        radio_button = self.sender()
        self.paramsStaticMap['l'] = self.lParams[radio_button.text()]
        self.loadImage()

    def search_button(self) -> None:
        if self.checkBox.isChecked():
            coord, name, postal_code = self.getCoordinate(f'{self.coordX.text()},{self.coordY.text()}')
        else:
            coord, name, postal_code = self.getCoordinate(self.address.text())
        self.editTextLine(postal_code=postal_code, name=name)
        self.ll = coord
        self.paramsStaticMap['ll'] = coord
        self.paramsStaticMap['pt'] = coord
        self.loadImage()

    def editTextLine(self, postal_code: str, name: str) -> None:
        self.textEdit.setText(name + (f'\nПочтовый индекс: {postal_code}'
                                      if postal_code and self.checkBox_2.isChecked() else ''))

    def clear_search(self) -> None:
        self.textEdit.clear()
        self.coordX.clear()
        self.coordY.clear()
        self.address.clear()
        try:
            del self.paramsStaticMap['pt']
        except KeyError:
            pass
        self.loadImage()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp(ll=input('[+] Введите координаты X, Y через запятую -> '))
    ex.show()
    sys.exit(app.exec_())
