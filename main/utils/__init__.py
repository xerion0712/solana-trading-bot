def append_to_log_file(text):
    with open('log.txt', 'a') as log_file:
        log_file.write(text + '\n')