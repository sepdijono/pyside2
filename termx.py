from PySide2 import QtCore, QtGui
from PySide2.QtCore import QEvent, Qt, QSize
from PySide2.QtGui import QTextCursor, QMouseEvent, QKeyEvent, QFont, QCursor
from PySide2.QtWidgets import QTextEdit, QApplication
from abc import abstractmethod, ABC
import os
import platform
import getpass

dog = \
    """
              .--~~,__
:-....,-------`~~'._.'
 `-,,,  ,_      ;'~U'
  _,-' ,'`-__; '--.
 (_/'~~      ''''(;
        Who let the dogs out

"""

# ASCII Art : https://www.asciiart.eu/animals/dogs

# A Simple Terminal Emulator Like QTextEdit
# Author  : Yusep Budijono Al Yoyon (pyy)
# Mail    : sepdijono@gmail.com
#
# TermX   : is class derived from QTextEdit implement input text terminal emulator like
# Usage   : implement method 'execute_cmd(self, cmd)' by returning the result from subproses or ssh client like paramiko
# Example : please refers to main program sample written below


LINUX_DEFAULT_PROMPT = "~$"
WINDOWS_DEFAULT_PROMPT = "$>"
DEFAULT_EXECUTE_CMD_TXT = "Please implement this abstract method: 'execute_cmd'\n"
DEFAULT_FONT_SIZE = 10
DEFAULT_FONT_NAME = "Terminal"


class TermX(QTextEdit):
    def __init__(self):
        super(TermX, self).__init__()
        self.cursor = self.textCursor()
        self.cursor.insertText(dog)
        self.old_cursor = self.textCursor()
        self.pwd = ""
        self.pwd_wo_home = ""
        self.prompt = ""
        self.update_pwd()
        self.set_widget()
        self.cmd_suggestion = []
        self.curr_suggestion = 0
        self.cmd_history = []
        self.curr_history = 0
        self.selecting_text = False
        self.selectionChanged.connect(self.handle_selection_changed)

    @abstractmethod
    def execute_cmd(self, cmd):
        pass

    @abstractmethod
    def update_pwd(self):
        pass

    def set_widget(self):
        font = QFont(DEFAULT_FONT_NAME, DEFAULT_FONT_SIZE, QFont.Normal)
        self.setFont(font)
        self.cursor.insertText(f'{self.prompt} ')
        self.cursor.movePosition(QTextCursor.End)
        self.setTextCursor(self.cursor)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    @abstractmethod
    def pop_a_history(self):
        pass

    @abstractmethod
    def pop_a_suggestion(self, cmd):
        pass

    @abstractmethod
    def push_suggestion(self):
        pass

    def keyPressEvent(self, event: QKeyEvent) -> None:

        if event.type() == QEvent.KeyPress:
            self.push_suggestion()
            if event.key() == QtCore.Qt.Key_Tab and self.hasFocus():
                self.setReadOnly(True)

            if event.key() == Qt.Key_L and event.modifiers() == Qt.ControlModifier:
                self.clear()
                self.cursor.insertText(dog)
                self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
                self.cursor.insertText(f'{self.prompt} ')

            if event.key() == QtCore.Qt.Key_Up:
                if self.curr_history > 0:
                    self.pop_a_history()
                    self.curr_history -= 1
                return

            if event.key() == QtCore.Qt.Key_Down:
                if self.curr_history < len(self.cmd_history):
                    self.pop_a_history()
                    self.curr_history += 1
                return

            if event.key() in (QtCore.Qt.Key_Left, QtCore.Qt.Key_Home, QtCore.Qt.Key_End):
                return

            if self.cursor.positionInBlock() < len(self.prompt) + 2:
                if self.hasFocus():
                    if event.key() == QtCore.Qt.Key_Backspace:
                        return

        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        count = len(self.toPlainText().split("\n"))
        lines = self.toPlainText().split("\n")
        if event.type() == QEvent.KeyRelease:
            if event.key() == QtCore.Qt.Key_Tab and self.hasFocus():
                if self.curr_suggestion < len(self.cmd_suggestion):
                    self.curr_suggestion += 1
                elif self.curr_suggestion >= len(self.cmd_suggestion):
                    self.curr_suggestion = 1
                las_ln = lines[count - 1]
                for las_ln_x in self.cmd_suggestion:
                    las_ln = las_ln.replace(las_ln_x, "")
                self.setReadOnly(False)
                self.pop_a_suggestion(las_ln.replace(self.prompt, ""))
                return
            elif event.key() == QtCore.Qt.Key_Return and self.hasFocus():
                i = 1
                cmd = ""
                for l in self.toPlainText().split("\n"):
                    if i == count - 1:
                        cmd = l.strip().replace(self.prompt, "")
                        break
                    i += 1
                lines = None
                if cmd.strip() != 'clear':
                    lines = self.execute_cmd(cmd)
                else:
                    self.clear()
                    self.cursor.insertText(dog)
                    self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
                    # self.cursor.insertText(f'{self.prompt} ')

                self.cmd_history.append(cmd)
                self.curr_history += 1
                if (lines is not DEFAULT_EXECUTE_CMD_TXT) and (lines is not None):
                    for line in lines:
                        if type(line) != int:
                            self.cursor.insertText(f'{line}\n')

                self.cursor.insertText(f'{self.prompt} ')
                self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
        super().keyPressEvent(event)

    def handle_selection_changed(self):
        text = self.textCursor().selectedText()
        if len(text) != 0:
            self.selecting_text = True
        else:
            self.selecting_text = False

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == QtCore.Qt.LeftButton:
                if not len(self.textCursor().selectedText()) > 0:
                    self.old_cursor = self.textCursor()
                    super().mousePressEvent(event)
                else:
                    self.setTextCursor(self.old_cursor)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.type() == QEvent.MouseButtonRelease:
            if event.button() == QtCore.Qt.LeftButton:
                if len(self.textCursor().selectedText()) == 0:
                    self.setTextCursor(self.old_cursor)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        return


if __name__ == "__main__":
    # TermX Example
    import subprocess
    import sys


    def get_host():
        if platform.system() == "Windows":
            s = platform.uname().node
        else:
            s = os.uname()[1]
        return s

    # TermX Example Usage Code
    class TesterTerminal(TermX):
        # BUG HERE!
        def push_suggestion(self):
            self.cmd_suggestion = []
            if platform.system() == "Windows":
                cmd = 'dir /ad'
            else:
                cmd = 'ls -d */'
            lines = str(self.execute_cmd(cmd)[1]).split('\n')
            if (lines is not DEFAULT_EXECUTE_CMD_TXT) and (lines is not None):
                for line in lines:
                    # print(line)
                    if type(line) != int:
                        l_txt = line.replace("/", "").strip()
                        l_txt = l_txt.replace(" ", "\ ")
                        self.cmd_suggestion.append(l_txt)

        def pop_a_suggestion(self, cmd):
            cmd_len = len(cmd)
            self.setFocus()
            self.moveCursor(QTextCursor.StartOfBlock, QTextCursor.MoveAnchor)
            self.moveCursor(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
            self.textCursor().removeSelectedText()
            self.textCursor().deletePreviousChar()
            self.cursor.insertText(
                f'\n{self.prompt} {cmd.strip()} {self.cmd_suggestion[self.curr_suggestion - 1]}'.rstrip())
            self.moveCursor(QTextCursor.StartOfBlock, QTextCursor.MoveAnchor)
            for i in range(1, cmd_len):
                self.moveCursor(QTextCursor.NextCharacter, QTextCursor.MoveAnchor)
            self.moveCursor(QTextCursor.EndOfBlock, QTextCursor.MoveAnchor)

        def pop_a_history(self):
            self.setFocus()
            self.moveCursor(QTextCursor.StartOfBlock, QTextCursor.MoveAnchor)
            self.moveCursor(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
            self.textCursor().removeSelectedText()
            self.textCursor().deletePreviousChar()
            self.cursor.insertText(f'\n{self.prompt}{self.cmd_history[self.curr_history - 1]}')
            self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

        def update_pwd(self):
            self.pwd = os.getcwd()
            self.pwd_wo_home = self.pwd.replace(os.path.expanduser('~'), "")
            if platform.system() == "Windows":
                self.prompt = f'{getpass.getuser()}@{get_host()}:{WINDOWS_DEFAULT_PROMPT}' \
                              f' ~{self.pwd_wo_home}/'.replace("//", "/")
            else:
                self.prompt = f'{getpass.getuser()}@{get_host()}:{LINUX_DEFAULT_PROMPT}' \
                              f' ~{self.pwd_wo_home}/'.replace("//", "/")

        def execute_cmd(self, cmd):
            cmds = cmd.split()
            sp = subprocess.getstatusoutput(cmd)
            if len(cmds) > 1:
                if (sp[0] == 0) and (cmds[0] == 'cd'):
                    self.pwd = f'{self.pwd}/{cmds[1]}'
                    os.chdir(self.pwd)
            elif len(cmds) == 1:
                if (sp[0] == 0) and (cmds[0] == 'cd'):
                    os.chdir("/")
                    self.pwd = "/"
            self.update_pwd()
            return sp


    app = QApplication()
    w = TesterTerminal()
    w.show()
    w.setMinimumSize(QSize(800, 600))
    screen = QtGui.QGuiApplication.screenAt(QCursor().pos())
    fg = w.frameGeometry()
    fg.moveCenter(screen.geometry().center())
    w.move(fg.topLeft())
    sys.exit(app.exec_())
