from client import timeout_result

def should_retry():
    return not timeout_result()['ok']
