import sys
import os
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QLineEdit, QCheckBox, QFileDialog
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor
from PyQt5.QtCore import QTimer, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QDesktopServices
import subprocess
from datetime import datetime
import traceback

class XSSInspectorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.scanning_thread = None
        os.environ['PYTHONUNBUFFERED'] = '1'
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.process_updates)
        self.pending_updates = []

    def process_updates(self):
        if self.pending_updates:
            self.update_results_text("".join(self.pending_updates))
            self.pending_updates.clear()

    def initUI(self):
        self.setWindowTitle('XSS Inspector')
        self.setGeometry(100, 100, 600, 400)
        self.domain_label = QLabel('Domain:', self)
        self.domain_input = QLineEdit(self)
        self.url_list_label = QLabel('URL List File:', self)
        self.url_list_input = QLineEdit(self)
        self.browse_button = QPushButton('Browse', self)
        self.browse_button.clicked.connect(self.browse_for_file)
        self.reports_checkbox = QCheckBox('Generate Reports', self)
        self.threads_checkbox = QCheckBox('Use 50 Threads', self)
        self.include_subdomain_checkbox = QCheckBox('Include Subdomains', self)
        self.deep_crawl_checkbox = QCheckBox('Deep Crawl', self)
        self.results_text = QTextEdit(self)
        self.results_text.setReadOnly(True)
        self.timestamp_format = QTextCharFormat()
        self.timestamp_format.setForeground(QColor("darkGreen"))
        self.timestamp_format.setFontWeight(75)
        self.scan_button = QPushButton('Start Scan', self)
        self.scan_button.clicked.connect(self.start_scan)
        self.stop_button = QPushButton('Stop Scan', self)
        self.stop_button.clicked.connect(self.stop_scan)
        self.stop_button.setEnabled(False)
        self.close_button = QPushButton('Close App', self)
        self.close_button.clicked.connect(self.close_app)
        self.link_label = QLabel('<b>XSS Inspector</b> by Haroon Ahmad Awan | <a href="http://www.cyberzeus.pk">Cyberzeus.pk</a>', self)
        self.link_label.setOpenExternalLinks(True)
        self.link_label.linkActivated.connect(self.open_link)
        layout = QVBoxLayout()
        layout.addWidget(self.domain_label)
        layout.addWidget(self.domain_input)
        layout.addWidget(self.url_list_label)
        layout.addWidget(self.url_list_input)
        layout.addWidget(self.browse_button)
        layout.addWidget(self.reports_checkbox)
        layout.addWidget(self.threads_checkbox)
        layout.addWidget(self.include_subdomain_checkbox)
        layout.addWidget(self.deep_crawl_checkbox)
        layout.addWidget(self.results_text)
        layout.addWidget(self.scan_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.close_button)
        layout.addWidget(self.link_label)
        self.setLayout(layout)
        # Set the initial message
        self.set_text_color("Ready to scan.", QColor("darkGreen"))

    @pyqtSlot()
    def stop_scan(self):
        if self.scanning_thread and self.scanning_thread.is_alive():
            self.scanning_thread.stop_scan()
            self.scan_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    @pyqtSlot()
    def scan_finished(self):
        self.results_text.append("Scan finished.")
        self.scan_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def start_scan(self):
        self.results_text.clear()
        self.scan_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.set_text_color("Initializing...", QColor("darkGreen"))
        domain = self.domain_input.text()
        url_list = self.url_list_input.text()
        if not domain and not url_list:
            self.set_text_color("Please enter a domain or select a URL list file.", QColor("red"))
            self.scan_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            return
        command = ["python3", "xssinspector.py", "--domain", domain, "--list", url_list]

        # Create a thread to run xssinspector.py and capture output
        self.scanning_thread = threading.Thread(target=self.run_scan, args=(command,))
        self.scanning_thread.start()

    def run_scan(self, command):
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in process.stdout:
                self.update_results_text(line)

            process.wait()
            self.scan_finished()
        except Exception as e:
            self.update_results_text(f"Error: {str(e)}")
            self.scan_finished()

    @pyqtSlot(str)
    def update_results_text(self, output):
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
        cursor = self.results_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(timestamp, self.timestamp_format)
        cursor.insertText(output)
        self.results_text.setTextCursor(cursor)
        self.results_text.verticalScrollBar().setValue(self.results_text.verticalScrollBar().maximum())

    def close_app(self):
        if self.scanning_thread and self.scanning_thread.is_alive():
            self.scanning_thread.stop()
        self.close()

    def open_link(self, url):
        QDesktopServices.openUrl(QUrl(url))

    def browse_for_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(self, "Select URL List File", "", "Text Files (*.txt);;All Files (*)", options=options)
        if file_name:
            self.url_list_input.setText(file_name)

    def set_text_color(self, text, color):
        document = self.results_text.document()
        cursor = QTextCursor(document)
        format = QTextCharFormat()
        format.setForeground(color)
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text, format)
        self.results_text.setTextCursor(cursor)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = XSSInspectorApp()
    window.show()
    sys.exit(app.exec_())
