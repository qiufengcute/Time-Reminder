import time
import threading
import pystray
from PIL import Image
from pystray import MenuItem as item
import tkinter as tk
from tkinter import messagebox
import os
import sys
import winshell
import json
from queue import Queue

def get_set(is_new_wait_time=True):
    try:
        app_data_path = os.path.join(os.getenv('LOCALAPPDATA'), 'time_re_data')
        config_path = os.path.join(app_data_path, 'data.json')
        with open(config_path, 'r') as file:
            config = json.load(file)
        wt = config['wait_time']
        rt = config['re_time']
    except:
        wt = 30
        rt = 5
    if is_new_wait_time:
        return wt
    else:
        return rt

start_time = 0
is_stop = False
wait_time = get_set()
re_time = get_set(False)
num = 1
go_time = 0
is_reminding = False

def open_start():
    script_path = os.path.abspath(sys.argv[0])
    startup_folder = winshell.startup()
    shortcut_path = os.path.join(startup_folder, "open_start.lnk")
    is_in_startup = os.path.exists(shortcut_path)
    if not is_in_startup:
        with winshell.shortcut(os.path.join(startup_folder, "open_start.lnk")) as shortcut:
            shortcut.path = script_path
            shortcut.description = "open_start"
        message_queue.put(("成功", "已经设置开机自启动"))
    else:
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
            message_queue.put(("成功", "已经关闭开机自启动"))
        else:
            message_queue.put(("失败", "开机自启动文件夹没有文件,无法关闭"))

def get_time():
    global is_stop, num
    if not is_stop:
        message_queue.put(("数据", f"目前为第{num}次计时,目前计时时间为时间为{(time.time() - start_time) / 60:.2f}分钟"))
    else:
        message_queue.put(("数据", f"目前为第{num}次计时,目前计时时间为时间为{go_time / 60:.2f}分钟,已暂停"))

def get_setting():
    message_queue.put(("设置", f"目前计时时间为{wait_time}分钟,休息时间为{re_time}分钟"))

def stop_or_go():
    global start_time, is_stop, go_time
    if is_stop:
        is_stop = False
        start_time = time.time() - go_time
        message_queue.put(("成功", "已经继续计时"))
    else:
        is_stop = True
        go_time = time.time() - start_time
        message_queue.put(("成功", "已经暂停计时"))

def all_reset():
    reset_time(False)
    reset_num(False)
    message_queue.put(("成功", "已经全部重置"))

def reset_time(is_message=True):
    global start_time, go_time
    start_time = time.time()
    go_time = 0
    if is_message:
        message_queue.put(("成功", "已经重置计时"))

def reset_num(is_message=True):
    global num
    num = 1
    if is_message:
        message_queue.put(("成功", "已经重置次数"))

def create_image():
    width = 64
    height = 64
    image = Image.new('RGB', (width, height), (0, 0, 255))
    return image

def on_quit(icon, item):
    message_queue.put(("确认", "确定要退出吗?"))

def setting():
    def s():
        new = entry_nw.get()
        ner = entry_nr.get()
        try:
            new = int(new)
            ner = int(ner)
            if new < 0 or ner < 0:
                messagebox.showerror('错误','输入错误')
                return
        except:
            messagebox.showerror('错误','输入错误')
            return
        
        app_data_path = os.path.join(os.getenv('LOCALAPPDATA'), 'time_re_data')
        os.makedirs(app_data_path, exist_ok=True)
        file_path = os.path.join(app_data_path, 'data.json')
        with open(file_path, 'w') as file:
            json.dump({'wait_time': new, 're_time': ner}, file)
        
        global wait_time, re_time
        wait_time = new
        re_time = ner
        messagebox.showinfo('成功','设置成功')
        reset_time(False)
        setting_window.destroy()

    # Create settings window with proper styling
    setting_window = tk.Toplevel()
    setting_window.title('设置')
    
    # Center the settings window on screen
    window_width = 300
    window_height = 200
    screen_width = setting_window.winfo_screenwidth()
    screen_height = setting_window.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    setting_window.geometry(f'{window_width}x{window_height}+{x}+{y}')
    
    label_now = tk.Label(setting_window, text=f'\n目前计时时间:{str(get_set())}分钟\n\n目前休息时间:{str(get_set(False))}分钟')
    label_now.pack()
    
    label_nw = tk.Label(setting_window, text='请输入新的计时时间(分钟):')
    label_nw.pack()
    
    entry_nw = tk.Entry(setting_window)
    entry_nw.pack()
    
    label_nr = tk.Label(setting_window, text='请输入新的休息时间(分钟):')
    label_nr.pack()
    
    entry_nr = tk.Entry(setting_window)
    entry_nr.pack()
    
    button = tk.Button(setting_window, text='确定', command=s)
    button.pack()
    
    # Make the window stay on top
    setting_window.attributes('-topmost', True)

def reminder():
    global start_time, num, is_reminding
    message_queue.put(("成功", "启动成功了!"))
    while True:
        start_time = time.time()
        while is_stop or time.time() - start_time < wait_time * 60:
            time.sleep(1)
        if not is_reminding:
            is_reminding = True
            message_queue.put(("提醒", f"{wait_time}分钟到了,休息{re_time}分钟吧"))
            is_reminding = False
        while is_stop or time.time() - start_time < wait_time * 60 + re_time * 60:
            time.sleep(1)
        if not is_reminding:
            is_reminding = True
            message_queue.put(("提醒", "休息时间结束"))
            is_reminding = False
        num += 1

def process_messages():
    try:
        message_type, message = message_queue.get_nowait()
        if message_type == "确认":
            if messagebox.askyesno('退出', message):
                icon.stop()
                root.quit()
                sys.exit()
        else:
            messagebox.showinfo(message_type, message)
    except:
        pass
    root.after(100, process_messages)

message_queue = Queue()

menu = (
    item('目前计时时间', get_time, default=True),
    item('查看设置', get_setting),
    item('设置', setting),
    item('暂停/继续', stop_or_go),
    item('全部重置', all_reset),
    item('重置计时', reset_time),
    item('重置次数', reset_num),
    item('设置开机自启动', open_start),
    item('退出', on_quit),
)

# Create and configure the root window to be completely invisible
root = tk.Tk()
root.withdraw()
root.attributes('-alpha', 0)
root.attributes('-topmost', True)
root.overrideredirect(True)
root.attributes('-toolwindow', True)
root.geometry(f'1x1+-{root.winfo_screenwidth()}+-{root.winfo_screenheight()}')

# Create and start the system tray icon
icon = pystray.Icon("name", create_image(), "提醒程序", menu)
icon_thread = threading.Thread(target=icon.run)
icon_thread.daemon = True
icon_thread.start()

# Start the reminder thread
reminder_thread = threading.Thread(target=reminder)
reminder_thread.daemon = True
reminder_thread.start()

# Start processing messages
process_messages()
root.mainloop()
