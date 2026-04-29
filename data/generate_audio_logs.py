import os
import sqlite3
from gtts import gTTS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, 'audio')

if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

# Synthetic Support Calls
# We will generate these with gTTS. While gTTS sounds robotic, it's sufficient 
# for a hackathon proof-of-concept of Audio RAG to prove we can pass .mp3 to Gemini.
calls = {
    "angry": "This is ridiculous! I have been overcharged on my internet bill for three months in a row. I have called you people five times and nothing gets fixed. If you don't fix this today, I am canceling my service immediately. It's completely unacceptable!",
    "sarcastic": "Oh, wonderful. My fiber optic connection dropped right in the middle of my presentation. Again. I just love paying premium prices for a service that works half the time. It's truly a fantastic experience. Please, take your time fixing it.",
    "neutral": "Hi, I am just calling to check if my recent payment went through. I set up autopay last week but I haven't received a confirmation email yet. Can you please verify my account status? Thank you."
}

def generate_audio():
    # Generate MP3s
    files = {}
    for tone, text in calls.items():
        print(f"Generating {tone} call...")
        tts = gTTS(text=text, lang='en', slow=False)
        filename = f"{tone}_call.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)
        tts.save(filepath)
        files[tone] = filepath
    return files

def map_to_customers(files):
    # Map these to the first few customers in the mock CRM
    db_path = os.path.join(BASE_DIR, 'mock_crm.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get first 3 customers
    cursor.execute("SELECT customer_id FROM customers LIMIT 3")
    rows = cursor.fetchall()
    
    if len(rows) < 3:
        print("Not enough customers to map audio.")
        return
        
    mappings = {
        rows[0][0]: files['angry'],
        rows[1][0]: files['sarcastic'],
        rows[2][0]: files['neutral']
    }
    
    # Create or replace audio mappings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS support_audio (
        customer_id INTEGER PRIMARY KEY,
        audio_path TEXT
    )
    ''')
    
    for customer_id, path in mappings.items():
        cursor.execute("INSERT OR REPLACE INTO support_audio (customer_id, audio_path) VALUES (?, ?)", (customer_id, path))
        
    conn.commit()
    conn.close()
    print("Mapped audio files to customers in the database.")

if __name__ == "__main__":
    generated_files = generate_audio()
    map_to_customers(generated_files)
    print("Audio generation complete.")
