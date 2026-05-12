import os


def load_dictionary(file_path):
    '''dictionary.txt 파일을 읽어 단어 집합을 반환한다.'''
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            words = {line.strip().lower() for line in f if line.strip()}
        return words
    except FileNotFoundError:
        print(f'경고: 사전 파일을 찾을 수 없습니다 - {file_path}')
        return set()
    except PermissionError:
        print(f'경고: 사전 파일 접근 권한이 없습니다 - {file_path}')
        return set()
    except OSError as e:
        print(f'경고: 사전 파일을 읽는 중 문제가 발생했습니다 - {e}')
        return set()


def read_password_file(file_path):
    '''password.txt 파일을 읽어 내용을 반환한다.'''
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f'오류: 파일을 찾을 수 없습니다 - {file_path}')
        return None
    except PermissionError:
        print(f'오류: 파일 접근 권한이 없습니다 - {file_path}')
        return None
    except OSError as e:
        print(f'오류: 파일을 읽는 중 문제가 발생했습니다 - {e}')
        return None


def caesar_cipher_decode(target_text, shift):
    '''카이사르 암호를 주어진 자리수(shift)로 해독한다.'''
    result = []
    for char in target_text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            decoded = chr((ord(char) - base - shift) % 26 + base)
            result.append(decoded)
        else:
            result.append(char)
    return ''.join(result)


def contains_dictionary_word(text, dictionary):
    '''해독된 텍스트에 사전 단어(3글자 이상)가 포함되어 있는지 확인한다.'''
    lower_text = text.lower()
    words = lower_text.split()
    for word in words:
        if len(word) >= 3 and word in dictionary:
            return True
    return False


def save_result(text, file_path):
    '''해독된 결과를 result.txt에 저장한다.'''
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'결과가 저장되었습니다: {file_path}')
    except PermissionError:
        print(f'오류: 파일 저장 권한이 없습니다 - {file_path}')
    except OSError as e:
        print(f'오류: 파일 저장 중 문제가 발생했습니다 - {e}')


def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    password_path = os.path.join(current_dir, '..', 'week10', 'password.txt')
    dictionary_path = os.path.join(current_dir, 'dictionary.txt')
    result_path = os.path.join(current_dir, 'result.txt')

    cipher_text = read_password_file(password_path)
    if cipher_text is None:
        return

    dictionary = load_dictionary(dictionary_path)

    print(f'암호문: {cipher_text}')
    print('-' * 40)

    auto_found_shift = None

    for shift in range(1, 27):
        decoded = caesar_cipher_decode(cipher_text, shift)
        print(f'shift {shift:2d}: {decoded}')

        if contains_dictionary_word(decoded, dictionary):
            print(f'  --> 사전 단어 발견! shift {shift}에서 자동 탐지됨')
            auto_found_shift = shift
            break

    print('-' * 40)

    if auto_found_shift is not None:
        decoded_result = caesar_cipher_decode(cipher_text, auto_found_shift)
        print(f'자동 탐지된 암호 해독 결과 (shift {auto_found_shift}): {decoded_result}')
        save_result(decoded_result, result_path)
    else:
        try:
            user_input = input('해독된 자리수를 입력하세요 (1~26): ')
            shift = int(user_input)
            if 1 <= shift <= 26:
                decoded_result = caesar_cipher_decode(cipher_text, shift)
                print(f'shift {shift} 해독 결과: {decoded_result}')
                save_result(decoded_result, result_path)
            else:
                print('오류: 1~26 사이의 숫자를 입력해야 합니다.')
        except ValueError:
            print('오류: 숫자를 입력해야 합니다.')


if __name__ == '__main__':
    main()
