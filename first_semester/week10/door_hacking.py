import itertools
import multiprocessing
import os
import string
import time
import zipfile
import zlib


ZIP_FILE = 'emergency_storage_key.zip'
PASSWORD_FILE = 'password.txt'
CHARSET = string.ascii_lowercase + string.digits
PASSWORD_LENGTH = 6


def get_target_info(zf):
    file_infos = [info for info in zf.infolist() if not info.is_dir()]
    if not file_infos:
        raise ValueError('ZIP 파일에 확인할 파일이 없습니다.')
    return min(file_infos, key=lambda info: info.file_size)


def save_password(password):
    try:
        with open(PASSWORD_FILE, 'w', encoding='utf-8') as file:
            file.write(password)
        print(f'암호가 {PASSWORD_FILE}에 저장되었습니다.')
    except OSError as error:
        print(f'파일 저장 중 오류가 발생했습니다: {error}')


def check_password_chunk(args):
    zip_filepath, first_char, stop_event = args
    attempts = 0

    try:
        with zipfile.ZipFile(zip_filepath, 'r') as zf:
            target_info = get_target_info(zf)

            for guess_tuple in itertools.product(CHARSET, repeat=PASSWORD_LENGTH - 1):
                if stop_event.is_set():
                    return None, attempts

                attempts += 1
                guess = first_char + ''.join(guess_tuple)
                pwd_bytes = guess.encode('utf-8')

                try:
                    with zf.open(target_info, pwd=pwd_bytes) as file:
                        while file.read(8192):
                            pass
                    stop_event.set()
                    return guess, attempts
                except (RuntimeError, zipfile.BadZipFile, zlib.error):
                    pass
    except (FileNotFoundError, PermissionError, OSError, ValueError) as error:
        return f'error:{error}', attempts

    return None, attempts


def unlock_zip(zip_filepath=ZIP_FILE):
    start_time = time.time()
    print(f'탐색 시작 시간: {time.strftime("%Y-%m-%d %H:%M:%S")}')

    if not os.path.exists(zip_filepath):
        print(f'오류: {zip_filepath} 파일을 찾을 수 없습니다.')
        return None

    try:
        with zipfile.ZipFile(zip_filepath, 'r') as zf:
            get_target_info(zf)
    except (FileNotFoundError, PermissionError, OSError, ValueError) as error:
        print(f'오류: ZIP 파일을 열 수 없습니다: {error}')
        return None

    manager = multiprocessing.Manager()
    stop_event = manager.Event()
    tasks = [(zip_filepath, char, stop_event) for char in CHARSET]
    cpu_cores = multiprocessing.cpu_count()

    print(f'활성화된 코어 수: {cpu_cores}개')
    print('병렬 탐색을 시작합니다...')

    total_attempts = 0
    found_password = None

    with multiprocessing.Pool(processes=cpu_cores) as pool:
        for result_guess, result_attempts in pool.imap_unordered(check_password_chunk, tasks):
            total_attempts += result_attempts

            if isinstance(result_guess, str) and result_guess.startswith('error:'):
                print(result_guess[6:])
                pool.terminate()
                break

            if result_guess:
                found_password = result_guess
                pool.terminate()
                break

    elapsed = time.time() - start_time

    if found_password:
        print('[성공] 암호를 찾았습니다!')
        print(f'찾은 암호: {found_password}')
        print(f'총 반복 횟수: {total_attempts}회')
        print(f'진행 시간: {elapsed:.2f}초')
        save_password(found_password)
        return found_password

    print('모든 조합을 시도했지만 암호를 찾지 못했습니다.')
    print(f'진행 시간: {elapsed:.2f}초')
    return None


if __name__ == '__main__':
    unlock_zip()
