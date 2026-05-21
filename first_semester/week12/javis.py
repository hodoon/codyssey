import os
import wave
from datetime import datetime

import pyaudio


class AudioRecorder:
    """
    음성 녹음을 담당하는 클래스입니다.
    기본 설정으로 청크 크기, 채널 수, 샘플링 레이트를 초기화합니다.
    """
    def __init__(self, chunk_size=1024, channels=1, rate=44100):
        self.chunk_size = chunk_size  # 한 번에 읽어들일 오디오 데이터의 크기 (프레임 수)
        self.audio_format = pyaudio.paInt16  # 16비트 포맷 사용
        self.channels = channels  # 1채널 (모노) 지원
        self.rate = rate  # 샘플링 레이트 (Hz)

    def record_audio(self, duration=5):
        """
        주어진 시간(초) 동안 마이크를 통해 음성을 녹음하고 파일로 저장합니다.
        """
        audio_interface = pyaudio.PyAudio()

        # 녹음을 위한 오디오 스트림 열기
        stream = audio_interface.open(
            format=self.audio_format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )

        print('Recording...')

        frames = []
        # 지정된 시간(duration) 동안 읽어들일 총 청크의 수 계산
        total_chunks = int(self.rate / self.chunk_size * duration)
        
        # 실제 오디오 데이터 읽기
        for _ in range(0, total_chunks):
            data = stream.read(self.chunk_size)
            frames.append(data)

        print('Finished recording.')

        # 스트림 정지 및 닫기, PyAudio 인스턴스 종료
        stream.stop_stream()
        stream.close()
        audio_interface.terminate()

        # 녹음된 데이터를 파일로 저장하는 내부 메서드 호출
        self._save_to_file(audio_interface, frames)

    def _save_to_file(self, audio_interface, frames):
        """
        녹음된 프레임 데이터를 .wav 파일로 저장합니다.
        파일 이름은 현재 시간을 기준으로 'YYYYMMDD-HHMMSS.wav' 형식으로 생성합니다.
        """
        target_dir = 'records'
        # 저장할 폴더가 없으면 생성
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        # 현재 시간을 구하고 요구사항에 맞는 형식의 파일명 생성
        current_time = datetime.now()
        file_name = current_time.strftime('%Y%m%d-%H%M%S') + '.wav'
        file_path = os.path.join(target_dir, file_name)

        # wave 모듈을 사용하여 파일 쓰기
        wave_file = wave.open(file_path, 'wb')
        wave_file.setnchannels(self.channels)
        wave_file.setsampwidth(audio_interface.get_sample_size(self.audio_format))
        wave_file.setframerate(self.rate)
        wave_file.writeframes(b''.join(frames))
        wave_file.close()

        print(f'Saved to {file_path}')


def find_records_in_range(start_date_str, end_date_str):
    """
    특정 날짜 범위 내에 생성된 녹음 파일 목록을 검색하여 출력합니다. (보너스 과제)
    start_date_str, end_date_str: 'YYYYMMDD' 형식의 문자열
    """
    target_dir = 'records'
    # 기록 폴더가 없는 경우
    if not os.path.exists(target_dir):
        print('No records found.')
        return

    # 날짜 문자열을 datetime 객체로 변환 시도
    try:
        start_date = datetime.strptime(start_date_str, '%Y%m%d')
        end_date = datetime.strptime(end_date_str, '%Y%m%d')
    except ValueError:
        print('Invalid date format. Use YYYYMMDD.')
        return

    file_list = os.listdir(target_dir)
    matched_files = []

    # 폴더 내의 파일을 순회하며 조건에 맞는 파일 찾기
    for file_name in file_list:
        if file_name.endswith('.wav'):
            # 파일명에서 날짜 부분(YYYYMMDD) 추출
            date_part = file_name.split('-')[0]
            try:
                file_date = datetime.strptime(date_part, '%Y%m%d')
                # 추출한 날짜가 검색 범위 내에 있는지 확인
                if start_date <= file_date <= end_date:
                    matched_files.append(file_name)
            except ValueError:
                # 파일명이 올바른 날짜 형식이 아니면 건너뜀
                continue

    # 결과 출력
    if matched_files:
        print(f'Records from {start_date_str} to {end_date_str}:')
        for matched_file in matched_files:
            print(matched_file)
    else:
        print(f'No records found from {start_date_str} to {end_date_str}.')


def main():
    """
    프로그램의 메인 진입점. 
    음성 녹음을 실행하고, 오늘 날짜로 저장된 파일을 검색하는 기능까지 시연합니다.
    """
    recorder = AudioRecorder()
    
    print('Starting recording for 5 seconds...')
    # 5초간 녹음 실행
    recorder.record_audio(duration=5)
    
    print('\nChecking records for today (Bonus task):')
    # 오늘 생성된 녹음 파일 검색
    today_str = datetime.now().strftime('%Y%m%d')
    find_records_in_range(today_str, today_str)


if __name__ == '__main__':
    main()
