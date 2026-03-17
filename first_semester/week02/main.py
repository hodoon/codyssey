print('Hello Mars')


def read_log(file_path):
    '''로그 파일을 읽어 헤더와 데이터 행 목록을 반환한다.'''
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f'오류: 파일을 찾을 수 없습니다 - {file_path}')
        return None, []
    except PermissionError:
        print(f'오류: 파일 읽기 권한이 없습니다 - {file_path}')
        return None, []
    except OSError as e:
        print(f'오류: 파일을 읽는 중 문제가 발생했습니다 - {e}')
        return None, []

    if not lines:
        print('오류: 파일이 비어 있습니다.')
        return None, []

    header = lines[0].rstrip('\n')
    data_lines = [line.rstrip('\n') for line in lines[1:] if line.strip()]
    return header, data_lines


def parse_log_line(line):
    '''로그 한 줄을 파싱해 (timestamp, event, message) 튜플을 반환한다.'''
    parts = line.split(',', 2)
    if len(parts) == 3:
        return parts[0].strip(), parts[1].strip(), parts[2].strip()
    return None


def is_error_line(message):
    '''문제가 되는 로그 항목인지 판별한다.'''
    keywords = ['unstable', 'explosion', 'error', 'fail', 'critical', 'warning']
    return any(keyword in message.lower() for keyword in keywords)


def print_log(header, data_lines):
    '''로그 전체 내용을 화면에 출력한다.'''
    print(header)
    for line in data_lines:
        print(line)


def print_log_reversed(header, data_lines):
    '''로그 내용을 시간의 역순으로 정렬해 출력한다.'''
    sorted_lines = sorted(data_lines, reverse=True)
    print(header)
    for line in sorted_lines:
        print(line)


def save_error_log(data_lines, output_path):
    '''문제가 되는 로그 항목만 별도 파일로 저장한다.'''
    error_lines = []
    for line in data_lines:
        parsed = parse_log_line(line)
        if parsed and is_error_line(parsed[2]):
            error_lines.append(line)

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for line in error_lines:
                f.write(line + '\n')
        print(f'\n문제 로그 {len(error_lines)}건이 {output_path}에 저장되었습니다.')
    except PermissionError:
        print(f'오류: 파일 쓰기 권한이 없습니다 - {output_path}')
    except OSError as e:
        print(f'오류: 파일 저장 중 문제가 발생했습니다 - {e}')


def main():
    log_path = 'mission_computer_main.log'
    error_log_path = 'mission_computer_error.log'

    header, data_lines = read_log(log_path)
    if header is None:
        return

    print('\n--- 로그 전체 출력 (시간 역순) ---')
    print_log_reversed(header, data_lines)

    save_error_log(data_lines, error_log_path)


main()
