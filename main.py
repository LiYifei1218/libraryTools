import tkinter as tk
from tkinter import messagebox, scrolledtext
import nlc_isbn
from formatting import format_metadata
import pyperclip
import webbrowser


def search_isbn():
    isbn = entry_isbn.get()
    log_message("检索 ISBN: " + isbn)
    update_status("正在检索...")
    text_result.delete('1.0', tk.END)
    root.update_idletasks()

    try:
        metadata = nlc_isbn.isbn2meta(isbn)
        if metadata:
            formatted_result = format_metadata(metadata)
            text_result.insert(tk.END, formatted_result)
            update_status("检索完成")
        else:
            text_result.insert(tk.END, "无法找到元数据。")
            update_status("未找到数据")
    except Exception as e:
        messagebox.showerror("错误", str(e))
        update_status("检索出错")


def copy_to_clipboard():
    text = text_result.get("1.0", tk.END)
    pyperclip.copy(text)
    log_message("信息已复制到剪贴板。")


def open_github():
    webbrowser.open("https://github.com/Hellohistory/EbookDataGeter")


def log_message(message):
    text_log.insert(tk.END, message + "\n")


def update_status(message):
    status_label.config(text=message)


# 创建主窗口
root = tk.Tk()
root.title("EbookDataGeter")
root.geometry("600x400")

# 设置窗口图标
root.iconbitmap('logo.ico')

# 使用 Grid 布局
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)

# 状态栏
status_label = tk.Label(root, text="就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W)
status_label.grid(row=2, column=0, sticky="ew")

# 创建并放置控件
frame = tk.Frame(root)
frame.grid(row=0, column=0, sticky="ew")

label_isbn = tk.Label(frame, text="请输入ISBN号码：")
label_isbn.pack(side=tk.LEFT)

entry_isbn = tk.Entry(frame)
entry_isbn.pack(side=tk.LEFT)

button_search = tk.Button(frame, text="查询", command=search_isbn)
button_search.pack(side=tk.LEFT)

button_copy = tk.Button(frame, text="复制信息", command=copy_to_clipboard)
button_copy.pack(side=tk.LEFT)

text_result = scrolledtext.ScrolledText(root, height=10)
text_result.grid(row=1, column=0, sticky="nsew")

text_log = scrolledtext.ScrolledText(root, height=5)
text_log.grid(row=3, column=0, sticky="nsew")

# 添加超链接按钮到右下角
github_link = tk.Label(root, text="Github地址", fg="blue", cursor="hand2")
github_link.grid(row=4, column=0, sticky="se")
github_link.bind("<Button-1>", lambda e: open_github())

root.mainloop()
