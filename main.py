import tkinter as tk
import re
from tkinter import messagebox, scrolledtext, filedialog
import threading
import csv
import os
import pyperclip
import webbrowser

import nlc_isbn
from formatting import format_metadata
import bookmarkget

# 线程锁，用于避免多线程同时写CSV产生冲突
csv_lock = threading.Lock()

def store_metadata_to_csv(metadata, csv_file="metadata.csv"):
    """
    将元数据追加存储到CSV文件中。
    如果文件不存在则自动创建并写入表头。
    
    CSV列顺序：书名, ISBN, 作者, 标签, 出版社, 出版时间
    """
    fieldnames = ["书名", "ISBN", "作者", "标签", "出版社", "出版时间"]
    
    # 检查文件是否已经存在
    file_exists = os.path.isfile(csv_file)
    
    # 提取metadata中的数据
    # 根据你的实际metadata结构来获取；以下是一个示例
    title = metadata.get("title", "")
    isbn = metadata.get("isbn", "")
    
    # 作者（假设metadata["authors"]是列表）
    # 如果不是列表，请根据实际情况修改
    authors = metadata.get("authors", [])
    if isinstance(authors, list):
        authors_str = ";".join(authors)
    else:
        authors_str = authors  # 如果已经是字符串，就直接用
    
    # 标签（假设metadata["tags"]是列表）
    tags = metadata.get("tags", [])
    if isinstance(tags, list):
        tags_str = ";".join(tags)
    else:
        tags_str = tags  # 如果已经是字符串，就直接用

    publisher = metadata.get("publisher", "")
    pubdate = metadata.get("pubdate", "")
    
    with csv_lock, open(csv_file, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # 如果文件还不存在，则先写入表头
        if not file_exists:
            writer.writeheader()
        
        # 组装要写入的数据
        row_data = {
            "书名": title,
            "ISBN": isbn,
            "作者": authors_str,
            "标签": tags_str,
            "出版社": publisher,
            "出版时间": pubdate
        }
        
        
        writer.writerow(row_data)

def background_search(isbn):
    """
    后台线程执行的函数：
    1. 获取书签信息
    2. 获取元数据
    3. 更新界面、写入CSV
    """
    try:
        # 获取书签信息
        bookmarks_info = bookmarkget.get_book_details(isbn)
        # 更新到 text_bookmarks（注意：Tkinter要在主线程里更新UI，所以用root.after）
        root.after(0, lambda: text_bookmarks.insert(tk.END, bookmarks_info + "\n"))
    except Exception as e:
        root.after(0, lambda: messagebox.showerror("错误", str(e)))

    # 然后获取元数据
    try:
        metadata = nlc_isbn.isbn2meta(isbn, update_status)
        if metadata:
            # 格式化后显示到 text_result
            formatted_result = format_metadata(metadata)
            root.after(0, lambda: (
                text_result.insert(tk.END, formatted_result + "\n"),
                update_status("检索完成")
            ))
            # 写入CSV
            store_metadata_to_csv(metadata)
            
        else:
            root.after(0, lambda: (
                text_result.insert(tk.END, "无法找到元数据。\n"),
                update_status("未找到数据")
            ))
    except Exception as e:
        root.after(0, lambda: (
            messagebox.showerror("错误", str(e)),
            update_status("检索出错")
        ))

def search_isbn(event=None):
    """
    从输入框中获取ISBN后，启动后台线程去查询书签和元数据
    """
    isbn = entry_isbn.get()
    log_message("检索 ISBN: " + isbn)
    update_status("正在检索...")

    # 在查询前清空结果区（可选）
    text_result.delete('1.0', tk.END)
    text_bookmarks.delete('1.0', tk.END)
    root.update_idletasks()

    # 启动一个线程来处理查询，避免阻塞主线程
    threading.Thread(target=lambda: background_search(isbn), daemon=True).start()

def copy_to_clipboard():
    text = text_result.get("1.0", tk.END)
    pyperclip.copy(text)
    log_message("信息已复制到剪贴板。")

def copy_bookmarks_to_clipboard():
    bookmarks_text = text_bookmarks.get("1.0", tk.END)
    pyperclip.copy(bookmarks_text)
    log_message("书签信息已复制到剪贴板。")

def save_bookmarks_to_file():
    bookmarks_text = text_bookmarks.get("1.0", tk.END)
    file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                             filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
    if file_path:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(bookmarks_text)
        log_message("书签信息已保存到文件：" + file_path)

def open_github():
    webbrowser.open("https://github.com/Hellohistory/EbookDataTools")

def open_gitee():
    webbrowser.open("https://github.com/Hellohistory/EbookDataTools")

def log_message(message):
    text_log.insert(tk.END, message + "\n")

def update_status(message):
    status_label.config(text=message)

def filter_input(event):
    """只允许输入数字内容。"""
    input_text = entry_isbn.get()
    filtered_text = re.sub(r'[^0-9]', '', input_text)
    entry_isbn.delete(0, tk.END)
    entry_isbn.insert(0, filtered_text)

# ========== GUI 配置 ==========
FONT_NORMAL = ("Arial", 10)
FONT_BOLD = ("Arial", 10, "bold")
BACKGROUND_COLOR = "#F0F0F0"
BUTTON_COLOR = "#E0E0E0"

root = tk.Tk()
root.title("EbookDataGeter")
root.geometry("900x600")
root.iconbitmap('logo.ico')  # 如果没有ico文件可注释掉本行
root.configure(bg=BACKGROUND_COLOR)

root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(1, weight=1)

# 状态栏
status_label = tk.Label(root, text="就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W, bg=BACKGROUND_COLOR, font=FONT_NORMAL)
status_label.grid(row=2, column=0, columnspan=2, sticky="ew")

# 输入区
frame = tk.Frame(root, bg=BACKGROUND_COLOR)
frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

label_isbn = tk.Label(frame, text="请输入ISBN号码：", font=FONT_NORMAL, bg=BACKGROUND_COLOR)
label_isbn.pack(side=tk.LEFT)

# ISBN输入框
entry_isbn = tk.Entry(frame, font=FONT_NORMAL)
entry_isbn.pack(side=tk.LEFT, padx=5)

# 输入过滤（只允许数字）
entry_isbn.bind("<KeyRelease>", filter_input)

# 回车查询
entry_isbn.bind("<Return>", search_isbn)

button_search = tk.Button(frame, text="查询", command=search_isbn, bg=BUTTON_COLOR, font=FONT_BOLD)
button_search.pack(side=tk.LEFT, padx=5)

button_copy = tk.Button(frame, text="复制信息", command=copy_to_clipboard, bg=BUTTON_COLOR, font=FONT_BOLD)
button_copy.pack(side=tk.LEFT, padx=5)

button_copy_bookmarks = tk.Button(frame, text="复制书签信息", command=copy_bookmarks_to_clipboard, bg=BUTTON_COLOR, font=FONT_BOLD)
button_copy_bookmarks.pack(side=tk.LEFT, padx=5)

button_save_bookmarks = tk.Button(frame, text="保存书签信息", command=save_bookmarks_to_file, bg=BUTTON_COLOR, font=FONT_BOLD)
button_save_bookmarks.pack(side=tk.LEFT, padx=5)

# 结果区（元数据）
text_result = scrolledtext.ScrolledText(root, height=10, font=FONT_NORMAL)
text_result.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

# 书签信息
text_bookmarks = scrolledtext.ScrolledText(root, height=10, font=FONT_NORMAL)
text_bookmarks.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)

# 日志信息
text_log = scrolledtext.ScrolledText(root, height=5, font=FONT_NORMAL)
text_log.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)

# 底部链接
link_frame = tk.Frame(root, bg=BACKGROUND_COLOR)
link_frame.grid(row=4, column=1, sticky="se", padx=10, pady=5)

gitee_link = tk.Label(link_frame, text="Gitee地址", fg="blue", cursor="hand1", bg=BACKGROUND_COLOR, font=FONT_NORMAL)
gitee_link.pack(side=tk.RIGHT, padx=(2, 0))
gitee_link.bind("<Button-1>", lambda e: open_gitee())

github_link = tk.Label(link_frame, text="Github地址", fg="blue", cursor="hand2", bg=BACKGROUND_COLOR, font=FONT_NORMAL)
github_link.pack(side=tk.RIGHT, padx=(2, 2))
github_link.bind("<Button-1>", lambda e: open_github())

root.mainloop()
