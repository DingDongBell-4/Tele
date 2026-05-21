#!/usr/bin/env python3
"""
Telegram Quiz Scheduler - Native Telegram Scheduling
Schedules quizzes directly in Telegram's scheduled messages using Unix timestamps
"""

import os
import json
import asyncio
import re
import random
from datetime import datetime, timedelta
from typing import List, Dict
import argparse

# Install: pip install python-telegram-bot httpx

import httpx
from docx import Document


class TelegramNativeScheduler:
    def __init__(self, bot_token: str):
        """Initialize the scheduler with bot token"""
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        
    async def extract_quizzes_from_docx(self, file_path: str) -> List[Dict]:
        """Extract quizzes from DOCX file"""
        print(f"📂 Reading: {file_path}")
        
        doc = Document(file_path)
        full_text = "\n".join([para.text for para in doc.paragraphs])
        
        # Split by "Question:"
        blocks = [b.strip() for b in re.split(r'Question:', full_text, flags=re.IGNORECASE) if b.strip()]
        
        print(f"✅ Found {len(blocks)} questions")
        
        quizzes = []
        skipped = 0
        
        for idx, block in enumerate(blocks, 1):
            quiz = self._parse_quiz_block(block, idx)
            
            if quiz:
                quizzes.append(quiz)
            else:
                skipped += 1
        
        print(f"📋 Valid quizzes: {len(quizzes)}, Skipped: {skipped}")
        return quizzes
    
    def _parse_quiz_block(self, block: str, question_num: int) -> Dict or None:
        """Parse a single quiz block"""
        
        # Remove explanation (everything after Ans:)
        clean_block = re.split(r'Ans:', block, flags=re.IGNORECASE)[0]
        
        # Extract question
        question_match = re.match(r'([\s\S]*?)(?=\([a-d]\))', clean_block, re.IGNORECASE)
        if not question_match:
            print(f"⏭️  Q{question_num}: Skipped - No question found")
            return None
        
        question = question_match.group(1).strip()
        
        # Check for LaTeX
        if re.search(r'\$[\s\S]*?\$|\\[\w\{\}]+', block):
            print(f"⏭️  Q{question_num}: Skipped - LaTeX code detected")
            return None
        
        # Check for tables
        if re.search(r'^\s*\|[\s\S]*\|', clean_block, re.MULTILINE):
            print(f"⏭️  Q{question_num}: Skipped - Table format detected")
            return None
        
        # Check for images
        if re.search(r'\[img\]|<img|\.jpg|\.png|\.gif|\.bmp|image:', block, re.IGNORECASE):
            print(f"⏭️  Q{question_num}: Skipped - Image reference detected")
            return None
        
        # Extract options
        option_matches = re.finditer(r'\([a-d]\)\s*([\s\S]*?)(?=\([a-d]\)|$)', clean_block, re.IGNORECASE)
        options = []
        for match in option_matches:
            opt = match.group(1).strip()
            if opt:
                options.append(opt)
        
        # Extract answer
        answer_match = re.search(r'Ans:\s*([a-d])', block, re.IGNORECASE)
        if not answer_match:
            print(f"⏭️  Q{question_num}: Skipped - No answer found")
            return None
        
        correct_idx = ord(answer_match.group(1).lower()) - ord('a')
        
        # Validation
        if len(options) < 2:
            print(f"⏭️  Q{question_num}: Skipped - Less than 2 options")
            return None
        
        if len(options) > 10:
            print(f"⏭️  Q{question_num}: Skipped - More than 10 options")
            return None
        
        if len(question) > 300:
            print(f"⏭️  Q{question_num}: Skipped - Question too long ({len(question)} chars)")
            return None
        
        if correct_idx >= len(options):
            print(f"⏭️  Q{question_num}: Skipped - Answer index invalid")
            return None
        
        if any(len(opt) > 100 for opt in options):
            print(f"⏭️  Q{question_num}: Skipped - Option too long")
            return None
        
        return {
            'number': question_num,
            'question': question,
            'options': options,
            'correct_option_id': correct_idx
        }
    
    async def schedule_quizzes(
        self,
        quizzes: List[Dict],
        chat_ids: List[int],
        start_time: datetime,
        delay_minutes: int,
        explanation: str = "",
        is_anonymous: bool = True,
        open_period: int = 30,
        random_count: int = None,
        random_seed: int = None
    ):
        """Schedule quizzes using Telegram's native scheduling feature
        
        Args:
            quizzes: List of quiz questions
            chat_ids: Target chat IDs
            start_time: When to start sending
            delay_minutes: Delay between quizzes
            explanation: Common explanation
            is_anonymous: Anonymous voting
            open_period: Auto-close time
            random_count: Number of random questions to select (None = all)
            random_seed: Seed for random selection (None = use current time)
        """
        
        # Select random questions if specified
        if random_count and random_count < len(quizzes):
            if random_seed is not None:
                random.seed(random_seed)
            
            quizzes = random.sample(quizzes, min(random_count, len(quizzes)))
            quizzes = sorted(quizzes, key=lambda x: x['number'])  # Keep original order
            print(f"\n🎲 Random Selection: Picked {len(quizzes)} questions randomly")
            print(f"📌 Questions selected: {[q['number'] for q in quizzes]}")
        
        print(f"\n⏰ Using Telegram Native Scheduling")
        print(f"📅 Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Delay: {delay_minutes} minute(s) between quizzes")
        print(f"👥 Target groups: {len(chat_ids)}")
        print(f"📊 Total quizzes: {len(quizzes)}")
        print("─" * 50)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Schedule each quiz
            for idx, quiz in enumerate(quizzes):
                # Calculate send time for this quiz
                send_time = start_time + timedelta(minutes=idx * delay_minutes)
                
                # Convert to Unix timestamp (Telegram requirement)
                unix_timestamp = int(send_time.timestamp())
                
                current_unix = int(datetime.now().timestamp())
                
                # Send to all groups
                for chat_id in chat_ids:
                    try:
                        # Prepare the poll data
                        payload = {
                            'chat_id': chat_id,
                            'question': quiz['question'],
                            'options': quiz['options'],
                            'type': 'quiz',
                            'correct_option_id': quiz['correct_option_id'],
                            'is_anonymous': is_anonymous,
                        }
                        
                        # Add optional fields
                        if explanation:
                            payload['explanation'] = explanation[:200]
                        
                        if open_period >= 5:
                            payload['open_period'] = open_period
                        
                        # Send to Telegram
                        response = await client.post(
                            f"{self.base_url}/sendPoll",
                            json=payload
                        )
                        
                        result = response.json()
                        
                        if result.get('ok'):
                            if unix_timestamp > current_unix:
                                print(f"✅ Q{quiz['number']} → {chat_id}: Scheduled for {send_time.strftime('%Y-%m-%d %H:%M:%S')}")
                            else:
                                print(f"✅ Q{quiz['number']} → {chat_id}: Sent immediately")
                        else:
                            print(f"❌ Q{quiz['number']} → {chat_id}: {result.get('description', 'Unknown error')}")
                    
                    except Exception as e:
                        print(f"❌ Q{quiz['number']} → {chat_id}: {str(e)}")
                
                # Small delay between API calls
                await asyncio.sleep(0.5)
        
        print("─" * 50)
        print("🎉 All quizzes have been sent!")
        print("📱 Check 'Scheduled Messages' in your Telegram groups")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Schedule Telegram quizzes using native Telegram scheduling',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python telegram_native_scheduler.py --token YOUR_BOT_TOKEN --file quiz.docx --chat 123456789 --time "2024-05-20 10:00"
  
  # Random 5 questions
  python telegram_native_scheduler.py --token YOUR_BOT_TOKEN --file quiz.docx --chat 123456789 --time "10:00" --random 5
  
  # Random 3 questions with seed (reproducible)
  python telegram_native_scheduler.py --token YOUR_BOT_TOKEN --file quiz.docx --chat 123456789 --time "10:00" --random 3 --seed 42
  
  # Multiple groups with random questions
  python telegram_native_scheduler.py --token YOUR_BOT_TOKEN --file quiz.docx --chat 123456789 --chat 987654321 --time "10:00" --random 5 --delay 2
  
  # With explanation
  python telegram_native_scheduler.py --token YOUR_BOT_TOKEN --file quiz.docx --chat 123456789 --time "10:30" --explanation "Check the answer" --random 10
        """
    )
    
    parser.add_argument('--token', required=True, help='Telegram Bot Token')
    parser.add_argument('--file', required=True, help='DOCX file with quizzes')
    parser.add_argument('--chat', type=int, action='append', required=True, dest='chats', help='Chat ID (can be used multiple times)')
    parser.add_argument('--time', required=True, help='Start time (format: YYYY-MM-DD HH:MM or "HH:MM" for today)')
    parser.add_argument('--delay', type=int, default=1, help='Delay in minutes between quizzes (default: 1)')
    parser.add_argument('--explanation', default='', help='Common explanation for wrong answers')
    parser.add_argument('--anonymous', action='store_true', default=True, help='Anonymous voting (default: True)')
    parser.add_argument('--open-period', type=int, default=30, help='Auto-close poll after N seconds (default: 30)')
    parser.add_argument('--random', type=int, help='Select random N questions from document')
    parser.add_argument('--seed', type=int, help='Seed for random selection (for reproducibility)')
    
    args = parser.parse_args()
    
    # Parse time
    try:
        if ' ' in args.time:
            # Full datetime provided
            start_time = datetime.strptime(args.time, '%Y-%m-%d %H:%M')
        else:
            # Only time provided, use today
            today = datetime.now().date()
            time_part = datetime.strptime(args.time, '%H:%M').time()
            start_time = datetime.combine(today, time_part)
    except ValueError:
        print("❌ Invalid time format. Use 'YYYY-MM-DD HH:MM' or 'HH:MM'")
        return
    
    # Validate file exists
    if not os.path.exists(args.file):
        print(f"❌ File not found: {args.file}")
        return
    
    # Initialize scheduler
    scheduler = TelegramNativeScheduler(args.token)
    
    # Extract quizzes
    quizzes = await scheduler.extract_quizzes_from_docx(args.file)
    
    if not quizzes:
        print("❌ No valid quizzes found")
        return
    
    # Schedule quizzes
    await scheduler.schedule_quizzes(
        quizzes=quizzes,
        chat_ids=args.chats,
        start_time=start_time,
        delay_minutes=args.delay,
        explanation=args.explanation,
        is_anonymous=args.anonymous,
        open_period=args.open_period,
        random_count=args.random,
        random_seed=args.seed
    )


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Scheduler stopped by user")
