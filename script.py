#!/usr/bin/env python3
"""
Telegram Quiz Scheduler - Tkinter Desktop Application
Professional UI for scheduling and managing Telegram quizzes
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import asyncio
import threading
import os
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict
import queue

# Install: pip install python-telegram-bot python-docx

from telegram import Bot
from telegram.error import TelegramError
from docx import Document


class QuizSchedulerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📮 Telegram Quiz Scheduler")
        self.root.geometry("1000x750")
        self.root.configure(bg='#f0f0f0')
        
        # Set style
        self.setup_styles()
        
        # Queue for thread-safe logging
        self.log_queue = queue.Queue()
        
        # Config file
        self.config_file = 'quiz_scheduler_config.json'
        self.config = self.load_config()
        
        # Create UI
        self.create_ui()
        
        # Check log queue periodically
        self.check_log_queue()
    
    def setup_styles(self):
        """Setup ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Colors
        self.PRIMARY_COLOR = '#667eea'
        self.SECONDARY_COLOR = '#10b981'
        self.DANGER_COLOR = '#ef4444'
        self.WARNING_COLOR = '#f59e0b'
        
        # Configure styles
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Helvetica', 10))
        style.configure('Title.TLabel', background='#f0f0f0', font=('Helvetica', 14, 'bold'))
        style.configure('Header.TLabel', background='#f0f0f0', font=('Helvetica', 12, 'bold'), foreground=self.PRIMARY_COLOR)
        style.configure('Accent.TButton', foreground=self.PRIMARY_COLOR)
    
    def create_ui(self):
        """Create the main UI"""
        # Main container with notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tab 1: Settings
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text='⚙️ Settings')
        self.create_settings_tab()
        
        # Tab 2: Quiz Scheduler
        self.scheduler_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.scheduler_frame, text='📅 Schedule Quiz')
        self.create_scheduler_tab()
        
        # Tab 3: Logs
        self.logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.logs_frame, text='📋 Logs')
        self.create_logs_tab()
    
    def create_settings_tab(self):
        """Create settings tab"""
        container = ttk.Frame(self.settings_frame)
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title = ttk.Label(container, text='Bot Configuration', style='Header.TLabel')
        title.pack(anchor='w', pady=(0, 20))
        
        # Bot Token
        ttk.Label(container, text='Bot Token:').pack(anchor='w', pady=(10, 5))
        self.token_entry = ttk.Entry(container, width=60, show='•')
        self.token_entry.pack(anchor='w', fill='x')
        self.token_entry.insert(0, self.config.get('token', ''))
        
        # Help text
        help_text = ttk.Label(container, text='Get token from @BotFather on Telegram', font=('Helvetica', 9), foreground='gray')
        help_text.pack(anchor='w', pady=(0, 20))
        
        # Groups Section
        groups_title = ttk.Label(container, text='Target Groups', style='Header.TLabel')
        groups_title.pack(anchor='w', pady=(20, 10))
        
        # Group entry
        group_frame = ttk.Frame(container)
        group_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(group_frame, text='Group Chat ID:').pack(side='left', padx=(0, 10))
        self.group_entry = ttk.Entry(group_frame, width=30)
        self.group_entry.pack(side='left', padx=(0, 10))
        
        add_group_btn = ttk.Button(group_frame, text='+ Add Group', command=self.add_group)
        add_group_btn.pack(side='left')
        
        # Groups list with scrollbar
        list_frame = ttk.Frame(container)
        list_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.groups_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=8)
        self.groups_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.groups_listbox.yview)
        
        # Load saved groups
        for group in self.config.get('groups', []):
            self.groups_listbox.insert('end', str(group))
        
        # Remove button
        remove_btn = ttk.Button(container, text='🗑️ Remove Selected Group', command=self.remove_group)
        remove_btn.pack(fill='x', pady=(0, 20))
        
        # Quiz Settings
        quiz_title = ttk.Label(container, text='Default Quiz Settings', style='Header.TLabel')
        quiz_title.pack(anchor='w', pady=(20, 10))
        
        # Anonymous voting
        self.anonymous_var = tk.BooleanVar(value=self.config.get('anonymous', True))
        ttk.Checkbutton(container, text='Anonymous Voting', variable=self.anonymous_var).pack(anchor='w', pady=5)
        
        # Open period
        open_frame = ttk.Frame(container)
        open_frame.pack(fill='x', pady=5)
        ttk.Label(open_frame, text='Auto-close poll (seconds):').pack(side='left', padx=(0, 10))
        self.open_period_var = tk.StringVar(value=str(self.config.get('open_period', 30)))
        ttk.Spinbox(open_frame, from_=5, to=300, textvariable=self.open_period_var, width=10).pack(side='left')
        
        # Save button
        save_btn = ttk.Button(container, text='💾 Save Settings', command=self.save_settings)
        save_btn.pack(fill='x', pady=(20, 0))
    
    def create_scheduler_tab(self):
        """Create scheduler tab"""
        container = ttk.Frame(self.scheduler_frame)
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title = ttk.Label(container, text='Schedule New Quiz', style='Header.TLabel')
        title.pack(anchor='w', pady=(0, 20))
        
        # File selection
        file_frame = ttk.LabelFrame(container, text='📄 Quiz Document', padding=10)
        file_frame.pack(fill='x', pady=(0, 20))
        
        self.file_label = ttk.Label(file_frame, text='No file selected', foreground='gray')
        self.file_label.pack(anchor='w', pady=(0, 10))
        
        file_btn = ttk.Button(file_frame, text='📂 Select DOCX File', command=self.select_file)
        file_btn.pack(fill='x')
        
        self.selected_file = None
        
        # Schedule settings
        sched_frame = ttk.LabelFrame(container, text='⏰ Schedule Settings', padding=10)
        sched_frame.pack(fill='x', pady=(0, 20))
        
        # Start time
        time_frame1 = ttk.Frame(sched_frame)
        time_frame1.pack(fill='x', pady=(0, 15))
        
        ttk.Label(time_frame1, text='Start Date:').pack(side='left', padx=(0, 10))
        self.date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        ttk.Entry(time_frame1, textvariable=self.date_var, width=15).pack(side='left', padx=(0, 20))
        
        ttk.Label(time_frame1, text='Start Time (HH:MM):').pack(side='left', padx=(0, 10))
        self.time_var = tk.StringVar(value='10:00')
        ttk.Entry(time_frame1, textvariable=self.time_var, width=10).pack(side='left')
        
        # Delay between quizzes
        delay_frame = ttk.Frame(sched_frame)
        delay_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(delay_frame, text='Delay between quizzes (minutes):').pack(side='left', padx=(0, 10))
        self.delay_var = tk.StringVar(value='1')
        ttk.Spinbox(delay_frame, from_=1, to=60, textvariable=self.delay_var, width=10).pack(side='left')
        
        # Explanation
        ttk.Label(sched_frame, text='Common Explanation (optional):').pack(anchor='w', pady=(0, 5))
        self.explanation_var = tk.StringVar()
        explanation_entry = ttk.Entry(sched_frame, textvariable=self.explanation_var, width=60)
        explanation_entry.pack(fill='x', pady=(0, 15))
        
        # Group selection
        group_frame = ttk.Frame(sched_frame)
        group_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(group_frame, text='Send to Groups:').pack(side='left', padx=(0, 10))
        self.send_groups_var = tk.StringVar()
        
        if self.groups_listbox.size() > 0:
            groups_text = ', '.join([self.groups_listbox.get(i) for i in range(self.groups_listbox.size())])
            self.send_groups_var.set(groups_text)
        
        ttk.Label(group_frame, textvariable=self.send_groups_var, foreground='blue').pack(side='left')
        
        # Schedule button
        schedule_btn = ttk.Button(container, text='🚀 Schedule Quiz', command=self.schedule_quiz)
        schedule_btn.pack(fill='x', pady=(20, 0))
    
    def create_logs_tab(self):
        """Create logs tab"""
        container = ttk.Frame(self.logs_frame)
        container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        title = ttk.Label(container, text='Activity Log', style='Header.TLabel')
        title.pack(anchor='w', pady=(0, 10))
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(
            container, 
            height=25, 
            width=100,
            bg='#1a1a2e',
            fg='#00ff88',
            font=('Courier', 9),
            insertbackground='#00ff88'
        )
        self.log_text.pack(fill='both', expand=True)
        
        # Configure tags for colors
        self.log_text.tag_config('success', foreground='#00ff88')
        self.log_text.tag_config('error', foreground='#ff6b6b')
        self.log_text.tag_config('info', foreground='#4dabf7')
        self.log_text.tag_config('warn', foreground='#ffd93d')
        
        # Clear button
        button_frame = ttk.Frame(container)
        button_frame.pack(fill='x', pady=(10, 0))
        
        clear_btn = ttk.Button(button_frame, text='🗑️ Clear Logs', command=self.clear_logs)
        clear_btn.pack(side='right', padx=(0, 0))
    
    def add_group(self):
        """Add a group to the list"""
        group_id = self.group_entry.get().strip()
        
        if not group_id:
            messagebox.showwarning('Warning', 'Please enter a Chat ID')
            return
        
        try:
            int(group_id)
        except ValueError:
            messagebox.showerror('Error', 'Chat ID must be a number')
            return
        
        if group_id in self.groups_listbox.get(0, 'end'):
            messagebox.showwarning('Warning', 'Group already added')
            return
        
        self.groups_listbox.insert('end', group_id)
        self.group_entry.delete(0, 'end')
        self.log('Group added: ' + group_id, 'success')
    
    def remove_group(self):
        """Remove selected group"""
        selection = self.groups_listbox.curselection()
        if not selection:
            messagebox.showwarning('Warning', 'Please select a group to remove')
            return
        
        self.groups_listbox.delete(selection[0])
        self.log('Group removed', 'success')
    
    def select_file(self):
        """Select DOCX file"""
        filename = filedialog.askopenfilename(
            title='Select Quiz Document',
            filetypes=[('Word Documents', '*.docx'), ('All Files', '*.*')]
        )
        
        if filename:
            self.selected_file = filename
            self.file_label.config(text=f'✅ {os.path.basename(filename)}', foreground='green')
            self.log(f'File selected: {filename}', 'info')
    
    def save_settings(self):
        """Save settings to config file"""
        self.config['token'] = self.token_entry.get()
        self.config['groups'] = list(self.groups_listbox.get(0, 'end'))
        self.config['anonymous'] = self.anonymous_var.get()
        self.config['open_period'] = int(self.open_period_var.get())
        
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        
        self.log('Settings saved successfully', 'success')
        messagebox.showinfo('Success', 'Settings saved!')
    
    def load_config(self):
        """Load config from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'token': '', 'groups': [], 'anonymous': True, 'open_period': 30}
    
    def schedule_quiz(self):
        """Schedule the quiz"""
        # Validation
        if not self.token_entry.get().strip():
            messagebox.showerror('Error', 'Please enter Bot Token')
            self.log('Error: Bot Token is empty', 'error')
            return
        
        if not self.selected_file:
            messagebox.showerror('Error', 'Please select a DOCX file')
            self.log('Error: No file selected', 'error')
            return
        
        if self.groups_listbox.size() == 0:
            messagebox.showerror('Error', 'Please add at least one group in Settings tab')
            self.log('Error: No groups added', 'error')
            return
        
        # Get parameters
        token = self.token_entry.get().strip()
        
        # Get groups from listbox with proper validation
        try:
            groups = []
            for i in range(self.groups_listbox.size()):
                group_str = self.groups_listbox.get(i).strip()
                if group_str:
                    groups.append(int(group_str))
            
            if not groups:
                messagebox.showerror('Error', 'Invalid group IDs')
                self.log('Error: Invalid group IDs', 'error')
                return
        except ValueError as e:
            messagebox.showerror('Error', f'Invalid group ID format: {str(e)}')
            self.log(f'Error: Invalid group ID - {str(e)}', 'error')
            return
        
        # Validate date/time
        try:
            date_str = self.date_var.get().strip()
            time_str = self.time_var.get().strip()
            
            if not date_str or not time_str:
                messagebox.showerror('Error', 'Please set date and time')
                self.log('Error: Date or time is empty', 'error')
                return
            
            start_time = datetime.strptime(
                f"{date_str} {time_str}",
                '%Y-%m-%d %H:%M'
            )
        except ValueError as e:
            messagebox.showerror('Error', f'Invalid date/time format: {str(e)}')
            self.log(f'Error: Invalid date/time - {str(e)}', 'error')
            return
        
        # Validate delay
        try:
            delay_str = self.delay_var.get().strip()
            if not delay_str:
                messagebox.showerror('Error', 'Please set delay')
                self.log('Error: Delay is empty', 'error')
                return
            delay = int(delay_str)
            if delay < 1:
                messagebox.showerror('Error', 'Delay must be at least 1 minute')
                self.log('Error: Delay must be >= 1', 'error')
                return
        except ValueError as e:
            messagebox.showerror('Error', f'Delay must be a number: {str(e)}')
            self.log(f'Error: Invalid delay - {str(e)}', 'error')
            return
        
        # Validate open period
        try:
            open_period = int(self.open_period_var.get())
            if open_period < 5:
                open_period = 30
        except ValueError:
            open_period = 30
        
        self.log(f'📅 Starting scheduler...', 'info')
        self.log(f'🔐 Bot Token: {token[:10]}...', 'info')
        self.log(f'👥 Groups: {groups}', 'info')
        self.log(f'📄 File: {self.selected_file}', 'info')
        self.log(f'⏰ Start: {start_time}', 'info')
        self.log(f'⏱️ Delay: {delay} minutes', 'info')
        
        # Run in background thread
        thread = threading.Thread(
            target=self._run_scheduler,
            args=(token, self.selected_file, groups, start_time, delay, self.explanation_var.get(), open_period)
        )
        thread.daemon = True
        thread.start()
        
        messagebox.showinfo('Success', f'Quiz scheduled for {start_time.strftime("%Y-%m-%d %H:%M")}')
    
    def _run_scheduler(self, token, file, groups, start_time, delay, explanation, open_period=30):
        """Run scheduler in background thread"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                self._schedule_async(token, file, groups, start_time, delay, explanation, open_period)
            )
        except Exception as e:
            self.log(f'Error: {str(e)}', 'error')
            messagebox.showerror('Error', f'Scheduler error: {str(e)}')
    
    async def _schedule_async(self, token, file, groups, start_time, delay, explanation, open_period=30):
        """Async scheduler"""
        from quiz_scheduler import QuizScheduler
        
        try:
            scheduler = QuizScheduler(token)
            
            # Extract quizzes
            self.log('📂 Reading document...', 'info')
            quizzes = await scheduler.extract_quizzes_from_docx(file)
            
            if not quizzes:
                self.log('❌ No valid quizzes found', 'error')
                return
            
            # Schedule
            self.log(f'⏰ Scheduling {len(quizzes)} quizzes', 'info')
            await scheduler.schedule_quizzes(
                quizzes=quizzes,
                chat_ids=groups,
                start_time=start_time,
                delay_minutes=delay,
                explanation=explanation,
                is_anonymous=self.anonymous_var.get(),
                open_period=open_period
            )
            
            # Wait for completion
            await scheduler.wait_for_completion()
            
            self.log('🎉 All quizzes scheduled successfully!', 'success')
            messagebox.showinfo('Success', 'All quizzes have been sent!')
            
        except Exception as e:
            self.log(f'❌ Error: {str(e)}', 'error')
    
    def log(self, message, tag='info'):
        """Add message to log"""
        self.log_queue.put((message, tag))
    
    def check_log_queue(self):
        """Check log queue and update UI"""
        try:
            while True:
                message, tag = self.log_queue.get_nowait()
                
                timestamp = datetime.now().strftime('%H:%M:%S')
                log_message = f'[{timestamp}] {message}\n'
                
                self.log_text.insert('end', log_message, tag)
                self.log_text.see('end')
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_log_queue)
    
    def clear_logs(self):
        """Clear the log text"""
        self.log_text.delete('1.0', 'end')
        self.log('Log cleared', 'info')


def main():
    root = tk.Tk()
    app = QuizSchedulerApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
