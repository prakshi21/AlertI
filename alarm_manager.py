"""
alarm_manager.py - Manages the audible alarm and text-to-speech warnings.
"""

import os
import wave
import math
import struct
import threading
import time
import winsound
import win32com.client
import config

class AlarmManager:
    def __init__(self):
        self.sound_path = config.ALARM_SOUND_PATH
        self.is_alarm_playing = False
        self.tts_enabled = config.TTS_ENABLED
        self.last_speech_time = 0.0
        self.speech_cooldown = 4.0  # Seconds between TTS announcements
        self.tts_thread = None
        self.tts_lock = threading.Lock()
        
        # Ensure the alarm sound file exists
        self.ensure_alarm_file()

    def ensure_alarm_file(self):
        """Generates a loud sine wave beep if it does not already exist."""
        if os.path.exists(self.sound_path):
            return
            
        print(f"Generating default alarm sound: {self.sound_path}...")
        
        sample_rate = 44100
        frequency = config.ALARM_FREQUENCY
        duration = config.ALARM_DURATION_SEC
        amplitude = 30000  # Loud volume (max is 32767 for 16-bit audio)
        
        # Calculate samples
        num_samples = int(sample_rate * duration)
        data = bytearray()
        
        for i in range(num_samples):
            # Calculate sine wave sample value
            t = float(i) / sample_rate
            value = int(amplitude * math.sin(2 * math.pi * frequency * t))
            
            # Pack value as 16-bit signed integer (little-endian)
            data.extend(struct.pack('<h', value))
            
        # Write to wave file
        with wave.open(self.sound_path, 'wb') as wav_file:
            wav_file.setnchannels(1)      # Mono
            wav_file.setsampwidth(2)      # 2 bytes (16-bit)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(data)
            
        print("Alarm sound generated successfully.")

    def trigger_alarm(self):
        """Starts the audible loop alarm if not already playing."""
        if not self.is_alarm_playing:
            try:
                # Play loop alarm asynchronously
                winsound.PlaySound(
                    self.sound_path, 
                    winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP
                )
                self.is_alarm_playing = True
                print("Audible alarm triggered.")
            except Exception as e:
                print(f"Error playing alarm via winsound: {e}")
                # Fallback to simple Beep
                winsound.Beep(config.ALARM_FREQUENCY, 1000)

        # Trigger TTS alert if enabled and not cooling down
        if self.tts_enabled:
            self.speak_warning_async("Warning! Drowsiness detected. Please wake up!")

    def stop_alarm(self):
        """Stops the audible alarm if it is currently playing."""
        if self.is_alarm_playing:
            try:
                # Purge all playing sounds
                winsound.PlaySound(None, winsound.SND_PURGE)
                self.is_alarm_playing = False
                print("Audible alarm stopped.")
            except Exception as e:
                print(f"Error stopping alarm via winsound: {e}")
                self.is_alarm_playing = False

    def speak_warning_async(self, text):
        """Speaks a warning string asynchronously on a separate thread if cooldown has passed."""
        current_time = time.time()
        
        # Check if TTS is already speaking or cooling down
        with self.tts_lock:
            if current_time - self.last_speech_time < self.speech_cooldown:
                return
            
            # Update last speech time to prevent overlapping speaks
            self.last_speech_time = current_time

        # Start thread to say the warning message
        self.tts_thread = threading.Thread(target=self._speak, args=(text,), daemon=True)
        self.tts_thread.start()

    def _speak(self, text):
        """Worker function that runs on a separate thread to handle Windows TTS."""
        try:
            # Initialize COM in the worker thread (necessary for SAPI5 in threads)
            import pythoncom
            pythoncom.CoInitialize()
            
            # Dispatch SAPI voice object
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            speaker.Speak(text)
            
            # Clean up COM
            pythoncom.CoUninitialize()
        except Exception as e:
            print(f"Error in TTS warning thread: {e}")
            
    def cleanup(self):
        """Stop any active alarm sound."""
        self.stop_alarm()
