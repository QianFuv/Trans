import sys
import tkinter as tk
from tkinter import ttk, messagebox, Menu
import json
import configparser
import os
import re

script_dir = os.path.dirname(os.path.realpath(sys.executable))
CONFIG_FILE = os.path.join(script_dir, 'gui_config.ini')
file_path = os.path.join(script_dir, 'dict.json')

# 加载词典数据
def load_dictionary(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return {item['origin_name']: item for item in json.load(file)}

# 保存窗口位置和大小
def save_window_position(window):
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
    config['Window'] = {
        'x': str(window.winfo_x()), 
        'y': str(window.winfo_y()),
        'width': str(window.winfo_width()), 
        'height': str(window.winfo_height())
    }
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

# 恢复窗口位置和大小
def restore_window_position(window):
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    if 'Window' in config:
        window.geometry(f"{config['Window']['width']}x{config['Window']['height']}+{config['Window']['x']}+{config['Window']['y']}")

def levenshtein_distance(s1, s2):
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2 + 1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]

# 搜索功能
def search(event=None):
    query = entry.get()
    exact_matches = []
    partial_matches = []

    # 对查询词进行分词并构建正则表达式模式
    query_words = query.lower().split()
    pattern = '.*?'.join(query_words)
    regex = re.compile(pattern)

    # 遍历词典，区分完全匹配和部分匹配
    for word, details in dictionary.items():
        # 检查词典键是否匹配正则表达式模式
        if regex.fullmatch(word.lower()):
            exact_matches.append((word, details))
        elif regex.search(word.lower()):
            # 计算编辑距离
            distance = levenshtein_distance(query, word)
            partial_matches.append((word, details, distance))

    # 对部分匹配的结果按编辑距离进行排序
    partial_matches.sort(key=lambda x: x[2])

    # 清空treeview的当前内容
    for row in tree.get_children():
        tree.delete(row)

    # 插入完全匹配的结果
    for word, meaning in exact_matches:
        tree.insert('', 'end', values=(word, meaning['trans_name']))

    # 插入部分匹配的结果
    for word, meaning, _ in partial_matches:
        tree.insert('', 'end', values=(word, meaning['trans_name']))

# 复制选中的内容
def copy_selection(event, root):
    selected_item = tree.identify_row(event.y)
    if selected_item:
        # 只获取Meaning列的值
        item_text = tree.item(selected_item, 'values')[1]
        root.clipboard_clear()
        root.clipboard_append(item_text)
        messagebox.showinfo("复制成功", "选中的释义已复制到剪贴板。")

def paste_into_entry(event, root):
    # 获取鼠标指针在输入框中的位置
    cursor_position = entry.index(tk.INSERT)
    # 从剪贴板粘贴内容到输入栏，插入到鼠标指针位置
    clipboard_content = root.clipboard_get()
    entry.insert(cursor_position, clipboard_content)

def clear_entry(event, root):
    # 清空输入栏
    entry.delete(0, tk.END)

def create_context_menu(event, root):
    # 创建上下文菜单
    menu = Menu(tearoff=0)
    menu.add_command(label="粘贴", command=lambda: paste_into_entry(event, root))
    menu.add_command(label="清空", command=lambda: clear_entry(event, root))
    menu.post(event.x_root, event.y_root)

# 返回列表顶部
def return_to_top():
    tree.selection_set(tree.get_children()[0])
    tree.focus(tree.get_children()[0])
    tree.see(tree.get_children()[0])

# 在主函数中绑定上下文菜单到输入栏
def main():
    global dictionary, entry, tree

    dictionary = load_dictionary(file_path)

    root = tk.Tk()
    root.title("简单查词工具")

    # 尝试恢复窗口位置和大小
    restore_window_position(root)

    # 设置窗口的最小和最大尺寸
    root.minsize(width=400, height=300)
    root.maxsize(width=1600, height=1200)

    frame = ttk.Frame(root, padding="10")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    # 配置网格的列和行，使其能够自动调整大小
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)

    entry = ttk.Entry(frame, width=50)
    entry.grid(row=0, column=0, padx=5, pady=5, sticky=tk.EW)
    entry.bind('<Return>', search)
    entry.bind("<Button-3>", lambda event: create_context_menu(event, root))  # 绑定右键菜单

    search_button = ttk.Button(frame, text="搜索", command=search)
    search_button.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

    top_button = ttk.Button(frame, text="返回顶部", command=return_to_top)
    top_button.grid(row=0, column=2, padx=5, pady=5, sticky=tk.E)

    tree = ttk.Treeview(frame, columns=('Word', 'Meaning'), show='headings')
    tree.heading('Word', text='单词')
    tree.heading('Meaning', text='释义')
    tree.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))

    # 配置列和行以使Treeview控件能够调整大小
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=1)

    # 绑定右键点击事件
    tree.bind("<Button-3>", lambda event: copy_selection(event, root))

    # 在窗口关闭时保存窗口位置和大小
    root.protocol("WM_DELETE_WINDOW", lambda: (save_window_position(root), root.destroy()))

    root.mainloop()

if __name__ == "__main__":
    main()
