from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import StringProperty, BooleanProperty
import datetime
import webbrowser
import speech_recognition as sr
import pyttsx3
import threading
import time

class FridayAssistantApp(App):
    def build(self):
        self.title = "Friday Assistant"
        Window.size = (400, 700)
        self.icon = 'F.R.I.D.A.Y.png'
        
        # تنظیمات صدای زنانه
        self.setup_voice()
        
        # تشخیص صدا
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()
        self.listening = True
        
        # مخاطبین
        self.contacts = {
            "fadakar": "09302645236",
            "farzad": "09906203907",
            "salar": "09386943161",
            "hossein": "09379695344"
        }
        
        # دستورات
        self.commands = {
            "hello friday": "Hello sir, how can I help you today?",
            "how are you": "I feel great. What about you?",
            "i am fine thank you": "That's lovely to hear.",
            "what is your name": "My name is Friday, your intelligent assistant.",
            "who made you": "I was created by the genius Armin Arbshahi.",
            "open google": ("Opening Google...", "https://www.google.com"),
            "open youtube": ("Opening YouTube...", "https://www.youtube.com"),
            "open chatgpt": ("Opening ChatGPT...", "https://chatgpt.com"),
            "what time is it": lambda: f"The time is {datetime.datetime.now().strftime('%H:%M')}",
            "what date today": lambda: f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}",
            "what is the capital of iran": "Tehran is the capital of Iran.",
            "tell me a joke": "Why did the robot go on a diet? Because he had too many bytes!",
            "what is python": "Python is a smart programming language used by awesome people like you.",
            "thank you": "You're welcome, dear.",
            "who is armin": "He is my boss and I like him.",
            "armin": "I am not Mr. Armin. Do you want to message him?",
            "my name is armin": "Hello Mr. Armin, how are you?",
            "i am good": "That's good to hear",
            "what can you do": "For now I can execute simple commands. Maybe I'll improve in the future.",
            "hello": "Hello, what is your name?",
            "my name is mahsa": "Hello Mahsa, how are you?",
            "i am fine": "That's lovely to hear.",
            "my name is farzad": "Hello Farzad, how are you?",
            "my name is salar": "Hello Salar, how are you man?",
            "my name is raha": "Hello Raha, how are you?",
            "my name is hossein": "Hello Hossein, how are you bro?",
            "my name is maedeh": "Hello Maedeh, how are you?",
            "my name is fadakar": "Hello Fadakar, how are you?",
            "my name is shahab": "Hello Shahab, how are you?",
            "can you hack someone": "If you are Mr. Armin, yes I can do it for you",
            "my name is safora": "Hello safora, how are you?",
        }
        
        # رابط کاربری
        self.setup_ui()
        
        # شروع گوش دادن
        self.start_listening_thread()
        
        return self.main_layout
    
    def setup_voice(self):
        """تنظیم صدای زنانه برای دستیار"""
        try:
            # اول سعی می‌کنیم از TTS اندروید استفاده کنیم
            from android.tts import TTS
            self.android_tts = TTS()
            self.use_android_tts = True
            self.android_tts.setLanguage('en')  # یا 'fa' برای فارسی
        except:
            # اگر در اندروید نبود، از pyttsx3 استفاده می‌کنیم
            self.use_android_tts = False
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 130)
            self.engine.setProperty('volume', 1.0)
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
    
    def setup_ui(self):
        """تنظیم رابط کاربری"""
        self.main_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # هدر
        self.header = Label(
            text="Friday Assistant",
            font_size='24sp',
            size_hint=(1, 0.1),
            color=(1, 0.4, 0.7, 1)
        self.main_layout.add_widget(self.header)
        
        # آیکون میکروفون
        self.mic_icon = Label(
            text="🎙️",
            font_size='60sp',
            size_hint=(1, 0.2)
        self.main_layout.add_widget(self.mic_icon)
        
        # وضعیت
        self.status_label = Label(
            text="💗 Friday is listening...",
            font_size='18sp',
            size_hint=(1, 0.1),
            color=(1, 0.7, 0.8, 1))
        self.main_layout.add_widget(self.status_label)
        
        # دکمه میکروفون
        self.mic_button = Button(
            text="Disable Microphone",
            size_hint=(1, 0.1),
            background_color=(1, 0.4, 0.7, 1),
            background_normal='',
            on_press=self.toggle_microphone)
        self.main_layout.add_widget(self.mic_button)
        
        # لاگ فعالیت‌ها
        self.log_label = Label(
            text="Activity Log:",
            font_size='16sp',
            size_hint=(1, 0.05),
            color=(1, 0.7, 0.8, 1),
            halign='left')
        self.main_layout.add_widget(self.log_label)
        
        # ناحیه اسکرول لاگ
        scroll_view = ScrollView(size_hint=(1, 0.45))
        self.log_area = TextInput(
            text="",
            font_size='14sp',
            size_hint=(1, None),
            readonly=True,
            background_color=(0.2, 0.2, 0.2, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 1))
        self.log_area.height = 500
        scroll_view.add_widget(self.log_area)
        self.main_layout.add_widget(scroll_view)
        
        # وضعیت سیستم
        self.system_status = Label(
            text="System: Ready | Microphone: Active",
            font_size='14sp',
            size_hint=(1, 0.05),
            color=(0.7, 0.7, 0.7, 1))
        self.main_layout.add_widget(self.system_status)
    
    def toggle_microphone(self, instance):
        """تغییر وضعیت میکروفون"""
        self.listening = not self.listening
        self.update_mic_status()
    
    def update_mic_status(self):
        """به‌روزرسانی وضعیت میکروفون در UI"""
        if self.listening:
            self.mic_button.text = "Disable Microphone"
            self.mic_button.background_color = (1, 0.4, 0.7, 1)
            self.status_label.text = "💗 Friday is listening..."
            self.system_status.text = "System: Ready | Microphone: Active"
            self.add_to_log("Microphone enabled")
        else:
            self.mic_button.text = "Enable Microphone"
            self.mic_button.background_color = (0.3, 0.8, 0.3, 1)
            self.status_label.text = "🔇 Microphone disabled"
            self.system_status.text = "System: Ready | Microphone: Disabled"
            self.add_to_log("Microphone disabled")
    
    def add_to_log(self, message):
        """اضافه کردن پیام به لاگ"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_area.text += f"[{timestamp}] {message}\n"
        self.log_area.cursor = (0, len(self.log_area.text))
    
    def update_status(self, message):
        """به‌روزرسانی وضعیت"""
        self.status_label.text = message
        self.add_to_log(message)
    
    def speak(self, text):
        """صحبت کردن با صدای زنانه"""
        try:
            if hasattr(self, 'use_android_tts') and self.use_android_tts:
                self.android_tts.speak(text)
            else:
                self.engine.say(text)
                self.engine.runAndWait()
        except Exception as e:
            self.add_to_log(f"Speech error: {str(e)}")
    
    def process_command(self, command):
        """پردازش دستورات"""
        command = command.lower().strip()
        if command in self.commands:
            response = self.commands[command]
            if isinstance(response, tuple):
                return {"type": "action", "message": response[0], "url": response[1]}
            elif callable(response):
                return {"type": "response", "message": response()}
            else:
                return {"type": "response", "message": response}
        elif command.startswith("call "):
            name = command[5:].strip()
            number = self.contacts.get(name.lower(), None)
            if number:
                return {"type": "call", "name": name, "number": number}
            else:
                return {"type": "error", "message": f"Contact '{name}' not found"}
        else:
            return {"type": "ignore", "message": f"Ignored command: {command}"}
    
    def handle_command_result(self, result):
        """مدیریت نتایج دستورات"""
        self.update_status(result["message"])
        
        if result["type"] == "action":
            self.speak(result["message"])
            webbrowser.open(result["url"])
        elif result["type"] == "response":
            self.speak(result["message"])
        elif result["type"] == "call":
            self.speak(f"Calling {result['name']}...")
            webbrowser.open(f"tel:{result['number']}")
    
    def listen_loop(self):
        """حلقه اصلی گوش دادن به صدا"""
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source)
        
        while True:
            if self.listening:
                try:
                    with self.mic as source:
                        audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=5)
                    
                    command = self.recognizer.recognize_google(audio)
                    result = self.process_command(command)
                    Clock.schedule_once(lambda dt: self.handle_command_result(result))
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    continue
                except sr.RequestError:
                    Clock.schedule_once(lambda dt: self.update_status("Error: Internet connection issue"))
                except Exception as e:
                    Clock.schedule_once(lambda dt: self.update_status(f"Error: {str(e)}"))
            time.sleep(0.1)
    
    def start_listening_thread(self):
        """شروع ریسه گوش دادن"""
        thread = threading.Thread(target=self.listen_loop, daemon=True)
        thread.start()

if __name__ == "__main__":
    FridayAssistantApp().run()