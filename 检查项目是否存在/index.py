import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import json
import queue
import os
import sys
import shutil

# 处理 zhconv 字典文件加载问题
def init_zhconv():
    try:
        from zhconv import convert
        # 测试是否能正常使用
        convert("测试", "zh-cn")
        return convert
    except Exception as e:
        print(f"zhconv 初始化失败: {e}")
        # 尝试从程序目录或临时目录复制字典文件
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        zhconv_dir = os.path.join(base_path, "zhconv")
        
        if os.path.exists(zhconv_dir):
            # 如果打包时有包含 zhconv 目录，尝试复制到临时目录
            import tempfile
            temp_zhconv = tempfile.mkdtemp()
            try:
                shutil.copytree(zhconv_dir, os.path.join(temp_zhconv, "zhconv"))
                sys.path.insert(0, temp_zhconv)
                from zhconv import convert
                print("zhconv 从临时目录加载成功")
                return convert
            except Exception as e2:
                print(f"临时目录加载失败: {e2}")
        
        # 如果以上都不行，提供一个简单的转换函数（只做 trim，不做繁简转换）
        print("zhconv 不可用，将使用简单的 trim 替代")
        def simple_convert(text, target='zh-cn'):
            return text.strip()
        return simple_convert

convert = init_zhconv()
from utils import sarch_task


class SearchUI:
    def __init__(self, root):
        self.root = root
        self.root.title("批量搜索工具")
        self.root.geometry("900x680")
        self.root.resizable(False, False)
        self.root.configure(bg="#1a1a2e")

        # 持久化文件路径
        self.pending_file = "pending_tasks.json"
        self.completed_file = "completed_tasks.json"

        # 任务队列和状态
        self.task_queue = queue.Queue()
        self.all_tasks = []
        self.completed_tasks = []
        self.is_running = False
        self.stop_flag = False
        self.lock = threading.Lock()

        # 颜色配置
        self.colors = {
            "bg": "#1a1a2e",
            "card": "#16213e",
            "card_hover": "#1e2a4a",
            "accent": "#e94560",
            "accent_hover": "#ff6b6b",
            "success": "#00d9ff",
            "success_bg": "#0a3d62",
            "fail": "#ff4757",
            "fail_bg": "#5c1a1a",
            "zero": "#ffa502",
            "zero_bg": "#5c4a1a",
            "has_result": "#7bed9f",
            "has_result_bg": "#1a5c3a",
            "text": "#eee",
            "text_dim": "#888",
            "border": "#2a2a4a"
        }

        # 主容器
        main_frame = tk.Frame(root, bg=self.colors["bg"], padx=25, pady=20)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

        # 标题栏
        header = tk.Frame(main_frame, bg=self.colors["bg"])
        header.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 12))
        header.columnconfigure(1, weight=1)

        tk.Label(
            header,
            text="批量搜索工具",
            font=("Microsoft YaHei", 20, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["accent"]
        ).grid(row=0, column=0, sticky=tk.W)

        # 状态指示器
        self.status_indicator = tk.Label(
            header,
            text="● 就绪",
            font=("Microsoft YaHei", 10),
            bg=self.colors["bg"],
            fg=self.colors["success"]
        )
        self.status_indicator.grid(row=0, column=2, sticky=tk.E)

        # 输入区域
        input_frame = self.create_card(main_frame)
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(0, weight=1)

        input_header = tk.Frame(input_frame, bg=self.colors["card"])
        input_header.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        input_header.columnconfigure(1, weight=1)

        tk.Label(
            input_header,
            text="任务输入",
            font=("Microsoft YaHei", 11, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"]
        ).grid(row=0, column=0, sticky=tk.W)

        tk.Label(
            input_header,
            text="JSON 数组格式",
            font=("Microsoft YaHei", 8),
            bg=self.colors["card"],
            fg=self.colors["text_dim"]
        ).grid(row=0, column=1, sticky=tk.E)

        # JSON输入框
        self.text_input = scrolledtext.ScrolledText(
            input_frame,
            width=60,
            height=15,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#0f0f23",
            fg=self.colors["text"],
            relief=tk.FLAT,
            padx=10,
            pady=8,
            insertbackground=self.colors["accent"],
            selectbackground=self.colors["accent"],
            selectforeground="white"
        )
        self.text_input.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        self.text_input.insert(tk.END, '')

        # 按钮组
        btn_frame = tk.Frame(input_frame, bg=self.colors["card"])
        btn_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))

        self.add_btn = self.create_button(
            btn_frame, "+ 添加任务", self.colors["accent"], self.colors["accent_hover"],
            self.on_add_tasks
        )
        self.add_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.start_btn = self.create_button(
            btn_frame, "▶ 开始搜索", self.colors["success"], "#00a8ff",
            self.on_start
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.stop_btn = self.create_button(
            btn_frame, "■ 停止", self.colors["fail"], "#ff6b81",
            self.on_stop, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.clear_btn = self.create_button(
            btn_frame, "清空", "#576574", "#8395a7",
            self.on_clear
        )
        self.clear_btn.pack(side=tk.LEFT)

        # 统计面板
        stats_frame = self.create_card(main_frame)
        stats_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        stats_frame.columnconfigure(0, weight=1)

        # 队列信息（与统计卡片合并在一行）
        queue_info = tk.Frame(stats_frame, bg=self.colors["card"])
        queue_info.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        queue_info.columnconfigure(1, weight=1)

        tk.Label(
            queue_info,
            text="任务队列",
            font=("Microsoft YaHei", 11, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"]
        ).grid(row=0, column=0, sticky=tk.W)

        self.queue_label = tk.Label(
            queue_info,
            text="队列: 0 | 已完成: 0 | 总计: 0",
            font=("Microsoft YaHei", 9),
            bg=self.colors["card"],
            fg=self.colors["text_dim"]
        )
        self.queue_label.grid(row=0, column=2, sticky=tk.E)

        # 统计卡片网格
        cards_frame = tk.Frame(stats_frame, bg=self.colors["card"])
        cards_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        cards_frame.columnconfigure((0, 1, 2, 3, 4), weight=1)

        # 进度卡片
        self.progress_card = self.create_stat_card(
            cards_frame, 0, "总进度", "0/0", "0%", self.colors["accent"], "#2a1a3e"
        )

        # 成功卡片
        self.success_card = self.create_stat_card(
            cards_frame, 1, "成功", "0", None, self.colors["success"], self.colors["success_bg"]
        )

        # 失败卡片
        self.fail_card = self.create_stat_card(
            cards_frame, 2, "失败", "0", None, self.colors["fail"], self.colors["fail_bg"]
        )

        # 存在(0条)卡片
        self.zero_card = self.create_stat_card(
            cards_frame, 3, "存在(0条)", "0", None, self.colors["zero"], self.colors["zero_bg"]
        )

        # 有结果卡片
        self.has_result_card = self.create_stat_card(
            cards_frame, 4, "有结果", "0", None, self.colors["has_result"], self.colors["has_result_bg"]
        )

        # 当前检查
        current_frame = tk.Frame(stats_frame, bg=self.colors["card"])
        current_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(8, 0))
        tk.Label(
            current_frame,
            text="当前检查: ",
            font=("Microsoft YaHei", 9),
            bg=self.colors["card"],
            fg=self.colors["text_dim"]
        ).pack(side=tk.LEFT)
        self.current_label = tk.Label(
            current_frame,
            text="无",
            font=("Microsoft YaHei", 9, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"]
        )
        self.current_label.pack(side=tk.LEFT)

        # 进度条
        self.progress_bar = tk.Canvas(
            main_frame,
            height=4,
            bg=self.colors["bg"],
            highlightthickness=0
        )
        self.progress_bar.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        self.progress_fill = self.progress_bar.create_rectangle(
            0, 0, 0, 4, fill=self.colors["accent"], outline=""
        )

        # 状态变量
        self.stats = {
            "success": 0,
            "fail": 0,
            "zero": 0,
            "has_result": 0,
        }

        # 启动时加载未完成任务
        self.load_pending_tasks()

    def create_card(self, parent):
        """创建卡片容器"""
        card = tk.Frame(parent, bg=self.colors["card"], padx=20, pady=16)
        card.bind("<Enter>", lambda e: card.config(bg=self.colors["card_hover"]))
        card.bind("<Leave>", lambda e: card.config(bg=self.colors["card"]))
        return card

    def create_button(self, parent, text, bg, active_bg, command, state=tk.NORMAL):
        """创建自定义按钮"""
        btn = tk.Label(
            parent,
            text=text,
            font=("Microsoft YaHei", 10, "bold"),
            bg=bg,
            fg="white",
            padx=20,
            pady=8,
            cursor="hand2" if state == tk.NORMAL else "",
            relief=tk.FLAT
        )
        if state == tk.NORMAL:
            btn.bind("<Button-1>", lambda e: command())
            btn.bind("<Enter>", lambda e: btn.config(bg=active_bg))
            btn.bind("<Leave>", lambda e: btn.config(bg=bg))
        else:
            btn.config(fg="#888")
        return btn

    def create_stat_card(self, parent, column, title, value, sub_value, fg_color, bg_color):
        """创建统计卡片"""
        card = tk.Frame(parent, bg=bg_color, padx=15, pady=12)
        card.grid(row=0, column=column, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)

        tk.Label(
            card,
            text=title,
            font=("Microsoft YaHei", 9),
            bg=bg_color,
            fg=fg_color
        ).pack()

        value_label = tk.Label(
            card,
            text=value,
            font=("Microsoft YaHei", 16, "bold"),
            bg=bg_color,
            fg=fg_color
        )
        value_label.pack()

        if sub_value:
            sub_label = tk.Label(
                card,
                text=sub_value,
                font=("Microsoft YaHei", 9),
                bg=bg_color,
                fg=fg_color
            )
            sub_label.pack()
            return {"value": value_label, "sub": sub_label}

        return {"value": value_label}

    def log(self, message):
        """打印日志到控制台"""
        print(message)

    def save_pending_tasks(self):
        """保存待完成任务到本地文件"""
        with self.lock:
            pending = [task for task in self.all_tasks if task not in self.completed_tasks]
        try:
            with open(self.pending_file, "w", encoding="utf-8") as f:
                json.dump(pending, f, ensure_ascii=False, indent=2)
            self.log(f"已保存 {len(pending)} 个待完成任务到 {self.pending_file}")
        except Exception as e:
            self.log(f"保存待完成任务失败: {e}")

    def load_pending_tasks(self):
        """从本地文件加载未完成任务"""
        if not os.path.exists(self.pending_file):
            return
        try:
            with open(self.pending_file, "r", encoding="utf-8") as f:
                pending = json.load(f)
            if isinstance(pending, list) and pending:
                with self.lock:
                    for keyword in pending:
                        if isinstance(keyword, str) and keyword.strip():
                            self.all_tasks.append(keyword)
                            self.task_queue.put(keyword)
                self.update_queue_display()
                self.update_progress()
                self.log(f"已加载 {len(pending)} 个未完成任务")
        except Exception as e:
            self.log(f"加载未完成任务失败: {e}")

    def save_completed_tasks(self):
        """保存已完成任务到本地文件"""
        with self.lock:
            completed = self.completed_tasks.copy()
        try:
            with open(self.completed_file, "w", encoding="utf-8") as f:
                json.dump(completed, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"保存已完成任务失败: {e}")

    def parse_json_input(self):
        """解析JSON输入"""
        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("警告", "请输入JSON数组")
            return []

        # 显示输入的前100个字符用于调试
        preview = text[:100] + "..." if len(text) > 100 else text
        self.log(f"正在解析JSON，输入预览: {preview}")

        try:
            data = json.loads(text)
            if isinstance(data, list):
                keywords = []
                for item in data:
                    if isinstance(item, str) and item.strip():
                        keywords.append(convert(item.strip(), 'zh-cn'))
                self.log(f"成功解析 {len(keywords)} 个关键词")
                return keywords
            else:
                messagebox.showwarning("警告", "JSON必须是数组格式，例如：[\"关键词1\", \"关键词2\"]")
                return []
        except json.JSONDecodeError as e:
            error_msg = f"JSON解析失败: {e}\n\n请确保输入的是标准JSON数组格式，例如：\n[\"关键词1\", \"关键词2\"]"
            messagebox.showerror("错误", error_msg)
            self.log(f"JSON解析错误: {e}")
            return []
        except Exception as e:
            messagebox.showerror("错误", f"解析时发生未知错误: {e}")
            self.log(f"未知解析错误: {e}")
            return []

    def update_queue_display(self):
        """更新队列显示"""
        with self.lock:
            total = len(self.all_tasks)
            completed = len(self.completed_tasks)
            pending = self.task_queue.qsize()
        self.queue_label.config(text=f"队列: {pending} | 已完成: {completed} | 总计: {total}")

    def update_progress(self):
        """更新进度显示"""
        with self.lock:
            total = len(self.all_tasks)
            completed = len(self.completed_tasks)
        percent = int((completed / total) * 100) if total > 0 else 0

        # 更新进度卡片
        self.progress_card["value"].config(text=f"{completed}/{total}")
        self.progress_card["sub"].config(text=f"{percent}%")

        # 更新进度条
        width = self.progress_bar.winfo_width()
        fill_width = int(width * percent / 100)
        self.progress_bar.coords(self.progress_fill, 0, 0, fill_width, 4)

    def update_stats_display(self):
        """更新统计面板"""
        self.success_card["value"].config(text=str(self.stats["success"]))
        self.fail_card["value"].config(text=str(self.stats["fail"]))
        self.zero_card["value"].config(text=str(self.stats["zero"]))
        self.has_result_card["value"].config(text=str(self.stats["has_result"]))

    def on_add_tasks(self):
        """添加任务到队列"""
        keywords = self.parse_json_input()
        if not keywords:
            return

        with self.lock:
            existing_tasks = set(self.all_tasks)
            added = []
            skipped = []
            for keyword in keywords:
                if keyword in existing_tasks:
                    skipped.append(keyword)
                else:
                    self.all_tasks.append(keyword)
                    self.task_queue.put(keyword)
                    existing_tasks.add(keyword)
                    added.append(keyword)

        self.update_queue_display()
        self.update_progress()
        self.save_pending_tasks()

        if added:
            self.log(f"已添加 {len(added)} 个任务到队列")
        if skipped:
            self.log(f"跳过 {len(skipped)} 个重复任务")

        self.text_input.delete("1.0", tk.END)

    def on_start(self):
        """开始搜索"""
        if self.is_running:
            return

        if self.task_queue.empty():
            self.on_add_tasks()
            if self.task_queue.empty():
                messagebox.showwarning("警告", "没有任务可执行")
                return

        self.is_running = True
        self.stop_flag = False
        self.status_indicator.config(text="● 运行中", fg=self.colors["accent"])

        # 禁用开始按钮，启用停止按钮
        self.start_btn.config(fg="#888", cursor="")
        self.start_btn.unbind("<Button-1>")
        self.stop_btn.config(fg="white", cursor="hand2")
        self.stop_btn.bind("<Button-1>", lambda e: self.on_stop())

        thread = threading.Thread(target=self.worker_loop, daemon=True)
        thread.start()

    def worker_loop(self):
        """工作线程循环"""
        while not self.stop_flag:
            try:
                keyword = self.task_queue.get(timeout=1)
            except queue.Empty:
                with self.lock:
                    if len(self.completed_tasks) >= len(self.all_tasks):
                        break
                continue

            self.root.after(0, lambda k=keyword: self.current_label.config(
                text=k[:30] + "..." if len(k) > 30 else k
            ))

            try:
                count = sarch_task(keyword)

                with self.lock:
                    self.completed_tasks.append(keyword)

                if count == -1:
                    self.stats["fail"] += 1
                    self.root.after(0, lambda k=keyword: self.log(f"[失败] {k}"))
                elif count == 0:
                    self.stats["success"] += 1
                    self.stats["zero"] += 1
                    self.root.after(0, lambda k=keyword: self.log(f"[存在-0条] {k}"))
                else:
                    self.stats["success"] += 1
                    self.stats["has_result"] += 1
                    self.root.after(0, lambda k=keyword, c=count: self.log(f"[有结果-{c}条] {k}"))

            except Exception as e:
                with self.lock:
                    self.completed_tasks.append(keyword)
                self.stats["fail"] += 1
                self.root.after(0, lambda k=keyword, err=str(e): self.log(f"[异常] {k}: {err}"))

            self.root.after(0, self.update_queue_display)
            self.root.after(0, self.update_progress)
            self.root.after(0, self.update_stats_display)
            self.root.after(0, self.save_pending_tasks)
            self.root.after(0, self.save_completed_tasks)

            self.task_queue.task_done()

        self.root.after(0, self.on_worker_done)

    def on_worker_done(self):
        """工作线程完成"""
        self.is_running = False
        self.status_indicator.config(text="● 完成", fg=self.colors["success"])

        # 恢复按钮状态
        self.start_btn.config(fg="white", cursor="hand2")
        self.start_btn.bind("<Button-1>", lambda e: self.on_start())
        self.stop_btn.config(fg="#888", cursor="")
        self.stop_btn.unbind("<Button-1>")

        self.current_label.config(text="完成")
        self.log("\n========== 搜索完成 ==========")
        self.log(f"总计: {len(self.all_tasks)} 个任务")
        self.log(f"已完成: {len(self.completed_tasks)} 个")
        self.log(f"成功: {self.stats['success']} 个")
        self.log(f"失败: {self.stats['fail']} 个")
        self.log(f"存在(0条): {self.stats['zero']} 个")
        self.log(f"有结果: {self.stats['has_result']} 个")

        # 清空待完成任务文件
        if os.path.exists(self.pending_file):
            try:
                os.remove(self.pending_file)
                self.log("已清空待完成任务文件")
            except Exception as e:
                self.log(f"清空待完成任务文件失败: {e}")

    def on_stop(self):
        """停止搜索"""
        self.stop_flag = True
        self.status_indicator.config(text="● 停止中", fg=self.colors["fail"])
        self.log("\n正在停止...")
        self.stop_btn.config(fg="#888", cursor="")
        self.stop_btn.unbind("<Button-1>")

        # 保存当前状态
        self.save_pending_tasks()
        self.save_completed_tasks()

    def on_clear(self):
        """清空全部"""
        with self.lock:
            while not self.task_queue.empty():
                try:
                    self.task_queue.get_nowait()
                    self.task_queue.task_done()
                except queue.Empty:
                    break
            self.all_tasks.clear()
            self.completed_tasks.clear()

        self.stats = {
            "success": 0,
            "fail": 0,
            "zero": 0,
            "has_result": 0,
        }

        self.update_queue_display()
        self.update_progress()
        self.update_stats_display()
        self.current_label.config(text="无")
        self.status_indicator.config(text="● 就绪", fg=self.colors["success"])

        # 清空持久化文件
        for f in [self.pending_file, self.completed_file]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

        self.log("已清空所有任务和结果")


def main():
    root = tk.Tk()
    app = SearchUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
