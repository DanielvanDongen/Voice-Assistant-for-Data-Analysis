import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
from PIL import Image, ImageTk
import speech_recognition as sr
from openai import OpenAI
import time
import threading
import io

# Start OpenAI client
client = OpenAI()

r = sr.Recognizer()
is_recording = False
recorded_text = ""
ID_assistant = ""
assistant = None  

def create_assistant():
    global assistant

    # Select a CSV file
    file_path = filedialog.askopenfilename(
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    
    if not file_path:
        messagebox.showwarning("No file selected", "Please select a CSV file to create the assistant.")
        return

    try:
        # Upload the selected file 
        file = client.files.create(
            file=open(file_path, "rb"),
            purpose='assistants'
        )

        # Create an assistant using the file ID + instructions
        assistant = client.beta.assistants.create(
            instructions="As a Data Analyst, your role is to load and explore Excel/CSV files and perform analysis through descriptive statistics, trends, and correlations. Generate relevant visualizations like bar charts, line charts, and scatter plots, and interpret them for the user. Compile these findings into a clear and concise report, incorporating both text and charts. Always give one Text and Diagram",
            model="gpt-4o-mini",
            tools=[{"type": "code_interpreter"}],
            tool_resources={
                "code_interpreter": {
                    "file_ids": [file.id]
                }
            }
        )
        global ID_assistant
        ID_assistant = assistant.id
        messagebox.showinfo("Assistant Created", f"Assistant created successfully with ID: {ID_assistant}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while creating the assistant: {e}")

def record_text():
    global is_recording, recorded_text
    while is_recording:
        try:
            with sr.Microphone() as source2:
                r.adjust_for_ambient_noise(source2, duration=0.2)
                audio2 = r.listen(source2)
                MyText = r.recognize_google(audio2)
                MyText = MyText.lower()
                recorded_text += MyText + "\n"
                output_text(MyText)
        except sr.RequestError as e:
            output_text(f"Could not request results; {0}".format(e))

def output_text(text):
    text_display.insert(tk.END, text + "\n")
    text_display.see(tk.END)

def start_recording():
    global is_recording
    is_recording = True
    start_button.config(state=tk.DISABLED)
    stop_button.config(state=tk.NORMAL)
    restart_button.config(state=tk.DISABLED)
    threading.Thread(target=record_text).start()

def stop_recording():
    global is_recording
    is_recording = False
    stop_button.config(state=tk.DISABLED)
    restart_button.config(state=tk.NORMAL)
    loading_label.place(x=270, y=450)
    threading.Thread(target=process_openai_request).start()

def restart_program():
    global recorded_text, is_recording
    recorded_text = ""
    is_recording = False  
    text_display.delete(1.0, tk.END)
    image_label.config(image='')
    start_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)
    restart_button.config(state=tk.DISABLED)

def download_image():
    if hasattr(image_label, 'image') and image_label.image:
        file_path = filedialog.asksaveasfilename(defaultextension=".png",
        filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
        if file_path:
            # Convert PhotoImage back to PIL Image
            img = ImageTk.getimage(image_label.image)
            img.save(file_path)
            messagebox.showinfo("Download", "Image saved successfully!")
    else:
        messagebox.showwarning("Download", "No image to save.")

def process_openai_request():
    global recorded_text

    chat = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": recorded_text,
            }
        ]
    )

    run = client.beta.threads.runs.create(thread_id=chat.id, assistant_id=ID_assistant)
    while run.status != "completed":
        run = client.beta.threads.runs.retrieve(thread_id=chat.id, run_id=run.id)
        time.sleep(0.5)

    loading_label.place_forget()  
    message_response = client.beta.threads.messages.list(thread_id=chat.id)
    messages = message_response.data
    latest_message = messages[0]

    text_display.insert(tk.END, "\nAI Response:\n" + latest_message.content[1].text.value + "\n")

    image_data = client.files.content(latest_message.content[0].image_file.file_id)
    image_data_bytes = image_data.read()

    # Display the image directly from bytes in tkinter
    img = Image.open(io.BytesIO(image_data_bytes))
    
    # Resize the image to fit within the window
    max_width, max_height = 500, 300  
    img.thumbnail((max_width, max_height), Image.LANCZOS)
    
    img_tk = ImageTk.PhotoImage(img)
    image_label.config(image=img_tk)
    image_label.image = img_tk 

    restart_button.config(state=tk.NORMAL)

# GUI Setup
window = tk.Tk()
window.title("Voice User Interface")
window.geometry("600x650")
window.configure(bg="#1a1a2e") 

# Header Label
header_label = tk.Label(window, text="Voice User Interface", font=("Helvetica", 24, "bold"), fg="#f8f8f2", bg="#1a1a2e")
header_label.pack(pady=20)

# Create Assistant Button
create_assistant_button = tk.Button(window, text="🆕 Create Assistant", command=create_assistant, font=("Helvetica", 16), bg="#3a3d5c", fg="#f8f8f2", activebackground="#4e517d", activeforeground="#f8f8f2")
create_assistant_button.pack(pady=10)

# Start and Stop Buttons
start_button = tk.Button(window, text="🎤 Start", command=start_recording, font=("Helvetica", 16), bg="#3a3d5c", fg="#f8f8f2", activebackground="#4e517d", activeforeground="#f8f8f2")
start_button.pack(pady=10)

stop_button = tk.Button(window, text="🛑 Stop", command=stop_recording, font=("Helvetica", 16), bg="#3a3d5c", fg="#f8f8f2", activebackground="#4e517d", activeforeground="#f8f8f2")
stop_button.pack(pady=10)
stop_button.config(state=tk.DISABLED)

# Restart Button
restart_button = tk.Button(window, text="🔄 Restart", command=restart_program, font=("Helvetica", 16), bg="#3a3d5c", fg="#f8f8f2", activebackground="#4e517d", activeforeground="#f8f8f2")
restart_button.pack(pady=10)
restart_button.config(state=tk.DISABLED)

# Download Button
download_image_button = tk.Button(window, text="💾 Download Image", command=download_image, font=("Helvetica", 16), bg="#3a3d5c", fg="#f8f8f2", activebackground="#4e517d", activeforeground="#f8f8f2")
download_image_button.pack(pady=10)

# Text Display
text_display = scrolledtext.ScrolledText(window, wrap=tk.WORD, width=60, height=15, font=("Helvetica", 14), fg="#f8f8f2", bg="#0f0f1e")
text_display.pack(pady=20)

# Image Display
image_label = tk.Label(window, bg="#1a1a2e")
image_label.pack(pady=10)

# Loading Label
loading_label = tk.Label(window, text="⏳ Processing...", font=("Helvetica", 16), fg="#f8f8f2", bg="#1a1a2e")

window.mainloop()
