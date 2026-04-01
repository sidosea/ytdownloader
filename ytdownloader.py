import os
import threading
import tkinter.messagebox as messagebox
import customtkinter as ctk
import yt_dlp

# Set modern appearance
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class YTDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("유튜브 다운로더 (YouTube Downloader)")
        self.geometry("600x450")
        self.resizable(False, False)

        # Title Label
        self.title_label = ctk.CTkLabel(
            self, 
            text="🎥 유튜브 영상/음원 다운로더", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=(30, 20))

        # URL Input
        self.url_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.url_frame.pack(fill="x", padx=40, pady=10)
        
        self.url_label = ctk.CTkLabel(self.url_frame, text="동영상 URL:", font=ctk.CTkFont(size=14))
        self.url_label.pack(side="left", padx=(0, 10))
        
        self.url_entry = ctk.CTkEntry(
            self.url_frame, 
            placeholder_text="https://www.youtube.com/watch?v=...", 
            width=380
        )
        self.url_entry.pack(side="left", fill="x", expand=True)

        # Format Selection
        self.format_var = ctk.StringVar(value="video")
        
        self.radio_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.radio_frame.pack(pady=20)
        
        self.video_radio = ctk.CTkRadioButton(
            self.radio_frame, 
            text="동영상 (MP4 최고화질)", 
            variable=self.format_var, 
            value="video"
        )
        self.video_radio.pack(side="left", padx=20)
        
        self.audio_radio = ctk.CTkRadioButton(
            self.radio_frame, 
            text="음원 (MP3 축출)", 
            variable=self.format_var, 
            value="audio"
        )
        self.audio_radio.pack(side="left", padx=20)

        # Download Button
        self.download_btn = ctk.CTkButton(
            self, 
            text="다운로드 시작", 
            font=ctk.CTkFont(size=16, weight="bold"),
            height=40,
            command=self.start_download_thread
        )
        self.download_btn.pack(pady=20)

        # Status Label
        self.status_label = ctk.CTkLabel(
            self, 
            text="대기 중...", 
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        self.status_label.pack(pady=10)

    def start_download_thread(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("입력 오류", "유튜브 URL을 입력해주세요.")
            return

        # UI 업데이트: 다운로드 중 상태로 변경
        self.download_btn.configure(state="disabled", text="다운로드 진행 중...")
        self.status_label.configure(text="다운로드 중입니다. 완료될 때까지 잠시만 기다려주세요...", text_color="#f39c12")
        self.url_entry.configure(state="disabled")
        self.video_radio.configure(state="disabled")
        self.audio_radio.configure(state="disabled")

        format_choice = self.format_var.get()

        # 별도 스레드에서 다운로드 실행 (GUI 멈춤 방지)
        thread = threading.Thread(target=self.download_video, args=(url, format_choice))
        thread.daemon = True
        thread.start()

    def download_video(self, url, format_choice):
        # 기본 다운로드 경로를 사용자의 Downloads 폴더로 설정
        download_path = os.path.join(os.path.expanduser('~'), 'Downloads')
        
        ydl_opts = {
            'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }

        # 포맷 옵션 설정
        if format_choice == "audio":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            ydl_opts.update({
                # 비디오와 오디오를 합친 mp4 제공 (ffmpeg 필요할 수 있음)
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            })

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # 다운로드 성공 시 메인 스레드에서 UI 업데이트
            self.after(0, self.on_download_success, download_path)
            
        except Exception as e:
            error_msg = str(e)
            # 다운로드 실패 시 메인 스레드에서 UI 업데이트
            self.after(0, self.on_download_error, error_msg)

    def reset_ui(self):
        self.download_btn.configure(state="normal", text="다운로드 시작")
        self.url_entry.configure(state="normal")
        self.video_radio.configure(state="normal")
        self.audio_radio.configure(state="normal")
        self.url_entry.delete(0, 'end')

    def on_download_success(self, download_path):
        self.reset_ui()
        self.status_label.configure(text=f"다운로드 완료! 경로: {download_path}", text_color="#27ae60")
        messagebox.showinfo("완료", f"성공적으로 다운로드되었습니다.\n저장 위치: {download_path}")

    def on_download_error(self, error_msg):
        self.reset_ui()
        self.status_label.configure(text="다운로드 실패", text_color="#e74c3c")
        
        # ffmpeg 관련 에러인 경우 사용자 친화적 메시지 추가
        if "ffmpeg" in error_msg.lower() or "ffprobe" in error_msg.lower():
            extra_msg = "\n\n💡 참고: 고화질 영상 또는 MP3 변환을 위해서는 컴퓨터에 'ffmpeg'가 설치되어 있어야 합니다."
        else:
            extra_msg = ""
            
        messagebox.showerror("오류", f"다운로드 중 문제가 발생했습니다:\n{error_msg}{extra_msg}")

if __name__ == "__main__":
    app = YTDownloaderApp()
    app.mainloop()
