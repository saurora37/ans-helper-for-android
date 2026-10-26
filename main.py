# -*- coding: utf-8 -*-
"""
学生手册题库 - 安卓离线查题助手
Kivy 重写版：复用本地 SQLite 题库，纯离线运行。
功能：关键词搜索、按题库分类筛选、点击卡片展开/收起答案。
本地调试：python main.py
打包 APK：见 buildozer.spec 与 README.md
"""
import os
import sqlite3
import shutil

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

DB_NAME = "questions.db"


def writable_dir():
    """返回安卓/桌面都可用的可写目录"""
    # 安卓：用户私有目录
    for cand in ("/sdcard/StudentHandbook",):
        if os.path.exists("/sdcard"):
            return cand
    # 桌面：脚本同目录
    return os.path.dirname(os.path.abspath(__file__))


def get_db():
    """优先用可写目录里的库；首次运行从打包资源复制一份"""
    os.makedirs(writable_dir(), exist_ok=True)
    writable = os.path.join(writable_dir(), DB_NAME)
    bundled = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)
    if not os.path.exists(writable) and os.path.exists(bundled):
        shutil.copy(bundled, writable)
    target = writable if os.path.exists(writable) else bundled
    conn = sqlite3.connect(target)
    conn.execute('''CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL,
        answer TEXT NOT NULL,
        category TEXT NOT NULL DEFAULT '默认题库',
        timestamp DATETIME NOT NULL)''')
    return conn


class ResultCard(BoxLayout):
    """单条结果卡片：题目 + 答案（点击展开/收起）"""
    def __init__(self, row, **kw):
        super().__init__(orientation="vertical", size_hint_y=None,
                         spacing=dp(6), padding=[dp(10), dp(8)], **kw)
        # row: (id, content, answer, category, timestamp)
        self.content_text = row[1]
        self.answer_text = row[2]
        self.category = row[3]
        self.revealed = False
        self.answer_label = Label(text="", size_hint_y=None, halign="left",
                                  valign="top", color=(0.1, 0.5, 0.1, 1),
                                  markup=True)
        self.title_btn = Button(text=f"[{self.category}]\n{self.content_text}",
                                size_hint_y=None, halign="left", valign="top",
                                background_normal="", background_color=(0.93, 0.95, 1.0, 1),
                                color=(0.1, 0.1, 0.1, 1))
        self.title_btn.bind(on_release=self.toggle)
        self.add_widget(self.title_btn)
        self.add_widget(self.answer_label)
        self.bind(minimum_height=self.setter("height"))

    def toggle(self, *_):
        self.revealed = not self.revealed
        if self.revealed:
            self.answer_label.text = f"[b]答案：[/b]{self.answer_text}"
        else:
            self.answer_label.text = ""
        # 自适应高度
        self.answer_label.texture_update()
        self.answer_label.height = self.answer_label.texture_size[1]
        self.title_btn.texture_update()
        self.title_btn.height = max(dp(44), self.title_btn.texture_size[1] + dp(20))


class MainScreen(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation="vertical", spacing=dp(8),
                         padding=[dp(10), dp(10), dp(10), dp(14)], **kw)
        self.conn = get_db()

        # 顶栏：标题
        self.add_widget(Label(text="Ans Helper · 离线查题", size_hint_y=None,
                              height=dp(36), bold=True, font_size="16sp"))

        # 搜索行
        search_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        self.search_input = TextInput(hint_text="输入关键词搜题（可点搜索、留空看全部）",
                                      multiline=False, size_hint_x=0.7)
        self.search_input.bind(on_text_validate=self.do_search)
        search_btn = Button(text="搜索", size_hint_x=0.3)
        search_btn.bind(on_release=self.do_search)
        search_row.add_widget(self.search_input)
        search_row.add_widget(search_btn)
        self.add_widget(search_row)

        # 分类筛选行
        cat_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        self.cat_spinner = Spinner(text="全部分类", values=self.categories(),
                                   size_hint_x=0.6)
        self.cat_spinner.bind(on_text=self.do_search)
        show_all_btn = Button(text="显示全部", size_hint_x=0.4)
        show_all_btn.bind(on_release=self.show_all)
        cat_row.add_widget(self.cat_spinner)
        cat_row.add_widget(show_all_btn)
        self.add_widget(cat_row)

        # 结果滚动区
        self.scroll = ScrollView()
        self.result_box = BoxLayout(orientation="vertical", size_hint_y=None,
                                    spacing=dp(8))
        self.result_box.bind(minimum_height=self.result_box.setter("height"))
        self.scroll.add_widget(self.result_box)
        self.add_widget(self.scroll)

        # 初始载入全部
        self.show_all()

    def categories(self):
        rows = self.conn.execute(
            "SELECT DISTINCT category FROM questions ORDER BY category").fetchall()
        return ["全部分类"] + [r[0] for r in rows]

    def _render(self, rows):
        self.result_box.clear_widgets()
        if not rows:
            self.result_box.add_widget(
                Label(text="没有找到匹配的题目", size_hint_y=None, height=dp(60)))
            return
        for r in rows:
            self.result_box.add_widget(ResultCard(r))

    def _query(self, keyword):
        cat = self.cat_spinner.text
        where, params = [], []
        if keyword:
            where.append("(content LIKE ? OR answer LIKE ?)")
            params += [f"%{keyword}%", f"%{keyword}%"]
        if cat and cat != "全部分类":
            where.append("category = ?")
            params.append(cat)
        sql = "SELECT id, content, answer, category, timestamp FROM questions"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY id"
        return self.conn.execute(sql, params).fetchall()

    def do_search(self, *_):
        kw = self.search_input.text.strip()
        self._render(self._query(kw))

    def show_all(self, *_):
        self.search_input.text = ""
        self.cat_spinner.text = "全部分类"
        self._render(self._query(""))


class HandbookApp(App):
    def build(self):
        self.title = "Ans Helper"
        # 竖屏手机窗口
        try:
            Window.size = (380, 720)
        except Exception:
            pass
        return MainScreen()


if __name__ == "__main__":
    HandbookApp().run()
