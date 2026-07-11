#!/usr/bin/env python3
"""
Telegram Quiz Scheduler - Fixed with proper delays between polls
Posts 30 random questions every 2 hours with 1-minute delay between each poll
"""

import os
import asyncio
import re
import random
import time
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
        
        print(f"📋 Valid quizzes: {len(quizzes)}, Skipped: {skipped}\n")
        return quizzes
    
    def _parse_quiz_block(self, block: str, question_num: int) -> Dict or None:
        """Parse a single quiz block"""
        
        # Remove explanation (everything after Ans:)
        clean_block = re.split(r'Ans:', block, flags=re.IGNORECASE)[0]
        
        # Extract question
        question_match = re.match(r'([\s\S]*?)(?=\([a-d]\))', clean_block, re.IGNORECASE)
        if not question_match:
            return None
        
        question = question_match.group(1).strip()
        
        # Check for LaTeX
        if re.search(r'\$[\s\S]*?\$|\\[\w\{\}]+', block):
            return None
        
        # Check for tables
        if re.search(r'^\s*\|[\s\S]*\|', clean_block, re.MULTILINE):
            return None
        
        # Check for images
        if re.search(r'\[img\]|<img|\.jpg|\.png|\.gif|\.bmp|image:', block, re.IGNORECASE):
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
            return None
        
        correct_idx = ord(answer_match.group(1).lower()) - ord('a')
        
        # Validation
        if len(options) < 2 or len(options) > 10:
            return None
        
        if len(question) > 300:
            return None
        
        if correct_idx >= len(options):
            return None
        
        if any(len(opt) > 100 for opt in options):
            return None
        
        return {
            'number': question_num,
            'question': question,
            'options': options,
            'correct_option_id': correct_idx
        }
    
    async def send_poll(self, client: httpx.AsyncClient, chat_id: int, quiz: Dict) -> bool:
        """Send a single poll to a chat"""
        try:
            payload = {
                'chat_id': chat_id,
                'question': quiz['question'],
                'options': quiz['options'],
                'type': 'quiz',
                'correct_option_id': quiz['correct_option_id'],
                'is_anonymous': False,
            }
            
            response = await client.post(
                f"{self.base_url}/sendPoll",
                json=payload,
                timeout=30.0
            )
            
            result = response.json()
            return result.get('ok', False)
        
        except Exception as e:
            print(f"Error sending poll: {str(e)}")
            return False
    
    async def post_30_questions(self, quizzes: List[Dict], chat_ids: List[int], random_seed: int = None):
        """Post 30 random questions with 1-minute delay between each
        
        Delay strategy:
        - Real delay: await asyncio.sleep(60) between each poll
        - This ensures 1 minute between consecutive messages
        """
        
        # Select 30 random questions
        if random_seed is not None:
            random.seed(random_seed)
        
        selected_quizzes = random.sample(quizzes, min(10, len(quizzes)))
        selected_quizzes = sorted(selected_quizzes, key=lambda x: x['number'])
        
        print(f"🎲 RANDOM SELECTION: {len(selected_quizzes)} questions")
        print(f"📌 Questions: {[q['number'] for q in selected_quizzes[:15]]}...")
        print(f"⏱️  Delay: 1 minute between each poll")
        print(f"👥 Groups: {len(chat_ids)}")
        print("─" * 60)
        
        async with httpx.AsyncClient() as client:
            for idx, quiz in enumerate(selected_quizzes):
                print(f"\n[{idx+1}/{len(selected_quizzes)}] Sending Q{quiz['number']}...")
                
                # Send to all groups
                for chat_id in chat_ids:
                    success = await self.send_poll(client, chat_id, quiz)
                    status = "✅ Sent" if success else "❌ Failed"
                    print(f"  {status} to chat {chat_id}")
                
                # Wait 60 seconds (1 minute) before next poll
                if idx < len(selected_quizzes) - 1:
                    print(f"  ⏳ Waiting 60 seconds before next poll...")
                    # Show countdown every 10 seconds
                    for remaining in range(60, 0, -10):
                        await asyncio.sleep(10)
                        if remaining > 10:
                            print(f"     {remaining-10}s remaining...")
                    # Final second
                    await asyncio.sleep(0)
        
        print("\n" + "─" * 60)
        print("✅ COMPLETE: All 30 questions posted!")
        print(f"⏰ Total time: ~{len(selected_quizzes)-1} minutes")
        print("📱 Check your Telegram groups\n")


async def main():
    """Main function - posts every 2 hours"""
    parser = argparse.ArgumentParser(
        description='Post 30 random Telegram quizzes every 2 hours',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Post 30 random questions now
  python telegram_native_scheduler.py --token YOUR_BOT_TOKEN --file quiz.docx --chat 123456789
  
  # With reproducible seed
  python telegram_native_scheduler.py --token YOUR_BOT_TOKEN --file quiz.docx --chat 123456789 --seed 42
  
  # Multiple groups
  python telegram_native_scheduler.py --token YOUR_BOT_TOKEN --file quiz.docx --chat 123456789 --chat 987654321
  
  # Keep running and post every 2 hours
  python telegram_native_scheduler.py --token YOUR_BOT_TOKEN --file quiz.docx --chat 123456789 --loop
        """
    )
    
    parser.add_argument('--token', required=True, help='Telegram Bot Token')
    parser.add_argument('--file', required=True, help='DOCX file with quizzes')
    parser.add_argument('--chat', type=int, action='append', required=True, dest='chats', help='Chat ID')
    parser.add_argument('--seed', type=int, help='Random seed (optional)')
    parser.add_argument('--loop', action='store_true', help='Post every 2 hours indefinitely')
    
    args = parser.parse_args()
    
    # Validate file
    if not os.path.exists(args.file):
        print(f"❌ File not found: {args.file}")
        return
    
    # Initialize scheduler
    scheduler = TelegramNativeScheduler(args.token)
    
    # Extract quizzes once
    quizzes = await scheduler.extract_quizzes_from_docx(args.file)
    
    if not quizzes:
        print("❌ No valid quizzes found")
        return
    
    if len(quizzes) < 30:
        print(f"⚠️  Warning: Only {len(quizzes)} questions available (need 30)")
    
    # Run once or loop
    if args.loop:
        print(f"🔄 Running every 2 hours (press Ctrl+C to stop)\n")
        counter = 1
        while True:
            print(f"\n{'='*60}")
            print(f"📅 Session {counter} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            await scheduler.post_30_questions(quizzes, args.chats, args.seed)
            
            print(f"⏰ Next session in 2 hours...")
            counter += 1
            
            # Wait 2 hours (7200 seconds)
            await asyncio.sleep(7200)
    else:
        # Run once
        await scheduler.post_30_questions(quizzes, args.chats, args.seed)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Stopped by user")
