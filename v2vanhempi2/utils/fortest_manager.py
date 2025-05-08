# utils/fortest_manager.py
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot, QMetaObject, Qt, Q_ARG
from utils.fortest_handler import ForTestHandler

class ForTestWorker(QObject):
    resultReady = pyqtSignal(object, int, str)  # tulos, operaatiokoodi, virheviesti
    
    def __init__(self, port='/dev/ttyUSB1', baudrate=19200):
        super().__init__()
        try:
            self.fortest = ForTestHandler(port=port, baudrate=baudrate)
        except Exception as e:
            print(f"ForTest-yhteys epäonnistui: {e}")
            from utils.fortest_handler import DummyForTestHandler
            self.fortest = DummyForTestHandler()
    
    @pyqtSlot()
    def start_test(self):
        """Käynnistä testi taustasäikeessä"""
        try:
            result = self.fortest.start_test()
            self.resultReady.emit(result, 1, "")  # 1 = käynnistys
        except Exception as e:
            self.resultReady.emit(False, 1, f"Virhe testin käynnistyksessä: {str(e)}")
    
    @pyqtSlot()
    def abort_test(self):
        """Keskeytä testi taustasäikeessä"""
        try:
            result = self.fortest.abort_test()
            self.resultReady.emit(result, 2, "")  # 2 = keskeytys
        except Exception as e:
            self.resultReady.emit(False, 2, f"Virhe testin keskeytyksessä: {str(e)}")
    
    @pyqtSlot()
    def read_status(self):
        """Lue testin tila taustasäikeessä"""
        try:
            result = self.fortest.read_status()
            self.resultReady.emit(result, 3, "")  # 3 = tilan luku
        except Exception as e:
            self.resultReady.emit(None, 3, f"Virhe testin tilan lukemisessa: {str(e)}")
    
    @pyqtSlot()
    def read_results(self):
        """Lue testin tulokset taustasäikeessä"""
        try:
            result = self.fortest.read_results()
            self.resultReady.emit(result, 4, "")  # 4 = tulosten luku
        except Exception as e:
            self.resultReady.emit(None, 4, f"Virhe testin tulosten lukemisessa: {str(e)}")

class ForTestManager(QObject):
    resultReady = pyqtSignal(object, int, str)  # tulos, operaatiokoodi, virheviesti
    
    def __init__(self, port='/dev/ttyUSB1', baudrate=19200):
        super().__init__()
        
        # Luo säie ja työluokka
        self.thread = QThread()
        self.worker = ForTestWorker(port, baudrate)
        
        # Siirrä työluokka säikeeseen
        self.worker.moveToThread(self.thread)
        
        # Yhdistä signaalit
        self.worker.resultReady.connect(self.handle_result)
        
        # Käynnistä säie
        self.thread.start()
    
    def handle_result(self, result, op_code, error_msg):
        """Välitä tulos eteenpäin"""
        self.resultReady.emit(result, op_code, error_msg)
    
    def start_test(self):
        """Käynnistä testi taustasäikeessä"""
        QMetaObject.invokeMethod(
            self.worker, 
            "start_test",
            Qt.QueuedConnection
        )
    
    def abort_test(self):
        """Keskeytä testi taustasäikeessä"""
        QMetaObject.invokeMethod(
            self.worker, 
            "abort_test",
            Qt.QueuedConnection
        )
    
    def read_status(self):
        """Lue testin tila taustasäikeessä"""
        QMetaObject.invokeMethod(
            self.worker, 
            "read_status",
            Qt.QueuedConnection
        )
    
    def read_results(self):
        """Lue testin tulokset taustasäikeessä"""
        QMetaObject.invokeMethod(
            self.worker, 
            "read_results",
            Qt.QueuedConnection
        )
    
    def cleanup(self):
        """Siivoa resurssit"""
        self.thread.quit()
        self.thread.wait()