import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from pathlib import Path
import re

APP_NAME = "Mafore Notepad"
VERSION = "1.0.1"
ENGINE = "Ravlik"
COMPANY = "Mafore Entertainment"

class MaforeNotepad:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} — Безымянный")
        self.root.geometry("1000x700")
        self.root.minsize(650, 420)
        self.file_path = None
        self.dirty = False
        self.word_wrap = True
        self.dark_mode = False
        self.font_size = 12
        self.current_font = "Consolas"
        self._build_menu()
        self._build_ui()
        self._bind_shortcuts()
        self._update_status()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_menu(self):
        bar = tk.Menu(self.root)
        file_menu = tk.Menu(bar, tearoff=False)
        file_menu.add_command(label="Новый", accelerator="Ctrl+N", command=self.new_file)
        file_menu.add_command(label="Открыть…", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_command(label="Сохранить", accelerator="Ctrl+S", command=self.save_file)
        file_menu.add_command(label="Сохранить как…", accelerator="Ctrl+Shift+S", command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Экспорт в TXT…", command=self.export_txt)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.on_close)
        bar.add_cascade(label="Файл", menu=file_menu)

        edit_menu = tk.Menu(bar, tearoff=False)
        edit_menu.add_command(label="Отменить", accelerator="Ctrl+Z", command=lambda: self.text.edit_undo())
        edit_menu.add_command(label="Повторить", accelerator="Ctrl+Y", command=lambda: self.text.edit_redo())
        edit_menu.add_separator()
        edit_menu.add_command(label="Найти", accelerator="Ctrl+F", command=self.find_text)
        edit_menu.add_command(label="Заменить", accelerator="Ctrl+H", command=self.replace_text)
        edit_menu.add_command(label="Перейти к строке…", accelerator="Ctrl+G", command=self.goto_line)
        edit_menu.add_separator()
        edit_menu.add_command(label="Выделить всё", accelerator="Ctrl+A", command=lambda: self.text.tag_add("sel", "1.0", "end-1c"))
        bar.add_cascade(label="Правка", menu=edit_menu)

        view_menu = tk.Menu(bar, tearoff=False)
        view_menu.add_command(label="Увеличить шрифт", accelerator="Ctrl++", command=lambda: self.change_font_size(1))
        view_menu.add_command(label="Уменьшить шрифт", accelerator="Ctrl+-", command=lambda: self.change_font_size(-1))
        view_menu.add_command(label="Переключить тему", command=self.toggle_theme)
        view_menu.add_command(label="Перенос строк", command=self.toggle_wrap)
        bar.add_cascade(label="Вид", menu=view_menu)

        tools_menu = tk.Menu(bar, tearoff=False)
        tools_menu.add_command(label="Вставить дату и время", command=self.insert_datetime)
        tools_menu.add_command(label="Статистика текста", command=self.statistics)
        tools_menu.add_command(label="Подсветить поиск", command=self.find_text)
        bar.add_cascade(label="Инструменты", menu=tools_menu)

        help_menu = tk.Menu(bar, tearoff=False)
        help_menu.add_command(label="О программе", command=self.about)
        bar.add_cascade(label="Справка", menu=help_menu)
        self.root.config(menu=bar)

    def _build_ui(self):
        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True)
        self.text = tk.Text(frame, wrap="word", undo=True, maxundo=-1,
                            font=(self.current_font, self.font_size), padx=12, pady=10,
                            relief="flat", borderwidth=0)
        yscroll = tk.Scrollbar(frame, command=self.text.yview)
        xscroll = tk.Scrollbar(frame, orient="horizontal", command=self.text.xview)
        self.text.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        yscroll.pack(side="right", fill="y")
        xscroll.pack(side="bottom", fill="x")
        self.text.pack(side="left", fill="both", expand=True)
        self.text.bind("<<Modified>>", self._on_modified)
        self.status = tk.Label(self.root, text="", anchor="w", padx=8, pady=4, relief="sunken")
        self.status.pack(side="bottom", fill="x")
        self._apply_theme()

    def _bind_shortcuts(self):
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-Shift-S>", lambda e: self.save_as())
        self.root.bind("<Control-f>", lambda e: self.find_text())
        self.root.bind("<Control-h>", lambda e: self.replace_text())
        self.root.bind("<Control-g>", lambda e: self.goto_line())
        self.root.bind("<Control-plus>", lambda e: self.change_font_size(1))
        self.root.bind("<Control-equal>", lambda e: self.change_font_size(1))
        self.root.bind("<Control-minus>", lambda e: self.change_font_size(-1))
        self.root.bind("<Control-a>", lambda e: self.text.tag_add("sel", "1.0", "end-1c"))
        self.root.bind("<F1>", lambda e: self.about())

    def _on_modified(self, _event=None):
        if self.text.edit_modified():
            self.dirty = True
            self.text.edit_modified(False)
            self._update_title()
            self._update_status()

    def _update_title(self):
        name = self.file_path.name if self.file_path else "Безымянный"
        marker = "*" if self.dirty else ""
        self.root.title(f"{marker}{name} — {APP_NAME}")

    def _update_status(self):
        content = self.text.get("1.0", "end-1c")
        line, col = map(int, self.text.index("insert").split("."))
        words = len(re.findall(r"\b[\w'-]+\b", content, flags=re.UNICODE))
        self.status.config(text=f" Строка: {line}   Столбец: {col+1}   Слов: {words}   Символов: {len(content)}   {'Тёмная тема' if self.dark_mode else 'Светлая тема'}")
        self.root.after(250, self._refresh_status_once)

    def _refresh_status_once(self):
        if self.root.winfo_exists():
            content = self.text.get("1.0", "end-1c")
            line, col = map(int, self.text.index("insert").split("."))
            words = len(re.findall(r"\b[\w'-]+\b", content, flags=re.UNICODE))
            self.status.config(text=f" Строка: {line}   Столбец: {col+1}   Слов: {words}   Символов: {len(content)}   {'Тёмная тема' if self.dark_mode else 'Светлая тема'}")

    def ask_save_changes(self):
        if not self.dirty:
            return True
        answer = messagebox.askyesnocancel("Несохранённые изменения", "Сохранить изменения перед продолжением?")
        if answer is None:
            return False
        if answer:
            return self.save_file()
        return True

    def new_file(self):
        if not self.ask_save_changes(): return
        self.text.delete("1.0", "end")
        self.file_path = None
        self.dirty = False
        self._update_title()
        self.text.edit_reset()

    def open_file(self):
        if not self.ask_save_changes(): return
        path = filedialog.askopenfilename(title="Открыть файл",
            filetypes=[("Текстовые файлы", "*.txt *.md *.py *.json *.html *.css *.js *.log"), ("Все файлы", "*.*")])
        if not path: return
        try:
            content = Path(path).read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            try: content = Path(path).read_text(encoding="cp1251")
            except Exception as exc:
                messagebox.showerror("Ошибка открытия", str(exc)); return
        except Exception as exc:
            messagebox.showerror("Ошибка открытия", str(exc)); return
        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self.file_path = Path(path)
        self.dirty = False
        self.text.edit_modified(False)
        self.text.edit_reset()
        self._update_title()
        self._update_status()

    def save_file(self):
        if not self.file_path:
            return self.save_as()
        try:
            self.file_path.write_text(self.text.get("1.0", "end-1c"), encoding="utf-8")
            self.dirty = False
            self._update_title()
            self._update_status()
            return True
        except Exception as exc:
            messagebox.showerror("Ошибка сохранения", str(exc))
            return False

    def save_as(self):
        path = filedialog.asksaveasfilename(title="Сохранить файл", defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt"), ("Markdown", "*.md"), ("Все файлы", "*.*")])
        if not path: return False
        self.file_path = Path(path)
        return self.save_file()

    def export_txt(self):
        path = filedialog.asksaveasfilename(title="Экспортировать текст", defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt")])
        if not path: return
        try:
            Path(path).write_text(self.text.get("1.0", "end-1c"), encoding="utf-8")
            messagebox.showinfo("Экспорт", "Текст успешно экспортирован.")
        except Exception as exc:
            messagebox.showerror("Ошибка экспорта", str(exc))

    def find_text(self):
        query = simpledialog.askstring("Найти", "Введите текст для поиска:")
        if not query: return
        self.text.tag_remove("search_hit", "1.0", "end")
        start = "1.0"
        count = 0
        while True:
            pos = self.text.search(query, start, stopindex="end", nocase=True)
            if not pos: break
            end = f"{pos}+{len(query)}c"
            self.text.tag_add("search_hit", pos, end)
            start = end
            count += 1
        self.text.tag_config("search_hit", background="#ffe66d", foreground="#202020")
        first = self.text.tag_ranges("search_hit")
        if first:
            self.text.mark_set("insert", first[0])
            self.text.see(first[0])
        messagebox.showinfo("Поиск", f"Найдено совпадений: {count}")

    def replace_text(self):
        old = simpledialog.askstring("Заменить", "Что найти?")
        if old is None or old == "": return
        new = simpledialog.askstring("Заменить", "На что заменить?")
        if new is None: return
        content = self.text.get("1.0", "end-1c")
        count = content.count(old)
        self.text.delete("1.0", "end")
        self.text.insert("1.0", content.replace(old, new))
        messagebox.showinfo("Замена", f"Заменено вхождений: {count}")

    def goto_line(self):
        line = simpledialog.askinteger("Перейти к строке", "Номер строки:", minvalue=1)
        if line:
            self.text.mark_set("insert", f"{line}.0")
            self.text.see("insert")
            self.text.focus_set()

    def change_font_size(self, delta):
        self.font_size = max(8, min(32, self.font_size + delta))
        self.text.configure(font=(self.current_font, self.font_size))

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self._apply_theme()
        self._update_status()

    def _apply_theme(self):
        if self.dark_mode:
            bg, fg, insert, status_bg = "#1e1e1e", "#e8e8e8", "#ffffff", "#2b2b2b"
        else:
            bg, fg, insert, status_bg = "#ffffff", "#202020", "#111111", "#eeeeee"
        self.text.configure(background=bg, foreground=fg, insertbackground=insert,
                            selectbackground="#4169a1", selectforeground="#ffffff")
        self.status.configure(background=status_bg, foreground=fg)

    def toggle_wrap(self):
        self.word_wrap = not self.word_wrap
        self.text.configure(wrap="word" if self.word_wrap else "none")

    def insert_datetime(self):
        import datetime
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.text.insert("insert", stamp)
        self.text.focus_set()

    def statistics(self):
        content = self.text.get("1.0", "end-1c")
        words = len(re.findall(r"\b[\w'-]+\b", content, flags=re.UNICODE))
        lines = content.count("\n") + 1 if content else 0
        messagebox.showinfo("Статистика текста",
            f"Символов: {len(content)}\nСлов: {words}\nСтрок: {lines}\nАбзацев: {len([p for p in content.splitlines() if p.strip()])}")

    def about(self):
        messagebox.showinfo("О программе",
            f"{APP_NAME}\n\nСоздана компанией {COMPANY}\nВерсия {VERSION}\nСоздана на движке {ENGINE}\n\nДополнительные функции: поиск и замена, статистика текста,\nтёмная тема, масштабирование шрифта и переход к строке.")

    def on_close(self):
        if self.ask_save_changes():
            self.root.destroy()

def main():
    root = tk.Tk()
    try:
        root.iconname(APP_NAME)
    except Exception:
        pass
    MaforeNotepad(root)
    root.mainloop()

if __name__ == "__main__":
    main()
