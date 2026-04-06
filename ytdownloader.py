import os
import shutil
import threading
import webbrowser
import tkinter.messagebox as messagebox
import tkinter.filedialog as filedialog
import customtkinter as ctk
import yt_dlp

# 고화질 병합(MP4)·MP3 변환에 필요. Windows 사용자는 PATH에 ffmpeg.exe가 있어야 합니다.
FFMPEG_DOWNLOAD_URL = "https://ffmpeg.org/download.html"

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

        # Default download folder
        self.download_folder = os.path.join(os.path.expanduser('~'), 'Downloads')

        # Folder Selection
        self.folder_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.folder_frame.pack(fill="x", padx=40, pady=(10, 0))

        self.folder_label = ctk.CTkLabel(
            self.folder_frame,
            text=f"저장 폴더: {self.download_folder}",
            anchor="w",
            font=ctk.CTkFont(size=12)
        )
        self.folder_label.pack(side="left", fill="x", expand=True)

        self.choose_folder_btn = ctk.CTkButton(
            self.folder_frame,
            text="폴더 선택",
            font=ctk.CTkFont(size=12),
            width=110,
            command=self.choose_download_folder
        )
        self.choose_folder_btn.pack(side="left", padx=(10, 0))

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

        # Open Folder Button (disabled until download succeeds)
        self.open_folder_btn = ctk.CTkButton(
            self,
            text="다운로드 폴더 열기",
            font=ctk.CTkFont(size=14),
            height=35,
            state="disabled",
            command=self.open_download_folder
        )
        self.open_folder_btn.pack(pady=(0, 10))

        self.last_download_path = None

    @staticmethod
    def _ffmpeg_on_path():
        return shutil.which("ffmpeg") is not None

    def _offer_ffmpeg_download_page(self):
        if messagebox.askyesno(
            "FFmpeg 필요",
            "이 프로그램은 고화질 영상 병합(MP4)과 음원 MP3 변환에 FFmpeg가 필요합니다.\n"
            "현재 시스템 PATH에서 ffmpeg를 찾을 수 없습니다.\n\n"
            "FFmpeg 공식 다운로드 페이지를 브라우저에서 여시겠습니까?\n"
            "(설치 후 터미널에서 'ffmpeg -version'이 되도록 PATH를 설정해 주세요.)",
            icon="warning",
        ):
            webbrowser.open(FFMPEG_DOWNLOAD_URL)

    def start_download_thread(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("입력 오류", "유튜브 URL을 입력해주세요.")
            return

        if not self._ffmpeg_on_path():
            self._offer_ffmpeg_download_page()
            return

        # UI 업데이트: 다운로드 중 상태로 변경
        self.download_btn.configure(state="disabled", text="다운로드 진행 중...")
        self.status_label.configure(text="다운로드 중입니다. 완료될 때까지 잠시만 기다려주세요...", text_color="#f39c12")
        self.url_entry.configure(state="disabled")
        self.video_radio.configure(state="disabled")
        self.audio_radio.configure(state="disabled")
        self.choose_folder_btn.configure(state="disabled")

        format_choice = self.format_var.get()

        # 별도 스레드에서 다운로드 실행 (GUI 멈춤 방지)
        thread = threading.Thread(target=self.download_video, args=(url, format_choice))
        thread.daemon = True
        thread.start()

    def download_video(self, url, format_choice):
        # 사용자가 선택한 다운로드 경로를 사용
        download_path = self.download_folder
        
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
                # Shorts나 일부 영상에서 mp4 포맷이 없을 때도 자동으로 가장 좋은 영상/오디오를 선택
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
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
        self.choose_folder_btn.configure(state="normal")
        self.open_folder_btn.configure(state="disabled")
        self.url_entry.delete(0, 'end')

    def choose_download_folder(self):
        selected_folder = filedialog.askdirectory(initialdir=self.download_folder)
        if selected_folder:
            self.download_folder = selected_folder
            self.folder_label.configure(text=f"저장 폴더: {self.download_folder}")

    def open_download_folder(self):
        if self.last_download_path and os.path.isdir(self.last_download_path):
            try:
                os.startfile(self.last_download_path)
            except Exception as e:
                messagebox.showerror("오류", f"폴더를 열 수 없습니다:\n{e}")
        else:
            messagebox.showwarning("경고", "다운로드 폴더를 찾을 수 없습니다.")

    def on_download_success(self, download_path):
        self.last_download_path = download_path
        self.reset_ui()
        self.open_folder_btn.configure(state="normal")
        self.status_label.configure(text=f"다운로드 완료! 경로: {download_path}", text_color="#27ae60")
        messagebox.showinfo("완료", f"성공적으로 다운로드되었습니다.\n저장 위치: {download_path}")

    def on_download_error(self, error_msg):
        self.reset_ui()
        self.last_download_path = None
        self.status_label.configure(text="다운로드 실패", text_color="#e74c3c")

        lowered = error_msg.lower()
        ffmpeg_related = "ffmpeg" in lowered or "ffprobe" in lowered

        messagebox.showerror(
            "오류",
            f"다운로드 중 문제가 발생했습니다:\n{error_msg}"
            + (
                "\n\n💡 고화질 영상 병합 또는 MP3 변환에는 FFmpeg가 필요합니다."
                if ffmpeg_related
                else ""
            ),
        )

        if ffmpeg_related:
            if messagebox.askyesno(
                "FFmpeg 안내",
                "FFmpeg 설치·PATH 설정 안내를 위해 공식 다운로드 페이지를 브라우저에서 여시겠습니까?",
                icon="warning",
            ):
                webbrowser.open(FFMPEG_DOWNLOAD_URL)

if __name__ == "__main__":
    app = YTDownloaderApp()
    app.mainloop()
